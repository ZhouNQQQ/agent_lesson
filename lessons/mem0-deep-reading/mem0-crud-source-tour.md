# Mem0 CRUD 源码带读 — get() / get_all() / update() / delete() / history()

> 文件：`mem0/memory/main.py`（3296 行）
> 方法位置：`get()` @L989, `get_all()` @L1032, `update()` @L1545, `delete()` @L1568, `history()` @L1598

---

## `get()` — 单条精确查询

### 使用场景

已知 `memory_id`，要查这条记忆的完整内容。比如用户说"帮我看看 ID 为 abc123 的记忆是什么"。

### 完整代码

```python
def get(self, memory_id):
    capture_event("mem0.get", self, {"memory_id": memory_id, "sync_type": "sync"})
    memory = self.vector_store.get(vector_id=memory_id)
    if not memory:
        return None

    promoted_payload_keys = [
        "user_id", "agent_id", "run_id", "actor_id", "role",
    ]
    core_and_promoted_keys = {"data", "hash", "created_at", "updated_at", "id", "text_lemmatized", "attributed_to", *promoted_payload_keys}

    result_item = MemoryItem(
        id=memory.id,
        memory=memory.payload.get("data", ""),
        hash=memory.payload.get("hash"),
        created_at=memory.payload.get("created_at"),
        updated_at=memory.payload.get("updated_at"),
    ).model_dump()

    for key in promoted_payload_keys:
        if key in memory.payload:
            result_item[key] = memory.payload[key]

    additional_metadata = {k: v for k, v in memory.payload.items() if k not in core_and_promoted_keys}
    if additional_metadata:
        result_item["metadata"] = additional_metadata

    return result_item
```

### Layer 1: 数据获取

```python
memory = self.vector_store.get(vector_id=memory_id)
if not memory:
    return None
```

**设计意图**：直接查 `vector_store`，不是查 `db`（SQLite history 表）。向量库是**主存储**，SQLite 只是审计日志。如果向量库丢了，数据就没了。

**面试角度**：如果 `vector_store` 挂了（网络超时），这里会抛异常。但 `get()` 没有 try-catch，异常会直接上抛。这是设计选择——`get()` 是精确查询，失败就该报错，而不是返回 `None` 让调用方误判为"记录不存在"。

### Layer 2: 字段分层

```python
promoted_payload_keys = ["user_id", "agent_id", "run_id", "actor_id", "role"]
core_and_promoted_keys = {"data", "hash", "created_at", "updated_at", "id", "text_lemmatized", "attributed_to", *promoted_payload_keys}
```

**设计意图**：
- `promoted_payload_keys`：常用查询字段，提升到 API 响应顶层。
- `core_and_promoted_keys`：核心字段 + 提升字段，剩余的全部归入 `metadata`。

**面试角度**：这是**API 层级优化**。用户 80% 的查询需要 `user_id`/`agent_id`，不用每次都钻 `metadata`。同时，如果存了图片 URL、token、session 上下文等，它们不会污染顶层，而是归在 `metadata` 里。这保证了 API 响应的稳定性——核心字段位置固定，扩展字段不干扰。

**类比**：就像 HTTP 响应中 `status`/`headers`/`body` 的分层。`id`/`memory`/`hash` 是核心，`metadata` 是扩展。

### Layer 3: 响应组装

```python
result_item = MemoryItem(...).model_dump()
for key in promoted_payload_keys:
    if key in memory.payload:
        result_item[key] = memory.payload[key]
additional_metadata = {k: v for k, v in memory.payload.items() if k not in core_and_promoted_keys}
if additional_metadata:
    result_item["metadata"] = additional_metadata
```

**设计意图**：`MemoryItem` 只装核心字段，promoted 字段后补，剩余字段塞 `metadata`。

**面试角度**：为什么不直接 `return memory.payload`？因为 `payload` 可能包含内部字段（如 `text_lemmatized` 用于 BM25，调用方不需要）。`MemoryItem` 是**领域模型**，屏蔽了存储层细节。

---

## `get_all()` — 批量列表查询

### 使用场景

列出某个用户/代理/运行的所有记忆。比如"显示我所有的学习记录"。不需要 query，纯过滤。

### 完整代码

```python
def get_all(self, *, filters=None, top_k=20, **kwargs):
    _reject_top_level_entity_params(kwargs, "get_all")
    _validate_search_params(top_k=top_k)

    effective_filters = dict(filters) if filters else {}
    if "user_id" in effective_filters:
        effective_filters["user_id"] = _validate_and_trim_entity_id(effective_filters["user_id"], "user_id")
    if "agent_id" in effective_filters:
        effective_filters["agent_id"] = _validate_and_trim_entity_id(effective_filters["agent_id"], "agent_id")
    if "run_id" in effective_filters:
        effective_filters["run_id"] = _validate_and_trim_entity_id(effective_filters["run_id"], "run_id")

    if not any(key in effective_filters for key in ("user_id", "agent_id", "run_id")):
        raise ValueError("filters must contain at least one of: user_id, agent_id, run_id")

    limit = top_k
    all_memories_result = self._get_all_from_vector_store(effective_filters, limit)
    return {"results": all_memories_result}
```

### Layer 1: 参数清理

```python
_reject_top_level_entity_params(kwargs, "get_all")
```

**设计意图**：拒绝旧版 API 的 `user_id=xxx` 直接传参，强制用 `filters={"user_id": "xxx"}`。

**面试角度**：这是**API 版本演进**。旧版可能支持 `get_all(user_id="u1")`，新版统一为 `get_all(filters={"user_id": "u1"})`。`_reject_top_level_entity_params` 防止新旧参数混用导致意外行为。比如用户同时传 `user_id="u1"` 和 `filters={"user_id": "u2"}"`，到底用哪个？干脆拒绝旧方式，强制新方式。

**关键问题**：为什么出现新旧参数？因为 API 迭代过程中，可能早期设计是扁平参数，后来发现需要扩展（加 metadata 过滤、加逻辑运算符 AND/OR），扁平参数不够用了，所以升级到 dict 结构。`_reject_top_level_entity_params` 是**迁移期的强制约束**。

### Layer 2: 字段校验与截断

```python
effective_filters["user_id"] = _validate_and_trim_entity_id(...)
```

**设计意图**：entity ID 有长度限制（比如 64 字符），超长自动截断。同时校验非法字符。

**面试角度**：这是**输入防御**。如果用户传了 1000 字符的 `user_id`，向量库可能报错或性能下降。截断在前端做，防止垃圾输入打到存储层。

### Layer 3: 强制过滤（安全边界）

```python
if not any(key in effective_filters for key in ("user_id", "agent_id", "run_id")):
    raise ValueError("filters must contain at least one of: user_id, agent_id, run_id")
```

**设计意图**：必须带一个 entity ID，否则抛异常。

**面试角度**：**不是性能优化**（`list()` 有 `top_k` 限制），是**多租户安全**。防止 `get_all()` 无过滤扫描全表，把别人的记忆拉出来。

**类比**：就像数据库查询必须带 `WHERE tenant_id = ?`，否则就是跨租户数据泄露。`get_all()` 的 `top_k=20` 本身就限制了返回数量，所以性能不是问题。真正的问题是安全——如果我是用户 A，我不应该能看到用户 B 的记忆。

### Layer 4: 统一返回格式

```python
return {"results": all_memories_result}
```

**设计意图**：外层包 `{"results": [...]}`，和 `search()` 返回格式一致。

**面试角度**：API 一致性。调用方不用猜返回结构——不管是 `get_all()` 还是 `search()`，都是 `result["results"]` 取列表。

---

## `_get_all_from_vector_store()` — 适配层

### 使用场景

内部方法，解包不同 vector store 的返回格式。

### 完整代码

```python
def _get_all_from_vector_store(self, filters, limit):
    memories_result = self.vector_store.list(filters=filters, top_k=limit)

    if isinstance(memories_result, (tuple, list)) and len(memories_result) > 0:
        first_element = memories_result[0]
        if isinstance(first_element, (list, tuple)):
            actual_memories = first_element
        else:
            actual_memories = memories_result
    else:
        actual_memories = memories_result

    promoted_payload_keys = ["user_id", "agent_id", "run_id", "actor_id", "role"]
    core_and_promoted_keys = {"data", "hash", "created_at", "updated_at", "id", "text_lemmatized", "attributed_to", *promoted_payload_keys}

    formatted_memories = []
    for mem in actual_memories:
        memory_item_dict = MemoryItem(
            id=mem.id,
            memory=mem.payload.get("data", ""),
            hash=mem.payload.get("hash"),
            created_at=mem.payload.get("created_at"),
            updated_at=mem.payload.get("updated_at"),
        ).model_dump(exclude={"score"})

        for key in promoted_payload_keys:
            if key in mem.payload:
                memory_item_dict[key] = mem.payload[key]

        additional_metadata = {k: v for k, v in mem.payload.items() if k not in core_and_promoted_keys}
        if additional_metadata:
            memory_item_dict["metadata"] = additional_metadata

        formatted_memories.append(memory_item_dict)

    return formatted_memories
```

### Layer 1: 格式解包

```python
if isinstance(memories_result, (tuple, list)) and len(memories_result) > 0:
    first_element = memories_result[0]
    if isinstance(first_element, (list, tuple)):
        actual_memories = first_element
    else:
        actual_memories = memories_result
```

**设计意图**：不同 vector store 返回格式不同：
- Chroma 返回 `[[mem1, mem2]]`（嵌套 list）
- Qdrant 返回 `[mem1, mem2]`（扁平 list）

**面试角度**：**Factory 模式 + 适配层**。加新 vector store 时不用改 `get_all()`，只需保证 `_get_all_from_vector_store()` 能解包。这是**开闭原则**——对扩展开放（加新 store），对修改关闭（不改核心逻辑）。

### Layer 2: 格式统一

```python
memory_item_dict = MemoryItem(...).model_dump(exclude={"score"})
```

**设计意图**：`get_all()` 没有 relevance score，所以 `exclude={"score"}`。`search()` 有 score，所以不 exclude。

**面试角度**：同一套 `MemoryItem` 模型服务两个场景，通过 `exclude` 控制输出字段。避免为 `get_all()` 和 `search()` 各写一个模型。

---

## `get()` vs `get_all()` 核心差异

| 维度 | `get()` | `get_all()` |
|------|---------|-------------|
| 查询方式 | 精确 ID 查询 | 批量过滤查询 |
| 必须参数 | `memory_id` | filters 含 `user_id`/`agent_id`/`run_id` |
| 返回格式 | `{"id": ..., "memory": ...}`（单条 dict） | `{"results": [...]}`（列表包装） |
| 安全设计 | 无（ID 本身已隔离） | 强制 entity 过滤（防跨租户） |
| 底层调用 | `vector_store.get()` | `vector_store.list()` |
| 使用场景 | 已知 ID 查详情 | 列出一个 namespace 的所有记忆 |

---

## `update()` — 内容替换 + 实体重建

### 使用场景

修改已有记忆的内容。比如用户说"把'喜欢 Python'改成'喜欢 Go'"。

### 入口代码

```python
def update(self, memory_id, data, metadata=None):
    capture_event("mem0.update", self, {"memory_id": memory_id, "sync_type": "sync"})
    existing_embeddings = {data: self.embedding_model.embed(data, "update")}
    self._update_memory(memory_id, data, existing_embeddings, metadata)
    return {"message": "Memory updated successfully!"}
```

### Layer 1: 提前 embedding

```python
existing_embeddings = {data: self.embedding_model.embed(data, "update")}
```

**设计意图**：`existing_embeddings` 是 dict，key 是 `data`，value 是 embedding。如果 `data` 在 batch 中重复出现，只算一次 embedding。

**面试角度**：`update()` 是单条调用，这里看起来过度设计。但实际上 `_create_memory()` 也用这个参数结构，所以 `update()` 和 `create()` 共享同一套 embedding 缓存逻辑。这是**代码复用**的设计。

---

## `_update_memory()` — 核心实现

### 使用场景

内部方法，处理 update 的完整逻辑。

### 完整代码

```python
def _update_memory(self, memory_id, data, existing_embeddings, metadata=None):
    try:
        existing_memory = self.vector_store.get(vector_id=memory_id)
    except Exception:
        raise ValueError(f"Error getting memory with ID {memory_id}. Please provide a valid 'memory_id'")

    if existing_memory is None:
        raise ValueError(f"Memory with id {memory_id} not found")

    prev_value = existing_memory.payload.get("data")

    new_metadata = deepcopy(metadata) if metadata is not None else {}
    new_metadata["data"] = data
    new_metadata["hash"] = hashlib.md5(data.encode()).hexdigest()
    new_metadata["text_lemmatized"] = lemmatize_for_bm25(data)
    new_metadata["created_at"] = existing_memory.payload.get("created_at")
    new_metadata["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Preserve session identifiers from existing memory only if not provided in new metadata
    if "user_id" not in new_metadata and "user_id" in existing_memory.payload:
        new_metadata["user_id"] = existing_memory.payload["user_id"]
    if "agent_id" not in new_metadata and "agent_id" in existing_memory.payload:
        new_metadata["agent_id"] = existing_memory.payload["agent_id"]
    if "run_id" not in new_metadata and "run_id" in existing_memory.payload:
        new_metadata["run_id"] = existing_memory.payload["run_id"]
    if "actor_id" in existing_memory.payload:
        new_metadata["actor_id"] = existing_memory.payload["actor_id"]
    if "role" not in new_metadata and "role" in existing_memory.payload:
        new_metadata["role"] = existing_memory.payload["role"]

    if data in existing_embeddings:
        embeddings = existing_embeddings[data]
    else:
        embeddings = self.embedding_model.embed(data, "update")
    self.vector_store.update(vector_id=memory_id, vector=embeddings, payload=new_metadata)

    self.db.add_history(memory_id, prev_value, data, "UPDATE", ...)
    self._remove_memory_from_entity_store(memory_id, session_filters)
    self._link_entities_for_memory(memory_id, data, session_filters)
```

### Layer 1: 容错设计

```python
try:
    existing_memory = self.vector_store.get(vector_id=memory_id)
except Exception:
    raise ValueError(f"Error getting memory with ID {memory_id}...")
```

**设计意图**：捕获所有异常，统一包装成 `ValueError`。

**面试角度**：如果 vector store 挂了（网络超时），这里不会暴露底层异常，而是给调用方一个友好的错误信息。属于**防御式编程**。但注意：这是 `except Exception`  broad catch，可能会吞掉本不该吞的异常（比如 `KeyboardInterrupt`）。更好的做法是 `except (ConnectionError, TimeoutError)`。

### Layer 2: 内容更新

```python
new_metadata["hash"] = hashlib.md5(data.encode()).hexdigest()
new_metadata["text_lemmatized"] = lemmatize_for_bm25(data)
new_metadata["created_at"] = existing_memory.payload.get("created_at")
new_metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
```

**设计意图**：重新算 `hash` 和 `text_lemmatized`（用于 BM25 关键词索引）。`created_at` 保留，`updated_at` 刷新。

**面试角度**：为什么连 `hash` 都重新算？因为内容变了，所有派生字段都必须同步。如果 hash 不更新，dedup 逻辑会误判两条内容不同的记录为相同。

### Layer 3: Session 标识继承（安全设计）

```python
if "user_id" not in new_metadata and "user_id" in existing_memory.payload:
    new_metadata["user_id"] = existing_memory.payload["user_id"]
```

**设计意图**：新 metadata 没提供 `user_id`/`agent_id`/`run_id` 时，从旧记录继承。

**面试角度**：这是**安全设计**，不是便利设计。如果允许覆盖，用户可能误操作把记录移到别人的 namespace 下。比如：
- 用户 A 调用 `update(memory_id="mem_1", data="new text", metadata={"user_id": "user_B"})`
- 如果不阻止，用户 A 能把用户 B 的记忆内容改掉

**代码逻辑**：新 metadata 显式传了不同的 `user_id`，代码会**接受覆盖**。因为条件判断是 `if "user_id" not in new_metadata`，不是 `if new_metadata.get("user_id") != old_user_id`。这实际上是**信任调用方**的设计——如果调用方显式传了 `user_id`，就尊重它的选择。

**潜在风险**：如果调用方是用户输入直接传递，可能被恶意篡改。应该在更上层做权限校验，而不是在 `_update_memory` 里做。

### Layer 4: 向量同步更新

```python
if data in existing_embeddings:
    embeddings = existing_embeddings[data]
else:
    embeddings = self.embedding_model.embed(data, "update")
self.vector_store.update(vector_id=memory_id, vector=embeddings, payload=new_metadata)
```

**设计意图**：`update()` 不仅是改 `payload`，**向量也重新算**。因为语义内容变了，embedding 必须同步。

**面试角度**：如果向量不更新，搜索时按新 query 匹配到旧向量，会出现**内容-向量不匹配**。比如记忆内容改成了 "Likes Go"，但向量还是 "Likes Python" 的 embedding，搜索 "Go" 时永远找不到这条记录。

### Layer 5: 实体图谱重建

```python
self._remove_memory_from_entity_store(memory_id, session_filters)
self._link_entities_for_memory(memory_id, data, session_filters)
```

**设计意图**：先拆旧关联，再建新的。

**面试角度**：为什么不是增量修改？因为文本内容变化后，实体可能**完全变了**。比如 "Likes Python" → "Likes Go"，Python 实体要移除，Go 实体要新增。增量修改会留下**脏数据**（Python 实体仍然关联这条记忆，但记忆内容已经不提 Python 了）。先拆后建保证了**实体图谱和文本内容始终一致**。

---

## `delete()` — 单条删除

### 使用场景

删除单条记忆。比如用户说"删掉那条关于 Python 的记录"。

### 入口代码

```python
def delete(self, memory_id):
    capture_event("mem0.delete", self, {"memory_id": memory_id, "sync_type": "sync"})
    existing_memory = self.vector_store.get(vector_id=memory_id)
    if existing_memory is None:
        raise ValueError(f"Memory with id {memory_id} not found")
    self._delete_memory(memory_id, existing_memory)
    return {"message": "Memory deleted successfully!"}
```

### Layer 1: 预检查

```python
existing_memory = self.vector_store.get(vector_id=memory_id)
if existing_memory is None:
    raise ValueError(f"Memory with id {memory_id} not found")
```

**设计意图**：先查存在性，再删。不是盲目调用 `vector_store.delete()`。

**面试角度**：如果 memory_id 不存在，向量库可能**静默成功**（幂等删除），但用户期望的是报错。这里显式检查，确保用户知道自己在删什么。

---

## `_delete_memory()` — 核心实现

### 完整代码

```python
def _delete_memory(self, memory_id, existing_memory=None):
    if existing_memory is None:
        existing_memory = self.vector_store.get(vector_id=memory_id)
        if existing_memory is None:
            raise ValueError(f"Memory with id {memory_id} not found")
    prev_value = existing_memory.payload.get("data", "")
    created_at = _normalize_iso_timestamp_to_utc(existing_memory.payload.get("created_at"))
    updated_at = datetime.now(timezone.utc).isoformat()
    payload = existing_memory.payload or {}
    session_filters = {k: payload[k] for k in ("user_id", "agent_id", "run_id") if payload.get(k)}

    self.vector_store.delete(vector_id=memory_id)
    self.db.add_history(
        memory_id, prev_value, None, "DELETE",
        created_at=created_at, updated_at=updated_at, is_deleted=1,
    )
    self._remove_memory_from_entity_store(memory_id, session_filters)
```

### Layer 1: 信息提取

```python
prev_value = existing_memory.payload.get("data", "")
created_at = _normalize_iso_timestamp_to_utc(existing_memory.payload.get("created_at"))
session_filters = {k: payload[k] for k in ("user_id", "agent_id", "run_id") if payload.get(k)}
```

**设计意图**：提取 `prev_value`、`created_at`、`session_filters`，用于 history 和 entity 清理。

### Layer 2: 物理删 + 软删记录

```python
self.vector_store.delete(vector_id=memory_id)
self.db.add_history(memory_id, prev_value, None, "DELETE", ..., is_deleted=1)
```

**设计意图**：
- `vector_store.delete()`：物理删除向量。
- `db.add_history(..., is_deleted=1)`：history 表标记删除，记录永久保留。

**面试角度**：为什么 history 不物理删？**审计需求**。用户可能问"这个记忆之前是什么内容？"可以查 history。如果物理删除，历史就无法追溯。这是**合规设计**（类似数据库的 soft delete）。

### Layer 3: 实体图谱清理

```python
self._remove_memory_from_entity_store(memory_id, session_filters)
```

**设计意图**：删除 memory 在 entity store 中的关联。

**面试角度**：如果漏掉这步，entity store 里会有指向不存在 memory 的**悬空指针**。搜索结果里会出现 ghost 数据——实体搜索返回了 memory_id，但 `get(memory_id)` 返回 `None`。

---

## `delete_all()` — 批量删除

### 使用场景

批量删除一个 namespace 的记忆。比如"删除我所有关于项目的记录"。

### 完整代码

```python
def delete_all(self, user_id=None, agent_id=None, run_id=None):
    filters = {}
    if user_id: filters["user_id"] = user_id
    if agent_id: filters["agent_id"] = agent_id
    if run_id: filters["run_id"] = run_id

    if not filters:
        raise ValueError("At least one filter is required... use `reset()`")

    memories = self.vector_store.list(filters=filters)[0]
    for memory in memories:
        self._delete_memory(memory.id)

    return {"message": "Memories deleted successfully!"}
```

### Layer 1: 强制过滤

```python
if not filters:
    raise ValueError("At least one filter is required... use `reset()`")
```

**设计意图**：和 `get_all()` 一样，必须带 entity ID。如果要全删，必须调用 `reset()`。

**面试角度**：这是**权限隔离**。`delete_all()` 是 namespace 级别操作，`reset()` 是全局级别。分开两个方法，防止误触全删。就像 Linux 的 `rm -rf /` 需要特殊确认。

### Layer 2: 逐条删除

```python
memories = self.vector_store.list(filters=filters)[0]
for memory in memories:
    self._delete_memory(memory.id)
```

**设计意图**：不是批量删除 API，而是循环单条删。

**面试角度**：为什么不用 batch delete？因为每条删除都要：
1. 写 history 记录（审计）
2. 清理 entity store（图谱一致性）
这些是逐条操作，batch delete 会丢失**审计粒度**。如果 100 条记忆被删，history 表应该有 100 条 DELETE 记录，而不是 1 条。

---

## `history()` — 审计查询

### 使用场景

查看一条记忆的变更历史。比如"这条记忆被改过几次？最初是什么内容？"

### 完整代码

```python
def history(self, memory_id):
    capture_event("mem0.history", self, {"memory_id": memory_id, "sync_type": "sync"})
    return self.db.get_history(memory_id)
```

### Layer 1: 单一数据源

```python
return self.db.get_history(memory_id)
```

**设计意图**：唯一数据来源是 `self.db`（SQLite），不是 `vector_store`。

**面试角度**：history 是"写时记录"，不依赖向量库的存储能力。即使换了 vector store（Chroma → Qdrant），history 表格式不变。这是**存储层解耦**——审计日志独立演化，不受存储后端影响。

**面试角度**：如果 `vector_store` 挂了，用户还能不能查历史？**能**。因为 `history()` 只查 `self.db`，不碰 `vector_store`。这是**高可用设计**——即使主存储故障，审计功能不受影响。

---

## CRUD 方法对照表

| 方法 | 使用场景 | 必须参数 | 返回格式 | 关键设计 |
|------|----------|----------|----------|----------|
| `get()` | 已知 memory_id，查单条详情 | `memory_id` | `{"id": ..., "memory": ...}` | 字段分层（promoted vs metadata） |
| `get_all()` | 列出一个 namespace 的所有记忆 | filters 含 entity ID | `{"results": [...]}` | 强制 entity 过滤（安全） |
| `search()` | 用自然语言查询，找相关记忆 | query + filters | `{"results": [...]}` | 5 层混合检索 |
| `update()` | 修改已有记忆内容 | `memory_id` + `data` | `{"message": ...}` | 向量同步 + 实体重建 |
| `delete()` | 删除单条记忆 | `memory_id` | `{"message": ...}` | 物理删 + 软删 history |
| `delete_all()` | 批量删除 namespace 记忆 | `user_id`/`agent_id`/`run_id` | `{"message": ...}` | 逐条删（保审计粒度） |
| `history()` | 查看记忆变更历史 | `memory_id` | `[{"action": "ADD/UPDATE/DELETE", ...}]` | 只查 SQLite（解耦） |
| `reset()` | 清空整个存储（全局删） | 无 | `{"message": ...}` | 独立方法（权限隔离） |

---

## 面试题

**Q1**：`get_all()` 中 `_reject_top_level_entity_params(kwargs, "get_all")` 的作用是什么？为什么从旧版 API 的 `user_id="xxx"` 切换到 `filters={"user_id": "xxx"}`？

> 你的回答：____________________________________

**Q2**：`_update_memory()` 中 session 标识继承的逻辑，如果新 metadata 显式传了不同的 `user_id`，代码会怎么做？这是安全设计还是信任调用方的设计？

> 你的回答：____________________________________

**Q3**：`delete_all()` 循环调用 `_delete_memory()` 逐条删，而不是用 vector store 的 batch delete。如果改为 batch delete，会丢失什么？

> 你的回答：____________________________________

**Q4**：`history()` 只查 `self.db`，不查 `vector_store`。如果 `vector_store` 挂了，用户还能不能查历史？这体现了什么设计原则？

> 你的回答：____________________________________
