# mem0 复习讲义（一份顶三份）

> 用途：忘了 mem0 就翻这一份，不用满仓库找。把散在
> `materials/02_mem0_search_pipeline.md` 里的核心收拢成"主动回忆"材料。
> 对应面试题：Q8（为什么不直接用 mem0）、Q10（over-fetch 4 倍）、Q13（改了哪个行为点）、Q14（Reranker）。
> 复习法：先盖住每节，看小标题自己讲一遍，再对照。最后做第 7 节自测。

---

## 1. mem0 是什么 / 解决什么

mem0 = 给 LLM 应用加"长期记忆"的开源框架。核心能力：**从对话里自动提取事实 → 去重/更新 → 存进向量库 → 下次按语义检索召回**。
解决的痛点：LLM 本身无跨会话记忆，每次对话都"失忆"；mem0 把值得记的事实沉淀下来，下次检索注入上下文。

**为什么你不直接用 mem0、要自研（Q8）**：mem0 核心库有几处固定死的地方（见第 5 节），不满足你的需求（自定义存储到 GitHub、自定义 Compaction），所以你**基于它的源码理解做继承+包装**，而不是重写或直接用。

---

## 2. 核心类关系（一张图记住）

```
Memory (mem0/memory/main.py)         ← 总入口
├── config: MemoryConfig             ← 配置（vector_store / llm / embedder / reranker / history_db_path）
├── embedding_model                  ← EmbedderFactory 产出，把文本变向量
├── vector_store                     ← VectorStoreFactory 产出（Qdrant/Chroma/FAISS…），可替换 ✓
├── llm                              ← LlmFactory 产出，做提取/摘要
├── db: SQLiteManager                ← 历史记录（ADD/UPDATE/DELETE 事件 + 最近消息），固定 ✗
├── reranker                         ← RerankerFactory 产出（可选）
└── entity_store                     ← 实体关联（懒加载，复用 vector_store）
```

记忆点：**抽象基类 + 工厂 + provider_to_class 字典映射** 是 mem0 的扩展套路（向量库/LLM/嵌入/重排都这么注册）。

---

## 3. 写入流水线：add() 的 Phase 0-8

对话进来，mem0 怎么把它变成记忆：

```
Phase 0  上下文收集    从 SQLite 读最近 10 条消息
Phase 1  现有记忆检索  用 embedding 搜向量库，取 top10 现有记忆（为了判断该 ADD 还是 UPDATE）
Phase 2  LLM 提取      一次 LLM 调用，从对话里抽出新事实
Phase 3  批量嵌入      把提取的记忆文本 embed
Phase 4-5 去重与哈希   MD5 哈希去重（现有 + 本批）
Phase 6  批量持久化    vector_store.insert() + SQLite 写历史
Phase 7  实体关联      抽实体 → entity_store 插入/更新
Phase 8  保存消息      SQLite 存最近消息（只留最近 10 条）
```

一句话：**读上下文 → 检索现有 → LLM 提取 → 嵌入去重 → 落库 → 建实体关联**。
关键：Phase 1 先检索现有记忆，是为了让 LLM 决策 ADD/UPDATE/DELETE/NOOP（新事实 vs 已有事实冲突）。

---

## 4. 检索链路：search 的 9 步（重点，最常考）

```
1 预处理 query      词形还原(lemmatize，给 BM25 用) + 实体提取
2 query 向量化      embedding_model.embed(query)
3 语义检索(向量)    ★ over-fetch: internal_limit = max(limit*4, 60)
4 关键词检索(BM25)  keyword_search，对专有名词/ID 精确
5 BM25 分数归一化   sigmoid 压到 [0,1]，按 query 长度自适应
6 实体加分(Entity Boost)  query 实体 → 实体库找关联记忆 → 加分
7 构建候选集
8 混合评分与排序    score_and_rank：语义分 + BM25分 + 实体分，取 top_k
9 格式化输出
   └─(可选) rerank=True → reranker 对结果再精排
```

### 4.1 Over-fetch：为什么检索 4 倍量（Q10）
```python
internal_limit = max(limit * 4, 60)   # limit=最终要返回的条数
```
- limit=5 → 实际检索 60 条；limit=20 → 80 条；limit=100 → 400 条。
- **为什么**：给后续混合评分（BM25 + entity boost）和 reranker 留**充足候选池**。只检索 limit 条的话，BM25/实体想加分的记忆可能根本没被向量检索捞到。
- **关键诚实点**：mem0 的 4 倍是**工程经验值，不是 recall@k 曲线实验得出的**。工业级调优应该用真实数据测 recall@internal_limit 来定倍数。（这是你的错题本第 1 条）

### 4.2 混合检索 = 向量 + BM25（取并集后混合打分，不是交集）
| 方式 | 负责 | 特点 |
|------|------|------|
| 语义(向量) | 语义相似 | 能关联 "likes" 和 "enjoys" |
| 关键词(BM25) | 字面匹配 | 专有名词/ID 精确 |

### 4.3 混合评分公式
```
综合分 = (语义分 + BM25分 + 实体分) / 满分基准
满分基准 = 1.0 (+1.0 若有BM25) (+0.5 若有实体) → 最多 2.5
threshold(默认0.1): 语义分低于门槛直接淘汰 —— 防 BM25 把完全不相关的记忆召回
```

### 4.4 Entity Boost（图记忆给检索加分）
- query 抽实体 → 实体库搜关联记忆 → 加分。
- **记忆数量权重衰减**：`1/(1+0.001*(n-1)²)`——某实体关联记忆越多，单条加分越少。防"热门实体"（如关联 100 条的"张三"）把所有相关记忆都推上去；而关联少的"X 项目"加分更猛。
- Entity Boost 上限 0.5，防实体分压倒语义分。

### 4.5 Reranker 接入点（Q14）
- 在 `_search_vector_store` **完成后**才调，输入是已混合评分的结果。
- **关键易错点**：mem0 喂给 Reranker 的只有 `limit` 条（默认 20），**不是 internal_limit（60~80）条**。即 Reranker 做"最后一公里精排"，不是从大候选池重筛——这和论文"从 100 个候选重排"略不同。
- 三种实现：HuggingFace（本地 Cross-Encoder，需 GPU，零 API 费）/ Cohere（云 API，按量计费）/ LLM（用大模型打分，最准最贵最慢）。

---

## 5. 关键结论 / 易错点（面试爱挖的"坑"）

1. **mem0 核心库没有自动 Compaction**。`history.db` 只记 ADD/UPDATE/DELETE 事件，不做自动压缩/时间衰减。（所以你的项目要**自研** Compaction 引擎——这是你自研的理由之一）
2. **存储层哪些可换哪些固定**：向量库可替换 ✓；但 `SQLiteManager`（history）、`~/.mem0/config.json`、messages 表都**固定不可替换 ✗**。（所以你用"继承+钩子包装"绕过，不改 mem0 源码）
3. **over-fetch 4 倍是经验值**，非 recall 曲线实验值。
4. **Reranker 输入是 limit 条不是 internal_limit 条**。
5. **threshold 先卡语义分**：BM25/实体分再高，语义分 < 0.1 也淘汰。

---

## 6. 串到你的项目（面试讲故事用）

- 你**读懂 mem0 源码后用继承+钩子包装**（不改源码），加了三样 mem0 核心库没有的：GitHub 远程同步、自动 Compaction（时间衰减+去重+滚动摘要）、MCP 暴露。
- "为什么不直接用 mem0"=mem0 存储层固定、无自动治理 → 你的需求（自定义存储+Compaction）要扩展 → 站在源码上改进而非重写。

---

## 7. 自测题（盖住上文，先自己讲）

1. mem0 的 add() 流水线大致几个阶段？读上下文之后第一件事干嘛、为什么？（→ §3，Phase1 检索现有为了 ADD/UPDATE 决策）
2. search 链路 9 步能背出主干吗？（→ §4）
3. over-fetch 公式是什么？为什么要 over-fetch？4 倍是怎么来的？（→ §4.1）
4. 混合检索是向量和 BM25 取交集还是并集？threshold 起什么作用？（→ §4.2/4.3，并集后打分；threshold 卡语义分防乱召回）
5. Entity Boost 为什么要按关联记忆数量衰减？（→ §4.4，防热门实体霸榜）
6. Reranker 在链路哪一步？mem0 喂它几条？（→ §4.5，最后；limit 条不是 internal_limit）
7. mem0 核心库有自动 Compaction 吗？这对你的项目意味着什么？（→ §5.1，没有 → 你自研）
8. 为什么你不直接用 mem0 要自研？（→ §1/§6）

能脱稿答出 3、5、6、7、8 这几条，mem0 这块面试就稳了。

---

## 8. 易错强化（自测踩过的坑，反复看）

### 坑 A：BM25 是"召回"，不是"Reranker/精排"（错题本第 4 条的老坑，又踩了一次）

把两个**不同阶段**的东西分清，别再搅在一起：

```
召回阶段（粗筛，并列两路，取并集）：
    向量检索（语义相似，Bi-Encoder）┐
                                    ├─→ 混合打分（语义分 + BM25归一化分 + 实体加分）
    BM25 检索（关键词字面匹配）      ┘
                                         ↓ 取 top ~limit(默认20) 条
精排阶段（可选）：
    Reranker（Cross-Encoder）对这 ~20 条逐对精排 → 最终 top_k
```

- **BM25 在召回阶段**，和向量检索**并列**，负责"字面/专有名词/ID"的精确匹配。
- **Reranker（Cross-Encoder）在召回之后**，是单独的精排步骤。
- **BM25 ≠ Reranker ≠ Cross-Encoder**——它们是不同阶段、不同作用，**绝不能划等号**。
- 记忆口诀：**向量 + BM25 一起"召回"，Cross-Encoder 之后"精排"。**

### 坑 B：mem0 喂给 Reranker 的是 limit 条（默认 20），不是粗筛全部（60~80）

- over-fetch 的 internal_limit（`max(limit*4,60)`，约 60~80 条）是给**召回阶段的混合打分**用的候选池。
- 混合打分后取 **limit 条（默认 20）** 才喂给 Reranker。
- 所以 Reranker 做的是"**最后一公里精排**"（对 ~20 条再排），**不是**从 60~80 条大池子重新筛。
- 一句话：**over-fetch 服务的是混合打分，不是 Reranker；Reranker 只吃最终那 ~20 条。**
