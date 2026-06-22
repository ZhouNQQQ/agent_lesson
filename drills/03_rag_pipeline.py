"""
手撕题 3：RAG Pipeline（检索增强生成，几乎必考）

★ RAG 分两个阶段，别混在一起（这是高频混淆点，也是面试爱挖的）：
  - 离线·索引阶段(indexing/ingestion)：文档加载 → 切分(chunk) → 嵌入 → 写入向量库。
    建库时做一次（文档更新时增量做）。
  - 在线·查询阶段(query)：用户问题 → 嵌入 → 检索 → 重排 → 拼上下文 → 生成。每次提问都做。
  → 切分(chunking)属于离线建库，**不是**每次提问都切文档。

何时用 RAG：模型需要它训练数据里没有的知识时——私有文档、最新信息、企业知识库问答。
在 Agent 里，RAG 检索常被封装成一个工具(retrieve)，供 ReAct 在 Action 阶段调用。

注：splitter / embedder / vector_store / reranker / llm 是约定省略的 helper。
"""


# ── 阶段一：离线索引（建库时做一次；文档更新时增量做）─────────────────
def build_index(documents, splitter, embedder, vector_store):
    chunks = splitter.split(documents)              # 切分：把长文档切成小块(chunk)。切太大→噪声多/Lost in Middle；切太小→丢上下文
    for chunk in chunks:                            # 遍历每个 chunk
        vec = embedder.encode(chunk.text)           # 把 chunk 文本嵌入成向量
        vector_store.add(vec, chunk)                # 连同原文一起写入向量库（建索引）
    # 关键：切分+嵌入+入库都在这一步一次性完成；查询阶段不再碰原始文档、不再切分。


# ── 阶段二：在线查询（每次用户提问都执行）───────────────────────────
def rag_query(query, embedder, vector_store, reranker, llm, top_k=10, rerank_k=3):
    q_vec = embedder.encode(query)                  # 用户问题嵌入成向量（必须和建库用同一个 embedder！）
    candidates = vector_store.search(q_vec, top_k=top_k)        # 粗筛(海选)：向量检索 top10 候选（over-fetch）
    ranked = reranker.rerank(query, candidates, top_k=rerank_k) # 精筛(决赛)：Cross-Encoder 重排出 top3
    context = "\n".join(c.text for c in ranked)     # 拼上下文：把 top3 片段拼成"证据"
    answer = llm.generate(                          # 生成：证据 + 问题一起给 LLM
        f"基于以下上下文回答问题：{context}\n问题：{query}"  # 明确"基于上下文回答"，把答案锚定在证据上（防幻觉）
    )
    return answer                                   # 返回答案


# ── 面试点（被考察什么）─────────────────────────────────────
# 1. 两阶段必须分清：切分/嵌入/入库 = 离线建库；检索/重排/生成 = 在线查询。混在一起是常见错误。
# 2. chunking 质量在"建库时"就定死了，查询时无法补救——切坏了检索就召不准，所以 chunk 策略很关键。
#    chunk 取舍：定长 vs 语义切分 vs 重叠窗口。
# 3. 建库和查询必须用同一个 embedder，否则向量空间对不上，检索失效。
# 4. 两段式检索：top10 粗筛(快) → top3 精排(准)，= over-fetch 后 rerank（精度-速度 trade-off）。
# 5. 防幻觉：prompt 强制"基于上下文回答" + 要求引用来源 + 允许说不知道。
# 6. 进阶优化：混合检索(向量+BM25)、query 改写/HyDE、父子块、检索侧 recall@k 评估。
# 7. 串联：RAG 和"记忆注入"本质都是"检索+增强"；在 Agent 里 retrieve 常作为一个工具被 ReAct 调用。
