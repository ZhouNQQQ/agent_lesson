# K.8 MCP：三原语 / 三角色 / 运行时发现 / vs Function Calling

> 配套讲义：`lessons/06_mcp/mcp_lesson.md`
> 缺口补齐：深圳/北京 JD 要求 MCP 管理；ROADMAP 标 MCP 热点。

---

## 一、一句话

MCP（Model Context Protocol）= 给 LLM 应用接工具/数据/提示的**标准协议**，类比 USB-C。把 M×N 定制对接降成 M+N。

---

## 二、三角色

| 角色 | 是什么 | 例子 |
|---|---|---|
| Host 宿主 | 用户用的 App，含 client | Cursor / Claude / 你的 Agent |
| Client | host 内连接模块，与 server 一对一 | 连接管理器 |
| Server | 工具/数据提供方 | 文件系统/GitHub/记忆 server |

一个 host 可连多个 server，互相隔离。

---

## 三、三原语（必背）

| 原语 | 是什么 | 谁触发 | 类比 |
|---|---|---|---|
| Tools | 可执行函数（有副作用） | 模型决定调 | POST/RPC |
| Resources | 只读数据 | 应用决定加载 | GET/文件 |
| Prompts | 提示/工作流模板 | 用户触发 | 收藏指令 |

---

## 四、运行时发现（精髓）

| 层 | 发生什么 | 重启? |
|---|---|---|
| 配置层 | `mcp.json` 声明连哪个 server | 改了要重启 |
| 发现层 | 连上后 `tools/list`，server 当场返回工具+schema | 不用，运行时动态 |

代码不硬编码工具名/schema，是"问出来"的 → 工具可热更新。

---

## 五、MCP vs Function Calling（区分度题）

| | Function Calling | MCP |
|---|---|---|
| 是什么 | 模型表达"调哪个函数+参数"的能力 | 工具如何被发现/描述/调用的协议 |
| 层级 | 模型层 | 应用/协议层 |
| 关系 | MCP 工具最终也靠 FC 让模型选 | 标准化"工具从哪来怎么接" |

**一句话**：FC 是"模型怎么表达要调工具"，MCP 是"工具怎么被标准化接进来"，互补。

---

## 六、传输层

JSON-RPC 2.0 编码；本地用 stdio（子进程标准输入输出），远程用 Streamable HTTP/SSE。

---

## 七、工具编排（Tool Orchestration）

| 模式 | 何时用 |
|---|---|
| 工具检索（对工具描述做 RAG 选 top-k） | 工具几百个，全塞烧 token |
| 顺序 / 并行 / 条件路由 | 按依赖关系 |
| DAG / 工作流引擎 | 复杂长任务（接 LangGraph） |

---

## 八、面试速答

| 问题 | 要点 |
|---|---|
| MCP 是什么？ | 接工具/数据/提示的标准协议，类 USB-C，M×N→M+N |
| 三原语？ | Tools(模型调,有副作用)/Resources(应用加载,只读)/Prompts(用户触发) |
| 运行时发现？ | 配置层声明(改要重启)+发现层 tools/list 动态拿，代码不硬编码 |
| MCP vs FC？ | FC=模型表达调用意图；MCP=工具接入协议；MCP 工具仍靠 FC 选；互补 |
| 工具太多？ | 工具检索做 RAG 选 top-k 注入 |

---

> 关联：`lessons/06_mcp/`、`lessons/01_react/react_lesson.md`、`drills/02_tool_router.py`、`knowledge/frameworks/LangGraph学习笔记.md`
