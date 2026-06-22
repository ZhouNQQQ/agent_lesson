# Honcho Memory — 完整原文 + 中文注释

> **原始来源**：/usr/lib/node_modules/openclaw/docs/concepts/memory-honcho.md
> **原始标题**：Honcho Memory
> **整理时间**：2026-06-02
> **说明**：以下内容为 OpenClaw 官方文档的完整原文，我在关键段落旁添加了中文注释（以 `【注：】` 标记）。

---

---
title: "Honcho Memory"
summary: "AI-native cross-session memory via the Honcho plugin"
read_when:
  - You want persistent memory that works across sessions and channels
  - You want AI-powered recall and user modeling
---

# Honcho Memory

[Honcho](https://honcho.dev) adds AI-native memory to OpenClaw. It persists
conversations to a dedicated service and builds user and agent models over time,
giving your agent cross-session context that goes beyond workspace Markdown
files.

【注：Honcho 定位 —— 不是替代 OpenClaw 的文件记忆，而是增强层。核心能力是：跨会话持久化 + 自动用户建模 + 多 Agent 感知。】

## What it provides

- **Cross-session memory** -- conversations are persisted after every turn, so
  context carries across session resets, compaction, and channel switches.

【注：跨会话记忆 —— 每次 AI 回复后自动保存对话，即使会话重置、压缩、换渠道，上下文不丢失。】

- **User modeling** -- Honcho maintains a profile for each user (preferences,
  facts, communication style) and for the agent (personality, learned
  behaviors).

【注：自动用户建模 —— 我前面整理的 honcho-user-modeling.md 的核心来源。Honcho 自动分析用户偏好、沟通风格、事实信息，生成动态画像。】

- **Semantic search** -- search over observations from past conversations, not
  just the current session.

【注：语义搜索 —— 基于对话观察（observations）而非文件内容，搜索范围是整个历史对话。】

- **Multi-agent awareness** -- parent agents automatically track spawned
  sub-agents, with parents added as observers in child sessions.

【注：多 Agent 感知 —— 父 Agent 启动子 Agent 时，父 Agent 自动成为子会话的观察者，能看到子 Agent 的对话上下文。】

## Available tools

Honcho registers tools that the agent can use during conversation:

**Data retrieval (fast, no LLM call):**

| Tool                        | What it does                                           |
| --------------------------- | ------------------------------------------------------ |
| `honcho_context`            | Full user representation across sessions               |
| `honcho_search_conclusions` | Semantic search over stored conclusions                |
| `honcho_search_messages`    | Find messages across sessions (filter by sender, date) |
| `honcho_session`            | Current session history and summary                    |

【注：快速查询工具 —— 不涉及 LLM 调用，直接查 Honcho 服务。context 获取完整用户画像，search 做语义检索，session 查当前会话。】

**Q&A (LLM-powered):**

| Tool         | What it does                                                              |
| ------------ | ------------------------------------------------------------------------- |
| `honcho_ask` | Ask about the user. `depth='quick'` for facts, `'thorough'` for synthesis |

【注：LLM 驱动工具 —— 用 Honcho 的数据 + LLM 推理生成回答。quick 模式查事实，thorough 模式做综合分析。】

## Getting started

Install the plugin and run setup:

```bash
openclaw plugins install @honcho-ai/openclaw-honcho
openclaw honcho setup
openclaw gateway --force
```

The setup command prompts for your API credentials, writes the config, and
optionally migrates existing workspace memory files.

<Info>
Honcho can run entirely locally (self-hosted) or via the managed API at
`api.honcho.dev`. No external dependencies are required for the self-hosted
option.
</Info>

【注：安装方式 —— 需要装插件 + 运行 setup。支持托管版（api.honcho.dev）和自托管版（本地部署）。setup 会引导配置 API key 并可选迁移现有 memory 文件。】

## How it works

After every AI turn, the conversation is persisted to Honcho. Both user and
agent messages are observed, allowing Honcho to build and refine its models over
time.

During conversation, Honcho tools query the service in the `before_prompt_build`
phase, injecting relevant context before the model sees the prompt. This ensures
accurate turn boundaries and relevant recall.

【注：注入时机 —— Honcho 在 "before_prompt_build" 阶段注入上下文，即构建 prompt 之前。这意味着 Honcho 的上下文和文件加载的上下文是并行的，不是互相替代。】

## Honcho vs builtin memory

|                   | Builtin / QMD                | Honcho                              |
| ----------------- | ---------------------------- | ----------------------------------- |
| **Storage**       | Workspace Markdown files     | Dedicated service (local or hosted) |
| **Cross-session** | Via memory files             | Automatic, built-in                 |
| **User modeling** | Manual (write to MEMORY.md)  | Automatic profiles                  |
| **Search**        | Vector + keyword (hybrid)    | Semantic over observations          |
| **Multi-agent**   | Not tracked                  | Parent/child awareness              |
| **Dependencies**  | None (builtin) or QMD binary | Plugin install                      |

【注：对比表 —— Honcho 是"服务化"记忆，Builtin 是"文件化"记忆。两者可以共存：Honcho 管跨会话 + 自动建模，Builtin 管本地文件 + 精细控制。】

Honcho and the builtin memory system can work together. When QMD is configured,
additional tools become available for searching local Markdown files alongside
Honcho's cross-session memory.

【注：可以并存！Honcho + QMD + Builtin 同时用，各取所长。】

---

> **中文注释完成。** 如需进一步解释某个段落，请告诉我。
