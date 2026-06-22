# Mem0 search() 方法带读笔记

> 来源：mem0/memory/main.py def search() + def _search_vector_store()
> 阅读策略：从上往下，每一步说明"是什么、为什么、关键要点"

---

## 第一步：入口参数校验（防御性编程）

```python
def search(self, query, *, top_k=20, filters=None, threshold=0.1, rerank=False, explain=False):
```

**三个校验动作：**

1. `_reject_top_level_entity_params(kwargs, "search")`  
   → 禁止 `user_id`/`agent_id`/`run_id` 直接传参，必须用 `filters={"user_id": "xxx"}`  
   **为什么：** 统一接口风格，防止误用

2. `_validate_search_params(threshold=threshold, top_k=top_k)`  
   → 检查 threshold 在 [0,1] 之间，top_k 非负整数  
   **为什么：** 尽早失败，避免把非法参数传给向量库

3. `_validate_and_trim_search_query(query)`  
   → 去空字符串，去首尾空格  
   **为什么：** 空查询会浪费一次 embedding API 调用

**关键要点：** Mem0 的每个公共方法都有严格的参数校验层。不是直接干活，而是先确认输入合法。

---

## 第二步：过滤器处理（高级查询能力）

```python
if self._has_advanced_operators(effective_filters):
    processed_filters = self._process_metadata_filters(effective_filters)
```

**支持的操作符：**
- `{"key": "value"}` → 精确匹配
- `{"key": {"eq": "v"}}` → 等于
- `{"key": {"ne": "v"}}` → 不等于
- `{"key": {"gt": 10}}` → 大于
- `{"key": {"in": ["a","b"]}}` → 在列表中
- `{"AND": [{...}, {...}]}` → 逻辑与
- `{"OR": [...]}` → 逻辑或
- `{"NOT": [...]}` → 逻辑非

**关键要点：** 这是 Mem0 的差异化能力。普通向量库只支持 `==` 过滤，Mem0 包装了一层通用过滤器 DSL，底层再翻译成各向量库的具体语法。

---

## 第三步：核心检索 `_search_vector_store()`（9 步流水线）

### Step 1: 预处理查询

```python
query_lemmatized = lemmatize_for_bm25(query)   # 词干还原，用于关键词检索
query_entities = extract_entities(query)       # 提取实体，用于实体 boost
```

**为什么两步：**
- 语义检索：用原始 query 向量化（保持语义完整）
- 关键词检索：用词干化后的 query（提高 BM25 召回率）
- 实体 boost：提取"人名、地名、组织"等，给相关记忆额外加分

**关键要点：** 这是**混合检索**（Hybrid Search）的基础。单一向量检索可能漏掉精确匹配的关键词，BM25 补充精确匹配能力。

---

### Step 2: 查询向量化

```python
embeddings = self.embedding_model.embed(query, "search")
```

**注意：** 传入 `"search"` 参数。Mem0 的 embedding provider 支持不同 action 用不同模型/参数（如 "add" vs "search" 可能用不同维度）。

**关键要点：** 这是与 LLM 无关的独立调用。embedding 通常比 LLM 生成快 100 倍，且成本低。

---

### Step 3: 语义检索（Over-fetch 策略）

```python
internal_limit = max(limit * 4, 60)   # 取 top_k 的 4 倍，至少 60 条
semantic_results = self.vector_store.search(
    query=query, vectors=embeddings, top_k=internal_limit, filters=filters
)
```

**为什么 over-fetch？**  
后面有 BM25 和实体 boost 重排序，如果语义检索只取 top_k=5，BM25 和实体 boost 就没有"候选池"可以调整了。先取 4 倍，给后续打分留余地。

**关键要点：** 这是召回（Recall）和精确（Precision）的权衡。先多召回，再精排。

---

### Step 4: 关键词检索（BM25）

```python
keyword_results = self.vector_store.keyword_search(
    query=query_lemmatized, top_k=internal_limit, filters=filters
)
```

**注意：** 不是每个向量库都支持 `keyword_search`。Chroma 不支持，Elasticsearch/PgVector 支持。返回 None 时会跳过。

**关键要点：** 语义检索擅长"意思相近但用词不同"，BM25 擅长"用词完全一致"。两者互补。

---

### Step 5-6: 计算 BM25 分数 + 实体 Boost

```python
bm25_scores = {}
if keyword_results:
    midpoint, steepness = get_bm25_params(query, lemmatized=query_lemmatized)
    for mem in keyword_results:
        bm25_scores[mem_id] = normalize_bm25(raw_score, midpoint, steepness)

entity_boosts = {}
if query_entities:
    entity_boosts = self._compute_entity_boosts(query_entities, filters)
```

**BM25 是什么：** 经典信息检索评分函数，基于词频和逆文档频率。Mem0 做了归一化，把 BM25 的绝对分数映射到 [0,1] 区间。

**实体 Boost 是什么：** 如果查询提到"Python"，Mem0 会在实体库中找"Python"相关的实体，然后给所有关联"Python"的记忆额外加分（最高 0.5）。

**关键要点：** 这是**多信号融合**（Multi-signal Fusion）。不是单一相似度，而是语义 + 关键词 + 实体 三个信号加权。

---

### Step 7-8: 构建候选集 + 综合打分排序

```python
candidates = []
for mem in semantic_results:
    candidates.append({"id": mem.id, "score": mem.score, "payload": mem.payload})

scored_results = score_and_rank(
    semantic_results=candidates,
    bm25_scores=bm25_scores,
    entity_boosts=entity_boosts,
    threshold=threshold,
    top_k=limit,
    explain=explain,
)
```

**打分公式：** `final_score = semantic_score + bm25_score + entity_boost`

**关键要点：** Mem0 的打分是**加法融合**（Additive Fusion），不是乘法。这意味着三个信号各自独立贡献，不会因为一个信号为 0 就抹杀其他信号。

---

### Step 9: 格式化结果

```python
for scored in scored_results:
    payload = scored.get("payload") or {}
    memory_item_dict = MemoryItem(
        id=scored["id"],
        memory=payload.get("data", ""),   # ← 原始文本在这里！
        hash=payload.get("hash"),
        score=scored["score"],
    ).model_dump()
```

**关键要点：** 返回给用户的不是向量，而是 `payload.data`（原始文本）。向量只用于检索阶段的相似度计算。

---

## 第四步：可选重排序（Reranker）

```python
if rerank and self.reranker and original_memories:
    reranked_memories = self.reranker.rerank(query, original_memories, limit)
```

**为什么需要重排序？** 向量相似度和"用户真正想要的"不完全一致。Reranker（通常是小模型）会重新理解 query 和候选记忆的相关性，做更精细的排序。

**关键要点：** Reranker 是可选增强项。默认关闭，因为它增加延迟和成本。

---

## 总结：Mem0 search 的 5 层检索架构

| 层级 | 作用 | 速度 | 是否必须 |
|------|------|------|----------|
| 1. 参数校验 | 防御非法输入 | 微秒 | ✅ 是 |
| 2. 语义检索 | 找意思相近的记忆 | 毫秒 | ✅ 是 |
| 3. 关键词检索 | 找用词精确匹配 | 毫秒 | ❌ 可选（向量库支持才启用） |
| 4. 多信号融合 | 语义 + BM25 + 实体加权 | 毫秒 | ✅ 是 |
| 5. 重排序 | 精排 Top-k | 百毫秒 | ❌ 可选 |

**核心设计哲学：** 先召回足够多候选，再用多信号融合精排，最后取 Top-k 给 LLM。不是"一步到位"，而是"分层过滤"。

---

## 对比你的 EchoMind 设计

| 维度 | Mem0 源码 | 你的 EchoMind 计划 |
|------|-----------|-------------------|
| 向量库 | 24 种可选（Chroma/PgVector/...） | 先用 Chroma + 自定义 GitHub 持久化 |
| 检索信号 | 语义 + BM25 + 实体 | 先从语义开始，后续加 BM25 |
| 过滤器 | 高级 DSL（AND/OR/NOT） | 先用 `agent_id` + `topic` 基础过滤 |
| 重排序 | 可选 Reranker | 暂不实现 |
| 实体 Boost | 内置实体库 | 暂不实现 |

**建议：** 先实现语义检索 + 基础过滤，跑通后再加 BM25 和实体。
