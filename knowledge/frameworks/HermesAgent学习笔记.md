# 学习资料：Hermes Agent 普及 — 自进化 AI Agent 框架

> 定位：普及知识面，理解 Hermes Agent 是什么、核心特点（闭环学习、自进化）、和 OpenClaw 的区别
> 来源：Nous Research 官方 + 多个技术文章综合整理
> 修正：2026-06-17 补充策划记忆方法论、记忆管理实现订正、和 mem0 理念对比（十）、FTS5 召回详解（十一）

---

## 一、Hermes Agent 是什么

**一句话：** Hermes Agent 是 **Nous Research 出品的开源 AI Agent 框架**（2026 年 2 月发布，MIT 协议），核心定位是 **self-improving AI agent（自进化 AI Agent）**。

**和市面上其他 Agent 框架的核心区别：**

| 框架 | 解决什么问题 | 核心能力 |
|------|------------|----------|
| **LangGraph** | 怎么编排 Agent 工作流 | 图编排（Node + Edge） |
| **AutoGen** | 怎么让多个 Agent 对话 | 多 Agent 对话 |
| **Manus** | 怎么执行复杂任务 | 多工具调用、任务执行 |
| **OpenClaw** | 多渠道自动化 | 多消息通道、工具编排 |
| **Claude Code** | 命令行编程辅助 | 代码生成、文件操作 |
| **Hermes Agent** | **怎么让 Agent 越用越聪明** | **闭环学习、技能自进化** |

**核心差异：** 大多数 Agent 框架解决的是"怎么让 LLM 更好地调用工具"。Hermes Agent 解决的是"怎么让 Agent 越用越聪明"。

---

## 二、核心架构：闭环学习（Closed Learning Loop）

Hermes Agent 的闭环学习包含五个环节：

```
完成任务
    │
    ▼
┌─────────────────────────────────────────┐
│ 1. 策划记忆（Curation）                  │
│ 任务完成后，Agent 自主判断什么值得记住    │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 2. 创建 Skill（Skill Creation）            │
│ 识别重复模式，自动生成 Markdown 格式的     │
│ Skill 文件（可复用的解决路径）             │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 3. Skill 自改进（Self-Improvement）       │
│ 现有 Skill 失败时自动优化                 │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 4. FTS5 召回（Retrieval）                  │
│ 按需检索历史对话（SQLite 全文索引）       │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 5. 用户建模（User Modeling）               │
│ 从行为推断偏好（Honcho 方言式建模）        │
└─────────────────────────────────────────┘
    │
    ▼
  循环 → 下次任务使用积累的知识
```

**对应认知科学的三种记忆：**

| 记忆类型 | 对应机制 | 存储方式 |
|----------|----------|----------|
| **情景记忆** | 会话历史 | `hermes_state.db`（SQLite + WAL） |
| **语义记忆** | 持久事实 | `MEMORY.md` |
| **程序性记忆** | 操作技能 | `skills/` 目录下的 Skill 文件 |

---

## 二·补充、策划记忆（Curation）方法论详解

> 回答"任务完成后，Agent 自主判断什么值得记住"背后的机制。
> 来源：Nous 官方 [Persistent Memory 文档](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory) + [Curator 文档](https://hermes-agent.nousresearch.com/docs/user-guide/features/curator)。内容已改写以符合引用规范。

**核心一句话：** Hermes 的策划记忆**不是"把任务全过程记下来"**，而是 **"后台定时触发 + 明确的存/弃判定标准 + 硬性容量预算逼着取舍"** 三件事的组合。把"记什么"的决策权交给 Agent 自己，但用"明确标准 + 有限容量"两个约束逼它只留高价值信息。

### 1. 触发机制：periodic nudge（后台 review，不阻塞主对话）

Agent 不是每说一句就判断要不要记，而是靠一个**后台 self-improvement review**：每个 turn 结束后，系统 fork 一个独立 Agent（约**每 10 轮**触发一次），在自己的 prompt cache 里跑，不打断当前对话。这个 fork 专门负责保存记忆、更新 Skill。

> 这就是 "periodic nudge" 机制——把"要不要记"的责任交给 Agent，但用周期性提醒驱动它，避免"记全部"或"啥都不记"两个极端。

### 2. 判定标准：明确的"存 vs 弃"清单

| 该主动存（Save） | 写入目标 |
|------------------|----------|
| 用户偏好（"我喜欢 TypeScript 多过 JavaScript"） | `user` |
| 环境事实（"服务器是 Debian 12 + PostgreSQL 16"） | `memory` |
| 纠正过的错误（"Docker 命令别加 sudo，用户在 docker 组"） | `memory` |
| 项目约定（缩进、行宽、文档风格） | `memory` |
| 已完成的工作（"2026-01-15 把库从 MySQL 迁到 PostgreSQL"） | `memory` |
| 用户明确要求记住的事 | `memory` |

| 该跳过（Skip） | 原因 |
|----------------|------|
| 琐碎/太笼统（"用户问了 Python"） | 太模糊没用 |
| 能轻易重新查到的事实（"Python 3.12 支持 f-string 嵌套"） | 联网就能查 |
| 原始数据堆（大段代码、日志、数据表） | 太大 |
| 单次会话的临时信息（临时路径、一次性调试上下文） | 用完即弃 |
| 已在 SOUL.md / AGENTS.md 等上下文文件里的内容 | 重复 |

> **判定原则一句话：** 存"以后还用得上、且不容易重新查到的稳定事实"，弃"琐碎的、临时的、可再生的、过大的"。

### 3. 容量预算：用"硬上限"逼着策划

| 文件 | 上限 | 大约条数 |
|------|------|---------|
| MEMORY.md（环境/约定/经验） | 2,200 字符（~800 token） | 8–15 条 |
| USER.md（用户画像/偏好） | 1,375 字符（~500 token） | 5–10 条 |

- **不自动压缩丢弃**：写入超限时 `memory` 工具直接**报错**，Agent 必须在同一轮里自己腾地方——用 `replace` 合并重叠条目、用 `remove` 删过时条目，再重试。
- **信息密度优先**：一条尽量打包多个相关事实，不要啰嗦展开。
- **冻结快照（frozen snapshot）**：记忆在会话开始时一次性注入 system prompt，会话中途新写的内容下次会话才生效（为了保住 prefix cache 性能）。

> 这个"紧字符预算 + 写满即报错"本身就是**强制策划机制**：空间有限，Agent 被迫不断判断"哪条更值得留"，而不是无脑追加。

### 4. 安全 + 门控

- **去重**：完全重复的条目自动拒绝。
- **安全扫描**：因记忆会注入 system prompt，写入前扫 prompt injection、凭据外泄、SSH 后门等模式，含隐藏 Unicode 也拦。
- **写入审批 `write_approval`**：默认放开自动写；设为 `true` 后，连后台自动写的内容也要先经用户 yes/no。

### 5. Curator：记忆/技能的后台清理

与记忆策划并行，还有一个 **Curator** 后台维护 Skill：跟踪每个 Skill 的查看/使用/打补丁次数，按 `active → stale（30 天未用）→ archived（90 天未用）` 流转，并周期性 fork 一个 aux 模型 review 来合并近似重复的 Skill。永不自动删除（最坏只归档到 `.archive/`，可恢复），且有快照/回滚机制。

---

## 三、核心架构组件

```
Hermes Agent 架构
├── run_agent.py              # Agent 主类，循环核心
├── agent/
│   ├── prompt_builder.py     # System Prompt 组装器
│   ├── memory_manager.py     # 记忆管理（双 Provider 架构）
│   ├── context_engine.py     # 上下文引擎（可插拔）
│   └── context_compressor.py # 轨迹压缩器
├── tools/                    # 40+ 工具实现
├── toolsets.py               # Toolset 定义和组合
├── hermes_state.py           # SQLite 状态存储（FTS5 全文搜索）
├── gateway/                  # 多平台消息网关
├── skills/                   # 内置 Skill 库（24 个分类）
├── plugins/                  # 插件系统
└── environments/             # 执行环境后端
    ├── local                 # 本地
    ├── Docker                # 容器
    ├── SSH                   # 远程
    ├── Daytona               # 云端开发环境
    └── Modal                 # 无服务器
```

**关键设计决策：**
- **Agent 循环和工具执行在同一进程**：单进程管理生命周期，没有微服务
- **工具自注册**：每个工具文件调用 `registry.register()` 声明自己，不需要中心化注册表
- **上下文压缩可插拔**：`ContextEngine` 是抽象基类，默认 `ContextCompressor`，可替换
- **SQLite + WAL 状态存储**：单文件数据库，支持多读者 + 单写者
- **MCP 双向支持**：既能作为 MCP 客户端，也能作为 MCP 服务端被 Cursor/VS Code 接入

---

## 四、核心能力详解

### 1. 记忆管理（双 Provider 架构）

```python
# 内置记忆的实际文件结构（~/.hermes/）
memories/MEMORY.md   # 语义记忆-环境/约定/经验（上限 2,200 字符）
memories/USER.md     # 语义记忆-用户画像/偏好（上限 1,375 字符）
state.db             # 情景记忆-全量会话（SQLite + WAL 模式 + FTS5 全文搜索）
```

- **语义记忆（MEMORY.md / USER.md）**：有字符上限的**策划文件**，会话开始时以冻结快照注入 system prompt。详细判定逻辑见「二·补充」。
- **情景记忆（state.db）**：所有 CLI 和消息会话存入 SQLite，采用 WAL（Write-Ahead Logging）模式支持多读单写，全量保存不截断。
- **FTS5 全文搜索**：通过 `session_search` 工具按需检索历史对话（约 20ms 查询），不经 LLM 总结、无 token 常驻成本。
- **外部 Provider**：内置之外还可挂 8 个外部记忆插件（Honcho、Mem0、OpenViking 等），提供知识图谱、语义检索、跨会话用户建模等能力，与内置记忆并存而非替换。

### 2. Skill 系统（程序性记忆）

```python
# Skill 自动创建流程
完成任务
  → 分析解决路径
  → 提取可复用模式
  → 生成 Markdown Skill 文件（skills/ 目录）
  → 下次遇到类似任务时自动调用
  → 失败时自动优化
```

**Skill 文件格式：**
```markdown
# Skill: 数据库迁移

## 触发条件
- 用户提到"迁移数据库"
- 检测到 schema 变更

## 执行步骤
1. 备份当前数据库
2. 生成迁移脚本
3. 测试迁移（staging 环境）
4. 执行生产迁移
5. 验证数据完整性

## 注意事项
- 迁移前必须备份
- 大表迁移需要分批次
```

### 3. 上下文压缩（Context Compression）

```python
# 问题：Agent 运行久了，上下文越来越长，token 消耗爆炸
# 解决方案：轨迹压缩器

原始轨迹：
  [Turn 1] 用户问... Agent 回答...
  [Turn 2] 用户问... Agent 调用工具... 结果... Agent 回答...
  [Turn 3] ...
  [Turn 50] ...  <-- 50 轮后上下文爆炸

压缩后：
  [Summary] 前 45 轮总结：用户要求重构认证模块，Agent 修改了 auth.py、middleware.py，测试通过
  [Turn 46-50] 最近 5 轮保留完整细节
```

### 4. 多模型支持

| 提供商 | 模型示例 |
|--------|----------|
| OpenAI | GPT-5.x |
| Anthropic | Claude Opus 4.6 |
| Google | Gemini 3.1 Pro |
| DeepSeek | DeepSeek-V3 |
| Hugging Face | 20+ 开放模型 |
| Ollama | 本地模型 |
| OpenRouter | 200+ 模型 |

**切换模型只需一条命令：** `hermes model`（不需要改代码）

---

## 五、和 OpenClaw 的对比

| 维度 | Hermes Agent | OpenClaw |
|------|-------------|----------|
| **核心定位** | 自进化 Agent（越用越聪明） | 多渠道自动化工作流 |
| **学习机制** | 闭环学习：Skill 自动生成 + 自改进 | 每次会话相对独立 |
| **记忆** | 语义记忆 + 情景记忆 + 程序性记忆 | 主要是配置注入（AGENTS.md 等） |
| **通道** | CLI、Telegram、Discord、Slack、钉钉 | 微信、QQ、飞书、Discord 等十多种 |
| **工具** | 40+ 工具 + MCP | browser、canvas、nodes、cron、sessions |
| **技能生态** | 内置 24 个分类，自动生成新 Skill | ClawHub 有大量现成技能 |
| **适用场景** | 长期陪伴、重复性工作、越用越强 | 多渠道自动化、即时任务 |
| **上手速度** | 中等（需要积累才能体现学习效果） | 快（开箱即用） |
| **并发** | 子 Agent 上限 3 个 | 受单机资源限制 |

**组合使用：**
- 用 **Hermes Agent** 做需要长期积累的 Agent（如个人助手、重复性工作）
- 用 **OpenClaw** 做需要多渠道触达的自动化（如消息通知、跨平台集成）
- 两者可以配合：Hermes 积累技能，OpenClaw 负责多渠道投递

---

## 六、和 Claude Code / Manus 的对比

| 维度 | Hermes Agent | Claude Code | Manus |
|------|-------------|-------------|-------|
| **定位** | 通用自进化 Agent | 命令行编程助手 | 通用任务执行 Agent |
| **学习** | ✅ 闭环学习（核心卖点） | ❌ 无长期学习 | ❌ 无长期学习 |
| **记忆** | 三层记忆 + 自动生成 Skill | 会话历史 + 注入文件 | 短期记忆 |
| **工具** | 40+ 工具 + MCP | 文件操作 + 命令执行 | 浏览器 + 命令行 + Python |
| **界面** | CLI + 多平台 | 命令行 | 云端 Web |
| **模型绑定** | 模型无关（15+ 提供商） | 默认 Claude（可换） | 默认 Claude（可换） |

---

## 七、适用场景

| 场景 | 适合用 Hermes Agent？ | 为什么 |
|------|---------------------|--------|
| 一次性任务 | ⚠️ 可以用，但优势不明显 | 学习机制需要积累才能体现价值 |
| 重复性工作（如日报、周报） | ✅ 非常适合 | 第一次做后生成 Skill，以后自动完成 |
| 长期陪伴助手 | ✅ 非常适合 | 越用越了解用户，Skill 不断积累 |
| 编程辅助 | ⚠️ 可以用 | Claude Code 可能更专业 |
| 多渠道自动化 | ❌ 不太适合 | OpenClaw 更适合 |
| 复杂任务执行 | ⚠️ 可以用 | Manus 可能更强大 |

---

## 八、一句话总结

> **Hermes Agent 是 Nous Research 出品的自进化 AI Agent 框架，核心定位是"让 Agent 越用越聪明"。通过闭环学习机制（策划记忆 → 创建 Skill → Skill 自改进 → FTS5 召回 → 用户建模），Agent 能在重复性工作中不断积累知识和经验，形成情景记忆、语义记忆、程序性记忆三层记忆体系。和 OpenClaw 的区别：Hermes 专注于长期积累和自我进化，OpenClaw 专注于多渠道自动化和即时任务。**

---

## 九、面试考点

| 问题 | 答案 |
|------|------|
| Hermes Agent 是什么？ | Nous Research 出品的自进化 AI Agent 框架，MIT 开源 |
| 核心定位是什么？ | self-improving AI agent（让 Agent 越用越聪明） |
| 闭环学习包含哪五个环节？ | 策划记忆 → 创建 Skill → Skill 自改进 → FTS5 召回 → 用户建模 |
| 三种记忆类型分别对应什么？ | 情景记忆（会话历史）、语义记忆（MEMORY.md）、程序性记忆（Skill 文件） |
| Skill 是怎么生成的？ | 完成任务后，Agent 自动分析解决路径，提取可复用模式，生成 Markdown Skill 文件 |
| **策划记忆的方法论是什么？** | **后台 periodic nudge 触发（约每 10 轮）+ 明确的存/弃判定标准 + 硬性字符预算（MEMORY 2200/USER 1375）逼着合并取舍 + 去重和安全扫描** |
| 该存什么 / 不该存什么？ | 存：用户偏好、环境事实、纠正、约定、已完成工作；弃：琐碎、可联网查到、大数据块、单次临时信息 |
| 和 OpenClaw 的区别？ | Hermes 专注于长期积累和自我进化，OpenClaw 专注于多渠道自动化 |
| 和 Claude Code 的区别？ | Hermes 是通用自进化框架，Claude Code 是编程专用命令行工具 |
| 适用什么场景？ | 重复性工作、长期陪伴助手（越用越强）；不适合一次性任务、多渠道自动化 |

---

## 十、和 mem0 的记忆理念对比

> 问题：Hermes 和 mem0 的记忆理念有什么差别？

**一句话概括分歧：**

> **Hermes 是"人类秘书式"——少而精，Agent 自己决定记几条关键事实，写成人能读的纸条，每次对话全带在身上；mem0 是"数据库式"——多而全，pipeline 自动把对话抽成结构化记忆条目存进库，用的时候再按相似度检索召回。**

### 核心对比表

| 维度 | Hermes Agent | mem0 |
|------|-------------|------|
| **谁决定记什么** | Agent 自主判断（LLM 按"存/弃清单"自己拍板） | 固定 pipeline 自动抽取（extractor 提事实 + updater 决策引擎，开发者不逐条干预） |
| **存储形态** | 有限的纯文本 Markdown（MEMORY.md / USER.md，人可读） | 结构化记忆库（向量库 + 可选图库，机器检索用） |
| **容量哲学** | 硬上限（2200/1375 字符），写满即报错，逼着合并取舍 | 无硬上限，可无限追加，靠检索时筛选 |
| **召回方式** | 语义记忆永驻 system prompt（零检索）+ 情景记忆走 FTS5 关键词全文搜索 | 向量语义检索 top-k（+可选图遍历多跳推理）+ over-fetch 重排 |
| **写入时机** | 后台 periodic nudge（异步、不阻塞、约每 10 轮 review 一次） | 每次 `add()` 即时处理（CQRS 写路径，写读分离） |
| **冲突/去重** | 字符预算 + consolidate 合并 + 完全重复拒绝 | embedding 相似度阈值驱动的 ADD/UPDATE/DELETE/NOOP |
| **记忆类型** | 三层：语义（MD）+ 情景（SQLite 全量会话）+ 程序性（Skill） | 聚焦事实记忆（语义），Graph Memory 补关系推理 |
| **产品定位** | 一个完整 Agent 产品的内置能力（开箱即用） | 一个可嵌入任何 App 的记忆中间件/SDK |

### 三个最值得讲的理念分歧

**1. "策划" vs "抽取" —— 决策权归谁**

Hermes 把"记什么"的决策权交给 Agent 自己：靠明确的存/弃标准 + 硬容量约束，让 LLM 主动判断哪条值得留。mem0 是工程化 pipeline：extractor 按固定 prompt 抽 7 类事实，updater 用相似度算法机械地决定 ADD/UPDATE/DELETE/NOOP——决策逻辑是代码写死的规则，不是 Agent 临场判断。一个是"让聪明的 Agent 自己当编辑"，一个是"用确定性流水线保证一致性"。

**2. "全量注入" vs "按需检索" —— 记忆怎么进上下文**

最硬核的架构分歧。Hermes 的语义记忆每次会话开头全量塞进 system prompt（零检索成本，但因此必须有字符上限，否则 prompt 爆炸）。mem0 的记忆平时躺在库里，用时才向量检索 top-k（无容量焦虑，但每次查询有检索延迟和召回不准的风险）。Hermes 用"容量换确定性"——重要的事永远在眼前；mem0 用"检索换无限"——能记很多，但得找得到。

**3. "纯文本" vs "结构化" —— 存成什么**

Hermes 存成人能读的 Markdown 纸条，强调可审计、可手改、可注入。mem0 存成 embedding 向量（+图谱），强调可计算相似度、可做多跳关系推理。注意：Hermes 的"情景记忆"虽然也用 SQLite，但召回是 FTS5 关键词搜索，不是向量语义检索——这点和 mem0 的向量召回是本质区别。

### 面试用一句话总结

> mem0 是"记忆基础设施"——把记忆当数据库工程问题来解（抽取、向量化、检索、冲突消解、CQRS）；Hermes 是"记忆产品体验"——把记忆当 Agent 自我管理问题来解（有限容量下的自主策划 + 全量注入 + 后台自进化）。前者适合给任意应用挂记忆能力，后者适合一个越用越懂你的长期助手。两者甚至能组合：Hermes 官方支持把 mem0 作为外部 memory provider 挂上去，用 mem0 补它的向量语义检索短板。

---

## 十一、FTS5 召回详解

> 问题：闭环学习里的"FTS5 召回"是什么？

### FTS5 是什么

**FTS5 = SQLite 的全文搜索引擎扩展（Full-Text Search version 5）。** 是 SQLite 内置模块，专门解决"在大量文本里快速找到包含某些词的记录"。Hermes 用它检索历史会话——所有 CLI/消息对话存进 `~/.hermes/state.db`，FTS5 让 Agent 能用 `session_search` 工具秒级查到"几周前聊过的某件事"。

### 怎么工作：倒排索引

核心机制是倒排索引（inverted index），和搜索引擎（Elasticsearch/Lucene）一个原理：

```
普通查询（没索引）：扫全表，逐行看文本里有没有这个词 → O(n) 慢
FTS5（倒排索引）：建一张"词 → 出现在哪些行"的映射表 → 查词直接命中 → 快
```

举例，存了三条会话：

```
行1: "用户在调试 Docker 网络问题"
行2: "Docker 容器启动失败"
行3: "讨论 PostgreSQL 索引优化"
```

FTS5 建的倒排索引大致是：

```
"Docker"      → [行1, 行2]
"PostgreSQL"  → [行3]
"索引"        → [行3]
"调试"        → [行1]
```

查 `Docker` 时不扫全表，直接查索引表拿到 `[行1, 行2]`。还支持 `AND`/`OR`/前缀匹配/短语匹配，并能用 BM25 算法排序（词频越高、越稀有的词命中权重越大）。

### 和"向量召回"的关键区别

| | FTS5（关键词召回） | 向量召回（语义召回） |
|---|---|---|
| **匹配依据** | 字面词是否出现（倒排索引） | 语义是否接近（embedding 余弦相似度） |
| **查"汽车"能否命中"轿车"** | ❌ 不能（字不同） | ✅ 能（语义近） |
| **查"Docker"命中"Docker"** | ✅ 精确命中 | ✅ 但可能被噪声干扰 |
| **成本** | 极低（纯文本索引，无需 LLM/embedding） | 高（要算 embedding + 向量库） |
| **速度** | ~20ms 量级 | 看向量库规模 |
| **可解释性** | 强（命中哪个词一目了然） | 弱（黑盒相似度） |

一句话：**FTS5 找"用词一样"的，向量找"意思相近"的。**

### 为什么 Hermes 情景记忆选 FTS5 而不是向量

- **省成本**：会话全量存着（可能上万条），每条都做 embedding 存向量库成本和维护都重。FTS5 是 SQLite 自带，零额外依赖、零 LLM 调用。
- **场景匹配**：情景记忆的典型查询是"我上次提到的那个服务器 IP / 项目名 / 命令是什么"——这类查询往往带精确关键词，关键词匹配反而比语义匹配更准、更不跑偏。
- **分层互补**：Hermes 把"需要语义理解的高价值事实"放进 MEMORY.md（永驻 prompt，零检索），把"海量原始对话"丢给 FTS5 按需关键词捞。语义层和关键词层各管一摊。

> 对比之下，mem0 的核心召回是向量语义检索——因为它要解决"模糊语义匹配"。两者选型差异正好印证理念分歧：Hermes 用低成本关键词搜全量历史，mem0 用向量语义搜结构化记忆库。

---

> 来源：
> - Nous Research 官方仓库：`https://github.com/NousResearch/hermes-agent`
> - 官方文档 - 持久记忆：`https://hermes-agent.nousresearch.com/docs/user-guide/features/memory`
> - 官方文档 - Curator：`https://hermes-agent.nousresearch.com/docs/user-guide/features/curator`
> - 技术解析：`https://cloud.tencent.com/developer/article/2665527`
> - 对比文章：`https://www.gm7.org/archives/89534`
