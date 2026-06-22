"""
手撕题 4：混合记忆召回（相似度 + 时间加权 + 关键词 + 去重）（记忆方向加分题）

面试场景：记忆系统检索时，不能只看语义相似度，还要考虑"新旧"和"关键词命中"。
这道题的核心逻辑和记忆系统 Compaction 引擎里的时间衰减 exp(-λt) + 去重一致，
这里把它组织成"召回打分"的形式。能默写打分公式 + 讲清三个权重就过关。

时间加权：time_score = e^(-λ * Δdays)  —— 越旧分越低（指数衰减）
最终得分：final = 0.5*相似度 + 0.3*时间分 + 0.2*关键词分

注：embeddings.encode / cosine_similarity / keyword_match / deduplicate 是约定省略的 helper。
"""

import math                                          # 用 math.exp 算指数衰减


# 入口：查询、候选记忆集、嵌入模型、返回 top_k、衰减系数 λ
def hybrid_memory_recall(query, memories, embeddings, top_k=5, lambda_decay=0.1):
    query_vec = embeddings.encode(query)            # 把查询编码成向量，用于算语义相似度
    results = []                                    # 收集 (记忆, 最终得分) 候选
    for mem in memories:                            # 遍历每一条候选记忆
        sim = cosine_similarity(query_vec, mem.embedding)   # ① 语义相似度：query 与该记忆向量的余弦（内容相关性）
        time_score = math.exp(-lambda_decay * mem.age_days) # ② 时间分：指数衰减，越旧(age_days 越大)分越低；λ 控衰减速度
        keyword_score = keyword_match(query, mem.text)      # ③ 关键词分：字面命中（补语义的不足，专有名词/ID 这类靠它）
        final = 0.5 * sim + 0.3 * time_score + 0.2 * keyword_score  # 加权融合：相似度主导(0.5)、新鲜度(0.3)、字面(0.2)
        results.append((mem, final))                # 记入候选
    return deduplicate(                             # 去重：合并语义重复的记忆，避免 top_k 被一堆近似条目占满
        sorted(
            results,
            key=lambda x: x[1],                     # 按 final 得分排
            reverse=True,                           # 降序：高分在前
        )
    )[:top_k]                                        # 取前 top_k 条返回


# ── 面试点（被考察什么）─────────────────────────────────────
# 1. 为什么不只用语义相似度：纯相似度会把"很相关但很旧/已过时"的记忆排前面；
#    时间加权让新记忆优先（符合"近期偏好更代表当前"），关键词分补专有名词/ID 这类语义模型的盲区。
# 2. 三个权重(0.5/0.3/0.2)怎么定：经验起点 + 用评测集调；强调它是可调超参，不是魔法数。
# 3. 为什么要去重：相似记忆会挤占 top_k，去重保证返回的是"多样且相关"的结果。
# 4. λ 怎么选：和 Compaction 的半衰期一致思路——λ = ln2 / 半衰期天数。
# 5. 串联项目：这正是记忆系统检索层该有的打分逻辑，配合 Compaction 的衰减+去重。
