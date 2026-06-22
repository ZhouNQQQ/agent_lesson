# Week 1 Part B 技术方案：评估 + 去重 + 持久化

> 文档类型：技术设计文档（Design Doc）
> 状态：✅ 已完成（编码 + 测试通过）
> 日期：2026-06-11

---

## 一、背景

### 1.1 为什么需要 Part B

Week 1 Part A 完成了 `Extractor`（提取器），但存在三个关键缺口：

| 缺口 | 问题 | 影响 |
|------|------|------|
| **无评估体系** | 10 条测试集，Mock F1=63%，无法量化真实 LLM 效果 | 不知道优化方向 |
| **内存存储** | `SimilaritySearch` 用 `np.ndarray` 存 embedding，进程重启数据丢失 | 不可用于生产 |
| **模块未串联** | Extractor、Updater、Store 各自可运行，未验证端到端链路 | 集成风险未知 |

### 1.2 核心挑战

- **TF-IDF Mock 的维度漂移**：动态 vocab 导致 embedding 维度变化，与 Chroma 的固定维度冲突
- **Chroma API 兼容性**：不同版本的 `include` 参数差异（`ids` 在 `query` 和 `get` 中的支持不同）
- **Update 决策与存储耦合**：Updater 需要知道存储层的接口契约

---

## 二、目标

### 2.1 里程碑（Part B 结束时）

1. **Updater 接入持久化向量库**：`MemoryUpdater` 直接调用 `ChromaVectorStore`，不再依赖内存数组
2. **4 个端到端场景验证**：ADD / UPDATE / DELETE / BATCH_MIXED 全部通过
3. **数据模型支持 ID 持久化**：`MemoryItem` 带 `id` 字段，与 Chroma 的 UUID 关联
4. **Mock 定位明确**：仅用于开发/测试阶段，非生产降级方案

### 2.2 非目标（不在 Part B 范围）

- 真实 LLM API 接入（Kimi key 401，阻塞中）
- 50 条测试集评估（需要真实 LLM）
- HNSW 算法深度优化（Week 2 内容）
- 多用户隔离（Week 4 内容）

---

## 三、技术方案

### 3.1 架构图

```
┌─────────────┐     ┌─────────────┐     ┌───────────────────┐
│  Conversation │ --> │  Extractor   │ --> │  MemoryItem[]     │
│  (对话文本)   │     │  (LLM/ Mock) │     │  (结构化记忆)      │
└─────────────┘     └─────────────┘     └───────────────────┘
                                                │
                                                ▼
                                        ┌───────────────────┐
                                        │   MemoryUpdater    │
                                        │  (分层决策引擎)     │
                                        │                   │
                                        │  - decide():      │
                                        │    ADD/UPDATE/    │
                                        │    DELETE/NOOP    │
                                        │  - apply():       │
                                        │    批量执行        │
                                        └───────────────────┘
                                                │
                                                ▼
                                        ┌───────────────────┐
                                        │  ChromaVectorStore │
                                        │  (持久化向量库)     │
                                        │                   │
                                        │  - insert()       │
                                        │  - search()       │
                                        │  - update()       │
                                        │  - delete()       │
                                        │  - list()         │
                                        └───────────────────┘
```

### 3.2 关键接口契约

**MemoryUpdater → ChromaVectorStore**

```python
class MemoryUpdater:
    def __init__(self, store: ChromaVectorStore):
        self.store = store  # 直接依赖存储层
        self.detector = ContradictionDetector()
        # 不再需要 self.searcher（已删除 SimilaritySearch）
    
    def decide(self, new_item: MemoryItem) -> Tuple[Operation, Optional[MemoryItem], str]:
        # 1. 调用 store.search() 做 Top-s 检索
        top_matches = self.store.search(new_item.content, top_k=self._top_s)
        # 2. 分层决策（高置信度 / 模糊区 / 无关）
        # 3. 矛盾检测（高相似 + 反义词）
        # 4. 返回 (op, target, reason)
    
    def apply(self, items: List[MemoryItem]) -> List[Dict]:
        # 对每个 item 调用 decide()，然后执行 store.insert/update/delete
        # 返回操作日志
```

### 3.3 数据模型变更

**MemoryItem 添加 `id` 字段**

```python
@dataclass
class MemoryItem:
    content: str
    category: MemoryCategory
    importance: float
    source: str
    timestamp: str
    entity: Optional[str] = None
    confidence: float = 1.0
    id: str = ""  # 新增：Chroma 持久化用 UUID
```

**原因**：Chroma 的 `collection.add()` 要求传入 `ids` 列表，用于后续 `update`/`delete`/`get_by_id`。如果 MemoryItem 不带 id，存储层需要自行维护 id ↔ item 的映射，增加复杂度。

### 3.4 ChromaVectorStore 设计

**存储结构**

| 字段 | Chroma 内部 | 说明 |
|------|------------|------|
| `id` | SQLite ids 列 | UUID，MemoryItem.id 直接映射 |
| `document` | SQLite documents 列 | 原始文本（MemoryItem.content） |
| `embedding` | Parquet 文件 | 向量（EmbeddingProvider.embed() 输出） |
| `metadata` | SQLite metadatas 列 | JSON：category, importance, entity, source, timestamp, confidence |

**关键实现细节**

1. **TF-IDF 维度漂移处理**：
   - 问题：Mock embedder 的 vocab 动态扩展，导致新查询的 embedding 维度与已有数据不一致
   - 解决：`search()` 中检查 `query_vec.shape[1] != stored_dim`，若不一致则重建整个 collection（删除 + 重新插入所有数据）
   - 代价：O(N) 重建，但 N 小时（测试阶段）可接受

2. **insert() 的合并逻辑**：
   - 如果 collection 已有数据，insert 时先 `list()` 所有数据 + 新数据，统一 embed 后重建 collection
   - 保证所有向量维度一致

3. **update() 的实现**：
   - Chroma 不支持原生 update，采用"先 delete 再 insert"策略
   - 保留相同 ID（如果 new_item.id 为空则生成新 ID）

---

## 四、关键决策记录

### 决策 1：Mock 的定位

- **选项 A**：Mock 作为生产降级方案（LLM 挂了切 Mock）
- **选项 B**：Mock 仅用于开发/测试，生产不启用
- **选择**：B
- **理由**：Mock 基于关键词规则匹配，无法处理真实用户的自然语言变体。生产降级应返回错误/缓存，而不是用 Mock 硬顶。

### 决策 2：Chroma 选型

- **选项 A**：Pinecone（托管，需 API key）
- **选项 B**：Milvus（分布式，过重）
- **选项 C**：Chroma（本地 SQLite + Parquet，零依赖）
- **选择**：C
- **理由**：学习阶段不需要托管服务，Chroma 本地持久化足够；API 简洁；社区活跃。

### 决策 3：MemoryItem 是否 frozen

- **选项 A**：保留 `frozen=True`，id 由存储层外部维护
- **选项 B**：取消 `frozen=True`，添加 `id: str = ""`
- **选择**：B
- **理由**：Chroma 的 `collection.add()` 需要传入 id，如果 MemoryItem 不可变，存储层需要创建 id→item 映射表，增加复杂度。取消 frozen 后，存储层可以直接修改 `item.id`。

---

## 五、测试结果

### 5.1 端到端测试（pipeline_test.py）

| 场景 | 输入 | 期望 | 结果 |
|------|------|------|------|
| **A: ADD** | 空库 + 2 条新记忆 | 库中有 2 条 | ✅ 通过 |
| **B: UPDATE** | 先插入"喜欢 Python"，再插入"非常喜欢 Python 做后端" | 旧记忆被替换，新内容入库 | ✅ 通过 |
| **C: DELETE** | 先插入"喜欢 Python"，再插入"不喜欢 Python"（高置信度否定） | 旧记忆被删除 | ✅ 通过 |
| **D: BATCH_MIXED** | 基础库 2 条 + 混合批（新增 + 更新 + 无关） | 最终 4 条，决策正确 | ✅ 通过 |

### 5.2 关键验证点

- **UPDATE 语义正确**："用户喜欢 Python" → "用户非常喜欢 Python 做后端"，触发 UPDATE（score=0.71，same entity+category）
- **DELETE 安全门控**："用户不喜欢 Python" 与 "用户喜欢 Python" 相似度 0.91，但检测到"不"反义词，触发 DELETE，且安全门控通过（高置信度否定）
- **批量操作无冲突**：3 条混合输入，Updater 正确区分 ADD/UPDATE/ADD，无 race condition

---

## 六、遗留问题

| 问题 | 优先级 | 负责周 |
|------|--------|--------|
| Kimi API key 401 | P0 | 阻塞 Week 1 评估 |
| 50 条测试集评估 | P1 | Week 1 收尾 |
| HNSW 索引深度优化 | P1 | Week 2 |
| 多用户隔离 | P2 | Week 4 |
| Embedding 换真实模型 | P1 | Week 2/3 |

---

## 七、产出物

```
memory-manager/
├── updater.py                # 修改：接入 ChromaVectorStore，删除 SimilaritySearch
├── extractor.py              # 修改：MemoryItem 添加 id 字段
├── chroma_store.py           # 新增：Chroma 向量库封装（含 TF-IDF 维度漂移处理）
├── pipeline_test.py          # 新增：端到端集成测试（4 场景）
└── venv/                     # 已安装 chromadb + pydantic
```

---

## 八、面试点总结

1. **"为什么用 Chroma 而不是 Pinecone？"**
   - 学习阶段本地优先，Chroma 零依赖；Pinecone 需要托管和 API key；Milvus 过重。

2. **"TF-IDF 维度漂移怎么处理？"**
   - 检测查询维度与存储维度不一致时，重建整个 collection（扩展 vocab 后重新 embed 所有数据）。

3. **"UPDATE 和 DELETE 的决策逻辑是什么？"**
   - UPDATE：相似度 0.3-0.9 + 同 entity + 同 category → 替换旧记忆
   - DELETE：相似度 > 0.9 + 矛盾检测通过（反义词/否定词）+ 安全门控（高置信度）→ 删除旧记忆

4. **"Mock 模式能用于生产吗？"**
   - 不能。Mock 是开发测试工具，用于验证架构链路。生产降级应返回错误。

5. **"MemoryItem 为什么取消 frozen？"**
   - Chroma 需要持久化 ID，frozen 会导致存储层维护额外的 id→item 映射，增加复杂度。
