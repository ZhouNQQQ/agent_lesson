# QMD Memory Engine — 完整原文 + 中文注释

> **原始来源**：/usr/lib/node_modules/openclaw/docs/concepts/memory-qmd.md
> **原始标题**：QMD Memory Engine
> **整理时间**：2026-06-02
> **说明**：以下内容为 OpenClaw 官方文档的完整原文，我在关键段落旁添加了中文注释（以 `【注：】` 标记）。

---

---
title: "QMD Memory Engine"
summary: "Local-first search sidecar with BM25, vectors, reranking, and query expansion"
read_when:
  - You want to set up QMD as your memory backend
  - You want advanced memory features like reranking or extra indexed paths
---

# QMD Memory Engine

[QMD](https://github.com/tobi/qmd) is a local-first search sidecar that runs
alongside OpenClaw. It combines BM25, vector search, and reranking in a single
binary, and can index content beyond your workspace memory files.

【注：QMD 定位 —— "本地优先"的搜索副驾。作为独立进程运行，不依赖云端 API，完全离线可用。核心能力：BM25 + 向量 + 重排序 + 查询扩展。】

## What it adds over builtin

- **Reranking and query expansion** for better recall.
- **Index extra directories** -- project docs, team notes, anything on disk.
- **Index session transcripts** -- recall earlier conversations.
- **Fully local** -- runs via Bun + node-llama-cpp, auto-downloads GGUF models.
- **Automatic fallback** -- if QMD is unavailable, OpenClaw falls back to the
  builtin engine seamlessly.

【注：五大增强 —— (1) 重排序让搜索结果更精准 (2) 扩展索引范围到任意目录 (3) 会话历史可搜索 (4) 完全离线 (5) 故障自动降级到 Builtin。】

## Getting started

### Prerequisites

- Install QMD: `npm install -g @tobilu/qmd` or `bun install -g @tobilu/qmd`
- SQLite build that allows extensions (`brew install sqlite` on macOS).
- QMD must be on the gateway's `PATH`.
- macOS and Linux work out of the box. Windows is best supported via WSL2.

【注：前置条件 —— 需要装 QMD 二进制、SQLite 扩展支持、PATH 配置。Windows 推荐 WSL2。】

### Enable

```json5
{
  memory: {
    backend: "qmd",
  },
}
```

OpenClaw creates a self-contained QMD home under
`~/.openclaw/agents/<agentId>/qmd/` and manages the sidecar lifecycle
automatically.

【注：启用方式 —— 只需改 backend 为 "qmd"。OpenClaw 自动管理 QMD 进程生命周期（启动、索引、关闭）。】

## How the sidecar works

- OpenClaw creates collections from your workspace memory files and any
  configured `memory.qmd.paths`, then runs `qmd update` + `qmd embed` on boot
  and periodically (default every 5 minutes).
- The default workspace collection tracks `MEMORY.md` plus the `memory/`
  tree. Lowercase `memory.md` remains a bootstrap fallback, not a separate QMD
  collection.
- Boot refresh runs in the background so chat startup is not blocked.
- Searches use the configured `searchMode` (default: `search`; also supports
  `vsearch` and `query`). If a mode fails, OpenClaw retries with `qmd query`.
- If QMD fails entirely, OpenClaw falls back to the builtin SQLite engine.

【注：工作机制 —— (1) 自动创建 collections (2) 定期 update + embed (3) 后台运行不阻塞启动 (4) 搜索模式可配置 (5) 故障降级。注意大小写敏感：MEMORY.md 被索引，memory.md 是 bootstrap fallback。】

<Info>
The first search may be slow -- QMD auto-downloads GGUF models (~2 GB) for
reranking and query expansion on the first `qmd query` run.
</Info>

【注：首次启动会下载约 2GB 的 GGUF 模型（重排序器 + 查询扩展器），所以第一次搜索可能慢。】

## Model overrides

QMD model environment variables pass through unchanged from the gateway
process, so you can tune QMD globally without adding new OpenClaw config:

```bash
export QMD_EMBED_MODEL="hf:Qwen/Qwen3-Embedding-0.6B-GGUF/Qwen3-Embedding-0.6B-Q8_0.gguf"
export QMD_RERANK_MODEL="/absolute/path/to/reranker.gguf"
export QMD_GENERATE_MODEL="/absolute/path/to/generator.gguf"
```

After changing the embedding model, rerun embeddings so the index matches the
new vector space.

【注：模型覆盖 —— 通过环境变量调 QMD 的模型，不需要改 OpenClaw 配置。换模型后需要重新 embedding。】

## Indexing extra paths

Point QMD at additional directories to make them searchable:

```json5
{
  memory: {
    backend: "qmd",
    qmd: {
      paths: [{ name: "docs", path: "~/notes", pattern: "**/*.md" }],
    },
  },
}
```

Snippets from extra paths appear as `qmd/<collection>/<relative-path>` in
search results. `memory_get` understands this prefix and reads from the correct
collection root.

【注：扩展索引路径 —— 可以索引 workspace 外的任意目录。搜索结果带 `qmd/<collection>/` 前缀，memory_get 能自动解析。】

## Indexing session transcripts

Enable session indexing to recall earlier conversations:

```json5
{
  memory: {
    backend: "qmd",
    qmd: {
      sessions: { enabled: true },
    },
  },
}
```

Transcripts are exported as sanitized User/Assistant turns into a dedicated QMD
collection under `~/.openclaw/agents/<id>/qmd/sessions/`.

【注：会话索引 —— 开启后把历史对话也纳入搜索。导出时会脱敏处理（sanitized）。】

## Search scope

By default, QMD search results are surfaced in direct and channel sessions
(not groups). Configure `memory.qmd.scope` to change this:

【注：默认只在私聊和频道会话中暴露 QMD 结果，群聊中不暴露（安全考虑）。】

## When to use

Choose QMD when you need:

- Reranking for higher-quality results.
- To search project docs or notes outside the workspace.
- To recall past session conversations.
- Fully local search with no API keys.

For simpler setups, the [builtin engine](/concepts/memory-builtin) works well
with no extra dependencies.

【注：选型指南 —— 需要重排序/外部目录/会话回忆/完全离线 → QMD。简单场景 → Builtin 够用。】

## Troubleshooting

**QMD not found?** Ensure the binary is on the gateway's `PATH`.

**First search very slow?** QMD downloads GGUF models on first use. Pre-warm
with `qmd query "test"` using the same XDG dirs OpenClaw uses.

【注：常见问题 —— QMD 二进制找不到（PATH 问题）、首次搜索慢（模型下载）。可以预热解决。】

---

> **中文注释完成。** 如需进一步解释某个段落，请告诉我。
