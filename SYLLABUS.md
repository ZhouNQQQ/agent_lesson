# 课程大纲（SYLLABUS）

本仓库的完整学习大纲。建议配合 [`AI_TUTOR_GUIDE.md`](./AI_TUTOR_GUIDE.md)（交给 AI 当陪练）和 [`ROADMAP.md`](./ROADMAP.md)（能力自评）一起用。

> 学习总路线：**LLM 基础 → ReAct → RAG → 记忆系统(最厚) → Agent 框架 → 多 Agent/系统设计 → 完整 stage 路线 → 手撕题 → 资料精读**
> 优先级：地基(模块0-2)必过，记忆系统(模块3)是护城河往深里学，其余按需。

---

## 模块 0 · LLM 运行机制（地基 · 浅学）
- **目标**：能答暖场题——token 为何中英文消耗不同、上下文窗口与 Lost in the Middle、Temperature/Top-P/Top-K 控什么、幻觉成因与缓解。
- **材料**：`lessons/00_llm_basics/llm_runtime_lesson.md`

## 模块 1 · 推理框架 ReAct（P0 · 必考·必须能手写）
- **目标**：从空白手写 Thought-Action-Observation 循环，能处理 Action 解析失败、工具异常、死循环检测、max_steps。
- **材料**：
  - 讲义 `lessons/01_react/react_lesson.md`（CoT→ReAct、FC vs system prompt、错误处理）
  - 实现 `lessons/01_react/react_agent.py`
  - 自测 `lessons/01_react/README.md`
- **配套手撕**：`drills/01_react_loop.py`

## 模块 2 · RAG（P0 · 几乎必考）
- **目标**：讲清并手写两阶段全链路——切分→Embedding→检索→重排→拼接上下文→生成→引用溯源。
- **材料**：`lessons/02_rag/rag_lesson.md`
- **配套手撕**：`drills/03_rag_pipeline.py`

## 模块 3 · 记忆系统（护城河 · 最深一块）
- **目标**：能从写入到检索、从一致性到治理，讲透并接得住高压追问。
- **复习讲义**：`lessons/03_memory/mem0_lesson.md`
- **知识卡片** `knowledge/`：
  - `know_cqrs.md` CQRS + 双水位一致性
  - `know_reranker.md` Bi-Encoder vs Cross-Encoder + over-fetch
  - `know_graph_memory.md` 向量 vs 图记忆
  - `know_rolling_summary.md` 热/冷路径 + Background Review
  - `know_compaction_decay.md` 触发时机 + 时间衰减
- **mem0 源码精读** `lessons/mem0-deep-reading/`：阅读指南 / 章节导读 / 探究问题 / 场景练习 / 核心概念速查 / 阅读计划 / `mem0-crud-source-tour.md`
- **记忆框架源码逐行批注** `lessons/curriculum/`：`memory-overview/builtin/config/search/qmd/honcho`（full-annotated 系列）、`compaction-full-annotated`、`dreaming-full-annotated`、`mem0-architecture(-relation)`、`mem0-search-walkthrough`、`echomind-vector-retrieval`、`honcho-user-modeling`、`openclaw-memory-injection`
- **配套手撕**：`drills/04_hybrid_memory_recall.py`（相似度+时间衰减+关键词+去重）

## 模块 4 · Agent 框架横向对比
- **目标**：说清主流框架的范式差异，面试被问到任一框架都能对比定位。
- **材料** `knowledge/frameworks/`：LangChain / LangGraph / AutoGen / AgentScope / Manus / Cursor / ClaudeCode / OpenClaw / OpenCode / HermesAgent 学习笔记
- **知识卡**：`knowledge/know_autogen.md`、`knowledge/know_agentscope.md`
- **配套手撕**：`drills/02_tool_router.py`（语义匹配选工具）

## 模块 5 · 多 Agent 与系统设计（P1 · 决定薪资）
- **目标**：把架构能力翻译成 Agent 语境（多 Agent 协作、路由、共享上下文、降级、可观测性）。
- **材料** `lessons/curriculum/`：
  - `stage-3-multi-agent.md` / `stage-3-multi-agent-full.md`（四种协作模式）
  - `agent-six-deep-dive-and-interview-guide.md`（六大 Agent 剖析 + 面试八股）
  - `se-lifecycle-agent-project-design.md`（软件工程全生命周期 Agent 实战）
  - `unified-agent-gateway-with-memory-enhancement.md`（统一入口 + 记忆增强架构）
  - `agent-llm-fundamentals-handbook.md`（安全约束 / 参数调优 / 部署）

## 模块 6 · 完整学习路线 stage 1-7
- **目标**：按阶段成体系推进，含时间投入、里程碑、产出物清单。
- **材料** `lessons/curriculum/`：
  - `stage-1-qclaw-intro.md` 平台入门 + 五阶段路线图
  - `stage-2-skill-memory.md` Skills 开发 + 记忆系统
  - `stage-3-multi-agent.md` 多 Agent 与任务编排
  - `stage-4-memory-manager.md` 企业级 MemoryManager
  - `stage-5-final-project.md` 综合实战项目
  - `stage-6-resources-and-career.md` 学习资源 + 求职准备
  - `stage-7-appendix.md` 检查清单
  - 索引/辅助：`learning-index.md`、`week1-partb-technical-design.md`、`boundary-test-selection.md`、`memory-system-learning-material.md`

## 模块 7 · 手撕题 `drills/`
- **目标**：能讲 ≠ 能写，关键算法要能空白默写。
- **题目**：`01_react_loop.py`（ReAct 循环）、`02_tool_router.py`（工具路由）、`03_rag_pipeline.py`（RAG）、`04_hybrid_memory_recall.py`（混合记忆召回）
- **建议顺序**：ReAct → RAG → 混合记忆召回 → 工具路由

## 模块 8 · 资料精读 + 可跑示例
- **资料精读** `materials/`：`01_paper_bert_rerank.md`（论文）、`02_mem0_search_pipeline.md`（mem0 检索链路源码）、`03_hf_cross_encoder.md`（HF 实践）
- **示例** `examples/`：`extractor.py`（LLM 记忆提取器）+ `sample_dialogs.jsonl`（合成样例）

---

## 模块 9 · 评测与可观测性（P1 · 真实 JD 硬要求 · 原课程最大缺口）
- **目标**：讲清 Agent 为何必须评测、评测三支柱、分层指标（检索/生成/Agent）、LLM-as-Judge 及其偏差、trace/span 埋点、badcase 闭环、评测接 CI/CD。
- **材料**：`lessons/05_evaluation/eval_observability_lesson.md`
- **知识卡**：`knowledge/know_evaluation.md`、`knowledge/know_observability.md`
- **配套手撕**：`drills/05_llm_as_judge.py`（pairwise + 位置消偏）
- **缺口来源**：JD3 全栈 AI-Native、JD4 开发工程师、JD6/JD7 平台架构师反复要求"评测/trace/eval/badcase/回归"。

## 模块 10 · MCP 协议与工具编排（P1 · 深圳/北京 JD 要求 · 热点）
- **目标**：讲清 MCP 是什么、三原语（Tools/Resources/Prompts）、三角色（Host/Client/Server）、运行时发现、传输层、MCP vs Function Calling、工具编排模式。
- **材料**：`lessons/06_mcp/mcp_lesson.md`
- **知识卡**：`knowledge/know_mcp.md`
- **配套手撕**：`drills/02_tool_router.py`（工具检索）
- **缺口来源**：深圳 JD "MCP 管理"、北京火山引擎 JD "Skill/MCP/Memory Infra 组件"。

## 模块 11 · Agent 工程化（P1 · 决定能否接平台架构岗）
- **目标**：讲清 Agent Harness、运行时编排与长任务状态管理（持久化/恢复/补偿）、可靠性三件套（重试/降级/熔断、fail-open/closed）、成本与性能优化、多模型路由、研发流水线。
- **材料**：`lessons/07_engineering/engineering_lesson.md`
- **知识卡**：`knowledge/know_cost_reliability.md`、`knowledge/know_model_routing.md`
- **配套手撕**：`drills/06_model_router.py`（级联路由）、`drills/07_retry_fallback.py`（重试+降级+熔断）
- **缺口来源**：JD4 "Harness/长任务调度/成本性能可靠性"、JD6/JD7 "运行时编排/多模型协同/状态持久化/故障恢复"。

## 模块 12 · Agent 安全（P1 · 必问）
- **目标**：讲清 Agent 攻击面、直接/间接 Prompt Injection 与防御、越狱、沙箱隔离、权限最小化与审计、HITL 审批时机、输出安全。
- **材料**：`lessons/08_security/security_lesson.md`
- **知识卡**：`knowledge/know_agent_security.md`
- **缺口来源**：深圳 JD "Agent 安全控制"、JD6 "权限/审计/人机协作"。

---

## 推荐学习顺序（按 ROI）

```
入场券(必过)        加分项(决定薪资)              锦上添花
模块1 ReAct         模块3 记忆系统(深)            模块4 框架横向
模块2 RAG     →     模块9 评测可观测(JD硬要求)  →  模块6 完整stage路线
模块0 LLM基础(浅)   模块11 工程化(Harness/可靠性) 模块8 资料精读
                    模块10 MCP / 模块12 安全
                    模块5 多Agent/系统设计
                    模块7 手撕题
```

> 模块 9-12 是据真实 JD 缺口新增的：评测可观测、MCP、工程化、安全。这些是把"懂原理"升级到"能落地生产"的关键，也是平台架构岗（90-260K）反复要求的能力。

> 每学完一块，回 `ROADMAP.md` 更新自评表；用"主动回忆 + 间隔复习"对抗遗忘。
