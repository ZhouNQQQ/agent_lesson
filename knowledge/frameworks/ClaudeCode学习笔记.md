# Claude Code (Claw Code) 学习笔记：命令行 AI 助手

> 学习日期：2026-06-16
> 来源：ultraworkers/claw-code GitHub 源码（github.com/ultraworkers/claw-code）
> 用途：AI Agent 记忆系统学习

---

## 一、Claude Code 是什么

**一句话：** Claude Code 是 **Anthropic 推出的命令行 AI 助手**，ultraworkers/claw-code 是它的 **Rust 开源实现**。

**定位：** 在终端里和 AI 协作编程，可以读文件、改代码、执行命令、搜索项目。

---

## 二、核心架构（Rust Workspace）

```
claw-code/rust/
├── api/                  # API 层（Provider 抽象）
├── commands/             # 命令处理（CLI 命令解析）
├── runtime/              # 运行时（Agent 执行循环）
├── tools/                # 工具系统（文件操作、搜索、命令执行）
├── plugins/              # 插件系统
├── telemetry/            # 遥测/日志
├── rusty-claude-cli/     # CLI 界面
└── compat-harness/      # 兼容性测试
```

---

## 三、工具系统（Tools）

Claude Code 的核心能力是**工具调用**，Agent 可以自主决定调用哪些工具：

| 工具 | 功能 | 用途 |
|------|------|------|
| **read_file** | 读取文件内容 | 查看代码、配置 |
| **write_file** | 写入文件 | 创建新文件 |
| **edit_file** | 编辑文件（diff 方式） | 修改代码 |
| **glob_search** | 按模式搜索文件 | 找文件 |
| **grep_search** | 按内容搜索 | 找代码片段 |
| **Bash** | 执行 shell 命令 | 运行测试、安装依赖 |
| **web_fetch** | 获取网页内容 | 查文档 |
| **browser** | 浏览器操作 | 复杂网页交互 |
| **sessions** | 会话管理 | 多会话切换 |

---

## 四、权限模式（Permission Modes）

Claude Code 有三种权限级别，防止 AI 误操作：

| 模式 | 权限 | 适用场景 |
|------|------|----------|
| **read-only** | 只能读文件、搜索 | 查看代码，不修改 |
| **workspace-write** | 读写工作区文件 | 日常开发（默认） |
| **danger-full-access** | 执行任意命令 | 需要特别授权 |

---

## 五、记忆系统

Claude Code 通过**注入文件**将记忆和上下文注入到 LLM：

| 文件 | 位置 | 作用 |
|------|------|------|
| **CLAUDE.md** | `.claw/CLAUDE.md` | 项目指导（编码规范、架构说明） |
| **AGENTS.md** | `.claw/AGENTS.md` | Agent 配置 |
| **SOUL.md** | `~/.claw/workspace/SOUL.md` | 助手人格/偏好 |
| **TOOLS.md** | `~/.claw/workspace/TOOLS.md` | 工具定义 |
| **Skills** | `.claw/skills/<skill>/SKILL.md` | 技能模块 |

**会话持久化：** 对话历史保存在 `.claw/sessions/` 目录下。

---

## 六、多 Provider 支持

Claude Code 不是只支持 Claude，支持多种 LLM：

| Provider | 模型示例 | 认证方式 |
|----------|----------|----------|
| **Anthropic** | claude-opus, claude-sonnet | ANTHROPIC_API_KEY |
| **OpenAI-compatible** | gpt-4.1, local models | OPENAI_API_KEY + OPENAI_BASE_URL |
| **xAI** | grok-3 | XAI_API_KEY |
| **DashScope** | qwen-max, qwen-plus | DASHSCOPE_API_KEY |
| **Ollama** | llama3.2, local models | OLLAMA_HOST |

---

## 七、和 Cursor 的对比

| | Claude Code | Cursor |
|--|-------------|--------|
| **界面** | 命令行/终端 | 编辑器 GUI（VS Code） |
| **交互方式** | 文本对话 | 文本 + 可视化 diff |
| **文件操作** | 命令行编辑 | 编辑器内直接修改 |
| **适用场景** | 自动化脚本、服务器操作 | 日常开发、代码审查 |
| **人介入** | 命令行确认 | 按钮点击（Accept/Reject） |

**关系：** 两者都是 AI 编程助手，但界面不同。Claude Code 更适合命令行环境，Cursor 更适合编辑器环境。

---

## 八、和 OpenClaw / Qclaw 的关系

| | OpenClaw | Claw Code (Claude Code) |
|--|----------|-------------------------|
| **定位** | 个人 AI 助手框架 | 命令行 AI 编程助手 |
| **配置兼容** | `.claw/` 目录 | `.claw/` 目录（兼容） |
| **注入文件** | AGENTS.md/SOUL.md/TOOLS.md | CLAUDE.md/AGENTS.md |
| **通道** | 多消息通道（微信/QQ/Slack） | 命令行/终端 |
| **核心能力** | 通用助手 | 编程专用 |

**关系：** Claw Code 和 OpenClaw 共享 `.claw/` 配置体系，但定位不同。OpenClaw 是通用助手，Claw Code 是编程专用。

---

## 九、核心工作流

```
用户输入命令/问题
    │
    ▼
Agent 读取上下文（CLAUDE.md + 项目文件 + 会话历史）
    │
    ▼
Agent 决定调用工具（read/edit/bash/grep...）
    │
    ▼
工具执行 → 返回结果
    │
    ▼
Agent 分析结果 → 决定下一步
    │
    ▼
  循环直到任务完成
    │
    ▼
  生成回复
```

---

## 十、一句话总结

> **Claude Code (Claw Code) 是命令行 AI 编程助手，Rust 实现。核心能力是工具调用（读文件、改代码、执行命令），通过 .claw/ 配置体系注入上下文和记忆。支持多 Provider（Claude/GPT/Grok/Qwen），有三种权限模式防止误操作。和 OpenClaw 共享配置体系，但定位是编程专用而非通用助手。**

---

## 十一、面试考点

| 问题 | 答案 |
|------|------|
| Claude Code 是什么？ | 命令行 AI 编程助手，可以读文件、改代码、执行命令 |
| Claude Code 有哪些工具？ | read_file, write_file, edit_file, glob_search, grep_search, Bash, web_fetch, browser |
| 权限模式有哪些？ | read-only（只读）、workspace-write（默认，可读写）、danger-full-access（完全访问） |
| 记忆系统怎么工作？ | 通过 .claw/ 目录下的 CLAUDE.md/AGENTS.md/SOUL.md/TOOLS.md 注入上下文 |
| 支持哪些 LLM？ | Anthropic(Claude)、OpenAI-compatible、xAI(Grok)、DashScope(Qwen)、Ollama(local) |
| 和 Cursor 的区别？ | Claude Code 是命令行，Cursor 是编辑器 GUI。两者都是 AI 编程助手 |
| 和 OpenClaw 的关系？ | 共享 .claw/ 配置体系，但 OpenClaw 是通用助手，Claw Code 是编程专用 |

---

> 来源：
> - GitHub：`https://github.com/ultraworkers/claw-code`
> - 官方文档：`https://docs.anthropic.com/en/docs/claude-code/overview`
