# LangChain 学习笔记：LLM 应用开发框架

> 学习日期：2026-06-16
> 来源：LangChain 官方文档 + 多个教程整理
> 用途：AI Agent 记忆系统学习

---

## 一、LangChain 是什么

**一句话：** LangChain 是**LLM 应用开发的基础框架**，提供标准化接口来连接 LLM、提示词、向量库、工具等组件。

**类比：** 如果你要做一个 AI 应用，LangChain 是**脚手架**，帮你把 LLM、数据库、API 等组件串起来。

---

## 二、核心概念（5 个）

| 概念 | 是什么 | 作用 |
|------|--------|------|
| **LLM** | 模型接口 | 统一调用 OpenAI/Anthropic/国产模型的接口 |
| **Prompt** | 提示模板 | 把变量（如用户输入）填充到模板中，生成完整 prompt |
| **Chain** | 链式调用 | 把多个组件串起来：Prompt → LLM → Output Parser |
| **Retriever** | 检索器 | 从向量库检索相关文档（RAG 的核心） |
| **Agent** | 自主代理 | LLM 决定调用哪个工具（ReAct 的实现） |

---

## 三、典型用法（Chain）

```python
from langchain import OpenAI, PromptTemplate, LLMChain

# 1. 定义 Prompt 模板
template = "用户问：{question}\n请用中文回答。"
prompt = PromptTemplate(template=template, input_variables=["question"])

# 2. 定义 LLM
llm = OpenAI(model="gpt-4")

# 3. 组成 Chain
chain = LLMChain(prompt=prompt, llm=llm)

# 4. 执行
result = chain.run(question="什么是 LangChain？")
# 内部：填充模板 → 调用 LLM → 返回结果
```

---

## 四、RAG 用法（Chain + Retriever）

```python
from langchain import OpenAI, VectorDBQA
from langchain.vectorstores import Chroma

# 1. 加载文档，切分，向量化，存入向量库
vectorstore = Chroma.from_documents(documents, embedding_model)

# 2. 定义检索器
retriever = vectorstore.as_retriever()

# 3. 组成 RAG Chain
qa = VectorDBQA.from_chain_type(llm=llm, chain_type="stuff", vectorstore=vectorstore)

# 4. 执行
result = qa.run("什么是 LangChain？")
# 内部：检索相关文档 → 构建 Prompt → LLM 生成回答
```

---

## 五、Agent 用法（ReAct）

```python
from langchain.agents import initialize_agent, Tool
from langchain.tools import DuckDuckGoSearchRun

# 1. 定义工具
tools = [
    Tool(name="Search", func=DuckDuckGoSearchRun(), description="搜索网页"),
]

# 2. 初始化 Agent
agent = initialize_agent(tools, llm, agent="zero-shot-react-description")

# 3. 执行
agent.run("2025年新能源汽车销量排名")
# 内部：LLM 思考 → 决定调用 Search → 获取结果 → 思考 → 生成回答
```

---

## 六、LangChain 和 LangGraph 的关系

```
LangChain（基础框架）
├── LLM 接口
├── Prompt 模板
├── Chain 链式调用
├── Retriever 检索器
├── Agent 基础实现
└── VectorStore 向量库
    │
    ▼
LangGraph（图编排扩展）
├── 用 Node + Edge 替代 Chain
├── 支持循环、条件分支、并行
├── 支持 Checkpoint 持久化
└── 依赖 LangChain 的所有组件
```

**关系：LangGraph 不能脱离 LangChain 单独使用。**

因为：
- LangGraph 的 Node 里调用 LLM → 用 LangChain 的 LLM 接口
- LangGraph 的 Node 里检索文档 → 用 LangChain 的 Retriever
- LangGraph 的 Node 里调用工具 → 用 LangChain 的 Agent

**LangGraph 是 LangChain 的"编排层"，不是替代品。**

---

## 七、一句话总结

> **LangChain 是 LLM 应用开发的基础框架，提供 Chain 链式调用、Retriever 检索器、Agent 自主代理等组件。LangGraph 是 LangChain 的图编排扩展，用 Node + Edge 替代 Chain，支持循环和条件分支，但不能脱离 LangChain 单独使用。**

---

## 八、面试考点

| 问题 | 答案 |
|------|------|
| LangChain 是什么？ | LLM 应用开发的基础框架，提供标准化接口连接 LLM、提示词、向量库、工具等 |
| Chain 是什么？ | 链式调用，把多个组件线性串起来（A→B→C） |
| Retriever 是什么？ | 检索器，从向量库检索相关文档，是 RAG 的核心 |
| LangChain 和 LangGraph 的关系？ | LangGraph 是 LangChain 的图编排扩展，依赖 LangChain 的 LLM 接口、向量库和工具定义 |
| 为什么 LangGraph 不能脱离 LangChain？ | LangGraph 的 Node 里调用 LLM、检索器、工具，都需要 LangChain 的接口 |

---

> 延伸阅读：
> - 官方文档：`https://python.langchain.com/`
> - 和 LangGraph 的关系：`https://langchain-ai.github.io/langgraph/`
