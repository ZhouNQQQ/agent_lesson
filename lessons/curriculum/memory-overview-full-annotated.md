# Memory Overview — 完整原文 + 中文注释

> **原始来源**：/usr/lib/node_modules/openclaw/docs/concepts/memory.md
> **原始标题**：Memory Overview
> **整理时间**：2026-06-01
> **说明**：以下内容为 OpenClaw 官方文档的完整原文，我在关键段落旁添加了中文注释（以 `【注：】` 标记），帮助理解。

---

---
title: "Memory Overview"
summary: "How OpenClaw remembers things across sessions"
read_when:
  - You want to understand how memory works
  - You want to know what memory files to write
---

# Memory Overview

OpenClaw remembers things by writing **plain Markdown files** in your agent's
workspace. The model only "remembers" what gets saved to disk -- there is no
hidden state.

【注：核心设计哲学 —— OpenClaw 的记忆不是数据库里的隐藏状态，而是写到磁盘上的 Markdown 文件。模型每次启动都重新读取这些文件，所以"记住"等于"写进文件"。】

## How it works

Your agent has three memory-related files:

- **`MEMORY.md`** -- long-term memory. Durable facts, preferences, and
  decisions. Loaded at the start of every DM session.

【注：MEMORY.md 是长期记忆，只在私聊（DM）会话启动时加载。群聊不加载，防止个人信息泄露。存放"不变的"事实和偏好。】

- **`memory/YYYY-MM-DD.md`** -- daily notes. Running context and observations.
  Today and yesterday's notes are loaded automatically.

【注：每日日志，记录当天发生的一切。今天和昨天的自动加载，超过两天的不自动加载（减少 token 消耗）。】

- **`DREAMS.md`** (experimental, optional) -- Dream Diary and dreaming sweep
  summaries for human review, including grounded historical backfill entries.

【注：实验性功能。 dreaming 系统的摘要输出，供人类审查 AI 觉得什么值得记住。不是必需文件。】

These files live in the agent workspace (default `~/.openclaw/workspace`).

## Memory tools

The agent has two tools for working with memory:

- **`memory_search`** -- finds relevant notes using semantic search, even when
  the wording differs from the original.

【注：语义搜索工具。配置了 embedding provider 后使用 hybrid search（向量+关键词），否则退化为关键词搜索。】

- **`memory_get`** -- reads a specific memory file or line range.

【注：精确读取工具。用于读取特定文件的特定行范围，不是搜索，是直接定位。】

Both tools are provided by the active memory plugin (default: `memory-core`).

## Memory Wiki companion plugin

If you want durable memory to behave more like a maintained knowledge base than
just raw notes, use the bundled `memory-wiki` plugin.

`memory-wiki` compiles durable knowledge into a wiki vault with:

- deterministic page structure
- structured claims and evidence
- contradiction and freshness tracking
- generated dashboards
- compiled digests for agent/runtime consumers
- wiki-native tools like `wiki_search`, `wiki_get`, `wiki_apply`, and `wiki_lint`

It does not replace the active memory plugin. The active memory plugin still
owns recall, promotion, and dreaming. `memory-wiki` adds a provenance-rich
knowledge layer beside it.

【注：memory-wiki 是可选插件，把原始笔记升级为"知识库"，有结构化声明、矛盾检测、仪表盘等功能。但它不替代 memory-core，是增强层。】

## Memory search

When an embedding provider is configured, `memory_search` uses **hybrid
search** -- combining vector similarity (semantic meaning) with keyword matching
(exact terms like IDs and code symbols). This works out of the box once you have
an API key for any supported provider.

【注：关键段落！Hybrid search = 向量相似度（语义）+ 关键词匹配（精确）。"一旦配置了任意支持的 provider 的 API key，就能开箱即用。"】

<Info>
OpenClaw auto-detects your embedding provider from available API keys. If you
have an OpenAI, Gemini, Voyage, or Mistral key configured, memory search is
enabled automatically.
</Info>

【注：自动检测机制。检测到 OPENAI_API_KEY 等环境变量或配置文件中的 key，就自动启用。不需要手动开启。】

## Memory backends

【注：三种后端可选。默认是 Builtin（SQLite），高级用户可选 QMD（重排序+外部目录索引），多用户场景可选 Honcho（AI-native 用户建模）。】

## Automatic memory flush

Before [compaction](/concepts/compaction) summarizes your conversation, OpenClaw
runs a silent turn that reminds the agent to save important context to memory
files. This is on by default -- you do not need to configure anything.

【注：自动 flush —— compaction（对话压缩）前，系统自动执行一个"静默回合"，提醒 agent 把重要上下文保存到 memory 文件。默认开启，零配置。】

## Dreaming (experimental)

Dreaming is an optional background consolidation pass for memory. It collects
short-term signals, scores candidates, and promotes only qualified items into
long-term memory (`MEMORY.md`).

It is designed to keep long-term memory high signal:

- **Opt-in**: disabled by default.
- **Scheduled**: when enabled, `memory-core` auto-manages one recurring cron job
  for a full dreaming sweep.
- **Thresholded**: promotions must pass score, recall frequency, and query
  diversity gates.
- **Reviewable**: phase summaries and diary entries are written to `DREAMS.md`
  for human review.

【注：dreaming 是后台自动整理机制。从短期记忆（每日日志）中筛选"高分"内容，晋升到长期记忆（MEMORY.md）。默认关闭，开启后自动创建 cron job。人类可通过 DREAMS.md 审查 AI 的整理结果。】

## CLI

```bash
openclaw memory status          # Check index status and provider
openclaw memory search "query"  # Search from the command line
openclaw memory index --force   # Rebuild the index
```

【注：三个常用命令。status 查看索引状态和 provider 是否就绪；search 命令行搜索；index --force 强制重建索引（换模型后需要）。】

---

> **中文注释完成。** 如需进一步解释某个段落，请告诉我。
