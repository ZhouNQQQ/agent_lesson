# AutoGen 学习笔记：多 Agent 对话框架

> 学习日期：2026-06-16
> 来源：AutoGen 官方文档 + 多个教程整理
> 用途：AI Agent 记忆系统学习

---

## 一、AutoGen 是什么

**一句话：** AutoGen 是 **Microsoft 开源的多 Agent 对话框架**，让多个 AI Agent 可以像微信群一样互相聊天、协作完成任务。

**类比：**
- LangGraph = 用"图"定义工作流（节点是操作，边是流转）
- AutoGen = 用"对话"定义工作流（Agent 是参与者，消息是流转）

---

## 二、核心概念（3 个）

| 概念 | 是什么 | 作用 |
|------|--------|------|
| **Agent** | 对话参与者 | 可以是 LLM（智能体）、人类（用户）、工具（代码执行器） |
| **Conversation** | 对话 | 两个 Agent 之间的消息交换 |
| **GroupChat** | 群聊 | 多个 Agent 在一个群里，由 Manager 决定谁发言 |

---

## 三、典型用法（两个 Agent 对话）

```python
from autogen import ConversableAgent

# 定义两个 Agent
assistant = ConversableAgent(
    name="assistant",
    system_message="你是一个编程助手",
    llm_config={"model": "gpt-4"}
)

user_proxy = ConversableAgent(
    name="user_proxy",
    system_message="你代表用户，可以执行代码",
    human_input_mode="NEVER"
)

# 启动对话
user_proxy.initiate_chat(
    assistant,
    message="写一个 Python 函数，计算斐波那契数列"
)
```

---

## 四、多 Agent 群聊（GroupChat）

```python
from autogen import GroupChat, GroupChatManager

# 定义多个 Agent
planner = ConversableAgent(name="planner", system_message="你负责规划")
coder = ConversableAgent(name="coder", system_message="你负责写代码")
reviewer = ConversableAgent(name="reviewer", system_message="你负责代码审查")

# 创建群聊
groupchat = GroupChat(
    agents=[planner, coder, reviewer],
    messages=[],
    max_round=10
)

# 群聊管理器：决定下一个谁发言
manager = GroupChatManager(groupchat=groupchat)

# 启动群聊
user_proxy.initiate_chat(manager, message="开发一个 REST API")
```

---

## 五、AutoGen 和 Manus 的区别

| | AutoGen | Manus |
|--|---------|-------|
| **驱动方式** | 对话驱动（Agent 之间聊天） | 任务驱动（Agent 执行工具） |
| **交互方式** | 消息传递 | 工具调用 |
| **Agent 关系** | 平等对话（像微信群） | 层级分工（规划→执行→验证） |
| **适用场景** | 协作式任务（讨论、头脑风暴） | 执行式任务（调研、生成报告） |
| **运行环境** | 本地/服务器 | 云端虚拟机 |

**类比：**
- AutoGen = 一群程序员在会议室里讨论方案（对话协作）
- Manus = 项目经理分配任务，各执行者完成（任务执行）

---

## 六、AutoGen 和 LangGraph 的区别

| | AutoGen | LangGraph |
|--|---------|-----------|
| **编排方式** | 对话编排（消息驱动） | 图编排（节点+边） |
| **Agent 交互** | Agent 之间直接对话 | Agent 通过 State 间接交互 |
| **循环控制** | 群聊管理器决定发言顺序 | 条件边决定流转路径 |
| **状态管理** | 对话历史（消息列表） | State 对象（结构化数据） |
| **可视化** | 对话记录 | 图结构 |

**关系：**
- AutoGen 的 GroupChat 可以用 LangGraph 的图来实现
- 但 AutoGen 更强调"对话"的灵活性，LangGraph 更强调"流程"的可控性

---

## 七、适用场景

| 场景 | 适合用 AutoGen？ | 为什么 |
|------|-----------------|--------|
| 简单问答（如"什么是 Python"） | ❌ 不适合 | 一个 LLM 直接回答，不需要多 Agent |
| 协作讨论（如"设计一个系统架构"） | ✅ 非常适合 | 需要多个 Agent 角色互相讨论 |
| 复杂执行任务（如"生成一份市场报告"） | ⚠️ 可以用但不是最优 | Manus/LangGraph 更适合 |
| 代码审查 | ✅ 适合 | 开发者 Agent + 审查者 Agent 对话 |

---

## 八、一句话总结

> **AutoGen 是 Microsoft 开源的多 Agent 对话框架，核心是让多个 Agent 像微信群一样协作。和 LangGraph 的区别：AutoGen 是对话编排，LangGraph 是图编排。和 Manus 的区别：AutoGen 是对话驱动（讨论），Manus 是任务驱动（执行）。AutoGen 最适合多角色协作讨论的场景。**

---

## 九、面试考点

| 问题 | 答案 |
|------|------|
| AutoGen 是什么？ | Microsoft 开源的多 Agent 对话框架，让多个 Agent 像微信群一样协作 |
| AutoGen 和 LangGraph 的区别？ | AutoGen 是对话编排（消息驱动），LangGraph 是图编排（节点+边） |
| AutoGen 和 Manus 的区别？ | AutoGen 是对话驱动（讨论协作），Manus 是任务驱动（工具执行） |
| GroupChat 怎么工作？ | 多个 Agent 在群里，GroupChatManager（主持人）决定下一个谁发言 |
| AutoGen 适合什么场景？ | 多角色协作讨论（如系统架构设计、代码审查），不适合简单问答或确定性执行任务 |

---

> 延伸阅读：
> - 官方文档：`https://microsoft.github.io/autogen/`
> - GitHub：`https://github.com/microsoft/autogen`
