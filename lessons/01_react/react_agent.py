"""
ReAct Agent —— 手写 Thought-Action-Observation 循环（面试练习版）

目标：面试要求"能手写 ReAct 循环"。这份实现刻意不依赖 LangChain，
把循环的每一步都摊开，覆盖 4 个工程考点：
  1. Thought-Action-Observation 主循环
  2. Action 解析失败的处理（模型没按格式输出怎么办）
  3. 工具执行失败的处理（工具抛异常怎么办）
  4. 死循环检测 + max_steps 兜底（Agent 反复做同一件事怎么办）

两种 LLM 后端：
  - GLMBackend：真实调用 GLM-4-Flash（从环境变量或本地 .env 读取 GLM_API_KEY）
  - ScriptedBackend：离线脚本后端，确定性演示循环机制（学习/讲解用，不烧 API）

运行：
  python react_agent.py --demo                # 离线演示，看清循环机制
  python react_agent.py "23 乘以 17 再加 100 等于多少？"   # 真实 GLM
  python react_agent.py --demo-fail           # 演示工具失败 + 死循环检测
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional


# ===========================================================================
# 0. 极简 .env 加载（无需 python-dotenv）
# ===========================================================================

def load_env_from_dotenv() -> None:
    """从本地 .env 读 GLM_API_KEY 等，写进 os.environ（不覆盖已有）。
    查找顺序：环境变量 GLM_DOTENV 指定路径 → 当前目录 .env → 仓库根目录 .env。
    """
    candidates = [
        os.environ.get("GLM_DOTENV", ""),
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
    ]
    for path in candidates:
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                os.environ.setdefault(k, v)
        break


# ===========================================================================
# 1. 工具注册表（生产里这层就是 Tool Registry / Function Schema）
# ===========================================================================

@dataclass
class Tool:
    name: str
    description: str
    func: Callable[[str], str]


TOOLS: Dict[str, Tool] = {}


def tool(name: str, description: str):
    """注册一个工具。工具签名统一为 (str) -> str，便于手写循环里调用。"""
    def deco(fn: Callable[[str], str]) -> Callable[[str], str]:
        TOOLS[name] = Tool(name=name, description=description, func=fn)
        return fn
    return deco


@tool("calculator", "做算术计算。输入一个数学表达式字符串，如 '23*17+100'。")
def calculator(expr: str) -> str:
    # 安全求值：只允许数字和运算符，杜绝任意代码执行（面试安全考点）
    if not re.fullmatch(r"[\d\s+\-*/().]+", expr):
        raise ValueError(f"非法表达式: {expr!r}，只允许数字和 + - * / ( )")
    return str(eval(expr, {"__builtins__": {}}, {}))  # noqa: S307 已做字符白名单


# 一个确定性的"知识库检索"工具（mock 数据，自包含，可复现）
_KB = {
    "raft": "Raft 是一种分布式共识算法，通过 Leader 选举 + 日志复制保证一致性，比 Paxos 更易理解。",
    "mcp": "MCP（Model Context Protocol）是 Anthropic 提出的标准协议，让 Agent 用统一方式接入工具/资源。",
    "react": "ReAct = Reasoning + Acting，让 LLM 交错产生推理(Thought)和动作(Action)，边想边做。",
}


@tool("search", "检索知识库。输入一个关键词，返回相关解释。已收录: raft / mcp / react。")
def search(query: str) -> str:
    key = query.strip().lower()
    for k, v in _KB.items():
        if k in key:
            return v
    return f"知识库中未找到与 '{query}' 相关的内容。"


@tool("flaky_tool", "一个故意会失败的工具，用于演示工具异常处理。")
def flaky_tool(arg: str) -> str:
    raise RuntimeError("外部服务 503 不可用（这是演示用的故意失败）")


def tools_description() -> str:
    return "\n".join(f"- {t.name}: {t.description}" for t in TOOLS.values())


# ===========================================================================
# 2. ReAct Prompt（文本协议版，对应"手写"而非原生 Function Calling）
# ===========================================================================

REACT_SYSTEM_PROMPT = """你是一个 ReAct 智能体。你通过"思考-行动-观察"循环来解决问题。

可用工具：
{tools}

你必须严格按以下格式输出，每次只走一步：

Thought: <你的推理，说明下一步要做什么>
Action: <工具名，必须是上面列表里的一个>
Action Input: <传给工具的输入字符串>

然后停下，等待系统返回：
Observation: <工具执行结果>

如此循环。当你已经能回答时，输出：

Thought: <最后的推理>
Final Answer: <给用户的最终答案>

规则：
- 一次只输出一个 Thought + 一个 Action（或 Final Answer），不要自己编造 Observation。
- Action 必须是工具列表里的名字，Action Input 是纯文本，不要加引号或 JSON 包裹。
- 如果工具返回错误，分析原因，换个输入或换个工具，不要重复同样的失败调用。
"""


# ===========================================================================
# 3. 解析模型输出（手写循环的关键：把自由文本切成结构化动作）
# ===========================================================================

@dataclass
class Step:
    thought: str
    action: Optional[str]
    action_input: Optional[str]
    final_answer: Optional[str]


def parse_step(text: str) -> Step:
    """从模型输出里抽取 Thought / Action / Action Input / Final Answer。"""
    thought = _grab(text, r"Thought:\s*(.*?)(?=\n(?:Action|Final Answer):|$)")
    final = _grab(text, r"Final Answer:\s*(.*)")
    if final:
        return Step(thought=thought, action=None, action_input=None, final_answer=final.strip())
    action = _grab(text, r"Action:\s*(.*?)(?=\n|$)")
    action_input = _grab(text, r"Action Input:\s*(.*?)(?=\n(?:Observation|Thought):|$)")
    return Step(
        thought=thought,
        action=action.strip() if action else None,
        action_input=action_input.strip() if action_input else None,
        final_answer=None,
    )


def _grab(text: str, pattern: str) -> str:
    m = re.search(pattern, text, re.DOTALL)
    return m.group(1).strip() if m else ""


# ===========================================================================
# 4. LLM 后端
# ===========================================================================

LLM = Callable[[List[dict], Optional[List[str]]], str]


def glm_backend() -> LLM:
    """真实 GLM-4-Flash 后端。注意 stop=['Observation:'] 防止模型自己幻觉出观察结果。"""
    from openai import OpenAI

    load_env_from_dotenv()
    api_key = os.getenv("GLM_API_KEY") or os.getenv("ZHIPU_API_KEY") or os.getenv("KIMI_API_KEY")
    if not api_key:
        raise ValueError("缺少 API key：请设置环境变量 GLM_API_KEY（或在 .env 中配置）")
    client = OpenAI(api_key=api_key, base_url=os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"))

    def call(messages: List[dict], stop: Optional[List[str]]) -> str:
        resp = client.chat.completions.create(
            model=os.getenv("GLM_MODEL", "glm-4-flash"),
            messages=messages,
            temperature=0.1,
            stop=stop,
            max_tokens=1024,
        )
        return resp.choices[0].message.content or ""

    return call


def scripted_backend(script: List[str]) -> LLM:
    """离线脚本后端：按预设台词逐步返回，确定性演示循环机制（不烧 API）。"""
    state = {"i": 0}

    def call(messages: List[dict], stop: Optional[List[str]]) -> str:
        i = state["i"]
        state["i"] += 1
        return script[i] if i < len(script) else "Thought: 我已经有答案了。\nFinal Answer: (脚本结束)"

    return call


# ===========================================================================
# 5. ReAct 主循环 —— 面试要默写的核心
# ===========================================================================

class ReActAgent:
    """ReAct 智能体 —— 一个"带外部调用的 while 循环"状态机。

    核心心智模型（面试默写时先在脑子里建好这张图）：
        初始化对话(system+user)
          └─> 循环最多 max_steps 次：
                1) 让 LLM 走一步（生成 Thought + Action，stop 在 Observation 处截断）
                2) 若是 Final Answer  → 返回，循环结束
                3) 否则解析出 Action  → 校验(格式/工具存在/是否死循环)
                4) 执行工具拿真实结果 → 包装成 Observation
                5) 把"本轮模型输出 + Observation"追加进对话 → 进入下一轮
          └─> 跑满 max_steps 仍无答案 → 兜底返回

    关键不变量：`messages` 这条对话列表就是 Agent 的"工作记忆"。
    每一轮把 (assistant 的思考/动作) 和 (user 角色承载的 Observation) 不断 append 进去，
    模型靠读这条越来越长的历史来决定下一步——这就是 ReAct 的"短期记忆"，没有它模型会失忆。
    """

    def __init__(self, llm: LLM, max_steps: int = 8, loop_threshold: int = 2, verbose: bool = True):
        # llm: 可替换的后端（真实 GLM 或离线脚本），签名统一为 (messages, stop) -> str
        self.llm = llm
        # max_steps: 硬上限，第一道兜底。防止模型一直换花样不收敛，把 token/钱/延迟烧爆
        self.max_steps = max_steps
        # loop_threshold: 同一个 (action, input) 重复几次就判定死循环。第二道兜底
        self.loop_threshold = loop_threshold
        self.verbose = verbose

    def run(self, question: str) -> str:
        # ---- 初始化"工作记忆"：system 装协议+工具清单，user 装本次问题 ----
        # system prompt 在这里注入"可用工具列表"，模型才知道自己能调哪些 Action
        system = REACT_SYSTEM_PROMPT.format(tools=tools_description())
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"问题：{question}"},
        ]
        # 死循环检测用：记录每一步的 (action|input) 签名，统计重复次数
        action_history: List[str] = []

        # ---- 主循环：每一圈 = 一个 Thought→Action→Observation 回合 ----
        for step_no in range(1, self.max_steps + 1):
            # 5.1 让 LLM 走一步。
            #     stop=["Observation:"] 是这里最关键的一行：强制模型生成到"Observation:"前就停，
            #     把"执行工具"的控制权交回给我们的代码。否则模型会一口气把"假的工具结果"也脑补出来，
            #     后续推理就建立在幻觉数据上（详见 react_lesson.md 坑 1）。
            raw = self.llm(messages, ["Observation:"])
            # 把模型吐的自由文本切成结构化的 Thought / Action / Action Input / Final Answer
            step = parse_step(raw)
            self._log(f"\n── Step {step_no} ──")
            if step.thought:
                self._log(f"Thought: {step.thought}")

            # 5.2 终止条件：模型认为可以回答了，输出了 Final Answer → 直接返回，结束循环
            if step.final_answer is not None:
                self._log(f"Final Answer: {step.final_answer}")
                return step.final_answer

            # 5.3 【容错·格式失败】模型没给出合法 Action（既不是 Final Answer 也没有 Action）。
            #     不崩溃：把一条"格式不对，请重来"的提示当 Observation 回喂，让模型自我纠正后重试。
            #     注意：先 append 模型这次的原始输出(assistant)，再 append 纠正提示(user)，
            #     保证对话历史里"模型说了啥 + 系统反馈了啥"成对出现，模型下一轮才看得懂上下文。
            if not step.action:
                self._log("⚠️ 未解析出 Action，回注格式纠正提示")
                messages.append({"role": "assistant", "content": raw})
                messages.append({"role": "user", "content":
                    "Observation: 解析失败——你没有按格式输出 Action。请用 'Action: <工具名>' 和 "
                    "'Action Input: <输入>'，或用 'Final Answer:' 给出答案。"})
                continue  # 不执行任何工具，直接进下一轮让模型重答

            # 5.4 【容错·未知工具】模型选了一个不存在的工具名（幻觉出工具）。
            #     同样不崩溃：告诉它有哪些可用工具，让它重选。
            if step.action not in TOOLS:
                self._log(f"⚠️ 未知工具: {step.action}")
                obs = f"工具 '{step.action}' 不存在。可用工具：{', '.join(TOOLS)}。"
                messages.append({"role": "assistant", "content": raw})
                messages.append({"role": "user", "content": f"Observation: {obs}"})
                continue

            # 5.5 【兜底·死循环检测】模型可能固执地反复调同一个工具+同样参数，永不收敛。
            #     用 (action|input) 签名计数，超过阈值就强制终止。类比：幂等键去重 + 熔断。
            sig = f"{step.action}|{step.action_input}"
            action_history.append(sig)
            if action_history.count(sig) > self.loop_threshold:
                self._log(f"🛑 检测到死循环：'{sig}' 重复 {action_history.count(sig)} 次，强制终止")
                return (f"[终止] Agent 陷入死循环，反复调用 {step.action}('{step.action_input}')。"
                        f"最后一次结果见上文。")

            # 5.6 【执行 + 容错·工具异常】真正调用工具拿"真实外部结果"。
            #     工具可能抛异常（超时/参数非法/外部 503）。用 try/except 兜住，
            #     把异常转成一条 Observation 回喂，让模型决定换参数还是换工具，
            #     而不是让异常冒泡把整个 Agent 干崩（类比：把下游异常包装成业务结果给上游决策）。
            self._log(f"Action: {step.action}  |  Action Input: {step.action_input}")
            try:
                result = TOOLS[step.action].func(step.action_input or "")
                obs = str(result)
            except Exception as e:
                obs = f"工具执行出错：{type(e).__name__}: {e}"
            self._log(f"Observation: {obs}")

            # 5.7 把这一回合写回"工作记忆"：
            #     - assistant: 模型本轮的原始输出（含 Thought/Action）
            #     - user:      工具返回的真实 Observation（这里 Observation 是"真实外部事实"，所以必须由代码产生，不能让模型编）
            #     下一轮模型读到这两条，就知道"我刚做了什么、得到了什么"，据此继续推理。
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": f"Observation: {obs}"})

        # 5.8 【兜底·步数耗尽】跑满 max_steps 还没拿到 Final Answer。
        #     说明问题太难/工具设计有问题/模型在绕圈。返回明确的终止信息，避免无声卡死。
        self._log(f"🛑 达到 max_steps={self.max_steps}，未得到最终答案")
        return f"[终止] 在 {self.max_steps} 步内未能得到最终答案，请检查问题或工具设计。"

    def _log(self, msg: str) -> None:
        # verbose=True 时打印每一步，方便你观察 Thought→Action→Observation 的流动
        if self.verbose:
            print(msg)


# ===========================================================================
# 6. 入口
# ===========================================================================

def _demo_script_success() -> List[str]:
    # 演示：算术 → 检索 → 给答案（确定性，不依赖网络）
    return [
        "Thought: 用户要算 23*17+100，我先用 calculator。\nAction: calculator\nAction Input: 23*17+100\n",
        "Thought: 结果是 491。问题已解决。\nFinal Answer: 23 乘以 17 再加 100 等于 491。\n",
    ]


def _demo_script_fail() -> List[str]:
    # 演示：工具失败 + 死循环检测（故意反复调 flaky_tool）
    fail = "Thought: 我调用 flaky_tool 试试。\nAction: flaky_tool\nAction Input: go\n"
    return [fail, fail, fail, fail]


def main() -> None:
    p = argparse.ArgumentParser(description="ReAct Agent 手写练习")
    p.add_argument("question", nargs="?", help="要解决的问题（不传则需加 --demo）")
    p.add_argument("--demo", action="store_true", help="离线演示：成功路径")
    p.add_argument("--demo-fail", action="store_true", help="离线演示：工具失败 + 死循环检测")
    args = p.parse_args()

    if args.demo:
        agent = ReActAgent(scripted_backend(_demo_script_success()))
        print("【离线演示 · 成功路径】")
        print("\n最终返回:", agent.run("23 乘以 17 再加 100 等于多少？"))
    elif args.demo_fail:
        agent = ReActAgent(scripted_backend(_demo_script_fail()), loop_threshold=2)
        print("【离线演示 · 工具失败 + 死循环检测】")
        print("\n最终返回:", agent.run("调用那个会失败的工具"))
    elif args.question:
        agent = ReActAgent(glm_backend())
        print(f"【真实 GLM-4-Flash】问题：{args.question}")
        print("\n最终返回:", agent.run(args.question))
    else:
        p.print_help()


if __name__ == "__main__":
    main()
