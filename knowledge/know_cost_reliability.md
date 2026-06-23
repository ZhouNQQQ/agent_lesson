# K.10 成本·性能·可靠性 + Harness + 长任务状态

> 配套讲义：`lessons/07_engineering/engineering_lesson.md`
> 缺口补齐：JD4 要求"成本/性能/可靠性/Harness/长任务调度/长记忆"；JD6/7 要求"运行时编排/状态持久化/故障恢复"。

---

## 一、Agent Harness 是什么

包裹 LLM 的运行时框架：上下文装配 + 执行循环 + 工具编排 + 状态管理 + 可靠性 + 可观测。
> 模型是引擎，Harness 是底盘+变速箱+安全系统。同一模型，Harness 决定它是 demo 还是生产可用。

---

## 二、长任务状态管理

| 能力 | 含义 | 实现 |
|---|---|---|
| 状态持久化 | 每步落盘 | 记当前步+工具调用+中间结果+上下文 |
| 中断恢复 Resume | 崩溃从断点继续 | checkpoint 恢复 |
| 异常补偿 | 失败回滚/补偿保幂等 | Saga 模式 |

> 后端类比：工作流引擎/状态机/Saga 事务。建模成状态机或 DAG，每节点存 checkpoint。

---

## 三、可靠性三件套

| 机制 | 解决 | 要点 |
|---|---|---|
| 重试 Retry | 瞬时故障 | 指数退避+抖动；限次数；只重试可重试错误 |
| 降级 Fallback | 主路径不可用 | 切备用模型/缓存；**别用 Mock 顶生产** |
| 熔断 Circuit Breaker | 下游持续故障 | 失败率超阈值→打开→快速失败→半开试探→恢复 |

**fail-open vs fail-closed**：
- 非关键增强（记忆/个性化）失败 → fail-open（保可用）
- 安全/权限/扣费失败 → fail-closed（保正确/安全）

---

## 四、成本优化

分级路由（小/大模型）+ Prompt 缓存（复用不变前缀）+ 语义缓存（相似 query 命中）+ 上下文压缩（compaction/摘要）+ 批处理 + 控步数（死循环检测+max_steps）。

---

## 五、性能/延迟

流式输出（降 TTFT）+ 并行工具调用 + 预计算 embedding + 投机解码。
关键指标：**TTFT（首 token）/ TPOT（每 token）/ P95-P99 总延迟 / 成本每请求**。先用 trace 定位瓶颈再优化。

---

## 六、易错点

### ❌ 用 Mock 当生产降级
正确：Mock 基于关键词无法处理真实自然语言。生产降级=切备用模型/缓存/诚实报错转人工。

### ❌ 所有失败都重试
正确：只重试瞬时/可重试错误（超时/限流/5xx）。逻辑错误、4xx 重试无意义还放大故障。

### ❌ 所有失败都 fail-closed 或都 fail-open
正确：看后果。增强失败 fail-open，安全失败 fail-closed。

---

## 七、面试速答

| 问题 | 要点 |
|---|---|
| Harness？ | 包裹 LLM 的运行时：上下文/循环/编排/状态/可靠/观测 |
| 长任务崩了？ | 状态机存 checkpoint，断点恢复，副作用步骤幂等+补偿(Saga) |
| 可靠性三件套？ | 重试(退避+抖动)/降级(切备用,别用Mock)/熔断(超阈值快失败) |
| fail-open/closed？ | 增强失败 open 保可用；安全失败 closed 保正确 |
| 省成本？ | 分级路由+prompt缓存+语义缓存+上下文压缩+批处理+控步数 |
| 降延迟？ | 流式降TTFT+并行工具+预计算；先trace定位瓶颈 |

---

> 关联：`lessons/07_engineering/`、`knowledge/know_model_routing.md`、`knowledge/know_compaction_decay.md`、`drills/07_retry_fallback.py`
