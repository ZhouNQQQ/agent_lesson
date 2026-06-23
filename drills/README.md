# 手撕题模板库（Agent 岗高频）

> 来源：学员收集的 Agent 岗高频"现场手撕"题。面试要求**能从空白默写**这些骨架。
> 这里每个文件 = 一道手撕题的**标准模板 + 逐行注释**，用于"先学懂结构 → 再合上默写"。
> 对应 [`../ROADMAP.md`](../ROADMAP.md) 第 4 节"手撕题清单"。

| 文件 | 题 | 可跑性 | 备注 |
|------|----|-------|------|
| `01_react_loop.py` | ReAct 执行循环 | 骨架（helper 省略） | 完整可跑生产版见 `../lessons/01_react/react_agent.py` |
| `02_tool_router.py` | 工具路由（语义匹配选工具） | 骨架 | = 讲义 3.5 的"工具检索" |
| `03_rag_pipeline.py` | RAG Pipeline | 骨架 | P0，必须能手写 |
| `04_hybrid_memory_recall.py` | 混合记忆召回 | 骨架 | 记忆方向加分题，逻辑与 Compaction 的衰减+去重一致 |
| `05_llm_as_judge.py` | LLM-as-Judge 评分器（pairwise+位置消偏） | 骨架 | 评测方向，配 `../lessons/05_evaluation/` |
| `06_model_router.py` | 多模型级联路由（置信门控升级） | 骨架 | 成本/工程方向，配 `../lessons/07_engineering/` |
| `07_retry_fallback.py` | 可靠性三件套（重试+降级+熔断） | 骨架 | 可靠性方向，配 `../lessons/07_engineering/` |

**用法**：①读懂带注释的模板 → ②合上文件，空白默写骨架 → ③对照，标记漏掉的行。
**注意**：这些是面试手撕模板，`parse_action / execute_tool / cosine_similarity / embeddings.encode` 等 helper 是约定省略的，重点是**主干结构和每行的意图**，不是跑通。
