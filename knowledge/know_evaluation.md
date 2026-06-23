# K.6 评测体系：三支柱 + 分层指标 + LLM-as-Judge

> 配套讲义：`lessons/05_evaluation/eval_observability_lesson.md`
> 缺口补齐：多份真实 JD（全栈 AI-Native / 开发工程师 / 平台架构师）硬性要求评测/回归/eval。

---

## 一、核心心智

**Agent 质量不是测出来的，是治理出来的**：离线评测 + 在线评测 + badcase 闭环，缺一不可。
因为 Agent 输出不确定（不能 assert ==）、改一处可能回归、长尾问题只在线上暴露。

---

## 二、评测三支柱速查

| 支柱 | 时机 | 数据 | 指标 | 局限 |
|---|---|---|---|---|
| 离线 Offline | 上线前 / 每次改动 | golden set | 准确率/Recall@K/Faithfulness | 覆盖不了线上长尾 |
| 在线 Online | 运行时持续 | 真实流量+埋点 | 成功率/延迟P95/成本/反馈率/接管率 | 有滞后，需埋点采样 |
| LLM-as-Judge / 人工 | 离线+在线叠加 | 抽样+评分prompt | 相关性/有用性/安全性打分 | 有偏差，需校准 |

---

## 三、分层指标（必须分开测）

| 层 | 指标 | 反什么问题 |
|---|---|---|
| 检索侧 | Recall@K / Precision@K / MRR / NDCG | "该捞的捞回了吗""排得前吗" |
| 生成侧 | Faithfulness / Answer Relevance / Context Precision | 幻觉 / 答非所问 |
| Agent 侧 | 任务成功率 / 工具调用准确率 / 步数收敛 / 轨迹合理性 | 端到端是否达成 + 过程是否合理 |

> 口诀："检索准但生成乱"和"生成好但检索漏"是两类问题，端到端准确率无法归因。

---

## 四、LLM-as-Judge

**三范式**：Pointwise（绝对打分）/ Pairwise（A-B 对比，更稳）/ Reference-based（对照标准答案）。

**四个偏差（必答）**：
1. 位置偏差 → 交换顺序各评一次取平均
2. 冗长偏差 → rubric 里强调简洁性
3. 自我偏好偏差 → 用不同厂商模型当裁判
4. 校准问题 → 和人工打分做一致性校验（Kappa/相关系数）

**评分 prompt**：给明确 rubric + 先理由后分数（CoT）+ 输出结构化 JSON。

---

## 五、错题/易错点

### ❌ 用端到端准确率一个数评 RAG
正确：分检索侧和生成侧。准确率低要先定位是检索漏了还是生成乱了。

### ❌ 离线指标好就上线
正确：离线分布 ≠ 线上分布，会过拟合 golden set。要 badcase 回流缩小分布差。

### ❌ 结果对就不用评过程
正确：结果对可能侥幸。Agent 要评轨迹（步数/工具是否合理/有无越权）。

### ❌ Pointwise 比 Pairwise 准
正确：Pairwise（比较）一致性更高，A/B 测优先用 pairwise。

---

## 六、面试高压题

**"你怎么证明改的 prompt 真的变好了，而不是错觉？"**
> "建版本化评测集（golden set + 线上回流的 badcase），离线对新旧版本跑同一套指标（任务成功率/Faithfulness/成本），看是否显著提升且无回退；再线上灰度 A/B，对比核心指标显著性，才全量。把'凭感觉'变成'数据驱动+回归门禁'。"

---

> 关联：`lessons/05_evaluation/`、`knowledge/know_observability.md`、`knowledge/know_reranker.md`、`drills/05_llm_as_judge.py`
