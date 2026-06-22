# Agent 研发工程师 · 学习路径 + 就绪度自评

> 目标岗位：**Agent 研发工程师**（围绕大模型做应用/基础设施开发，非算法训练岗）
> 用法：先用这份地图看清"市场考什么"，再用末尾的自评表标出自己的现状，按优先级补齐。配合 `AI_TUTOR_GUIDE.md` 交给 AI 带教。

---

## 1. 市场客观标准：Agent 研发工程师面试考什么

综合多份真题梳理与真实 JD，考点稳定落在 **5 个维度**（典型 JD 还要求 Python、异步/流式/成本工程）：

| # | 维度 | 高频考点 | 市场权重 |
|---|------|---------|---------|
| 1 | **推理框架** | CoT → ReAct → ToT；**ReAct 必须能手写** | 必考·地基 |
| 2 | **Agent 架构** | 记忆（短期/长期/反思）、规划（任务分解）、行动（工具调用/降级） | 记忆=高区分度高频 |
| 3 | **工具与协议** | Function Calling（JSON Schema）、MCP、A2A | 必会 FC，MCP 热点 |
| 4 | **系统设计** | 多 Agent 协作、**RAG 系统（几乎必考）**、Agent 框架、可观测性 | 重头戏 |
| 5 | **安全与评估** | Prompt Injection 防御、Human-in-the-loop、AgentBench/LLM-as-Judge | 必问安全 |

JD 还普遍要求：**LLM 基础**（Transformer/Tokenizer/上下文窗口管理）、向量库/Embedding/Chunking、Prompt 工程、异步编程、流式输出、错误处理、成本优化。

> 一句话画像：Agent 工程师 = 懂 LLM 能力边界 + 有工程化系统设计能力的**交叉岗**。不是纯调 API，也不是搞训练。
> 经验提示：面试是"短板决定能不能进门，长板决定给多少钱"。地基题（ReAct/RAG/LLM 基础）不会就可能第一轮被刷；记忆系统、系统设计能讲深则决定薪资。

---

## 2. 学习路径（按 ROI 排序）

### P0 — 入场券，必须先补
1. **手写 ReAct 循环** —— Thought-Action-Observation，能处理 Action 失败、死循环检测、max_steps。→ `lessons/01_react/` + `drills/01`
2. **RAG pipeline 串讲 + 手写** —— 切分 → Embedding → 检索 → 重排 → 拼上下文 → 生成 → 引用溯源。→ `lessons/02_rag/` + `drills/03`
3. **LLM 运行机制（浅）** —— token 消耗、上下文窗口与 Lost in the Middle、Temperature/Top-P/Top-K、幻觉成因与缓解。→ `lessons/00_llm_basics/`

### P1 — 加分项，进门后决定薪资
4. **记忆系统讲透** —— CQRS、Rolling Summary、Graph Memory、Reranker、Compaction。→ `knowledge/know_*` + `lessons/03_memory/` + `lessons/mem0-deep-reading/`
5. **安全** —— Prompt Injection 防御 + 越狱 + HITL 审批时机。
6. **系统设计大题** —— 多 Agent 协作 / RAG 系统 / 可观测性。
7. **评估体系** —— 离线/在线/LLM-as-Judge 三支柱 + RAG 的 Recall@K / Faithfulness。

### P2 — 锦上添花
8. Prompt 工程体系化（静态 → 动态组装）、流式输出（SSE）、成本优化（缓存/分级路由）。

---

## 3. 就绪度自评表（自己填）

> 状态记号：🔴 没学 / 🟡 学了但讲不透 / 🟢 能讲透且扛得住追问。每过一关就更新。

| 维度 | 市场要求 | 我的现状 | Gap | 优先级 | 状态 |
|------|---------|---------|-----|--------|------|
| 推理框架 ReAct | 必须能手写，处理 Action 失败/死循环 | | | P0 | ⬜ |
| RAG 系统 | 全链路 + 能手写 pipeline | | | P0 | ⬜ |
| LLM 基础/运行机制 | token/窗口/采样/幻觉 | | | P0 | ⬜ |
| 记忆系统 | 短期/长期/向量/图/反思、混合检索 | | | P1 | ⬜ |
| 工具与协议（MCP/FC） | FC 的 JSON Schema、MCP 三原语 | | | P1 | ⬜ |
| 安全 | Prompt Injection、越狱、HITL | | | P1 | ⬜ |
| 系统设计大题 | 多 Agent、可观测性 | | | P1 | ⬜ |
| 评估体系 | 离线/在线/LLM-as-Judge | | | P1 | ⬜ |
| Prompt 工程 | 静态→动态组装 | | | P2 | ⬜ |
| 工程基础（LLM 语境） | 异步/流式/成本 | | | P2 | ⬜ |

---

## 4. 手撕题清单（能讲 ≠ 能写）

| # | 手撕题 | 仓库位置 | 状态 |
|---|--------|---------|------|
| 1 | ReAct 执行循环（含重试/限步/终止） | `drills/01_react_loop.py` | ⬜ |
| 2 | 工具路由（cosine 相似度 + 优先级加权 + 阈值 + topK） | `drills/02_tool_router.py` | ⬜ |
| 3 | RAG Pipeline（chunk→检索 top10→rerank top3→生成） | `drills/03_rag_pipeline.py` | ⬜ |
| 4 | 混合记忆召回（相似度 + 时间衰减 e^(-λΔt) + 关键词加权 + 去重 + topK） | `drills/04_hybrid_memory_recall.py` | ⬜ |

**建议顺序**：先 ReAct 默写结业 → RAG（P0 大头）→ 混合记忆召回 → 工具路由。

---

## 5. 复习清单（对抗遗忘 · 主动回忆法）

方法：先盖住答案自己讲一遍 → 再对照材料 → 标记卡壳点 → 隔几天重测（第 1 天全过、第 3 天测红的、第 7 天再测仍红的）。

| 主题 | 复习材料 | 自测问题（先盖答案讲） |
|------|----------|----------------------|
| mem0 检索链路 | `materials/02_mem0_search_pipeline.md` | 9 步检索链路？over-fetch 为什么要多取？混合评分怎么算？ |
| Reranker | `knowledge/know_reranker.md`、`materials/01`、`materials/03` | Bi vs Cross-Encoder 怎么选？海选→决赛和 over-fetch 怎么串？ |
| CQRS+一致性 | `knowledge/know_cqrs.md` | 记忆系统为什么适合 CQRS？双水位/幂等怎么做？ |
| Rolling Summary | `knowledge/know_rolling_summary.md` | 热/冷路径怎么分界？Background Review vs 即时写入区别？ |
| Compaction+衰减 | `knowledge/know_compaction_decay.md`、`drills/04` | 何时触发？exponential vs power-law 衰减适用场景？ |
| Graph Memory | `knowledge/know_graph_memory.md` | 比向量强在哪？什么时候不上 Graph？ |

---

## 6. 来源（外部市场调研）

- 面试 AI Agent 工程师真题与知识图谱梳理（cnblogs，2026）——5 维度框架、ReAct 手写要求、记忆系统高频、MCP 热点。
- Top AI Engineer Interview Questions（interviewcoder）——RAG chunking、agent 失败模式、LLM-as-judge、延迟控制。
- RAG Interview Questions（datacamp / theinterviewguys）——RAG 几乎必考，考全链路系统级思维。
- 真实 JD（aijobs / builtin）——工具调用框架、沙箱执行、benchmark、CI-CD、Agentic Workflow 后端。

> 内容已按许可要求改写、压缩并标注来源，非逐字复制。
