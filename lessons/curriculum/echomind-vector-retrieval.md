# EchoMind 向量检索原理：向量怎么变回文本？

## 核心问题

> 向量是一串浮点数，LLM 看不懂浮点数。检索出来的 top-k 是向量，怎么知道具体内容是什么？

## 答案：向量 + Payload 一起存

向量库不是只存向量，而是**向量 + 元数据（payload）**成对存储：

```python
# 存入时
vector_store.insert(
    vectors=[[0.1, 0.3, -0.5, ...]],  # 768维浮点数组（机器用）
    payloads=[{
        "id": "mem_001",
        "text": "用户喜欢简洁直接的回答",  # ← 原始文本（LLM用）
        "category": "preference",
        "agent_id": "AIAgent学习笔记",
        "topic": "coding",
        "created_at": "2026-06-09T10:00:00Z",
    }]
)

# 检索时
results = vector_store.search(
    query="用户喜欢什么风格？",
    vectors=query_embedding,
    top_k=5
)
# 返回的是 [{id, score, payload}, ...]
# payload.text 就是原始文本，直接给 LLM
```

## 数据流向（详细版）

```
用户提问: "按照我的偏好来写"
         │
         ▼
    ┌────────────────────────┐
    │  1. 向量化查询          │
    │  "用户偏好风格" → [0.2, -0.1, ...] │
    └────────────────────────┘
         │
         ▼
    ┌────────────────────────┐
    │  2. 向量库检索          │
    │  找最相似的 top-k 向量  │
    └────────────────────────┘
         │
         ▼
    ┌────────────────────────┐
    │  3. 返回结果结构        │
    │  {                       │
    │    id: "mem_001",        │
    │    score: 0.92,          │  ← 相似度分数
    │    payload: {             │  ← 这才是 LLM 需要的
    │      text: "用户喜欢简洁...",
    │      category: "preference",
    │      ...                 │
    │    }                     │
    │  }                       │
    └────────────────────────┘
         │
         ▼
    ┌────────────────────────┐
    │  4. 构造 LLM Prompt     │
    │  相关记忆：              │
    │  - [preference] 用户喜欢简洁直接... │
    │  - [habit] 用户用Python...        │
    │  新消息：按照我的偏好来写          │
    └────────────────────────┘
         │
         ▼
    LLM 生成回复（带着这些记忆上下文）
```

## 类比

| 类比 | 向量 | Payload |
|------|------|---------|
| 图书馆 | 书的位置编码（索书号） | 书的实际内容 |
| 搜索引擎 | 网页的索引向量 | 网页标题+摘要 |
| 大脑 | 神经元激活模式 | 具体记忆内容 |

**向量是"地址"，payload 是"房子里的东西"。** 检索时按地址找到房子，取出里面的东西给 LLM。

## 代码示例（Mem0 源码中的实际结构）

```python
# mem0/vector_stores/base.py
class OutputData:
    id: Optional[str]      # 记忆 ID
    score: Optional[float]  # 相似度分数
    payload: Optional[Dict]   # ← 包含 text, metadata 等

# 检索结果
def search(self, query, vectors, top_k=5, filters=None):
    # 返回 List[OutputData]
    # LLM 看到的是 OutputData.payload["text"]
```

## 关键结论

1. **向量不直接给 LLM** — 向量是机器用的，payload.text 才是 LLM 用的
2. **检索的本质是"筛选"** — 从百万条记忆中，用向量相似度快速挑出最相关的 5 条
3. **节省的是 Token** — 只把 5 条相关记忆塞进 prompt，而不是 1000 条历史记录
