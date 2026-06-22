## 4. 阶段三：Multi-Agent与任务编排（2-3周）

### 4.1 学习目标（SMART）

- **具体（Specific）**：掌握四种多Agent协作模式，能使用sessions_spawn和sessions_send实现Agent间通信，构建至少3个Agent协作的复杂系统
- **可衡量（Measurable）**：完成一个多Agent协作系统，包含任务分配、子Agent委派、结果汇总、异常处理，至少覆盖2种协作模式
- **可实现（Achievable）**：基于阶段二的Skills和记忆基础，有编程基础的开发者2-3周可完成
- **相关性（Relevant）**：Multi-Agent是处理复杂任务的核心范式，是求职面试的高频考点
- **时限（Time-bound）**：3周内完成

### 4.2 具体任务清单

#### Part A：多Agent基础（第1周）

- [ ] 深入理解四种协作模式：
  - **Supervisor（监督者模式）**：中央统筹者接收任务，拆解后分配给Worker Agent
  - **Router（路由模式）**：根据任务类型自动路由到对应专业Agent
  - **Pipeline（流水线模式）**：任务按阶段串行处理，每个阶段由一个Agent负责
  - **Parallel（并行模式）**：多个Agent并行处理子任务，最后汇总结果
- [ ] 学习核心工具API：
  - `sessions_spawn`：主Agent派生子Agent执行任务
  - `sessions_send`：Agent间通信（"内线电话"机制）
- [ ] 配置agentToAgent白名单，启用A2A（Agent to Agent）通信
- [ ] 阅读并分析官方Multi-Agent示例配置

#### Part B：两种模式深度实践（第2周）

- [ ] **实践Supervisor模式**：
  - 创建1个Supervisor Agent + 3个Worker Agent
  - Supervisor负责任务拆解和分发
  - Worker Agent分别负责：资料收集、内容分析、报告撰写
  - 实现Worker向Supervisor汇报进度的机制
  - 处理Worker失败的重试和降级逻辑
- [ ] **实践Pipeline模式**：
  - 设计3阶段流水线：数据获取 -> 数据处理 -> 结果生成
  - 每个阶段输出作为下一阶段输入
  - 实现阶段间的数据校验和错误回退
  - 添加阶段执行日志和性能监控

#### Part C：复杂工作流编排（第3周）

- [ ] 学习Hook机制：在关键节点插入自定义逻辑
- [ ] 学习Plugin系统：扩展现有Agent的能力
- [ ] 设计状态机管理多Agent协作的状态流转
- [ ] 实现错误处理和重试机制
- [ ] 实现结果汇聚和冲突解决策略
- [ ] 综合项目：**构建"智能研报生成系统"**
  - Router Agent：接收用户主题，路由到对应领域Agent
  - Research Agent：并行收集多源资料（Web搜索、数据库、文档）
  - Analysis Agent：分析资料，提取关键观点和趋势
  - Writer Agent：整合分析结果，生成结构化研报
  - Reviewer Agent：审核研报质量，提出修改建议
  - 最终输出：Markdown格式的完整研报

### 4.3 推荐学习资源

| 资源类型 | 资源名称 | 链接/获取方式 | 学习重点 |
|----------|----------|--------------|----------|
| 官方文档 | Multi-Agent配置 | OpenClaw GitHub Wiki | 四种模式的配置方法 |
| API文档 | sessions_spawn | 安装目录docs | 子Agent创建参数 |
| API文档 | sessions_send | 安装目录docs | Agent间通信机制 |
| 技术博客 | "多Agent协作实战" | 搜索腾讯技术公众号 | 实际案例分享 |
| 论文 | Multi-Agent协作框架 | arxiv搜索multi-agent | 理论基础 |
| 参考项目 | AutoGen（Microsoft） | github.com/microsoft/autogen | 对比学习多Agent模式 |

### 4.4 阶段产出物

1. **Supervisor模式Demo**：1 Supervisor + 3 Worker的任务分发系统
2. **Pipeline模式Demo**：3阶段数据流水线
3. **智能研报生成系统**：完整的5-Agent协作系统（Router+Research+Analysis+Writer+Reviewer）
4. **多Agent架构设计文档**：包含时序图、状态图、通信协议说明

### 4.5 验证标准

| 验证项 | 通过标准 | 自测方法 |
|--------|----------|----------|
| Supervisor | 任务正确分发给Worker，Worker结果汇总 | 提交一个复杂任务，观察分发和汇总 |
| Pipeline | 数据正确流经3个阶段，错误可回退 | 触发各阶段的正常和错误场景 |
| A2A通信 | Agent间能相互发送和接收消息 | 检查sessions_send的收发日志 |
| 研报系统 | 输入主题，输出结构化的Markdown研报 | 用3个不同主题测试 |
| 错误处理 | Worker失败时能重试或降级 | 手动让一个Worker失败 |
| 并发安全 | 多个子Agent并行时无数据冲突 | 同时触发多个Worker |

### 4.6 常见坑点与避坑指南

| 坑点 | 现象 | 解决方案 |
|------|------|----------|
| A2A通信未开启 | Agent间无法通信 | 确保在配置中启用agentToAgent白名单 |
| 子Agent无响应 | sessions_spawn后无结果 | 检查子Agent的模型配置和权限设置 |
| 消息格式错误 | Agent间传数据解析失败 | 统一使用JSON格式，做好序列化/反序列化 |
| 死循环 | Agent间来回通信不停 | 设置最大轮次限制，添加超时机制 |
| 状态不一致 | Pipeline中某阶段失败影响全局 | 实现事务机制，支持阶段回滚 |
| 资源耗尽 | spawn太多Agent导致内存不足 | 限制并发Agent数，及时回收已完成Agent |

### 4.7 阶段三架构设计深入

**四种协作模式选型决策树**：

```
任务特点分析
|
|-- 需要中央协调和复杂决策？ --> Supervisor模式
|   例：项目管理、任务调度、资源分配
|
|-- 任务类型明确可分类？ --> Router模式
|   例：客服路由（技术/售后/销售）、领域专家咨询
|
|-- 任务有明显的前后依赖？ --> Pipeline模式
|   例：数据处理流水线、编译构建流程、ETL
|
|-- 子任务相互独立可并行？ --> Parallel模式
|   例：批量数据处理、多源信息收集、并行计算
|
|-- 混合需求？ --> 组合模式
    例：Supervisor + Parallel（中央分发+并行执行）
```

**Agent间通信协议设计**：

`sessions_send`本质上是Agent间的"内线电话"，设计良好的通信协议要考虑：

1. **消息格式标准化**：建议采用统一JSON Schema
   ```json
   {
     "msg_type": "request/response/heartbeat/error",
     "from": "agent_name",
     "to": "agent_name",
     "task_id": "uuid",
     "payload": {},
     "timestamp": "ISO8601",
     "timeout_ms": 30000
   }
   ```

2. **超时与重试**：网络不可靠，每次send都要设超时，失败时指数退避重试

3. **幂等设计**：同一消息可能重复送达，接收方要能去重（基于task_id）

4. **死信处理**：多次失败后放入死信队列，人工介入或降级处理

**状态机设计模式**：

复杂的多Agent协作建议用状态机管理，关键状态包括：

```
[Created] --> [Assigned] --> [Executing] --> [Completed]
                                      |
                                      v
                               [Failed] --> [Retrying] --> [Completed/Dead]
                                      |
                                      v
                               [Cancelled]
```

每个状态转换都对应Hook点，可以在转换时插入自定义逻辑（如日志记录、通知发送、超时检查等）。

---

