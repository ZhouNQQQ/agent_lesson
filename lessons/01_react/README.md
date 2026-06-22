# ReAct 手写练习（面试 P0）

> 目标：达到市场对 Agent 研发工程师的硬要求——**能从空白默写一个 ReAct 循环**，并讲清每个工程决策。
> 对应面试题：Q5-Q8（ReAct vs CoT、Action 失败、死循环、与 Function Calling 的关系）。

> ⚠️ **如果你还没学过 CoT/ReAct/Function Calling 这些概念，先读 [`react_lesson.md`](./react_lesson.md)（从零讲起的讲义），再回来看这份。**
> 正确学习顺序：**讲义（学概念）→ react_agent.py（看实现）→ 默写（练）→ 本 README 第 4 节（自测对答案）**。
> 本 README 是"答案/对照"，不是"教学"——直接背这里的答案过不了追问。

---

## 1. 原理速讲（30 秒能说清）

**CoT 只能"想"，ReAct 能"边想边做"。** ReAct = Reasoning + Acting：让 LLM 交错产生
`Thought`（推理下一步）和 `Action`（调用工具），工具返回 `Observation`，再喂回模型，
循环直到模型输出 `Final Answer`。

它解决 CoT 的致命伤：CoT 的推理全靠模型内部知识，**容易幻觉**；ReAct 每一步都能用工具
（检索/计算/查 API）拿到**真实外部信息**来纠偏，所以更可靠。

```
Thought → Action → Observation → Thought → Action → Observation → … → Final Answer
        （模型）   （工具）        （模型）   （工具）
```

---

## 2. 怎么跑

```bash
# 离线演示（不烧 API，看清循环机制）—— 成功路径
python react_agent.py --demo

# 离线演示 —— 工具失败 + 死循环检测
python react_agent.py --demo-fail

# 真实 GLM-4-Flash（先 pip install openai，并设置环境变量 GLM_API_KEY）
python react_agent.py "先查 Raft 是什么，再算 128/4"
```

已验证：真实 GLM 能正确走完 `search → calculator → Final Answer` 三步。

---

## 3. 四个必考工程点（代码里都标了行）

| 考点 | 面试官想听到的 | 代码位置 |
|------|---------------|---------|
| **主循环** | Thought-Action-Observation 怎么串、何时终止 | `ReActAgent.run` 5.1-5.7 |
| **Action 解析失败** | 模型没按格式输出 → 不崩溃，回注格式纠正提示让它重来 | 5.3 |
| **工具执行失败** | 工具抛异常 → 捕获后把错误当 Observation 回喂，让模型自我修正（而非整个 Agent 崩） | 5.6 |
| **死循环 + 兜底** | 同一 (action,input) 重复超阈值 → 强制终止；外加 `max_steps` 硬上限防烧钱 | 5.5 / 5.8 |

还有一个**隐藏加分点**：调用 LLM 时 `stop=["Observation:"]`——
**截断模型，绝不让它自己编造 Observation**。很多人手写时漏掉这条，模型会一口气把
"假的工具结果"也生成出来，导致整个推理建立在幻觉上。能主动讲这条，面试官会高看一眼。

---

## 4. 高频追问 Q&A（先盖住答案自己讲）

**Q：ReAct 和纯 CoT 的核心区别？**
CoT 是一条纯推理链，不与外界交互，知识截止于训练数据且易幻觉；ReAct 在推理中插入真实工具调用，
用 Observation 校正每一步。CoT 适合纯逻辑/数学题，ReAct 适合需要外部信息或多步操作的任务。

**Q：Action 失败了怎么优雅降级？**
分两类：①格式解析失败（模型没给合法 Action）→ 回注一条纠正提示，让它重新输出；
②工具执行失败（抛异常/超时）→ 捕获异常，把错误信息当作 Observation 回喂，模型据此换输入或换工具。
关键是**失败不冒泡到顶层让 Agent 崩**，而是变成循环里的一个可恢复信号。生产里还会加分类重试
（可重试错误指数退避，不可重试错误直接换路径）。

**Q：怎么判断 Agent 陷入死循环？怎么设 max_steps？**
死循环检测：记录每步的 `(action, input)` 签名，同一签名重复超过阈值（这里 2 次）就强制终止。
`max_steps` 是第二道兜底（这里 8），防止模型一直换花样但永远不收敛——**本质是成本和延迟的硬上限**。
阈值怎么定？看任务复杂度 + 单步成本：简单问答 3-5 步，复杂多工具任务可放到 10-15，再配 token 预算监控。

**Q：ReAct 和 Function Calling 是什么关系？能结合吗？**
能，而且生产里通常结合。ReAct 是**推理范式**（先想后做的循环结构）；Function Calling 是**实现机制**
（模型原生支持、用 JSON Schema 描述工具、结构化返回 tool_calls）。
这份练习用"文本协议"（`Action:`/`Action Input:`）手写解析，是为了把循环摊开给你看清楚；
生产里会把工具定义成 JSON Schema 交给模型的 function calling 接口，省掉脆弱的文本解析，更稳。
**一句话：ReAct 是骨架，Function Calling 是更可靠的关节。**

**Q：文本协议解析 vs 原生 Function Calling，各自风险？**
文本协议：实现简单、可读、不依赖模型特性，但**解析脆弱**（模型格式漂移就崩，要靠正则容错 + 纠正回注）。
原生 FC：结构化、稳，但依赖模型支持，且 schema 设计本身影响调用准确率（工具描述写不好模型会选错/传错参）。

---

## 5. 和记忆系统串联（面试讲故事用）

把"ReAct 循环"和"记忆做成 MCP 工具"接起来讲，就是一个完整的 Agent 故事。
假设有一个记忆框架暴露了 MCP server（`memory_add/search/compact`）：

> "我不仅理解 ReAct 循环，还把记忆做成了 **MCP 工具**。一个 ReAct Agent 在 Action 阶段
> 可以调用 `memory_search` 把长期记忆拉进上下文，在对话结束调用 `memory_add` 沉淀新记忆——
> ReAct 负责'怎么决策调哪个工具'，MCP 负责'工具怎么被标准化暴露'，记忆层负责'跨会话不失忆'。"

这一下把 **推理框架 + 工具协议 + 记忆系统** 三个高频考点串成了你一个人的端到端实践，区分度极高。

---

## 6. 默写挑战（真正练到"能手写"）

看懂 ≠ 会写。建议：
1. 读完 `react_agent.py` 的 `ReActAgent.run`，合上文件。
2. 拿白纸/空文件，从零默写主循环骨架：messages 初始化 → for max_steps → call llm(stop) →
   parse → final? → action 合法? → 死循环? → 执行(try/except) → 回喂 observation。
3. 写完和原文件对照，标记漏掉的分支（大概率漏 `stop=Observation` 和"解析失败回注"）。
4. 对着第 4 节的 Q&A，每题脱稿讲 30 秒。

能默写出骨架 + 答对 4 个追问 = 这块 P0 过关。
