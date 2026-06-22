# Dreaming (experimental) — 完整原文 + 中文注释

> **原始来源**：/usr/lib/node_modules/openclaw/docs/concepts/dreaming.md
> **原始标题**：Dreaming (experimental)
> **整理时间**：2026-06-02
> **说明**：以下内容为 OpenClaw 官方文档的完整原文，我在关键段落旁添加了中文注释（以 `【注：】` 标记）。

---

---
title: "Dreaming (experimental)"
summary: "Background memory consolidation with light, deep, and REM phases plus a Dream Diary"
read_when:
  - You want memory promotion to run automatically
  - You want to understand what each dreaming phase does
  - You want to tune consolidation without polluting MEMORY.md
---

# Dreaming (experimental)

Dreaming is the background memory consolidation system in `memory-core`.
It helps OpenClaw move strong short-term signals into durable memory while
keeping the process explainable and reviewable.

【注：核心概念 —— Dreaming 是"后台记忆整理系统"，类比人睡觉时的记忆巩固。它自动把短期记忆（每日日志）中有价值的信号晋升为长期记忆（MEMORY.md）。】

Dreaming is **opt-in** and disabled by default.

【注：默认关闭！不是自动运行的。需要手动在配置中开启。】

## What dreaming writes

Dreaming keeps two kinds of output:

- **Machine state** in `memory/.dreams/` (recall store, phase signals, ingestion checkpoints, locks).
- **Human-readable output** in `DREAMS.md` (or existing `dreams.md`) and optional phase report files under `memory/dreaming/<phase>/YYYY-MM-DD.md`.

Long-term promotion still writes only to `MEMORY.md`.

【注：三类输出位置 —— (1) 机器状态在 .dreams/ 目录 (2) 人类可读日记在 DREAMS.md (3) 长期晋升只写 MEMORY.md。分工明确。】

## Phase model

Dreaming uses three cooperative phases:

| Phase | Purpose                                   | Durable write     |
| ----- | ----------------------------------------- | ----------------- |
| Light | Sort and stage recent short-term material | No                |
| Deep  | Score and promote durable candidates      | Yes (`MEMORY.md`) |
| REM   | Reflect on themes and recurring ideas     | No                |

【注：三阶段模型 —— 类比人睡眠的浅睡/深睡/快速眼动期。Light 整理材料，Deep 决定晋升，REM 提取模式。只有 Deep 阶段会写长期记忆。】

These phases are internal implementation details, not separate user-configured
"modes."

【注：这是内部实现，用户不能单独配置"只跑 Light 不跑 Deep"，三阶段是绑定的。】

### Light phase

Light phase ingests recent daily memory signals and recall traces, dedupes them,
and stages candidate lines.

- Reads from short-term recall state, recent daily memory files, and redacted session transcripts when available.
- Writes a managed `## Light Sleep` block when storage includes inline output.
- Records reinforcement signals for later deep ranking.
- Never writes to `MEMORY.md`.

【注：Light 阶段 —— "吃"进短期信号，去重， staging（暂存）。产出是候选列表和强化信号，不写长期记忆。】

### Deep phase

Deep phase decides what becomes long-term memory.

- Ranks candidates using weighted scoring and threshold gates.
- Requires `minScore`, `minRecallCount`, and `minUniqueQueries` to pass.
- Rehydrates snippets from live daily files before writing, so stale/deleted snippets are skipped.
- Appends promoted entries to `MEMORY.md`.
- Writes a `## Deep Sleep` summary into `DREAMS.md` and optionally writes `memory/dreaming/deep/YYYY-MM-DD.md`.

【注：Deep 阶段 —— 核心决策阶段。有门槛：分数够高、被召回够多次、被不同查询触发过。从原始文件"补水"（rehydrate）确保不晋升已删除的内容。】

### REM phase

REM phase extracts patterns and reflective signals.

- Builds theme and reflection summaries from recent short-term traces.
- Writes a managed `## REM Sleep` block when storage includes inline output.
- Records REM reinforcement signals used by deep ranking.
- Never writes to `MEMORY.md`.

【注：REM 阶段 —— 提取模式和反思。发现重复主题、隐性关联。不写长期记忆，但产生的信号会影响 Deep 阶段的排名。】

## Deep ranking signals

Deep ranking uses six weighted base signals plus phase reinforcement:

| Signal              | Weight | Description                                       |
| ------------------- | ------ | ------------------------------------------------- |
| Frequency           | 0.24   | How many short-term signals the entry accumulated |
| Relevance           | 0.30   | Average retrieval quality for the entry           |
| Query diversity     | 0.15   | Distinct query/day contexts that surfaced it      |
| Recency             | 0.15   | Time-decayed freshness score                      |
| Consolidation       | 0.10   | Multi-day recurrence strength                     |
| Conceptual richness | 0.06   | Concept-tag density from snippet/path             |

【注：晋升评分公式 —— 六维加权。Relevance（检索质量）权重最高 0.30，Frequency（出现频次）0.24，Query diversity（被不同方式问到的次数）0.15。总分够高 + 门槛通过才能晋升。】

Light and REM phase hits add a small recency-decayed boost from
`memory/.dreams/phase-signals.json`.

【注：Light 和 REM 阶段的额外加分 —— 如果某个候选在 Light/REM 阶段被多次命中，会有小额加分。】

## Scheduling

When enabled, `memory-core` auto-manages one cron job for a full dreaming
sweep. Each sweep runs phases in order: light -> REM -> deep.

Default cadence behavior:

| Setting              | Default     |
| -------------------- | ----------- |
| `dreaming.frequency` | `0 3 * * *` |

【注：默认每天凌晨 3 点运行一次完整的 dreaming sweep。可配置 cron 表达式调整频率。】

## Quick start

Enable dreaming:

```json
{
  "plugins": {
    "entries": {
      "memory-core": {
        "config": {
          "dreaming": {
            "enabled": true
          }
        }
      }
    }
  }
}
```

【注：开启方式 —— 在 memory-core 插件配置中设置 dreaming.enabled = true。】

## CLI workflow

Use CLI promotion for preview or manual apply:

```bash
openclaw memory promote
openclaw memory promote --apply
openclaw memory promote --limit 5
```

【注：手动晋升 —— promote 预览，promote --apply 执行，--limit 限制数量。可以人工干预自动晋升过程。】

## Key defaults

All settings live under `plugins.entries.memory-core.config.dreaming`.

| Key         | Default     |
| ----------- | ----------- |
| `enabled`   | `false`     |
| `frequency` | `0 3 * * *` |

Phase policy, thresholds, and storage behavior are internal implementation
details (not user-facing config).

【注：用户可见配置只有两个：开不开、多久跑一次。具体的评分阈值、阶段策略是内部实现，用户不能调。】

## Dreams UI

When enabled, the Gateway **Dreams** tab shows:

- current dreaming enabled state
- phase-level status and managed-sweep presence
- short-term, grounded, signal, and promoted-today counts
- next scheduled run timing
- a distinct grounded Scene lane for staged historical replay entries
- an expandable Dream Diary reader backed by `doctor.memory.dreamDiary`

【注：可视化界面 —— Gateway 有 Dreams 标签页，能看到各阶段状态、候选数、已晋升数、下次运行时间等。】

---

> **中文注释完成。** 如需进一步解释某个段落，请告诉我。
