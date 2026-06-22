"""
手撕题 2：工具路由算法（语义匹配选工具）

面试场景：工具有很多个时，不能全塞进 prompt（烧 token + 模型选晕）。
先用"用户 query 和工具描述的语义相似度"筛出最相关的几个工具，再交给 LLM 决策。
这就是讲义 3.5 提到的"工具检索（tool retrieval）"。

注：embeddings.encode / cosine_similarity 是约定省略的 helper。
"""


# 入口：用户问题、全部工具、嵌入模型、返回前 top_k 个、相似度阈值
def tool_router(user_query, tools, embeddings, top_k=3, threshold=0.7):
    query_vec = embeddings.encode(user_query)       # 把用户问题编码成向量（语义表示），用于和工具描述比相似度
    scores = []                                     # 收集 (工具, 最终得分) 的候选列表
    for tool in tools:                              # 遍历每一个候选工具
        sim = cosine_similarity(query_vec, tool.embedding)  # 算 query 向量 与 工具描述向量 的余弦相似度（0~1，越大越相关）
        final_score = sim * tool.priority_weight    # 乘以工具的优先级权重：让重要/可靠的工具更容易被选中（业务先验）
        if final_score > threshold:                 # 阈值过滤：低于阈值的工具直接淘汰，宁缺毋滥（防乱选工具）
            scores.append((tool, final_score))      # 通过阈值的，进入候选
    return sorted(                                  # 对候选按得分排序
        scores,
        key=lambda x: x[1],                         # 按元组第二项（final_score）排
        reverse=True,                               # 降序：高分在前
    )[:top_k]                                        # 只取前 top_k 个返回（控制注入 prompt 的工具数量）


# ── 面试点（被考察什么）─────────────────────────────────────
# 1. 为什么要路由：工具多时全塞 prompt 既烧 token 又降低选择准确率 → 先检索缩小候选。
# 2. 为什么乘 priority_weight：纯语义相似度没有业务先验，加权让"更可靠/更该优先"的工具胜出。
# 3. 为什么要 threshold：没有任何工具够相关时，宁可返回空，也不要硬塞一个不相关工具。
# 4. 这本质是一次 RAG（对"工具描述"做检索），和 RAG Pipeline 同源。
