# Compaction — 完整原文 + 中文注释

> **原始来源**：/usr/lib/node_modules/openclaw/docs/concepts/compaction.md
> **原始标题**：Compaction
> **整理时间**：2026-06-02
> **说明**：以下内容为 OpenClaw 官方文档的完整原文，我在关键段落旁添加了中文注释（以 `【注：】` 标记）。

---

---
summary: "How OpenClaw summarizes long conversations to stay within model limits"
read_when:
  - You want to understand auto-compaction and /compact
  - You are debugging long sessions hitting context limits
title: "Compaction"
---

# Compaction

Every model has a context window -- the maximum number of tokens it can process.
When a conversation approaches that limit, OpenClaw **compacts** older messages
into a summary so the chat can continue.

【注：核心概念 —— LLM 有最大上下文限制（token 上限）。当对话太长时，OpenClaw 把旧消息"压缩"成摘要，腾出新空间继续聊。】

## How it works

1. Older conversation turns are summarized into a compact entry.
2. The summary is saved in the session transcript.
3. Recent messages are kept intact.

【注：三步过程 —— (1) 旧对话被摘要 (2) 摘要存入会话记录 (3) 最近消息保持原样。注意：完整历史还在磁盘上，只是模型看到的变短了。】

When OpenClaw splits history into compaction chunks, it keeps assistant tool
calls paired with their matching `toolResult` entries. If a split point lands
inside a tool block, OpenClaw moves the boundary so the pair stays together and
the current unsummarized tail is preserved.

【注：关键细节 —— 压缩时保持 tool call 和 tool result 成对。如果切割点在工具调用中间，会移动边界确保不拆散。这是为了避免模型看到"调用了工具但没结果"的混乱状态。】

The full conversation history stays on disk. Compaction only changes what the
model sees on the next turn.

【注：重要 —— 压缩不删除历史！完整记录还在磁盘上。只是下一次发给模型的 prompt 变短了（用摘要代替原始对话）。】

## Auto-compaction

Auto-compaction is on by default. It runs when the session nears the context
limit, or when the model returns a context-overflow error (in which case
OpenClaw compacts and retries). Typical overflow signatures include
`request_too_large`, `context length exceeded`, `input exceeds the maximum
number of tokens`, `input token count exceeds the maximum number of input
tokens`, `input is too long for the model`, and `ollama error: context length
exceeded`.

【注：自动压缩默认开启。触发条件有两个：(1) 接近上下文上限 (2) 模型返回溢出错误（此时会压缩后重试）。列出的错误签名都是常见 LLM 的"太长了"报错。】

<Info>
Before compacting, OpenClaw automatically reminds the agent to save important
notes to [memory](/concepts/memory) files. This prevents context loss.
</Info>

【注：关键设计 —— 压缩前会自动触发一次"静默回合"，提醒 agent 把重要内容保存到 memory 文件。这是防止压缩导致信息丢失的核心机制。】

Use the `agents.defaults.compaction` setting in your `openclaw.json` to configure compaction behavior (mode, target tokens, etc.).
Compaction summarization preserves opaque identifiers by default (`identifierPolicy: "strict"`). You can override this with `identifierPolicy: "off"` or provide custom text with `identifierPolicy: "custom"` and `identifierInstructions`.

【注：两个配置点：(1) compaction 行为模式、目标 token 数等 (2) 标识符保留策略。默认"严格"保留 ID/错误码等不透明标识符，防止摘要时把它们弄丢了。】

You can optionally specify a different model for compaction summarization via `agents.defaults.compaction.model`. This is useful when your primary model is a local or small model and you want compaction summaries produced by a more capable model. The override accepts any `provider/model-id` string:

【注：高级技巧 —— 可以用更强的模型（如 Claude Sonnet）来做压缩摘要，主模型保持轻量。这样压缩质量更高，主模型更快更便宜。】

## Pluggable compaction providers

Plugins can register a custom compaction provider via `registerCompactionProvider()` on the plugin API. When a provider is registered and configured, OpenClaw delegates summarization to it instead of the built-in LLM pipeline.

【注：插件扩展点 —— 第三方可以注册自定义压缩器，完全替代内置的 LLM 摘要逻辑。】

## Auto-compaction (default on)

When a session nears or exceeds the model's context window, OpenClaw triggers auto-compaction and may retry the original request using the compacted context.

You'll see:

- `🧹 Auto-compaction complete` in verbose mode
- `/status` showing `🧹 Compactions: <count>`

【注：用户可见的压缩提示。verbose 模式会显示扫帚 emoji，/status 显示压缩次数。】

Before compaction, OpenClaw can run a **silent memory flush** turn to store
durable notes to disk. See [Memory](/concepts/memory) for details and config.

【注：再次强调 —— 压缩前的 memory flush 是防止上下文丢失的关键。没有它，压缩后 agent 可能忘了刚才学到的东西。】

## Manual compaction

Type `/compact` in any chat to force a compaction. Add instructions to guide
the summary:

```
/compact Focus on the API design decisions
```

【注：手动压缩命令。可以附加指令指导摘要重点，比如"只保留 API 设计决策"。】

## Compaction start notice

By default, compaction runs silently. To show a brief notice when compaction
starts, enable `notifyUser`:

【注：默认静默压缩，用户无感知。开启 notifyUser 后会在压缩开始时提示用户。】

## Compaction vs pruning

|                  | Compaction                    | Pruning                          |
| ---------------- | ----------------------------- | -------------------------------- |
| **What it does** | Summarizes older conversation | Trims old tool results           |
| **Saved?**       | Yes (in session transcript)   | No (in-memory only, per request) |
| **Scope**        | Entire conversation           | Tool results only                |

【注：对比表 —— Compaction 是"摘要"（保存到磁盘），Pruning 是"修剪"（内存中临时删除旧工具结果）。Pruning 更轻量，只删工具输出不摘要对话。】

[Session pruning](/concepts/session-pruning) is a lighter-weight complement that
trims tool output without summarizing.

## Troubleshooting

**Compacting too often?** The model's context window may be small, or tool
outputs may be large. Try enabling
[session pruning](/concepts/session-pruning).

【注：压缩太频繁？说明上下文窗口太小或工具输出太大。启用 pruning 可以减少工具输出占用。】

**Context feels stale after compaction?** Use `/compact Focus on <topic>` to
guide the summary, or enable the [memory flush](/concepts/memory) so notes
survive.

【注：压缩后感觉上下文"变薄"了？用指令引导摘要重点，或开启 memory flush 确保关键信息写入文件。】

**Need a clean slate?** `/new` starts a fresh session without compacting.

【注：/new 开新会话，不压缩旧会话。】

---

> **中文注释完成。** 如需进一步解释某个段落，请告诉我。
