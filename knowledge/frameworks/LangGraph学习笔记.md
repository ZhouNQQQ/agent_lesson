# LangGraph 学习笔记：图编排 Agent 工作流

> 学习日期：2026-06-14  
> 来源：LangGraph 官方文档 + 多个教程综合整理  
> 用途：AI Agent 记忆系统学习

---

## 一、LangGraph 是什么

**一句话：** LangGraph 是 LangChain 生态中的**图编排框架**，用"节点（Node）+ 边（Edge）+ 状态（State）"来定义 Agent 的工作流。

**为什么需要图？** 普通函数调用是线性的，图支持：
- **循环**（反思重试）
- **条件分支**（if/else）
- **并行执行**
- **状态持久化**（Checkpoint）
- **人工介入**（human-in-the-loop）

---

## 二、核心概念（4 个）

### 1. State（状态）

**是什么：** 全局共享的数据结构，所有节点都能读和写。像 Git 的仓库，每次提交后状态更新。

**关键点：**
- State 是可序列化的（能存到磁盘/数据库）
- 每个节点返回的是 **State 的增量更新**（不是完整替换）
- LangGraph 会自动合并增量到全局 State

```python
class AgentState(TypedDict):
    messages: list          # 对话历史
    user_query: str         # 用户问题
    retrieved_docs: list    # 检索到的文档
    final_answer: str       # 最终答案
```

### 2. Node（节点）

**是什么：** 一个函数，接收 State，返回 State 的增量更新。

**关键点：**
- 节点是无状态的，只依赖输入的 State
- 可以调用 LLM、工具、数据库、API
- 可以跨工作流复用

```python
def retrieve_node(state: AgentState):
    query = state["user_query"]
    docs = vector_store.search(query)
    return {"retrieved_docs": docs}  # 只返回要更新的字段
```

### 3. Edge（边）

**是什么：** 节点之间的连接，决定执行顺序。

| 类型 | 含义 |
|------|------|
| **普通边** | A 执行完，一定执行 B |
| **条件边** | A 执行完，根据条件决定走 B 还是 C |

```python
# 普通边：检索 → 生成
workflow.add_edge("retrieve", "generate")

# 条件边：判断是否需要重试
workflow.add_conditional_edges(
    "generate",
    should_retry,
    {"retry": "retrieve", "end": END}
)
```

### 4. Checkpoint（检查点）

**是什么：** 每次节点执行后，State 被自动保存到持久化存储。

**有什么用：**
- **断点续传**：崩溃后从 checkpoint 恢复
- **时间旅行**：回滚到之前的 State，重新走不同分支
- **人工介入**：执行到某个节点暂停，等人审批

```python
# 启用 checkpoint
workflow.compile(checkpointer=MemorySaver())
```

---

## 三、运行流程

```
用户输入 → 初始化 State
    │
    ▼
入口节点（如：检索文档）
    │
    ▼
普通边：检索 → 生成
    │
    ▼
条件边：判断是否需要重试
  需要 → 回到检索（循环）
  不需要 → 结束
    │
    ▼
输出最终 State
```

---

## 四、LangGraph 和传统方式对比

| 特性 | 传统函数调用 | LangGraph 图编排 |
|------|-------------|------------------|
| 循环/重试 | 自己写 while | 条件边天然支持 |
| 条件分支 | 自己写 if/else | 条件边定义清晰 |
| 并行执行 | 自己写多线程 | 支持并行节点 |
| 状态持久化 | 自己管理 | Checkpoint 自动保存 |
| 可视化 | 代码难读 | 图结构就是文档 |
| 调试 | 打断点逐行 | 看每步 State 快照 |

---

## 五、和记忆系统的关系

**核心问题：** LangGraph 的 State 是**临时的**（一次 `invoke()` 内有效），换会话后 State 丢失。

**解决方案：在 LangGraph 的 State 中集成记忆层**

```python
# 入口节点：从记忆层加载用户画像
def entry_node(state: AgentState):
    user_id = state.get("user_id")
    user_profile = memory.search(f"user_id={user_id}", limit=5)
    return {"user_profile": user_profile}

# 出口节点：把新记忆写入记忆层
def exit_node(state: AgentState):
    new_memory = extract_from_conversation(state["messages"])
    memory.add(new_memory)  # 持久化
    return {}
```

**关键点：**
- LangGraph 负责**编排流程**（节点怎么跳转）
- 记忆层负责**持久化数据**（跨会话记住用户信息）
- 两者互补：LangGraph 用记忆层来增强 State

---

## 六、真实案例：客服 Agent

### 场景
用户张三经常查订单，Agent 需要：
- 记住"那个订单"是指哪个
- 跨时间、跨会话保持记忆

### 代码结构

```python
# 1. State 定义
class ChatState(TypedDict):
    messages: list
    user_id: str
    user_name: str
    last_order_id: str
    intent: str
    order_info: dict
    response: str

# 2. 节点定义
def load_memory_node(state: ChatState):
    """从记忆层加载用户画像"""
    user_id = state["user_id"]
    profile = memory.search(f"user_id={user_id}", limit=5)
    return {
        "user_name": profile.get("name"),
        "last_order_id": profile.get("last_order_id"),
    }

def diagnose_node(state: ChatState):
    """诊断意图"""
    last_message = state["messages"][-1]
    if "那个订单" in last_message and state.get("last_order_id"):
        intent = "query_last_order"
    elif "查订单" in last_message:
        intent = "query_order"
    else:
        intent = "general_chat"
    return {"intent": intent}

def query_order_node(state: ChatState):
    """查订单"""
    if state["intent"] == "query_last_order":
        order_id = state["last_order_id"]
    else:
        order_id = extract_order_id(state["messages"][-1])
    order_info = order_api.query(order_id)
    return {"order_info": order_info}

def generate_node(state: ChatState):
    """生成回复"""
    response = llm.generate(
        f"用户 {state['user_name']} 问：{state['messages'][-1]}\n"
        f"订单信息：{state['order_info']}"
    )
    return {"response": response}

def save_memory_node(state: ChatState):
    """保存新记忆"""
    new_facts = extract_facts(state["messages"])
    memory.add(new_facts, user_id=state["user_id"])
    return {}

# 3. 构建图
workflow = StateGraph(ChatState)
workflow.add_node("load_memory", load_memory_node)
workflow.add_node("diagnose", diagnose_node)
workflow.add_node("query_order", query_order_node)
workflow.add_node("generate", generate_node)
workflow.add_node("save_memory", save_memory_node)

workflow.set_entry_point("load_memory")
workflow.add_edge("load_memory", "diagnose")
workflow.add_conditional_edges(
    "diagnose",
    lambda s: "chat" if s["intent"] == "general_chat" else "query",
    {"query": "query_order", "chat": "generate"}
)
workflow.add_edge("query_order", "generate")
workflow.add_edge("generate", "save_memory")
workflow.add_edge("save_memory", END)

# 4. 启用 Checkpoint
checkpointer = MemorySaver()
graph = workflow.compile(checkpointer=checkpointer)
```

### 执行场景

**场景 A：第一次对话**
```python
config = {"configurable": {"thread_id": "zhangsan_001"}}
graph.invoke({"messages": ["帮我查订单"], "user_id": "zhangsan"}, config=config)
# 1. 从记忆层加载：张三，上次订单 ORD-12345
# 2. 诊断：query_order
# 3. 查订单：ORD-12345 已发货
# 4. 生成："张三，您的订单已发货"
# 5. 保存记忆："张三最后查的订单是 ORD-12345"
# Checkpoint 保存 State 快照
```

**场景 B：同一会话，3 小时后继续**
```python
graph.invoke({"messages": ["那个订单发货了吗？"], "user_id": "zhangsan"}, config=config)
# 1. 从 Checkpoint 加载上次 State（包含 last_order_id）
# 2. 诊断：query_last_order（"那个订单" + last_order_id）
# 3. 查订单：ORD-12345
# 4. 生成："张三，订单已发货，预计明天送达"
```

**场景 C：没有 Checkpoint（新会话）**
```python
graph.invoke({"messages": ["我上次问的订单怎么样了？"], "user_id": "zhangsan"})
# 1. State 从零开始，没有上次历史
# 2. 即使有记忆层的 last_order_id，State 里也没有对话上下文
# 3. 问"请问您指的是哪个订单？"
```

---

## 七、概念对照表

| 概念 | 对应 | 一句话解释 |
|------|------|----------|
| **State** | `ChatState` | 共享数据仓库，所有节点读/写 |
| **Node** | `load_memory_node`, `diagnose_node` | 操作单元，接收 State 返回增量 |
| **Edge** | `load_memory → diagnose` | 流转规则，条件边决定分支 |
| **Checkpoint** | `MemorySaver()` + `thread_id` | 保存 State 快照，同 thread_id 复用 |
| **thread_id** | `"zhangsan_001"` | Checkpoint 的键，区分不同会话 |
| **记忆层** | `memory.search()` / `memory.add()` | 外部持久化系统，跨 thread_id 共享 |
| **增量更新** | `return {"user_name": "张三"}` | 节点只返回要改的字段，LangGraph 合并 |

---

## 八、常见困惑解答

### 1. 没有 Checkpoint 会怎样？
每次 `graph.invoke()` 都是新 State，两次调用之间不共享。绝大多数入门教程不启用 Checkpoint。

### 2. thread_id 是什么？
会话的唯一标识。同一个 thread_id 的多次调用共享 Checkpoint 保存的 State。类比：微信群号。

### 3. State 的生命周期？
- 没有 Checkpoint：`invoke()` 开始 → 创建 → 执行 → 销毁
- 有 Checkpoint（同 thread_id）：第一次创建并保存 → 第二次加载并更新 → 继续保存

### 4. 增量更新是谁做的？
Node 返回 `{"new_field": "value"}`，LangGraph 引擎自动合并到 State。Node 只写业务逻辑，合并和持久化是引擎做的。

### 5. Checkpoint 和记忆层有什么区别？
- Checkpoint 保存的是 State 快照（运行时的临时数据）
- 记忆层保存的是长期知识（用户画像、历史事实）
- Checkpoint 丢了 → 只是当前会话状态丢了，下次重新加载记忆层即可
- 记忆层丢了 → 用户的所有长期知识丢了，无法恢复

---

## 九、一句话总结

> **LangGraph = 用"图"来编排 Agent 的工作流程。节点是操作，边是流转，状态是共享数据。它让 Agent 能循环、分支、并行，但 State 是临时的，需要外接记忆层才能实现跨会话持久化。**

---

## 十、面试考点

| 问题 | 答案 |
|------|------|
| LangGraph 是什么？ | LangChain 的图编排框架，用节点+边+状态定义 Agent 工作流 |
| 为什么需要图？ | 普通调用是线性的，图支持循环、条件分支、并行 |
| State 是什么？ | 全局共享数据结构，所有节点读写，用来传递上下文 |
| Checkpoint 是什么？ | 自动保存 State 快照，支持断点续传和人工介入 |
| 和记忆系统的关系？ | LangGraph 编排流程，记忆层持久化数据。State 里的记忆换会话会丢，需要外接记忆层 |
| 不用 Checkpoint 怎么实现会话记忆？ | 外接记忆层：入口节点加载，出口节点保存 |

---

> 延伸阅读：
> - 官方文档：`https://langchain-ai.github.io/langgraph/`
> - 和 LangChain 的关系：LangGraph 是 LangChain 生态的一部分
