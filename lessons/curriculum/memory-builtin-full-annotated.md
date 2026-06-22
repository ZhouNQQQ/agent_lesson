# Builtin Memory Engine — 完整原文 + 中文注释

> **原始来源**：/usr/lib/node_modules/openclaw/docs/concepts/memory-builtin.md
> **原始标题**：Builtin Memory Engine
> **整理时间**：2026-06-01
> **说明**：以下内容为 OpenClaw 官方文档的完整原文，我在关键段落旁添加了中文注释（以 `【注：】` 标记）。

---

---
title: "Builtin Memory Engine"
summary: "The default SQLite-based memory backend with keyword, vector, and hybrid search"
read_when:
  - You want to understand the default memory backend
  - You want to configure embedding providers or hybrid search
---

# Builtin Memory Engine

The builtin engine is the default memory backend. It stores your memory index in
a per-agent SQLite database and needs no extra dependencies to get started.

【注：默认后端是 SQLite，零额外依赖即可启动。这是开箱即用的设计。】

## What it provides

- **Keyword search** via FTS5 full-text indexing (BM25 scoring).

【注：关键词搜索 —— 使用 SQLite 的 FTS5 全文索引，BM25 打分。不需要任何 API Key，始终可用。】

- **Vector search** via embeddings from any supported provider.

【注：向量搜索 —— 需要 embedding provider（OpenAI/Gemini/Local 等），将文本转为向量后做相似度计算。】

- **Hybrid search** that combines both for best results.

【注：混合搜索 —— 同时跑关键词搜索和向量搜索，然后加权合并结果。这是默认推荐模式，但需要 embedding provider。】

- **CJK support** via trigram tokenization for Chinese, Japanese, and Korean.

【注：中日韩支持 —— 使用 trigram（三字一组）分词，对中文搜索更友好。】

- **sqlite-vec acceleration** for in-database vector queries (optional).

【注：可选加速 —— sqlite-vec 是 SQLite 的向量扩展，能在数据库内直接做向量查询，更快。】

## Getting started

If you have an API key for OpenAI, Gemini, Voyage, or Mistral, the builtin
engine auto-detects it and enables vector search. No config needed.

【注：再次强调自动检测。有 API key = 自动启用向量搜索。零配置。】

To set a provider explicitly:

```json5
{
  agents: {
    defaults: {
      memorySearch: {
        provider: "openai",
      },
    },
  },
}
```

Without an embedding provider, only keyword search is available.

【注：没有 embedding provider 时，只有关键词搜索可用。这是一个重要的降级策略 —— 功能不中断，只是变笨。】

## Supported embedding providers

| Provider | ID        | Auto-detected | Notes                               |
| -------- | --------- | ------------- | ----------------------------------- |
| OpenAI   | `openai`  | Yes           | Default: `text-embedding-3-small`   |
| Gemini   | `gemini`  | Yes           | Supports multimodal (image + audio) |
| Voyage   | `voyage`  | Yes           |                                     |
| Mistral  | `mistral` | Yes           |                                     |
| Ollama   | `ollama`  | No            | Local, set explicitly               |
| Local    | `local`   | Yes (first)   | GGUF model, ~0.6 GB download        |

Auto-detection picks the first provider whose API key can be resolved, in the
order shown. Set `memorySearch.provider` to override.

【注：provider 优先级表。Local 也能被自动检测（如果安装了 node-llama-cpp 且有模型文件），但默认排第一的是 Local，然后是 OpenAI 等。可以用配置强制指定。】

## How indexing works

OpenClaw indexes `MEMORY.md` and `memory/*.md` into chunks (~400 tokens with
80-token overlap) and stores them in a per-agent SQLite database.

【注：索引机制 —— 文件被切成约 400 token 的块，80 token 重叠。这样小块更精准，重叠保证上下文不丢失。存储在 SQLite 里。】

- **Index location:** `~/.openclaw/memory/<agentId>.sqlite`

【注：索引数据库位置。每个 agent 一个 sqlite 文件。】

- **File watching:** changes to memory files trigger a debounced reindex (1.5s).

【注：文件监控 —— 修改 memory 文件后 1.5 秒自动重建索引。防抖设计避免频繁写入时反复重建。】

- **Auto-reindex:** when the embedding provider, model, or chunking config
  changes, the entire index is rebuilt automatically.

【注：配置变更自动重建 —— 换了 embedding 模型或切分策略，自动全量重建。因为向量表示变了，旧索引无效。】

- **Reindex on demand:** `openclaw memory index --force`

【注：手动强制重建 —— 如果自动重建没触发（罕见情况），可以手动重建。】

## When to use

The builtin engine is the right choice for most users:

- Works out of the box with no extra dependencies.
- Handles keyword and vector search well.
- Supports all embedding providers.
- Hybrid search combines the best of both retrieval approaches.

Consider switching to [QMD](/concepts/memory-qmd) if you need reranking, query
expansion, or want to index directories outside the workspace.

Consider [Honcho](/concepts/memory-honcho) if you want cross-session memory with
automatic user modeling.

【注：选型指南。大多数人用默认就好。需要重排序/查询扩展/外部目录索引 → QMD。需要跨会话自动用户建模 → Honcho。】

## Troubleshooting

**Memory search disabled?** Check `openclaw memory status`. If no provider is
detected, set one explicitly or add an API key.

【注：排查步骤。memory search 不工作时，先运行 `openclaw memory status` 查看 provider 状态。】

**Stale results?** Run `openclaw memory index --force` to rebuild. The watcher
may miss changes in rare edge cases.

【注：结果过时 —— 文件监控可能偶尔漏掉变更，手动重建解决。】

---

> **中文注释完成。** 如需进一步解释某个段落，请告诉我。
