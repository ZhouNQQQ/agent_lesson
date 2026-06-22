# AutoGen 普及：多 Agent 对话框架

> 学习文档 | 课程标题：AutoGen 普及：多 Agent 对话框架
> 课程目标：理解 AutoGen 是什么、多 Agent 对话模式、和 Manus/LangGraph 的区别
> 日期：2026-06-16

---

## 一句话总结

AutoGen 是微软开源的多 Agent 框架，核心范式是**让多个 Agent 像人一样"对话"来协作完成任务**——你不写流程图，而是定义一群会说话的 Agent，让它们在群聊里你来我往，自然推进任务。

---

## 一、AutoGen 是什么

**AutoGen** 是 Microsoft Research 开源的多 Agent 编排框架（`pyautogen`），用来构建由多个 LLM Agent 协作的应用。

- **定位**：多 Agent 协作 + 人机协作。不是单 Agent 工具调用，而是一群 Agent 互相对话。
- **核心理念**：把复杂任务拆给多个"角色"（写代码的、审代码的、跑代码的、当用户的），让它们通过**自然语言消息**互相沟通，像开会一样推进。
- **关键能力**：对话编排、可插入人类（human-in-the-loop）、可执行代码、可调用工具。

> 注：AutoGen 0.2（`ConversableAgent`/`GroupChat`）是最广泛使用的经典版本；0.4 之后重构为 actor 模型的事件驱动架构（`autogen-agentchat` / `autogen-core`）。本文以经典的"对话驱动"心智模型讲解，这是理解 AutoGen 本质的最佳切入点。

---

## 二、核心概念

### 1. Agent（对话参与者）

Agent 是一个**能收发消息**的对话参与者。最基础的两类：

| Agent 类型 | 角色 | 典型用途 |
|-----------|------|---------|
| `AssistantAgent` | AI 助手，由 LLM 驱动 | 写代码、出方案、回答问题 |
| `UserProxyAgent` | 代表"用户"的代理 | 转达人类输入、执行代码、决定是否继续 |

关键点：**每个 Agent 都有 `send()` 和 `receive()`**。对话的本质就是 Agent 之间互相 `send` 消息、`receive` 后产生回复。

```python
from autogen import AssistantAgent, UserProxyAgent

assistant = AssistantAgent(name="coder", llm_config={"model": "gpt-4"})
user_proxy = UserProxyAgent(
    name="user",
    human_input_mode="NEVER",      # 不等真人输入，全自动
    code_execution_config={"work_dir": "coding"},  # 能跑代码
)
```

### 2. Conversation（对话）

两个 Agent 之间的**消息往返序列**就是一次 Conversation。用 `initiate_chat()` 发起：

```python
user_proxy.initiate_chat(
    assistant,
    message="写一个快速排序并测试它",
)
```

发起后，两个 Agent 自动来回对话：assistant 写代码 → user_proxy 执行 → 报错就反馈 → assistant 修复……直到任务完成或触发终止条件。**这就是"对话驱动"**：没有人写"先做 A 再做 B"的流程，推进完全靠对话本身。

### 3. GroupChat（多 Agent 群聊管理）

当参与者超过两个，就需要 `GroupChat` + `GroupChatManager` 来管理"谁该发言"：

```python
from autogen import GroupChat, GroupChatManager

groupchat = GroupChat(
    agents=[user_proxy, coder, reviewer, tester],
    messages=[],
    max_round=20,
)
manager = GroupChatManager(groupchat=groupchat, llm_config={"model": "gpt-4"})
user_proxy.initiate_chat(manager, message="开发并测试一个登录接口")
```

- **GroupChat**：维护参与者名单 + 共享消息历史。
- **GroupChatManager**：群聊"主持人"，负责 **speaker selection（选下一个发言人）**。
- **发言人选择策略**：`auto`（LLM 根据上下文挑）、`round_robin`（轮流）、`random`、`manual`（人选）。

---

## 三、多 Agent 模式

### 模式 1：两个 Agent 对话（Two-Agent Chat）

最简单形态。一个 `AssistantAgent` + 一个 `UserProxyAgent`，反复对话直到任务完成。

```
user_proxy  ──"写快排"──▶  assistant
user_proxy  ◀──代码──────  assistant
（user_proxy 执行代码，报错）
user_proxy  ──"报错X"──▶   assistant
user_proxy  ◀──修复──────  assistant
... 直到通过
```

适用：代码生成+执行、问答+校验等简单闭环。

### 模式 2：多个 Agent 群聊（Group Chat）

多个角色在一个群里协作，由 Manager 调度发言顺序。

```
                ┌──────────────────┐
                │  GroupChatManager │  ← 选下一个发言人
                └────────┬──────────┘
        ┌────────┬───────┼────────┬─────────┐
   user_proxy  coder  reviewer  tester   (共享消息历史)
```

适用：软件开发团队模拟（产品/开发/测试/审查）、辩论、多视角分析。

### 模式 3：嵌套对话（Nested Chat）

一个 Agent 在回复主对话前，**先在内部发起一段子对话**，把子对话结论"打包"成自己的回复。对外是一个 Agent，对内是一整个团队。

```
主对话:  A ──▶ B ──▶ C
                │
                └─(B 收到消息后，内部触发嵌套对话)
                   B ⇄ 内部Agent1 ⇄ 内部Agent2
                   └─ 内部讨论出结果，B 把结论返回主对话
```

适用：封装复杂子流程（如"审查"内部其实是多个专家讨论），对外保持接口简洁。通过 `register_nested_chats()` 注册。

---

## 四、和 Manus 的区别：对话驱动 vs 任务驱动

| 维度 | AutoGen（对话驱动） | Manus（任务驱动） |
|------|---------------------|-------------------|
| 核心范式 | 多 Agent **对话**协作 | 单 Agent **规划-执行**任务 |
| 推进方式 | 靠 Agent 间消息往返自然推进 | 靠任务分解 + 待办清单逐项执行 |
| 控制单元 | 一条条消息（message） | 一个个任务步骤（task/step） |
| 心智模型 | 一群人在"开会讨论" | 一个人拿着"待办清单"干活 |
| 终止条件 | 对话满足终止词 / 达到 max_round | 任务清单全部完成 |
| 典型场景 | 多视角协作、辩论、人机协同 | 端到端自动化交付（如自动做完一个项目） |

**一句话**：AutoGen 关心"谁该说话、说什么"；Manus 关心"下一步该做什么任务"。前者像群聊，后者像项目经理推进 todo。

---

## 五、和 LangGraph 的区别：对话编排 vs 图编排

| 维度 | AutoGen（对话编排） | LangGraph（图编排） |
|------|---------------------|---------------------|
| 编排单元 | 对话消息 + 发言人选择 | 图的节点（Node）和边（Edge） |
| 流程定义 | **隐式**：Manager 动态选发言人 | **显式**：预先画好状态图，定义节点跳转 |
| 控制粒度 | 粗（让 Agent 自由对话） | 细（每条边、每个条件都可控） |
| 状态管理 | 共享对话历史（messages） | 显式 State 对象在节点间流转 |
| 可预测性 | 较低（LLM 决定流向） | 高（图结构固定，分支可控） |
| 心智模型 | "一群 Agent 在群里讨论" | "数据在状态机/流程图里流动" |
| 适用场景 | 探索性、协作式、对话式任务 | 需要严格流程控制、可回溯、可分支的工作流 |

**一句话**：AutoGen 用"对话"组织 Agent，流程由对话动态涌现；LangGraph 用"图"组织节点，流程在运行前就被精确定义。要灵活协作选 AutoGen，要可控可预测选 LangGraph。

---

## 六、三者对比速查表

| 框架 | 编排范式 | 核心抽象 | 一句话记忆 |
|------|---------|---------|-----------|
| **AutoGen** | 对话驱动 / 对话编排 | Agent + GroupChat | 让 Agent 像人一样开会讨论 |
| **Manus** | 任务驱动 | Task / Plan + 待办清单 | 一个 Agent 照着 todo 干完活 |
| **LangGraph** | 图编排 | Node / Edge / State | 数据在流程图里按边流动 |

---

## 七、面试 / 追问要点

| 追问 | 答案 |
|------|------|
| AutoGen 怎么决定谁发言？ | GroupChatManager 的 speaker selection：auto（LLM 选）/ round_robin / random / manual |
| 对话不会无限循环吗？ | 靠 `max_round` 上限 + 终止词（`is_termination_msg`）+ `max_consecutive_auto_reply` |
| 怎么加入人类？ | UserProxyAgent 的 `human_input_mode`：ALWAYS / TERMINATE / NEVER |
| AutoGen 能执行代码吗？ | 能，UserProxyAgent 配 `code_execution_config`，自动跑 LLM 写的代码并回传结果 |
| 为什么不用 LangGraph？ | 当流程难以预先画成图、需要 Agent 自由协作/辩论时，对话驱动更自然 |
| 嵌套对话解决什么？ | 把复杂子流程封装成单个 Agent 的"内部团队"，对外保持简洁接口 |

---

## 关键记忆点

- AutoGen = 微软开源 + 多 Agent + **对话驱动**
- 三核心：**Agent**（会说话的参与者）、**Conversation**（消息往返）、**GroupChat**（群聊调度）
- 三模式：**两 Agent 对话** → **多 Agent 群聊** → **嵌套对话**
- vs Manus：对话驱动 vs 任务驱动（群聊 vs todo 清单）
- vs LangGraph：对话编排 vs 图编排（动态涌现 vs 预定义图）
