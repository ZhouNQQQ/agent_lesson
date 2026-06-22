# 学习资料：OpenCode 普及 — 开源 AI 编码助手

> 学习日期：2026-06-17
> 来源：OpenCode 官方文档 + 多个技术文章综合整理
> 用途：AI Agent 编码助手学习，与 Hermes 对比

---

## 一、OpenCode 是什么

**一句话：** OpenCode 是 **SST 团队（anomalyco）出品的开源 AI 编码助手**（MIT 协议），定位是 **Claude Code 的开源替代品**，有命令行 TUI、桌面应用、IDE 扩展三种界面。

**核心数据：**
- **GitHub Stars**: 145K+（增长最快的开源 AI 编码工具）
- **月活开发者**: 500 万+
- **模型提供商**: 75+（OpenAI/Anthropic/Google/AWS/Azure/Ollama 等）
- **协议**: MIT 开源
- **哲学**: BYOK（Bring Your Own Key，只付 API 费用，无额外订阅）

---

## 二、核心特点

### 1. 多 Agent 架构

| 内置 Agent | 职责 | 权限 |
|-----------|------|------|
| **Coder** | 写代码、改文件、执行命令 | 读写执行 |
| **Architect** | 分析项目、设计架构、制定计划 | 只读 |
| **Ask** | 问答、解释代码、提供帮助 | 只读 |

**自定义 Agent**：支持创建自己的 Agent，定义职责和权限。

### 2. 两种工作模式

| 模式 | 行为 | 适用场景 |
|------|------|----------|
| **Planning** | 分析请求 → 制定计划 → 展示方案 → 等用户批准 | 复杂任务，防止跑偏 |
| **Build** | 直接执行，边做边调整 | 简单任务，快速迭代 |

**Planning 模式：**
```
用户："重构认证模块，把 JWT 改成 Session"
OpenCode："我将按以下步骤执行：
  1. 分析 auth.js 中的 JWT 逻辑
  2. 创建 Session 存储（Redis）
  3. 修改 auth.js 使用 Session
  4. 更新 middleware.js
  5. 修改 routes.js
  6. 运行测试验证
  确认执行？"
用户：确认
→ OpenCode 开始执行
```

### 3. 项目记忆：AGENTS.md

```bash
opencode /init
→ 分析项目结构
→ 生成 AGENTS.md（项目记忆文件）
→ 包含：项目架构、编码规范、依赖关系、常用命令
```

**AGENTS.md 示例：**
```markdown
# OpenCode Project Memory

## 项目架构
- 前端：React + TypeScript
- 后端：Node.js + Express
- 数据库：PostgreSQL

## 编码规范
- 缩进：2 空格
- 引号：单引号
- 函数命名：camelCase

## 常用命令
- npm run dev：启动开发服务器
- npm test：运行测试
- npm run build：构建生产版本
```

### 4. LSP 集成

- 自动加载语言服务器
- 实时诊断、代码导航、上下文感知补全
- 直接在终端中提供 IDE 级功能

### 5. 多提供商支持

```bash
# 切换模型
/connect anthropic    # 使用 Claude
/connect openai       # 使用 GPT
/connect google       # 使用 Gemini
/connect ollama       # 使用本地模型

# 自由切换，无供应商锁定
```

### 6. 并行会话

```bash
# 同时运行多个会话
Session 1: opencode → 处理前端重构
Session 2: opencode → 处理后端 API
Session 3: opencode → 写单元测试
```

---

## 三、和 Claude Code 的对比

| 对比项 | OpenCode | Claude Code |
|--------|----------|-------------|
| **开源** | ✅ MIT 开源 | ❌ 闭源（ultraworkers/claw-code 是社区复刻） |
| **定价** | 免费（BYOK） | $20/月（Anthropic） |
| **模型** | 75+ 提供商 | 默认 Claude，可换 |
| **界面** | TUI + 桌面 + IDE | 命令行 |
| **多 Agent** | ✅ Coder/Architect/Ask | ❌ 单 Agent |
| **Planning 模式** | ✅ 显式计划 | ❌ 直接执行 |
| **项目记忆** | ✅ AGENTS.md | ✅ CLAUDE.md |
| **LSP** | ✅ Native | ❌ 无 |
| **并行会话** | ✅ 支持 | ❌ 单会话 |

**结论：** OpenCode 是 Claude Code 的**开源增强版**，增加了多 Agent、Planning 模式、多提供商、并行会话等能力。

---

## 四、和 Hermes Agent 的对比（重点）

| 对比维度 | OpenCode | Hermes Agent |
|----------|----------|-------------|
| **定位** | 编码助手（编程专用） | 通用自进化 Agent（不限领域） |
| **开源** | ✅ MIT | ✅ MIT |
| **核心能力** | 多 Agent 编码、Planning/Build 模式 | 闭环学习、Skill 自进化、记忆积累 |
| **记忆系统** | AGENTS.md（项目级静态配置） | 三层记忆（情景+语义+程序性）+ SQLite FTS5 |
| **自进化** | ❌ 无（每次项目独立） | ✅ 核心卖点（越用越聪明） |
| **学习机制** | 无长期学习 | 策划记忆→创建 Skill→自改进→FTS5 召回→用户建模 |
| **适用场景** | 编码任务、项目开发 | 重复性工作、长期陪伴、跨项目积累 |
| **界面** | TUI/桌面/IDE | CLI/多平台 |
| **模型** | 75+ 提供商 | 15+ 提供商 |
| **二次开发** | 插件系统（oh-my-opencode） | 插件系统 + 可替换上下文引擎 |

### 核心差异总结

| 如果你需要... | 选 OpenCode | 选 Hermes |
|--------------|------------|----------|
| **写代码、改项目** | ✅ 专用编码工具 | ⚠️ 可以，但不如专用 |
| **长期积累知识** | ❌ 无此能力 | ✅ 核心能力 |
| **跨项目复用经验** | ❌ 每个项目独立 | ✅ Skill 自动复用 |
| **自进化（越用越强）** | ❌ 无 | ✅ 核心卖点 |
| **多 Agent 协作编码** | ✅ Coder/Architect/Ask | ⚠️ 子 Agent 上限 3 |
| **Planning 模式（防跑偏）** | ✅ 显式计划 | ⚠️ 无显式 Planning |
| **本地优先/隐私** | ✅ 本地运行 | ✅ 本地运行 |

---

## 五、二次开发对比：哪个更方便？

### OpenCode 的扩展方式

```bash
# 1. 插件系统：oh-my-opencode
# 社区驱动的扩展系统，类似 oh-my-zsh
# 安装插件：
opencode plugin install <plugin-name>

# 2. 自定义 Agent
# 定义新的 Agent 角色和权限
# 通过配置文件或代码扩展

# 3. 修改源码
# MIT 开源，可以直接改源码
#  TypeScript 项目，代码结构清晰
```

**二次开发优势：**
- 社区活跃（145K+ stars，大量贡献者）
- 插件生态丰富（oh-my-opencode）
- TypeScript 代码，前端开发者熟悉
- 文档完善，上手快

### Hermes Agent 的扩展方式

```python
# 1. 插件系统
# 通过插件目录添加新能力

# 2. 自定义上下文引擎
# ContextEngine 是抽象基类，可以替换实现
# 例如：换成自己的向量检索方案

# 3. 自定义 Skill
# 手动编写 Skill 文件，或让 Agent 自动生成

# 4. 修改源码
# MIT 开源，Python 项目
# 核心文件：run_agent.py, agent/, tools/, hermes_state.py
```

**二次开发优势：**
- 上下文引擎可插拔（ContextEngine 抽象基类）
- 记忆系统可替换（双 Provider 架构）
- Skill 系统灵活（自动生成 + 手动编写）
- 工具系统可扩展（40+ 工具，自注册机制）

### 二次开发对比结论

| 场景 | 推荐选择 | 原因 |
|------|----------|------|
| **前端/TypeScript 开发者** | OpenCode | 代码熟悉，社区活跃，插件丰富 |
| **Python 开发者** | Hermes | 代码熟悉，架构清晰，可插拔设计 |
| **需要自定义编码工作流** | OpenCode | 多 Agent 架构，Planning/Build 模式 |
| **需要自定义记忆系统** | Hermes | 记忆系统可插拔（ContextEngine 抽象基类） |
| **需要长期积累知识** | Hermes | 闭环学习机制，Skill 自进化 |
| **需要快速上手** | OpenCode | 文档完善，社区大，示例多 |
| **需要深度定制架构** | Hermes | 模块化设计，组件可替换 |

**综合结论：**
- **OpenCode 更方便快速扩展编码能力**（插件、多 Agent、Planning 模式）
- **Hermes 更方便深度定制记忆和学习机制**（可插拔上下文引擎、Skill 系统）

---

## 六、一句话总结

> **OpenCode 是 Claude Code 的开源增强版，专注编码场景，有 TUI/桌面/IDE 三种界面、多 Agent 架构（Coder/Architect/Ask）、Planning/Build 两种模式、75+ 模型提供商。和 Hermes 的核心区别：OpenCode 是编码专用工具（项目级记忆），Hermes 是通用自进化框架（跨项目积累 Skill）。二次开发：OpenCode 适合快速扩展编码能力（TypeScript + 丰富插件），Hermes 适合深度定制记忆和学习机制（Python + 可插拔架构）。**

---

## 七、面试考点

| 问题 | 答案 |
|------|------|
| OpenCode 是什么？ | SST 团队出品的开源 AI 编码助手，Claude Code 的开源替代品，145K+ stars |
| OpenCode 和 Claude Code 的区别？ | OpenCode 开源免费、多 Agent、Planning 模式、75+ 提供商；Claude Code 闭源、$20/月、单 Agent |
| OpenCode 的核心特点？ | 多 Agent（Coder/Architect/Ask）、Planning/Build 模式、AGENTS.md 项目记忆、75+ 提供商、LSP 集成 |
| OpenCode 和 Hermes 的区别？ | OpenCode 编码专用（项目级），Hermes 通用自进化（跨项目积累 Skill） |
| 二次开发哪个更方便？ | 编码扩展选 OpenCode（TypeScript + 插件丰富），记忆/学习定制选 Hermes（Python + 可插拔） |
| OpenCode 的记忆系统是什么？ | AGENTS.md（项目级静态配置），不是长期积累 |
| OpenCode 有自进化能力吗？ | ❌ 无，每个项目独立，不会跨项目积累 |

---

> 来源：
> - 官网：`https://opencode.ai/`
> - 文档：`https://opencode.ai/docs/`
> - GitHub：`https://github.com/anomalyco/opencode`
> - 对比参考：多个技术文章综合整理
