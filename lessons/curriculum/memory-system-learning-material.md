# Memory 系统学习资料

> 📚 来源：OpenClaw 官方文档 + 实战理解
> 原始文档：/usr/lib/node_modules/openclaw/docs/concepts/memory.md
> 学习阶段：阶段二模块二（Memory 系统深度理解）

---

## 一、速讲版（5分钟读完）

### 核心概念：三层架构

OpenClaw 的 Memory 是**文件驱动的记忆系统**——模型记住什么，取决于写入磁盘的内容，没有隐藏状态。

| 层级 | 文件 | 作用 | 何时加载 |
|------|------|------|----------|
| **长期记忆** | `MEMORY.md` | 持久事实、偏好、决策 | 每次 DM 会话启动 |
| **短期记忆** | `memory/YYYY-MM-DD.md` | 当天日志、运行上下文 | 今天+昨天自动加载 |
| **梦境整理** | `DREAMS.md`（实验性） | 后台自动整理、晋升候选 | 按需/定时触发 |

### 两个关键工具

- `memory_search`：语义搜索（混合向量相似+关键词匹配）
- `memory_get`：精确读取指定文件或行范围

### 自动机制

- **自动 flush**：compaction 前自动提醒 agent 保存重要内容到 memory 文件
- **dreaming（可选）**：后台分析短期记忆，把高分内容晋升到长期记忆

---

## 二、详细版（深入理解）

### 1. 为什么叫"文件驱动"？

传统 LLM 应用的记忆是**对话上下文**——模型在同一个长对话里"记住"你说的话。但 OpenClaw 每次会话是独立的，模型每次醒来都是"失忆状态"。

所以 OpenClaw 的策略是：**不依赖模型内存，依赖文件系统**。每次会话启动时，把长期记忆和最近两天的日志一起加载到 prompt 里，让模型重新"认识"你。

> 类比：就像你每天早上到公司，先打开昨天的工作日志和项目文档，再继续干活。不是靠记忆力，是靠笔记。

### 2. MEMORY.md 的职责边界

MEMORY.md 不是**所有信息**的垃圾桶，是**精华库**。

**该写进去的：**
- 用户偏好和规则（如"用户要求同时给速讲版和原始版"）
- 重要决策（如"日报自动生成，不需要用户手动提供"）
- 身份认同（如"我是学习虾，用户是拙言"）
- 教训和洞察（如"上次犯了这个错，下次要注意验证文件路径再操作"）

**不该写进去的：**
- 每日琐事（放 memory/2026-05-31.md）
- 临时上下文（放对话里）
- 太长的原始资料（保留链接，不写全文）

### 3. memory/YYYY-MM-DD.md 的用法

这是**流水账**区域，记录当天发生了什么。

内容包括：
- 今天学了什么
- 今天完成了什么任务
- 今天的对话亮点
- 今天犯的错或踩的坑
- 用户今天的状态（比如"用户说今天很累，没学"）

格式：Markdown，无严格要求。但建议结构化，方便后续 dreaming 系统分析。

### 4. dreaming 系统（实验性）

这是 OpenClaw 的**自动整理机制**。

**原理：**
1. 后台定期扫描短期记忆（memory/*.md）
2. 分析哪些内容"值得记住"（评分机制：出现频率、重要性、用户强调）
3. 高分内容自动晋升到 MEMORY.md
4. 写一份人类可读的摘要到 DREAMS.md

**配置：**
- 默认关闭，需要手动开启
- 开启后会自动创建一个 cron job 做定期扫描
- 可以手动触发：`openclaw memory rem-backfill`

**用途：**
- 用户不需要手动维护 MEMORY.md，AI 自动帮你整理
- 但 DREAMS.md 是供人审查的，你可以看 AI 觉得什么值得记住

### 5. 混合搜索机制

`memory_search` 不是简单的关键词匹配，而是**混合搜索**：

- **向量相似**：语义匹配（比如搜"技能怎么写"也能找到"skill 创建规范"）
- **关键词匹配**：精确匹配（比如代码里的函数名、ID）
- **自动启用**：配置了任意 embedding provider（OpenAI/Gemini/Voyage/Mistral）后自动开启

**无 embedding 时**：退化为纯关键词搜索（SQLite 内置）

### 6. 后端选择

| 后端 | 特点 | 适用场景 |
|------|------|----------|
| **内置（默认）** | SQLite，零配置，支持向量和关键词 | 大多数人 |
| **QMD** | 本地优先，重排序，支持外部目录索引 | 高级用户，需要索引外部资料 |
| **Honcho** | AI-native，跨会话用户建模，多 agent 感知 | 多用户/多 agent 场景 |

### 7. 安全规则（flush 时的约束）

 compaction 前自动 flush 时，**以下文件是只读的**：
- `MEMORY.md`
- `DREAMS.md`
- `SOUL.md`
- `TOOLS.md`
- `AGENTS.md`

flush 只能写入 `memory/YYYY-MM-DD.md`，不能覆盖或修改上述文件。

> 为什么？因为这些是**人工维护的顶层设计文件**，不应该被自动化流程破坏。

---

## 三、原始版本位置

| 文件 | 路径 | 说明 |
|------|------|------|
| Memory 系统总览 | /usr/lib/node_modules/openclaw/docs/concepts/memory.md | 官方文档，最权威 |
| 内置 Memory 引擎 | /usr/lib/node_modules/openclaw/docs/concepts/memory-builtin.md | SQLite 后端细节 |
| QMD 引擎 | /usr/lib/node_modules/openclaw/docs/concepts/memory-qmd.md | 高级搜索选项 |
| Honcho 引擎 | /usr/lib/node_modules/openclaw/docs/concepts/memory-honcho.md | AI-native 记忆 |
| Memory 搜索 | /usr/lib/node_modules/openclaw/docs/concepts/memory-search.md | 搜索管道、provider 配置 |
| Dreaming（实验性） | /usr/lib/node_modules/openclaw/docs/concepts/dreaming.md | 后台晋升机制 |
| Memory 配置参考 | /usr/lib/node_modules/openclaw/docs/reference/memory-config.md | 所有配置参数 |
| Compaction | /usr/lib/node_modules/openclaw/docs/concepts/compaction.md | 压缩与 flush 的交互 |

---

## 四、实战思考题（供你思考）

1. **MEMORY.md 的"精华"标准**：你每天产生很多信息，什么值得进长期记忆？什么只留在当天日志？
2. **flush 的边界**：如果 compaction 前自动 flush 不能写 MEMORY.md，那它有什么用？（提示：它写 memory/YYYY-MM-DD.md，然后 dreaming 系统从那里晋升到 MEMORY.md）
3. **embedding 的必要性**：如果没有配置 OpenAI/Gemini API Key，memory_search 会怎样退化？对用户体验的影响是什么？
4. **三层架构的 DDD 映射**：长期记忆 = 聚合根（不变的事实），短期记忆 = 事件日志（每天发生的事），dreaming = 领域服务（整理规则）——这个映射合理吗？

---

> 生成时间：2026-05-31 23:45
> 学习教练：学习虾 🦞
