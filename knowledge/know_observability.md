# K.7 可观测性：Trace / Span / Metrics / Logs + badcase 闭环

> 配套讲义：`lessons/05_evaluation/eval_observability_lesson.md`
> 缺口补齐：JD 要求 trace / 结果回放 / 全链路监控 / badcase 平台。

---

## 一、三大支柱（OpenTelemetry 心智）

| 支柱 | 是什么 | Agent 语境记什么 |
|---|---|---|
| Traces | 一次请求的调用树 | 每步 LLM 调用、工具调用、检索、记忆读写 |
| Metrics | 可聚合数值 | 延迟 P50/P95/P99、token、成本/次、成功率、缓存命中 |
| Logs | 离散事件 | prompt 全文、模型原始输出、工具入参出参、异常栈 |

---

## 二、Agent Trace = Span 树

一次运行是一棵 span 树，靠 `trace_id + parent_span_id` 串联：

```
Trace: agent.run (root)
├── llm.plan          ← 决策调哪个工具 (记 tokens)
├── tool.weather_api  ← 工具调用 (记入参/出参/耗时)
├── llm.observe       ← 看结果决定下一步
└── llm.generate      ← 生成最终答案 (记 tokens/cost)
```

每个 span 记：`name / start / duration / status / 属性(tokens/cost/工具名/错误)`。
> 后端类比：就是 APM 分布式追踪（Jaeger/Zipkin）。trace_id 贯穿全链路，span = 每个"RPC"，只不过 RPC 换成 LLM/工具/检索。

---

## 三、结果回放（Replay）

线上 badcase 要能完整重放：当时的 prompt + 检索上下文 + 模型输出 + 工具返回。
所以埋点要存**全量上下文快照（脱敏）**，不能只记"失败了"。否则无法归因（检索漏？prompt 没约束？工具脏数据？）。

---

## 四、badcase 闭环（线上实验体系）

```
线上埋点 → badcase发现(负反馈/规则探针/抽样审) → 归因(trace replay)
→ 进回归集 → 修复 → 离线回归 → 灰度A/B → 回到线上
```

**关键设计点**：
- 发现：用户点踩 / 规则探针（输出空/超长/敏感词/工具连续失败）/ 抽样人审或 LLM 审
- 不再犯：每个修复的 badcase **必须进回归集**，否则会复发
- 确认更好：A/B（线上分流）或 shadow（只跑不影响用户）对比核心指标

---

## 五、把评测接进 CI/CD

每次改 prompt/代码 → 自动跑评测集 → 指标低于门禁 fail。
门禁例：`成功率≥0.85 且 Faithfulness≥0.9 且 成本/次≤阈值`。
把"凭感觉调 prompt"变成"数据驱动迭代"。

---

## 六、面试速答

| 问题 | 要点 |
|---|---|
| 怎么做可观测？ | trace（span树）+ metrics（延迟/成本/成功率）+ logs（全量快照供 replay） |
| 为什么要记全量上下文？ | 出 badcase 要能 replay 归因到具体层级 |
| badcase 怎么闭环？ | 发现→归因→进回归集→修复→离线回归→灰度A/B |
| 关键延迟指标？ | TTFT 首token延迟、TPOT、P95/P99 总延迟 |

---

> 关联：`lessons/05_evaluation/`、`lessons/07_engineering/engineering_lesson.md`、`knowledge/know_evaluation.md`
