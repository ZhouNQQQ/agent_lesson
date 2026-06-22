# OpenClaw 记忆注入与 Prompt 拼接机制

> **来源**：OpenClaw 官方文档 + 本地源码分析  
> **整理时间**：2026-06-01  
> **原始文档**：/usr/lib/node_modules/openclaw/docs/concepts/memory.md  
> **原始文档**：/usr/lib/node_modules/openclaw/docs/concepts/memory-search.md  
> **原始文档**：/usr/lib/node_modules/openclaw/docs/concepts/memory-builtin.md

---

## 一、记忆注入时序（启动时自动加载）

OpenClaw 每次会话启动时，按以下顺序加载文件到 prompt：

```
1. SOUL.md          → 人设、性格、语气（最高优先级）
2. AGENTS.md        → 系统规则、工作方式
3. USER.md          → 用户信息、偏好
4. TOOLS.md         → 环境特定的工具配置
5. MEMORY.md        → 长期记忆（精华沉淀）
6. memory/YYYY-MM-DD.md → 当日日志 + 昨日日志
7. [可选] 向量召回记忆 → 通过 memory_search 动态检索
```

**关键设计**：
- 文件即数据库：直接读写 markdown，无需额外存储
- 启动注入：每次 session 自动读取，无需显式查询
- 文本驱动：模型记住什么，取决于写入磁盘的内容

---

## 二、Prompt 拼接机制（不是再调用 LLM）

### 2.1 拼接结构

OpenClaw 使用 **Context Assembly Pipeline**（上下文组装流水线）：

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: System Prompt                                     │
│  - SOUL.md + AGENTS.md + USER.md + TOOLS.md               │
│  - 这是模型的"身份认同"和"操作手册"                         │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Workspace Bootstrap Files                         │
│  - MEMORY.md + memory/YYYY-MM-DD.md                        │
│  - 这是模型的"记忆"                                         │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Conversation History                              │
│  - 最近 N 轮对话（可配置）                                    │
│  - 这是"短期上下文"                                         │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: Tool Outputs                                      │
│  - 工具执行结果（如 exec、read、web_fetch 等）                │
│  - 这是"实时获取的信息"                                      │
├─────────────────────────────────────────────────────────────┤
│  Layer 5: Retrieved Memories（可选）                        │
│  - 通过 memory_search 向量召回的相关记忆                     │
│  - 这是"语义相似的历史信息"                                  │
├─────────────────────────────────────────────────────────────┤
│  Layer 6: Current User Query                                │
│  - 当前用户输入                                              │
└─────────────────────────────────────────────────────────────┘
                           ↓
                    直接发送给 LLM
```

### 2.2 拼接方式：直接字符串拼接

**不是再调用 LLM 生成 prompt！**  
**是程序化的字符串拼接。**

公式化表达：
```
final_prompt = system_prompt 
               ⊕ bootstrap_files 
               ⊕ conversation_history 
               ⊕ tool_outputs 
               ⊕ retrieved_memories 
               ⊕ user_query

response = LLM(final_prompt)
```

### 2.3 向量召回的触发时机

**什么时候会触发 memory_search？**

1. **自动注入（如果配置）**：
   - 用户提问前，系统先对 query 做 embedding
   - 在向量数据库中搜索相似记忆（top-k）
   - 将召回的记忆片段自动拼接到 prompt 中

2. **Agent 主动调用**：
   - Agent 判断需要回忆时，调用 `memory_search` 工具
   - 将搜索结果作为 tool output 放入上下文

3. **手动触发**：
   - 用户或 skill 显式调用 `memory_search`

---

## 三、两层存储结构详解

### 3.1 长期记忆（MEMORY.md）

**职责**：精华沉淀，跨会话永久保留

**内容**：
- 用户偏好和规则（如"用户要求同时给速讲版和原始版"）
- 重要决策（如"日报自动生成，不需要用户手动提供"）
- 身份认同（如"我是学习虾，用户是拙言"）
- 教训和洞察（如"上次犯了这个错，下次要注意验证文件路径"）

**加载规则**：
- 只在 **DM（私聊）** 会话中加载
- **群聊中不加载**（安全考虑，防止个人信息泄露）
- 启动时完整注入，不是按需读取

### 3.2 短期记忆（memory/YYYY-MM-DD.md）

**职责**：当天日志，详细流水

**内容**：
- 今天学了什么
- 今天完成了什么任务
- 今天的对话亮点
- 今天犯的错或踩的坑
- 用户今天的状态

**加载规则**：
- 今天 + 昨天的日志自动加载
- 超过两天的日志不自动加载（减少 token 消耗）
- 需要时可手动通过 `memory_get` 读取

---

## 四、Embedding 与混合搜索

### 4.1 索引机制

OpenClaw 将记忆文件切分为 chunks（约 400 tokens，80-token overlap），存入 SQLite 数据库：

- **索引位置**：`~/.openclaw/memory/<agentId>.sqlite`
- **文件监控**：记忆文件变更触发 debounced reindex（1.5s 防抖）
- **自动重建**：embedding provider、model 或 chunking 配置变更时自动全量重建

### 4.2 搜索模式

**Hybrid Search（混合搜索）**：

```
Query → Embedding ──→ Vector Search ──┐
                                      ├──→ Weighted Merge ──→ Top Results
Query → Tokenize ────→ BM25 Search ────┘
```

- **Vector Search**：语义匹配（"gateway host" 匹配 "运行 OpenClaw 的机器"）
- **BM25 Search**：关键词匹配（精确匹配 ID、错误字符串、配置键）
- **合并**：加权合并，默认 50/50

**无 Embedding 时**：
- 退化为纯 BM25 关键词搜索
- 仍支持 lexical ranking（提升查询词覆盖度高的结果）

### 4.3 Provider 选择

| Provider | 是否需要 API Key | 特点 |
|----------|------------------|------|
| OpenAI | ✅ | 默认，高质量 |
| Gemini | ✅ | 支持多模态 |
| Local | ❌ | 需 node-llama-cpp，离线运行 |
| Ollama | ❌ | 本地/自托管 |
| Mistral | ✅ | |
| Voyage | ✅ | 代码专用 embedding |

---

## 五、自动 Flush 机制

### 5.1 触发时机

在 **compaction（对话压缩）** 前，OpenClaw 自动执行一次静默 turn：
- 提醒 agent 保存重要上下文到 memory 文件
- 写入目标：`memory/YYYY-MM-DD.md`

### 5.2 只读约束

Flush 时，以下文件是**只读**的：
- `MEMORY.md`
- `DREAMS.md`
- `SOUL.md`
- `TOOLS.md`
- `AGENTS.md`

**原因**：这些是**人工维护的顶层设计文件**，不应被自动化流程破坏。

### 5.3 记忆晋升路径

```
对话上下文 → [自动 Flush] → memory/YYYY-MM-DD.md → [Dreaming] → MEMORY.md
              ↑                                    ↑
         每天自动保存                           可选后台整理
```

---

## 六、安全与边界

### 6.1 Prompt Injection 风险

OpenClaw 的 **Unified Context Stream** 存在安全风险：

- 所有内容（系统指令、对话历史、工具输出、文件内容）注入到同一个上下文流
- LLM 无法区分"开发者指令"和"用户数据"
- 攻击者可通过恶意文件内容注入指令

**防御措施**：
- 文件内容标记为 untrusted（用户提供的文本不作为元数据）
- Bootstrap 文件（SOUL/AGENTS/USER 等）在系统提示中优先级最高
- 但：攻击面仍然存在，特别是通过 `memory_search` 召回的内容

### 6.2 群聊安全

- MEMORY.md **不在群聊中加载**
- 防止个人敏感信息泄露到群组上下文
- 群聊中仅使用会话内上下文和 tool outputs

---

## 七、与 Mem0 的对比

| 维度 | OpenClaw | Mem0 |
|------|----------|------|
| 存储 | Markdown 文件 + SQLite | 向量数据库 |
| 更新 | 手动编辑 + 自动 flush | LLM 决策 ADD/UPDATE/DELETE |
| 索引 | 文件监控 + 自动 reindex | 实时更新 |
| 安全 | 文件只读约束 + 群聊隔离 | 存在 adversarial co-retrieval |
| 可控性 | 高（人工可审查） | 中（自动维护） |
| 适用 | 个人 Agent | 大规模对话系统 |

---

## 八、实战思考题

1. **分层策略**：为什么长期记忆是"精华"而不是"全部"？如果 MEMORY.md 太大，会有什么副作用？
2. **注入时序**：为什么 SOUL.md 在 USER.md 之前加载？如果顺序反过来，会发生什么？
3. **向量召回**：如果 embedding provider 失效，系统退化为何种模式？用户体验差异有多大？
4. **安全边界**：为什么群聊不加载 MEMORY.md？设计这个规则的出发点是什么？
