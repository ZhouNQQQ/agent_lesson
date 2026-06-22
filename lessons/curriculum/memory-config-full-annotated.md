# Memory configuration reference — 完整原文 + 中文注释

> **原始来源**：/usr/lib/node_modules/openclaw/docs/reference/memory-config.md
> **原始标题**：Memory configuration reference
> **整理时间**：2026-06-02
> **说明**：以下内容为 OpenClaw 官方文档的完整原文，我在关键段落旁添加了中文注释（以 `【注：】` 标记）。这是记忆系统最完整的配置参考文档。

---

---
title: "Memory configuration reference"
summary: "All configuration knobs for memory search, embedding providers, QMD, hybrid search, and multimodal indexing"
read_when:
  - You want to configure memory search providers or embedding models
  - You want to set up the QMD backend
  - You want to tune hybrid search, MMR, or temporal decay
  - You want to enable multimodal memory indexing
---

# Memory configuration reference

This page lists every configuration knob for OpenClaw memory search. For
conceptual overviews, see:

- [Memory Overview](/concepts/memory) -- how memory works
- [Builtin Engine](/concepts/memory-builtin) -- default SQLite backend
- [QMD Engine](/concepts/memory-qmd) -- local-first sidecar
- [Memory Search](/concepts/memory-search) -- search pipeline and tuning
- [Active Memory](/concepts/active-memory) -- enabling the memory sub-agent for interactive sessions

All memory search settings live under `agents.defaults.memorySearch` in
`openclaw.json` unless noted otherwise.

【注：核心配置入口 —— 绝大多数记忆搜索配置都在 `agents.defaults.memorySearch` 下。例外：dreaming 配置在 `plugins.entries.memory-core.config.dreaming`，active memory 配置在 `plugins.entries.active-memory`。注意区分层级。】

---

## Provider selection

| Key        | Type      | Default          | Description                                                                                 |
| ---------- | --------- | ---------------- | ------------------------------------------------------------------------------------------- |
| `provider` | `string`  | auto-detected    | Embedding adapter ID: `openai`, `gemini`, `voyage`, `mistral`, `bedrock`, `ollama`, `local` |
| `model`    | `string`  | provider default | Embedding model name                                                                        |
| `fallback` | `string`  | `"none"`         | Fallback adapter ID when the primary fails                                                  |
| `enabled`  | `boolean` | `true`           | Enable or disable memory search                                                             |

### Auto-detection order

When `provider` is not set, OpenClaw selects the first available:

1. `local` -- if `memorySearch.local.modelPath` is configured and the file exists.
2. `openai` -- if an OpenAI key can be resolved.
3. `gemini` -- if a Gemini key can be resolved.
4. `voyage` -- if a Voyage key can be resolved.
5. `mistral` -- if a Mistral key can be resolved.
6. `bedrock` -- if the AWS SDK credential chain resolves (instance role, access keys, profile, SSO, web identity, or shared config).

`ollama` is supported but not auto-detected (set it explicitly).

【注：自动检测优先级 —— Local 排第一！如果配置了本地模型路径且文件存在，优先用本地。然后才是 OpenAI、Gemini 等云端。Ollama 不支持自动检测，必须显式配置。】

### API key resolution

Remote embeddings require an API key. Bedrock uses the AWS SDK default
credential chain instead (instance roles, SSO, access keys).

| Provider | Env var                        | Config key                        |
| -------- | ------------------------------ | --------------------------------- |
| OpenAI   | `OPENAI_API_KEY`               | `models.providers.openai.apiKey`  |
| Gemini   | `GEMINI_API_KEY`               | `models.providers.google.apiKey`  |
| Voyage   | `VOYAGE_API_KEY`               | `models.providers.voyage.apiKey`  |
| Mistral  | `MISTRAL_API_KEY`              | `models.providers.mistral.apiKey` |
| Bedrock  | AWS credential chain           | No API key needed                 |
| Ollama   | `OLLAMA_API_KEY` (placeholder) | --                                |

Codex OAuth covers chat/completions only and does not satisfy embedding
requests.

【注：Key 来源 —— 可以是环境变量或配置文件。注意 Codex OAuth 只覆盖对话，不覆盖 embedding！这是常见坑点。】

---

## Remote endpoint config

For custom OpenAI-compatible endpoints or overriding provider defaults:

| Key              | Type     | Description                                        |
| ---------------- | -------- | -------------------------------------------------- |
| `remote.baseUrl` | `string` | Custom API base URL                                |
| `remote.apiKey`  | `string` | Override API key                                   |
| `remote.headers` | `object` | Extra HTTP headers (merged with provider defaults) |

【注：自定义端点模式示例：`provider: "openai"` + `remote.baseUrl: "<your-api-base-url>"` + `remote.apiKey: "<your-api-key>"` —— 这是 OpenAI 协议兼容的自定义端点模式，可对接任意兼容 OpenAI 接口的网关。】

---

## Hybrid search config

All under `memorySearch.query.hybrid`:

| Key                   | Type      | Default | Description                        |
| --------------------- | --------- | ------- | ---------------------------------- |
| `enabled`             | `boolean` | `true`  | Enable hybrid BM25 + vector search |
| `vectorWeight`        | `number`  | `0.7`   | Weight for vector scores (0-1)     |
| `textWeight`          | `number`  | `0.3`   | Weight for BM25 scores (0-1)       |
| `candidateMultiplier` | `number`  | `4`     | Candidate pool size multiplier     |

【注：混合搜索权重 —— 默认向量占 70%，BM25 占 30%。可以调整。如果关键词精确匹配更重要，可以提高 textWeight。】

### MMR (diversity)

| Key           | Type      | Default | Description                          |
| ------------- | --------- | ------- | -------------------------------------|
| `mmr.enabled` | `boolean` | `false` | Enable MMR re-ranking                |
| `mmr.lambda`  | `number`  | `0.7`   | 0 = max diversity, 1 = max relevance |

【注：MMR 多样性重排序 —— 默认关闭。开启后防止搜索结果重复。lambda 调平衡：0 最分散（不同主题），1 最相关（可能重复）。】

### Temporal decay (recency)

| Key                          | Type      | Default | Description               |
| ---------------------------- | --------- | ------- | ------------------------- |
| `temporalDecay.enabled`      | `boolean` | `false` | Enable recency boost      |
| `temporalDecay.halfLifeDays` | `number`  | `30`    | Score halves every N days |

Evergreen files (`MEMORY.md`, non-dated files in `memory/`) are never decayed.

【注：时间衰减 —— 默认关闭。开启后旧笔记权重按半衰期衰减。但 MEMORY.md 等"常青"文件不衰减。】

---

## Additional memory paths

| Key          | Type       | Description                              |
| ------------ | ---------- | ---------------------------------------- |
| `extraPaths` | `string[]` | Additional directories or files to index |

Paths can be absolute or workspace-relative. Directories are scanned
recursively for `.md` files.

【注：额外索引路径 —— 可以让记忆搜索扩展到 workspace 外的目录，比如团队文档、项目笔记。】

---

## Embedding cache

| Key                | Type      | Default | Description                      |
| ------------------ | --------- | ------- | -------------------------------- |
| `cache.enabled`    | `boolean` | `false` | Cache chunk embeddings in SQLite |
| `cache.maxEntries` | `number`  | `50000` | Max cached embeddings            |

Prevents re-embedding unchanged text during reindex or transcript updates.

【注：Embedding 缓存 —— 默认关闭。开启后避免重复计算 embedding，加速重建索引。适合大文档库。】

---

## Session memory search (experimental)

Index session transcripts and surface them via `memory_search`:

| Key                           | Type       | Default      | Description                             |
| ----------------------------- | ---------- | ------------ | --------------------------------------- |
| `experimental.sessionMemory`  | `boolean`  | `false`      | Enable session indexing                 |
| `sources`                     | `string[]` | `["memory"]` | Add `"sessions"` to include transcripts |

【注：会话记忆索引 —— 实验功能。默认只索引 memory 文件。开启后可以把完整对话历史也纳入搜索范围。】

---

## Dreaming (experimental)

Configured under `plugins.entries.memory-core.config.dreaming`:

| Key         | Type      | Default     | Description                                       |
| ----------- | --------- | ----------- | ------------------------------------------------- |
| `enabled`   | `boolean` | `false`     | Enable or disable dreaming entirely               |
| `frequency` | `string`  | `0 3 * * *` | Optional cron cadence for the full dreaming sweep |

【注：Dreaming 配置 —— 注意路径不同！不在 `agents.defaults.memorySearch` 下，而在 `plugins.entries.memory-core.config.dreaming` 下。】

---

## 关键配置示例汇总

### 开启 Hybrid + MMR + 时间衰减

```json5
{
  agents: {
    defaults: {
      memorySearch: {
        query: {
          hybrid: {
            vectorWeight: 0.7,
            textWeight: 0.3,
            mmr: { enabled: true, lambda: 0.7 },
            temporalDecay: { enabled: true, halfLifeDays: 30 },
          },
        },
      },
    },
  },
}
```

### 你的当前配置（kimi 代理 embedding）

```json5
{
  agents: {
    defaults: {
      memorySearch: {
        provider: "openai",
        model: "bge_m3_embed",
        remote: {
          baseUrl: "<your-api-base-url>",
          apiKey: "<your-api-key>",
          headers: {
            "User-Agent": "your-app-name",
            "X-Custom-Header": "your-value"
          }
        }
      }
    }
  }
}
```

【注：你的配置解析 —— provider 声明为 openai（协议兼容），实际 endpoint 是 kimi 网关，模型是 bge_m3_embed（国产 1024 维 embedding 模型）。】

---

> **中文注释完成。** 如需进一步解释某个配置项，请告诉我。
