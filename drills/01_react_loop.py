"""
手撕题 1：ReAct 执行循环（最高频）

面试场景：面试官让你现场写一个 ReAct 循环。
本文件是"面试最小模板"——结构最精简、便于默写；完整生产版（含死循环检测、stop 截断、
分类重试等）见 ../lessons/01_react/react_agent.py。

要求（面试官常加的约束）：处理格式错误（重试 3 次）、限制最多 5 步、支持 FinalAnswer 终止。

注：parse_action / execute_tool 是约定省略的 helper，本文件重点是主干结构与每行意图。
"""


# 主入口：用户问题、可用工具集、LLM 客户端、最大步数（默认 5）
def react_agent_executor(user_query, tools, llm, max_steps=5):
    # ★ 关键：必须把"工具清单(名字+描述)"告诉 LLM，否则它不知道有哪些工具、无法在 Action 里点名。
    #   文本协议做法 = 把工具描述拼进 system prompt；下面 _generate_with_retry 会把 tools 一起带上。
    context = []                                    # 累积每一步的 (thought, observation)，作为"工作记忆"喂给下一轮；模型靠它不失忆
    for step in range(max_steps):                   # 主循环：最多走 max_steps 步 —— 兜底①，防止不收敛无限烧钱
        response = _generate_with_retry(llm, user_query, context, tools)  # 调 LLM 生成"Thought+Action"文本（把 tools 一并喂给它 + 格式错误重试）
        action = parse_action(response)             # 把自由文本解析成结构化 Action（含 type / tool / args / thought）
        if action.type == "FinalAnswer":            # 终止条件：模型判断已经能回答了
            return action.content                   # 返回最终答案，结束整个循环
        observation = execute_tool(action, tools)   # 执行工具拿"真实结果"——Observation 必须由代码产生，绝不能让模型自己编（否则幻觉）
        context.append({                            # 把这一回合写回工作记忆：
            "thought": action.thought,              #   模型这一步的推理
            "observation": observation,             #   工具返回的真实观察
        })                                          # 下一轮 LLM 读到它，才知道"我刚做了什么、得到了什么"
    return "达到最大步数限制"                          # 跑满 max_steps 仍无 FinalAnswer → 兜底②，明确返回而不是无声卡死


# 把"格式错误重试 3 次"单独抽出来（对应要求里的"处理格式错误，重试 3 次"）
def _generate_with_retry(llm, user_query, context, tools, max_parse_retries=3):
    # 把工具清单拼进提示，让 LLM 知道有哪些工具可选（否则它点不出合法的 Action）
    prompt = _build_prompt(user_query, context, tools)  # system 段含"可用工具:<名字+描述>" + 历史 + 当前问题
    for attempt in range(max_parse_retries):        # 最多重试 3 次解析
        response = llm.generate(prompt)             # 调 LLM 生成一步输出（工具信息已在 prompt 里）
        try:                                        # 尝试解析，验证格式合法
            parse_action(response)                  # 解析失败会抛异常（说明模型没按 Thought/Action 格式输出）
            return response                         # 格式 OK，直接返回原始输出给主循环再次解析使用
        except Exception:                           # 解析失败（格式错误）
            if attempt == max_parse_retries - 1:    # 已是最后一次
                raise                               # 重试用尽仍失败 → 抛出，交由上层处理
            continue                                # 否则进入下一次重试，让模型重新生成


# 构造提示：把"工具清单 + 历史上下文 + 当前问题"组装成给 LLM 的输入。
# 这一步就是工具到达 LLM 的途径①（文本协议）。途径②是 Function Calling（tools= 参数走 schema）。
def _build_prompt(user_query, context, tools):
    tools_desc = "\n".join(f"- {t.name}: {t.description}" for t in tools)  # 列出每个工具的名字+描述
    return (
        f"你是 ReAct 智能体。可用工具：\n{tools_desc}\n"   # ← 没有这段，模型不知道有哪些工具
        f"按 Thought/Action/Action Input 格式作答，能回答时用 Final Answer。\n"
        f"历史：{context}\n问题：{user_query}"
    )
