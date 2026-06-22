# Agent统一入口与记忆增强框架设计——MultiCa竞品对标方案

> **文档版本**: v1.0
> **编写日期**: 2025年7月
> **文档定位**: 对《软件工程全生命周期Agent实战项目设计》的重要补充
> **核心聚焦**: 基于记忆增强的Agent统一入口框架，对标MultiCa，解决Agent碎片化与记忆断层痛点

---

## 目录

1. [项目定位与差异化战略](#1-项目定位与差异化战略)
2. [MultiCa竞品深度拆解](#2-multica竞品深度拆解)
3. [系统架构设计：Agent统一入口网关](#3-系统架构设计agent统一入口网关)
4. [核心模块详细设计](#4-核心模块详细设计)
5. [关键场景详细设计](#5-关键场景详细设计)
6. [技术选型](#6-技术选型)
7. [与QClaw/OpenClaw的集成方案](#7-与qclawopenclaw的集成方案)
8. [项目里程碑](#8-项目里程碑)
9. [代码实现示例](#9-代码实现示例)
10. [面试话术](#10-面试话术)

---

## 1. 项目定位与差异化战略

### 1.1 一句话定位

**基于记忆增强的Agent统一入口框架**——让用户不再在各Agent之间切来切去，让Agent真正记住你的一切。

### 1.2 市场痛点分析

当前AI编程Agent呈爆发态势：Claude Code、OpenAI Codex、Cursor、Windsurf、OpenClaw、Hermes……每个Agent都有独特优势，但用户面临三个核心痛点：

**痛点一：入口碎片化**
开发者需要在Claude Code（终端）、Codex（CLI/Web）、Cursor（IDE）、ChatGPT（网页）之间反复切换。每个Agent有独立的交互界面、命令语法和工作流。一个典型的全栈开发者的一天可能是：用Claude Code写后端API → 切换到Cursor调前端CSS → 切换到Codex做代码审查 → 切换到ChatGPT查文档。四个Agent，四种上下文，四次心智切换成本。

**痛点二：记忆断层**
每个Agent的会话相互隔离。你在Claude Code里花30分钟讨论的架构决策，切换到Codex后需要从头解释。昨天让Cursor优化的React组件性能，今天打开新的Composer对话，它完全不记得。记忆断层导致大量重复沟通，效率损失估计在30%-50%。

**痛点三：Agent管理缺位**
现有方案都是"单Agent单会话"模式，没有平台级的Agent管理。当Claude Code因为token限制突然中断时，用户只能手动切换到其他Agent并从头开始。没有健康监控、没有故障转移、没有任务接续——这相当于微服务架构缺少服务发现和熔断器。

### 1.3 核心价值主张：三个"统一"

| 统一维度 | 解决的问题 | 用户感知 |
|----------|-----------|----------|
| **统一入口** | 不再切来切去，一个界面管理所有Agent | 打开一个应用，所有Agent都在 |
| **统一管理** | Agent健康监控、故障转移、成本控制 | Agent挂了自动切换，费用可控 |
| **统一记忆** | 跨Agent记忆共享，上下文永不丢失 | 换Agent不用重新交代背景 |

### 1.4 对标MultiCa的差异化定位

MultiCa是目前最接近我们愿景的产品，但它的定位是"把coding agents当成团队成员管理"——本质上是AI版的Linear/Jira。我们的定位是"**让AI Agent真正记住你**"——本质是AI的分布式记忆系统。

这个差异化不是功能层面的微调，而是底层架构理念的差异：

- **MultiCa** 以"任务/工单"为核心抽象（Issue驱动）
- **本项目** 以"记忆/上下文"为核心抽象（Memory驱动）

任务会完成，但记忆会积累。任务驱动解决的是"如何把活分下去"，记忆驱动解决的是"如何让Agent越来越懂你"。两者可以互补，但记忆驱动具有更强的长期价值——因为记忆资产可以复利增长。

### 1.5 与MultiCa的差异化对比矩阵（10维度）

| 对比维度 | MultiCa | 本项目（记忆增强框架） | 差异说明 |
|----------|---------|---------------------|----------|
| **核心抽象** | Issue/工单驱动 | Memory/记忆驱动 | 本质理念差异 |
| **记忆能力** | 无持久记忆，Issue只记录过程 | 四层记忆架构，跨Agent共享 | **最大差异化** |
| **Agent切换** | 不支持，需手动切换 | 智能路由+故障转移+任务接续 | 解决核心痛点 |
| **统一入口** | Web平台统一入口 | Gateway统一入口+记忆同步 | 功能重叠但深度不同 |
| **任务编排** | Backlog-Todo-In Progress看板 | Pipeline编排+动态Agent选择 | 技术栈不同 |
| **Agent身份** | 名字/档案/专长/在线状态 | 能力注册+成本模型+健康状态 | 扩展了运行时信息 |
| **Skills沉淀** | 成功经验-可复用技能库 | 集成OpenClaw Skills+自学习 | 借助生态优势 |
| **Squads小组** | @FrontendTeam替代@个人 | 路由策略层面的抽象 | 实现方式不同 |
| **运行时检测** | 本地Daemon每3秒轮询 | 主动健康检查+事件驱动推送 | 架构更现代 |
| **目标用户** | 团队/项目管理视角 | 个人开发者效率视角 | 切入点不同 |
| **开源策略** | 开源Agent管理平台 | 开源记忆增强框架 | 互补而非竞争 |

### 1.6 SWOT分析

**优势（Strengths）**
- 记忆增强是行业空白点：所有主流Agent的记忆能力都很弱
- 统一入口解决真实痛点：每个开发者都在切来切去
- 架构可扩展：基于适配器模式，新Agent接入成本低

**劣势（Weaknesses）**
- 项目尚未启动，需要从零搭建
- 记忆同步的技术复杂度较高（上下文压缩、冲突解决）
- 依赖外部Agent的接口开放性

**机会（Opportunities）**
- MultiCa证明了市场对Agent管理的需求
- OpenClaw的Gateway和Memory机制可以复用
- Claude Code/Codex/Cursor都在快速发展但互不兼容

**威胁（Threats）**
- 各Agent厂商可能封闭接口（如Codex限制CLI功能）
- MultiCa可能补全记忆能力
- 大厂可能直接收购整合

### 1.7 战略定位总结

> **我们不是要做另一个MultiCa，而是要做Agent生态的"记忆层"。** MultiCa管"人"（Agent身份和任务分配），我们管"脑"（跨Agent记忆和上下文连续性）。两者互补，但记忆层的护城河更深——因为记忆资产具有排他性（一旦Agent习惯了你的记忆，迁移成本极高）。

---

## 2. MultiCa竞品深度拆解

### 2.1 MultiCa概览

| 属性 | 信息 |
|------|------|
| GitHub Stars | 26K / 3.1K Fork |
| 作者 | Jiayuan Zhang（张佳圆），国人，字节背景 |
| 之前项目 | Devv AI（AI搜索引擎） |
| 技术栈 | Go后端 + Next.js前端 + PostgreSQL + pgvector |
| 定位 | 开源Agent管理平台，AI版Linear/Jira |
| 核心能力 | Agent管理、任务看板、技能沉淀 |

### 2.2 架构逐层分析

#### 2.2.1 后端层（Go + Chi路由）

MultiCa后端采用Go语言+Chi路由框架，这是一个轻量级但高性能的选择：

- **Go语言优势**：原生高并发（goroutine）、静态编译、低内存占用，适合Daemon长期运行
- **Chi路由**：类似Express的轻量路由，支持中间件链式调用
- **RESTful API设计**：标准的CRUD API管理Issue、Agent、Squads等资源

**可借鉴点**：Go的并发模型适合处理多Agent并行任务的状态管理。

**待改进点**：没有采用事件驱动架构，Daemon轮询模式存在延迟。

#### 2.2.2 前端层（Next.js + React）

- **Next.js App Router**：服务端组件减少首屏加载
- **看板式UI**：类似Linear的拖拽式Issue管理
- **WebSocket实时通信**：Agent执行进度实时推送前端

**可借鉴点**：看板式UI直观展示多Agent状态，WebSocket实时推送提升用户体验。

#### 2.2.3 数据层（PostgreSQL + pgvector）

- **PostgreSQL**：关系型数据存储（Issue、Agent配置、用户信息）
- **pgvector**：向量扩展支持语义检索（Skills的向量存储）

**可借鉴点**：pgvector的向量检索能力可以用于Skills的语义匹配。

**关键短板**：没有为Agent设计持久记忆表。pgvector只用于Skills检索，没有存储Agent的对话历史、用户偏好、项目上下文等记忆数据。

#### 2.2.4 Daemon层（本地后台进程）

这是MultiCa的核心创新点：

- **每3秒轮询服务器**：检查是否有分配给本机的任务
- **自动检测CLI工具**：扫描Claude Code、Codex、OpenClaw等安装状态
- **任务执行代理**：接收服务器指令 → 调用本地CLI → 返回执行结果
- **最多20个Agent并行**：单任务超时2小时

**可借鉴点**：Daemon架构实现了"云端管理+本地执行"的混合模式，既保证管理的统一性，又利用本地计算资源。

**待改进点**：
1. 轮询模式有3秒延迟，应改用WebSocket长连接或SSE
2. 没有上下文保持机制——任务执行完后进程退出，上下文丢失
3. 故障转移缺失——一个Agent挂了不会自动切换

### 2.3 核心功能模块分析

#### 2.3.1 Issue面板看板

**流程**：Backlog -> Todo -> In Progress -> In Review -> Done

**分析**：
- 直接借鉴Linear/Jira的成熟模式，零学习成本
- Issue与Agent绑定，但Issue只记录"做什么"，不记录"Agent知道什么"
- 看板状态变更是人工触发，非自动感知Agent执行状态

#### 2.3.2 Agent身份系统

**设计**：每个Agent有名字、档案、专长标签、在线状态

**分析**：
- Agent人格化设计降低使用门槛
- 专长标签用于任务匹配（如"React专家"Agent分配给前端任务）
- 但Agent的"能力"是静态配置的，没有动态学习

#### 2.3.3 Squads小组

**设计**：@FrontendTeam可以替代@alice-or-bob，领导Agent自动分配任务给组内成员

**分析**：
- 抽象层次提升，减少人工指定
- 适合团队协作场景
- 路由逻辑简单（基于标签匹配），可以做得更智能

#### 2.3.4 Skills沉淀

**设计**：成功经验 -> 提取为Skill -> 存入向量库 -> 后续任务语义匹配复用

**分析**：
- 这是MultiCa最接近"记忆"的功能
- 但Skills是"集体智慧"（项目级），不是"个人记忆"（用户级）
- 向量匹配实现经验复用，设计思路可借鉴

#### 2.3.5 统一运行时

**设计**：本地+云端混合，自动检测CLI工具安装状态

**分析**：
- 降低配置成本，开箱即用
- 运行时检测可以告诉我们哪些Agent可用
- 但运行时只检测"有没有"，不检测"还能不能用"（token余额、速率限制）

### 2.4 能力矩阵：强在哪、弱在哪

| 能力维度 | 强度 | 说明 |
|----------|------|------|
| Agent管理 | 5星 | 身份系统、在线状态、Squads，业界最全 |
| 任务看板 | 4星 | 照搬Linear模式，成熟但无创新 |
| Skills沉淀 | 3星 | 向量检索复用，但只到项目级 |
| 运行时管理 | 4星 | Daemon检测CLI，混合架构 |
| **持久记忆** | 1星 | **几乎没有，最大短板** |
| 故障转移 | 1星 | 无自动切换能力 |
| 上下文连续 | 1星 | 每次任务从零开始 |
| 多Agent协作 | 2星 | Squads有但深度不足 |
| 成本控制 | 2星 | 无成本感知路由 |

### 2.5 重点分析：为什么MultiCa的Agent没有持久记忆是个大问题

#### 2.5.1 问题本质

MultiCa的Agent是"Stateless（无状态）"的：

```
任务开始 -> Agent启动 -> 执行任务 -> 返回结果 -> Agent退出
    无记忆                                       无记忆保留
```

每次任务执行都是全新进程，没有机制保存和恢复以下内容：
- 用户的编码风格偏好（喜欢early return还是嵌套if）
- 项目的架构上下文（为什么用Redis而不是Memcached）
- 之前的讨论结论（为什么这个字段不用枚举用字符串）
- 已知的陷阱和workaround（这个第三方库有bug需要patch）

#### 2.5.2 实际影响场景

**场景A：重复解释**
用户："像上次一样处理错误"
Claude Code："我不确定你指的是什么，能详细说明吗？"
（因为"上次"的对话没有被记忆）

**场景B：风格不一致**
昨天让Agent A写的代码用了functional style，今天Agent B写的代码用了OOP style，代码库风格混乱。

**场景C：决策遗忘**
上周决定"不用TypeScript的strict mode因为兼容性问题"，本周新Agent不知道这个决策，又改回了strict mode。

#### 2.5.3 根因分析

MultiCa的记忆缺失有架构层面的根因：

1. **Daemon只负责"执行"不负责"记忆"**：Daemon是任务调度器，不是上下文管理器
2. **Issue是工单不是记忆载体**：Issue记录"做什么"和"结果"，不记录"过程中积累了什么知识"
3. **Agent进程无持久化机制**：没有类似OpenClaw的MEMORY.md或类似机制
4. **向量库只存Skills**：pgvector的向量检索只用于技能匹配，没有用于对话历史检索

#### 2.5.4 我们的机会

这正是我们的核心切入点：

- **工作记忆同步**：任务执行中的关键信息实时保存
- **情景记忆检索**：基于向量检索找到相关历史任务
- **语义记忆沉淀**：用户偏好、项目决策持久化
- **跨Agent记忆共享**：Claude Code的记忆Codex也能用

### 2.6 MultiCa可借鉴的设计清单

| 设计 | 借鉴方式 | 改进点 |
|------|----------|--------|
| Issue看板 | 复用概念，改为Pipeline编排 | 增加自动状态感知 |
| Agent身份系统 | 复用并扩展为能力注册 | 增加成本模型和健康状态 |
| Squads | 抽象为路由策略 | 动态匹配替代静态分组 |
| Skills沉淀 | 集成OpenClaw Skills系统 | 扩展为个人记忆+集体技能 |
| Daemon架构 | 升级为事件驱动Gateway | WebSocket替代轮询，增加上下文保持 |


---

## 3. 系统架构设计：Agent统一入口网关

### 3.1 总体架构图

```
+---------------------------------------------------------------------+
|                        User Interface Layer                          |
|  +--------------+  +--------------+  +--------------+              |
|  |   Web控制台   |  |   CLI工具    |  |   IDE插件    |              |
|  +------+-------+  +------+-------+  +------+-------+              |
+---------+------------------+------------------+----------+          |
          |                  |                  |                     |
          +------------------+------------------+                     |
                             |                                        |
                             v                                        |
+---------------------------------------------------------------------+
|                   Agent Gateway（核心网关层）                          |
|  +--------------------------------------------------------------+   |
|  |                    Unified API（统一接口层）                    |   |
|  |   send / recv / health / cost / context_sync                 |   |
|  +--------------------------------------------------------------+   |
|  +--------------+  +--------------+  +-------------+  +---------+  |
|  |AgentAdapter  |  |ContextBridge |  |  MemoryHub  |  | Router  |  |
|  |  (适配器层)    |  | (上下文桥接)  |  |  (记忆中心)  |  | Engine  |  |
|  +------+-------+  +------+-------+  +------+------+  +----+----+  |
+---------+------------------+------------------+--------+      |     |
          |                  |                  |               |     |
          v                  v                  v               |     |
+--------------+  +-------------------------------+             |     |
|  Agent Pool   |  |       Memory & Data Layer      |             |     |
|  +----------+ |  |  +--------+ +--------+ +-----+---+         |     |
|  |ClaudeCode| |  |  | 工作记忆 | | 情景记忆 | | 语义记忆 |         |     |
|  | Adapter  | |  |  |(Redis) | |(PGVec) | |(PostgreSQL)        |     |
|  +----------+ |  |  +--------+ +--------+ +-----+---+         |     |
|  |  Codex   | |  |  +--------+ +------------------+            |     |
|  | Adapter  | |  |  | 过程记忆 | | 记忆同步队列       |            |     |
|  +----------+ |  |  |(文件)  | |(Redis Streams)  |            |     |
|  |  Cursor  | |  |  +--------+ +------------------+            |     |
|  | Adapter  | |  +-------------------------------+             |     |
|  +----------+ |                                                 |     |
|  | OpenClaw | |  +-------------------------------+              |     |
|  | Adapter  | |  |    Orchestration Layer         |              |     |
|  +----------+ |  |  +--------+ +------+ +-------+|              |     |
|  |  Hermes  | |  |  |Pipeline| |任务调度| |人机协作||              |     |
|  | Adapter  | |  |  +--------+ +------+ +-------+|              |     |
|  +----------+ |  +-------------------------------+              |     |
|  |  Custom  | |                                                  |     |
|  | Adapter  | |  +-------------------------------+               |     |
|  +----------+ |  |   Infrastructure Layer        |               |     |
|               |  |  +--------+ +--------+ +-----+|               |     |
|               |  |  | 消息队列 | | 监控告警 | | 日志 ||               |     |
|               |  |  | (Redis) | |(Prom)  | |(Trace)||               |     |
|               |  |  +--------+ +--------+ +-----+|               |     |
+---------------+  +-------------------------------+---------------+     |
+---------------------------------------------------------------------+
```

### 3.2 统一接入层（AgentAdapter）

#### 3.2.1 为什么需要适配器模式

每个Agent的接口差异巨大：

| Agent | 接口类型 | 协议 | 认证方式 | 输出格式 |
|-------|----------|------|----------|----------|
| Claude Code | CLI | 子进程+stdin/stdout | API Key | ANSI文本 |
| Codex | CLI + API | HTTP/REST | OAuth + API Key | JSON + Markdown |
| Cursor | IDE Plugin | 内部IPC | Session Cookie | 结构化JSON |
| OpenClaw | Gateway API | HTTP/WebSocket | API Key | Markdown |
| Hermes | 自部署 | HTTP + SQLite | 本地认证 | JSON |

没有统一适配器，网关需要为每个Agent写特殊逻辑，维护成本极高。

#### 3.2.2 适配器统一接口

每个AgentAdapter必须实现：

```python
class AgentAdapter(ABC):
    @abstractmethod
    async def send(self, message: AgentMessage) -> AgentResponse:
        pass  # 发送消息给Agent

    @abstractmethod  
    async def health(self) -> HealthStatus:
        pass  # 检查Agent健康状态

    @abstractmethod
    async def cost(self, task_hint: TaskHint) -> CostEstimate:
        pass  # 估算任务成本

    @abstractmethod
    async def context_sync(self, direction, context: ContextSnapshot) -> SyncResult:
        pass  # 上下文同步（上传/下载）

    @abstractmethod
    def capabilities(self) -> AgentCapabilities:
        pass  # 返回Agent能力清单
```

#### 3.2.3 能力注册系统

每个Agent接入时注册自己的能力、约束和成本模型：

```yaml
agent: claude-code
version: "2.0"
capabilities:
  coding: { languages: [python, typescript], max_files: 200 }
  debugging: { stack_trace_analysis: true }
constraints:
  context_window: 200000
  max_daily_tokens: 1000000
cost_model:
  type: per_token
  input: 0.000015
  output: 0.000075
  currency: USD
```

### 3.3 智能路由与切换引擎（RouterEngine）

#### 3.3.1 路由决策模型

路由引擎基于多维度评分选择最优Agent：

```
Score(Agent) = w1 * Availability(Agent)
             + w2 * CostEfficiency(Agent, Task)
             + w3 * CapabilityMatch(Agent, Task)
             + w4 * SpeedEstimate(Agent, Task)
             + w5 * MemoryAffinity(Agent, User)
             + w6 * RecentSuccessRate(Agent)
```

- **Availability**：Agent当前是否可用（进程运行、token充足、未触限流）
- **CostEfficiency**：任务成本预估（输入token量 x 单价）
- **CapabilityMatch**：Agent能力与任务需求的匹配度
- **SpeedEstimate**：预估响应时间
- **MemoryAffinity**：该Agent与用户相关记忆的关联度
- **RecentSuccessRate**：该Agent最近的成功率

#### 3.3.2 健康检查机制

```
健康检查维度：
+-- 进程级健康
|   +-- 进程是否存活（PID存在）
|   +-- 最后响应时间（>30秒视为异常）
|   +-- CPU/内存占用（>90%视为过载）
+-- Token级健康
|   +-- 剩余token余额（<10%预警，<5%切换）
|   +-- 速率限制状态
|   +-- 今日已用量 / 日限额
+-- 功能级健康
    +-- 基础响应测试（ping消息）
    +-- 核心功能探测
    +-- 错误率统计（最近10次>50%切换）
```

#### 3.3.3 故障转移策略

| 触发条件 | 检测方式 | 响应动作 | 恢复检查 |
|----------|----------|----------|----------|
| Token耗尽 | Token余额API返回0 | 切换到备选Agent，保存上下文 | 每小时检查余额恢复 |
| 进程崩溃 | PID消失/exit code非0 | 重启Agent或切换 | 5分钟后尝试重启 |
| 速率限制 | 429响应码 | 切换到备选Agent，原Agent冷却 | 15分钟后解除冷却 |
| 响应超时 | >60秒无响应 | 中断请求，切换到备选Agent | 下次路由时检测 |
| 质量下降 | 输出质量评分<阈值 | 渐进降级（重试->切换） | 完成质量回归测试 |

#### 3.3.4 任务接续核心设计——ContextBridge

任务接续是本项目的技术核心。当Agent A中断、切换到Agent B时，需要保证任务上下文不丢失。

**TaskState对象设计**：

```python
@dataclass
class TaskState:
    task_id: str                    # 全局唯一任务ID
    task_type: str                  # 任务类型
    status: TaskStatus              # 当前状态
    primary_agent: str              # 主执行Agent
    current_agent: str              # 当前正在执行的Agent
    agent_history: List[str]        # 执行过的Agent列表
    conversation_summary: str       # 对话历史摘要
    key_decisions: List[Decision]   # 关键决策记录
    code_changes: List[CodeChange]  # 已产生的代码变更
    environment_state: EnvState     # 环境状态
    intermediate_artifacts: List    # 中间产物
    checkpoints: List[Checkpoint]   # 执行检查点
    tokens_used: int = 0
    budget_remaining: float = 0.0
```

**上下文传输流程**：

```
Agent A执行中
    |
    v 检测到故障（token耗尽/崩溃/超时）
+-------------+
| 1. 紧急保存  | -> 序列化TaskState -> 写入MemoryHub
| 2. 状态标记  | -> TaskState.status = PAUSED
| 3. 切换触发  | -> 发布AgentSwitchEvent
+------+------+
       |
       v
+-------------+
| RouterEngine | -> 选择Agent B（排除A，重新评分）
| 路由决策     | -> 锁定Agent B
+------+------+
       |
       v
+-------------+
| ContextBridge| -> 从MemoryHub读取TaskState
| 上下文恢复   | -> 反序列化 -> 生成Agent B的启动prompt
|             | -> 注入记忆（偏好+规范+历史）
+------+------+
       |
       v
Agent B接管 -> "任务已接续，当前进度：..."
```

### 3.4 统一记忆管理层（MemoryHub）——核心差异化

#### 3.4.1 为什么记忆管理是核心差异化

这是本项目与MultiCa最本质的区别。我们的记忆层不是简单的"记录日志"，而是构建一个**跨Agent的共享记忆空间**。

#### 3.4.2 四层记忆架构

**第一层：工作记忆（Working Memory）**
- **存储**：Redis（低延迟读写，TTL=24小时）
- **内容**：当前任务的完整对话历史、正在编辑的文件、未提交的变更
- **作用**：单个任务内的上下文保持
- **同步**：Agent执行时实时写入，每5秒同步一次

**第二层：情景记忆（Episodic Memory）**
- **存储**：PostgreSQL + pgvector（向量检索）
- **内容**：过往任务执行记录（需求、方案、结果、经验教训）
- **作用**："类似的问题我之前怎么解决的"
- **检索**：基于任务描述的向量相似度匹配（top-k=5）
- **生命周期**：永久保留，定期归档

**第三层：语义记忆（Semantic Memory）**
- **存储**：PostgreSQL（结构化存储）
- **内容**：用户偏好、项目规范、技术决策
- **作用**："用户喜欢用这种方式处理这类问题"
- **示例**："Python用black格式化，行宽100"
- **更新**：Agent执行过程中自动提取 -> 人工确认后固化

**第四层：过程记忆（Procedural Memory）**
- **存储**：文档存储（Markdown文件/MEMORY.md）
- **内容**：工作流模板、最佳实践、常见陷阱规避方法
- **作用**："这类任务的标准流程是什么"
- **集成**：与OpenClaw的MEMORY.md格式兼容

#### 3.4.3 记忆同步机制

```
Agent执行中
    |
    +-- 每N轮对话 -> 提取关键信息 -> 写入工作记忆（Redis）
    |
    +-- 任务完成 -> 提取摘要 -> 写入情景记忆（PGVector）
    |               -> 提取偏好/决策 -> 写入语义记忆
    |               -> 提取可复用流程 -> 写入过程记忆
    |
    +-- Agent启动 -> 读取工作记忆（恢复未完成任务）
             -> 检索情景记忆（找相关历史任务）
             -> 加载语义记忆（用户偏好+项目规范）
             -> 读取过程记忆（相关工作流模板）
```

#### 3.4.4 记忆冲突解决

| 冲突类型 | 解决策略 | 示例 |
|----------|----------|------|
| 偏好冲突 | 时间优先（取最新）+ 人工确认 | A说喜欢early return，B说喜欢nested if |
| 决策冲突 | 附带上下文保留（记录决策背景） | 同一技术选型在不同约束下结论不同 |
| 风格冲突 | 领域隔离（不同语言不同风格） | Python和TypeScript的代码风格不同 |
| 信息过期 | 版本标记+自动提醒 | "此决策基于v2版本，当前v3可能需重评" |

#### 3.4.5 隐私控制

```yaml
memory_sharing:
  global:        # 所有Agent可见
    - 项目技术栈
    - 代码规范
    - 架构决策
  agent_specific:  # 仅特定Agent可见
    claude-code:
      - 个人API Key（不共享）
    codex:
      - GitHub Token（不共享）
  user_only:     # 仅用户可见
    - 薪资信息
    - 内部系统密码
```

### 3.5 任务编排引擎

#### 3.5.1 Pipeline编排模型

```
需求输入 -> 需求分析 -> 技术设计 -> 编码实现 -> 测试验证 -> 代码审查 -> 部署
             |           |           |           |           |
             v           v           v           v           v
          [PM Agent] [Architect] [Dev Agent] [QA Agent] [DevOps Agent]
             |           |           |           |           |
             +-----------+-----------+-----------+-----------+
                                     |
                                     v
                              RouterEngine
                          （每个阶段动态选择最优Agent）
```

#### 3.5.2 动态Agent选择

```python
async def select_agent_for_phase(phase: str, task_context: TaskContext):
    candidates = agent_pool.available_agents()
    capable = [a for a in candidates if phase in a.capabilities().phases]
    scored = [(a, await score_agent(a, phase, task_context)) for a in capable]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[0][0]
```

#### 3.5.3 人机协作节点

```
自动执行 -->> 人工确认节点 -->> 自动执行
              |
              +-- 架构设计确认
              +-- 大规模重构确认
              +-- 数据库Schema变更确认
              +-- 部署到生产环境确认
              +-- 密钥/权限相关操作确认
```


---

## 4. 核心模块详细设计

### 4.1 AgentAdapter（适配器模式）

#### 4.1.1 统一接口定义

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, AsyncIterator
from enum import Enum
from datetime import datetime
import json


class MessageType(Enum):
    TEXT = "text"
    CODE = "code"
    COMMAND = "command"
    SYSTEM = "system"
    ERROR = "error"
    PROGRESS = "progress"
    COMPLETION = "completion"


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    SWITCHING = "switching"


class HealthLevel(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    LIMITED = "limited"
    UNAVAILABLE = "unavailable"


class SyncDirection(Enum):
    UPLOAD = "upload"
    DOWNLOAD = "download"


@dataclass
class AgentMessage:
    """发送给Agent的标准消息"""
    content: str
    message_type: MessageType = MessageType.TEXT
    metadata: Dict[str, Any] = field(default_factory=dict)
    context_hint: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps({
            "content": self.content,
            "type": self.message_type.value,
            "metadata": self.metadata
        }, ensure_ascii=False)


@dataclass
class AgentResponse:
    """Agent的标准响应"""
    content: str
    message_type: MessageType = MessageType.TEXT
    metadata: Dict[str, Any] = field(default_factory=dict)
    tokens_used: int = 0
    latency_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def is_error(self) -> bool:
        return self.message_type == MessageType.ERROR


@dataclass
class HealthStatus:
    """Agent健康状态"""
    level: HealthLevel
    is_available: bool
    last_check: datetime
    response_time_ms: float
    error_rate_10min: float
    token_remaining: Optional[int] = None
    token_total: Optional[int] = None
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset_time: Optional[datetime] = None
    notes: List[str] = field(default_factory=list)

    @property
    def token_usage_percent(self) -> Optional[float]:
        if self.token_total and self.token_total > 0:
            used = self.token_total - (self.token_remaining or 0)
            return (used / self.token_total) * 100
        return None


@dataclass
class CostEstimate:
    """成本预估"""
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost_usd: float
    pricing_model: str
    confidence: float  # 0-1

    def __str__(self) -> str:
        return (f"预估: ${self.estimated_cost_usd:.4f} "
                f"({self.estimated_input_tokens}+{self.estimated_output_tokens} tokens)")


@dataclass
class AgentCapabilities:
    """Agent能力清单"""
    agent_id: str
    agent_name: str
    supported_tasks: List[str]
    supported_languages: List[str]
    max_context_tokens: int
    supported_protocols: List[str]
    special_features: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)


@dataclass
class ContextSnapshot:
    """上下文快照（简化版）"""
    task_id: str
    task_type: str = ""
    conversation_summary: str = ""
    working_files: List[str] = field(default_factory=list)
    memory_refs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SyncResult:
    """同步结果"""
    success: bool
    bytes_transferred: int
    items_synced: int
    errors: List[str] = field(default_factory=list)


class AgentAdapter(ABC):
    """
    Agent适配器抽象基类。

    所有外部Agent（Claude Code/Codex/Cursor等）必须实现此接口。
    适配器负责：
    1. 协议转换：将标准消息转Agent特定格式
    2. 健康监控：提供Agent的实时健康状态
    3. 成本控制：提供任务成本预估
    4. 上下文同步：支持任务接续的上下文导入导出
    """

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        self.agent_id = agent_id
        self.config = config
        self._health_history: List[HealthStatus] = []
        self._total_requests: int = 0
        self._error_count: int = 0

    @abstractmethod
    async def send(self, message: AgentMessage) -> AgentResponse:
        """发送消息给Agent并返回响应"""
        pass

    @abstractmethod
    async def send_stream(self, message: AgentMessage) -> AsyncIterator[AgentResponse]:
        """流式发送，实时获取增量输出"""
        response = await self.send(message)
        yield response

    @abstractmethod
    async def health(self) -> HealthStatus:
        """检查Agent健康状态"""
        pass

    @abstractmethod
    async def cost(self, task_hint: Dict[str, Any]) -> CostEstimate:
        """预估任务成本"""
        pass

    @abstractmethod
    async def context_sync(self, direction: SyncDirection,
                          snapshot: ContextSnapshot) -> SyncResult:
        """上下文同步"""
        pass

    @abstractmethod
    def capabilities(self) -> AgentCapabilities:
        """返回能力清单"""
        pass

    # --- 便捷方法（有默认实现）---

    async def is_available(self) -> bool:
        """检查Agent是否可用"""
        try:
            health = await asyncio.wait_for(self.health(), timeout=15.0)
            return health.is_available and health.level in (
                HealthLevel.HEALTHY, HealthLevel.DEGRADED
            )
        except asyncio.TimeoutError:
            return False

    async def get_token_usage(self) -> Optional[Dict[str, int]]:
        """获取token使用情况"""
        health = await self.health()
        if health.token_total is None:
            return None
        return {
            "remaining": health.token_remaining,
            "total": health.token_total,
            "used": health.token_total - (health.token_remaining or 0),
            "usage_percent": health.token_usage_percent
        }

    def record_health(self, status: HealthStatus):
        """记录健康历史"""
        self._health_history.append(status)
        if len(self._health_history) > 100:
            self._health_history = self._health_history[-100:]

    @property
    def recent_error_rate(self) -> float:
        """计算近期错误率"""
        if self._total_requests == 0:
            return 0.0
        return self._error_count / self._total_requests


class AgentPool:
    """Agent连接池"""

    def __init__(self):
        self._adapters: Dict[str, AgentAdapter] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}

    def register(self, adapter: AgentAdapter, metadata: Optional[Dict] = None):
        """注册Agent"""
        self._adapters[adapter.agent_id] = adapter
        self._metadata[adapter.agent_id] = metadata or {}

    def unregister(self, agent_id: str):
        """注销Agent"""
        self._adapters.pop(agent_id, None)
        self._metadata.pop(agent_id, None)

    def get(self, agent_id: str) -> Optional[AgentAdapter]:
        return self._adapters.get(agent_id)

    def list_all(self) -> List[AgentAdapter]:
        return list(self._adapters.values())

    async def available_agents(self) -> List[AgentAdapter]:
        """获取可用Agent"""
        result = []
        for adapter in self._adapters.values():
            if await adapter.is_available():
                result.append(adapter)
        return result

    def find_by_task(self, task_type: str) -> List[AgentAdapter]:
        """按任务类型查找Agent"""
        return [
            a for a in self._adapters.values()
            if task_type in a.capabilities().supported_tasks
        ]
```

#### 4.1.2 Claude Code适配器

```python
import asyncio
import subprocess
import shutil
import json


class ClaudeCodeAdapter(AgentAdapter):
    """Claude Code终端Agent适配器"""

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        self.cli_path = config.get("cli_path", "claude")
        self.project_dir = config.get("project_dir", ".")
        self.api_key = config.get("api_key")
        self.process: Optional[subprocess.Process] = None
        self._current_dir = self.project_dir

    async def _ensure_process(self):
        """确保Claude Code进程运行"""
        if self.process is None or self.process.returncode is not None:
            self.process = await asyncio.create_subprocess_exec(
                self.cli_path, "--json",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self._current_dir,
                env={"ANTHROPIC_API_KEY": self.api_key} if self.api_key else None
            )

    async def send(self, message: AgentMessage) -> AgentResponse:
        await self._ensure_process()
        start_time = datetime.now()

        cmd_input = f"{message.content}\n".encode()

        try:
            self.process.stdin.write(cmd_input)
            await self.process.stdin.drain()

            response_data = b""
            while True:
                chunk = await asyncio.wait_for(
                    self.process.stdout.readline(), timeout=60.0
                )
                if not chunk:
                    break
                response_data += chunk
                if b"completed" in chunk or b"done" in chunk:
                    break

            latency = (datetime.now() - start_time).total_seconds() * 1000

            try:
                parsed = json.loads(response_data.decode())
                content = parsed.get("response", parsed.get("content", response_data.decode()))
                tokens = parsed.get("usage", {}).get("total_tokens", 0)
            except json.JSONDecodeError:
                content = response_data.decode()
                tokens = 0

            return AgentResponse(
                content=content,
                message_type=MessageType.COMPLETION,
                tokens_used=tokens,
                latency_ms=int(latency)
            )

        except asyncio.TimeoutError:
            return AgentResponse(
                content="Claude Code响应超时（60秒）",
                message_type=MessageType.ERROR,
                metadata={"error_type": "timeout"}
            )
        except Exception as e:
            return AgentResponse(
                content=f"Claude Code执行错误: {str(e)}",
                message_type=MessageType.ERROR,
                metadata={"error_type": type(e).__name__}
            )

    async def health(self) -> HealthStatus:
        """检查Claude Code健康状态"""
        notes = []

        # 检查CLI是否安装
        if not shutil.which(self.cli_path):
            return HealthStatus(
                level=HealthLevel.UNAVAILABLE,
                is_available=False,
                last_check=datetime.now(),
                response_time_ms=0, error_rate_10min=0,
                notes=["Claude Code CLI未安装"]
            )

        # 检查进程健康
        process_healthy = (self.process is not None and 
                          self.process.returncode is None)

        # 发送ping测试
        start_time = datetime.now()
        try:
            ping_proc = await asyncio.create_subprocess_exec(
                self.cli_path, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(
                ping_proc.communicate(), timeout=10.0
            )
            latency = (datetime.now() - start_time).total_seconds() * 1000
            version = stdout.decode().strip()
            notes.append(f"版本: {version}")

            return HealthStatus(
                level=HealthLevel.HEALTHY if process_healthy else HealthLevel.DEGRADED,
                is_available=True,
                last_check=datetime.now(),
                response_time_ms=latency,
                error_rate_10min=0.0,
                notes=notes
            )

        except asyncio.TimeoutError:
            return HealthStatus(
                level=HealthLevel.DEGRADED,
                is_available=True,
                last_check=datetime.now(),
                response_time_ms=10000,
                error_rate_10min=0.0,
                notes=["版本检查超时"]
            )
        except Exception as e:
            return HealthStatus(
                level=HealthLevel.UNAVAILABLE,
                is_available=False,
                last_check=datetime.now(),
                response_time_ms=0, error_rate_10min=0,
                notes=[f"健康检查失败: {str(e)}"]
            )

    async def cost(self, task_hint: Dict[str, Any]) -> CostEstimate:
        """估算Claude Code任务成本"""
        estimated_input = task_hint.get("estimated_input_tokens", 4000)
        estimated_output = task_hint.get("estimated_output_tokens", 2000)
        input_cost = (estimated_input / 1_000_000) * 15.0
        output_cost = (estimated_output / 1_000_000) * 75.0

        return CostEstimate(
            estimated_input_tokens=estimated_input,
            estimated_output_tokens=estimated_output,
            estimated_cost_usd=input_cost + output_cost,
            pricing_model="per_token",
            confidence=0.7
        )

    async def context_sync(self, direction: SyncDirection, 
                          snapshot: ContextSnapshot) -> SyncResult:
        """与Claude Code同步上下文"""
        if direction == SyncDirection.UPLOAD:
            memory_injection = self._build_memory_prompt(snapshot)
            result = await self.send(AgentMessage(
                content=memory_injection,
                message_type=MessageType.SYSTEM
            ))
            return SyncResult(
                success=result.message_type != MessageType.ERROR,
                bytes_transferred=len(memory_injection.encode()),
                items_synced=1
            )
        else:
            result = await self.send(AgentMessage(
                content="请总结当前任务状态和关键决策",
                message_type=MessageType.COMMAND
            ))
            return SyncResult(
                success=True,
                bytes_transferred=len(result.content.encode()),
                items_synced=1
            )

    def capabilities(self) -> AgentCapabilities:
        return AgentCapabilities(
            agent_id=self.agent_id,
            agent_name="Claude Code",
            supported_tasks=[
                "coding", "debugging", "refactoring", "code_review",
                "architecture_design", "testing", "documentation"
            ],
            supported_languages=[
                "python", "typescript", "javascript", "rust", "go",
                "java", "kotlin", "swift", "ruby", "php", "c", "cpp"
            ],
            max_context_tokens=200_000,
            supported_protocols=["cli", "mcp"],
            special_features=[
                "compaction_api",
                "recap_session_recovery",
                "agent_teams",
                "hooks_system",
                "deep_file_analysis",
            ],
            limitations=[
                "无持久记忆（会话结束上下文丢失）",
                "依赖本地终端环境",
                "无跨会话记忆共享",
            ]
        )

    def _build_memory_prompt(self, snapshot: ContextSnapshot) -> str:
        """构建记忆注入提示"""
        prompt_parts = ["# 任务接续 - 之前的状态:"]
        prompt_parts.append(f"任务ID: {snapshot.task_id}")
        prompt_parts.append(f"时间: {snapshot.timestamp}")

        if snapshot.memory_refs:
            prompt_parts.append(f"\n相关记忆: {', '.join(snapshot.memory_refs)}")

        if snapshot.working_files:
            prompt_parts.append(f"\n工作文件: {', '.join(snapshot.working_files)}")

        prompt_parts.append("\n请基于以上上下文继续工作。")
        return "\n".join(prompt_parts)
```

#### 4.1.3 Codex适配器

```python
import aiohttp


class CodexAdapter(AgentAdapter):
    """OpenAI Codex适配器 - 基于HTTP API"""

    API_BASE = "https://api.openai.com/v1"

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        self.api_key = config["api_key"]
        self.organization = config.get("organization")
        self.model = config.get("model", "codex-latest")
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            if self.organization:
                headers["OpenAI-Organization"] = self.organization
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session

    async def send(self, message: AgentMessage) -> AgentResponse:
        session = await self._get_session()
        start_time = datetime.now()

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": message.metadata.get(
                    "system_prompt", "你是OpenAI Codex，一个AI编程助手。")},
                {"role": "user", "content": message.content}
            ],
            "max_tokens": message.metadata.get("max_tokens", 4000),
            "temperature": message.metadata.get("temperature", 0.7)
        }

        try:
            async with session.post(
                f"{self.API_BASE}/chat/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                latency = (datetime.now() - start_time).total_seconds() * 1000

                if resp.status == 429:
                    return AgentResponse(
                        content="Codex触发速率限制，请稍后再试",
                        message_type=MessageType.ERROR,
                        metadata={"error_type": "rate_limit"}
                    )

                if resp.status == 401:
                    return AgentResponse(
                        content="Codex API Key无效",
                        message_type=MessageType.ERROR,
                        metadata={"error_type": "auth_error"}
                    )

                resp.raise_for_status()
                data = await resp.json()

                choice = data["choices"][0]
                content = choice["message"][content"]
                tokens = data.get("usage", {}).get("total_tokens", 0)

                message_type = MessageType.CODE if "```" in content else MessageType.TEXT

                return AgentResponse(
                    content=content,
                    message_type=message_type,
                    tokens_used=tokens,
                    latency_ms=int(latency),
                    metadata={
                        "finish_reason": choice.get("finish_reason"),
                        "model": data.get("model")
                    }
                )

        except aiohttp.ClientError as e:
            return AgentResponse(
                content=f"Codex API请求失败: {str(e)}",
                message_type=MessageType.ERROR,
                metadata={"error_type": "api_error"}
            )

    async def health(self) -> HealthStatus:
        """检查Codex健康状态"""
        session = await self._get_session()
        start_time = datetime.now()

        try:
            async with session.get(
                f"{self.API_BASE}/models",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                latency = (datetime.now() - start_time).total_seconds() * 1000

                if resp.status == 401:
                    return HealthStatus(
                        level=HealthLevel.UNAVAILABLE,
                        is_available=False,
                        last_check=datetime.now(),
                        response_time_ms=latency,
                        error_rate_10min=0,
                        notes=["API Key无效"]
                    )

                resp.raise_for_status()

                rate_limit_remaining = resp.headers.get("X-RateLimit-Remaining")

                return HealthStatus(
                    level=HealthLevel.HEALTHY,
                    is_available=True,
                    last_check=datetime.now(),
                    response_time_ms=latency,
                    error_rate_10min=0.0,
                    rate_limit_remaining=int(rate_limit_remaining) if rate_limit_remaining else None,
                    notes=[f"模型: {self.model}"]
                )

        except Exception as e:
            return HealthStatus(
                level=HealthLevel.UNAVAILABLE,
                is_available=False,
                last_check=datetime.now(),
                response_time_ms=0, error_rate_10min=0,
                notes=[f"健康检查失败: {str(e)}"]
            )

    async def cost(self, task_hint: Dict[str, Any]) -> CostEstimate:
        """估算Codex任务成本"""
        estimated_input = task_hint.get("estimated_input_tokens", 4000)
        estimated_output = task_hint.get("estimated_output_tokens", 2000)
        input_cost = (estimated_input / 1_000_000) * 2.5
        output_cost = (estimated_output / 1_000_000) * 10.0

        return CostEstimate(
            estimated_input_tokens=estimated_input,
            estimated_output_tokens=estimated_output,
            estimated_cost_usd=input_cost + output_cost,
            pricing_model="per_token",
            confidence=0.75
        )

    async def context_sync(self, direction: SyncDirection,
                          snapshot: ContextSnapshot) -> SyncResult:
        """Codex上下文同步"""
        # Codex没有持久会话概念，每次请求独立
        # 需要通过system prompt注入上下文
        if direction == SyncDirection.UPLOAD:
            return SyncResult(success=True, bytes_transferred=0, items_synced=0)
        else:
            return SyncResult(
                success=True, bytes_transferred=0, items_synced=0,
                notes=["Codex不支持上下文导出"]
            )

    def capabilities(self) -> AgentCapabilities:
        return AgentCapabilities(
            agent_id=self.agent_id,
            agent_name="OpenAI Codex",
            supported_tasks=[
                "coding", "code_review", "refactoring", "testing",
                "documentation", "pr_creation"
            ],
            supported_languages=[
                "python", "typescript", "javascript", "rust", "go",
                "java", "csharp", "ruby", "php", "swift", "kotlin"
            ],
            max_context_tokens=128_000,
            supported_protocols=["http_rest", "cli"],
            special_features=[
                "async_execution",
                "parallel_tasks",
                "auto_pr_creation",
                "sandbox_execution",
                "credit_fallback",
            ],
            limitations=[
                "无持久记忆（每次会话独立）",
                "不支持跨会话上下文",
                "异步模式延迟较高",
            ]
        )
```


### 4.2 ContextBridge（上下文桥接）

ContextBridge是Agent切换时任务接续的核心组件。

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import hashlib
import json
import zlib
import base64
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class Decision:
    """关键决策"""
    decision_id: str
    topic: str
    decision: str
    reasoning: str
    alternatives: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self):
        return {
            "topic": self.topic,
            "decision": self.decision,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class CodeChange:
    """代码变更"""
    file_path: str
    change_type: str  # add/modify/delete
    summary: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self):
        return {"file": self.file_path, "type": self.change_type, "summary": self.summary}


@dataclass
class EnvState:
    """环境状态"""
    git_branch: str = ""
    git_commit: str = ""
    modified_files: List[str] = field(default_factory=list)
    working_dir: str = ""

    def to_dict(self):
        return {
            "branch": self.git_branch,
            "commit": self.git_commit[:8] if self.git_commit else "",
            "modified": self.modified_files
        }


@dataclass
class ContextSnapshot:
    """
    上下文快照 - Agent切换的核心数据结构

    设计原则：
    1. 自包含：包含任务恢复所需的全部信息
    2. 可序列化：支持JSON/Binary格式
    3. 可压缩：大上下文支持压缩传输
    4. 版本化：支持演进和向后兼容
    """

    # 基础标识
    task_id: str
    task_type: str = ""
    task_description: str = ""

    # Agent信息
    primary_agent: str = ""
    current_agent: str = ""
    agent_history: List[str] = field(default_factory=list)

    # 状态
    status: TaskStatus = TaskStatus.RUNNING
    progress_percent: float = 0.0
    current_phase: str = ""

    # 对话与决策
    conversation_summary: str = ""
    key_decisions: List[Decision] = field(default_factory=list)

    # 代码与环境
    code_changes: List[CodeChange] = field(default_factory=list)
    env_state: EnvState = field(default_factory=EnvState)
    working_files: List[str] = field(default_factory=list)

    # 记忆引用
    memory_refs: List[str] = field(default_factory=list)

    # 资源
    tokens_used: int = 0
    budget_used_usd: float = 0.0

    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1
    compression: Optional[str] = None

    def compute_hash(self) -> str:
        """计算哈希"""
        content = f"{self.task_id}:{self.current_agent}:{self.updated_at.isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "task_description": self.task_description,
            "primary_agent": self.primary_agent,
            "current_agent": self.current_agent,
            "agent_history": self.agent_history,
            "status": self.status.value,
            "progress_percent": self.progress_percent,
            "current_phase": self.current_phase,
            "conversation_summary": self.conversation_summary,
            "key_decisions": [d.to_dict() for d in self.key_decisions],
            "code_changes": [c.to_dict() for c in self.code_changes],
            "env_state": self.env_state.to_dict(),
            "working_files": self.working_files,
            "memory_refs": self.memory_refs,
            "tokens_used": self.tokens_used,
            "budget_used_usd": self.budget_used_usd,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "hash": self.compute_hash()
        }

    def to_json(self) -> str:
        """JSON序列化"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def to_compressed(self) -> str:
        """压缩序列化（用于传输）"""
        json_str = self.to_json()
        compressed = zlib.compress(json_str.encode(), level=6)
        self.compression = "zlib"
        return base64.b64encode(compressed).decode()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextSnapshot":
        """从字典反序列化"""
        snap = cls(
            task_id=data["task_id"],
            task_type=data.get("task_type", ""),
            task_description=data.get("task_description", ""),
            primary_agent=data.get("primary_agent", ""),
            current_agent=data.get("current_agent", ""),
            agent_history=data.get("agent_history", []),
            status=TaskStatus(data.get("status", "running")),
            progress_percent=data.get("progress_percent", 0.0),
            current_phase=data.get("current_phase", ""),
            conversation_summary=data.get("conversation_summary", ""),
            tokens_used=data.get("tokens_used", 0),
            budget_used_usd=data.get("budget_used_usd", 0.0),
            version=data.get("version", 1)
        )
        # 反序列化复杂类型
        if "key_decisions" in data:
            snap.key_decisions = [
                Decision(
                    decision_id=d.get("decision_id", f"d:{i}"),
                    topic=d["topic"],
                    decision=d["decision"],
                    reasoning=d.get("reasoning", ""),
                    alternatives=d.get("alternatives", [])
                ) for i, d in enumerate(data["key_decisions"])
            ]
        if "code_changes" in data:
            snap.code_changes = [
                CodeChange(
                    file_path=c.get("file", c.get("file_path", "")),
                    change_type=c.get("type", c.get("change_type", "")),
                    summary=c.get("summary", c.get("diff_summary", ""))
                ) for c in data["code_changes"]
            ]
        if "env_state" in data:
            es = data["env_state"]
            snap.env_state = EnvState(
                git_branch=es.get("branch", es.get("git_branch", "")),
                git_commit=es.get("commit", es.get("git_commit", "")),
                modified_files=es.get("modified", es.get("modified_files", [])),
                working_dir=es.get("working_dir", es.get("working_directory", ""))
            )
        if "working_files" in data:
            snap.working_files = data["working_files"]
        if "memory_refs" in data:
            snap.memory_refs = data["memory_refs"]
        return snap

    @classmethod
    def from_json(cls, json_str: str) -> "ContextSnapshot":
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def from_compressed(cls, compressed_str: str) -> "ContextSnapshot":
        compressed = base64.b64decode(compressed_str)
        json_str = zlib.decompress(compressed).decode()
        return cls.from_json(json_str)

    def get_summary_for_agent(self, target_agent: str, max_tokens: int = 4000) -> str:
        """
        生成适配目标Agent的上下文摘要。
        智能裁剪以适应目标Agent的token限制。
        """
        sections = []

        # 1. 任务概览（最高优先级，必须保留）
        sections.append("# 任务接续\n")
        sections.append(f"任务: {self.task_description}")
        sections.append(f"进度: {self.progress_percent}% | 阶段: {self.current_phase}")
        sections.append(f"切换: {self.current_agent} -> {target_agent}")

        # 2. 关键决策（高优先级）
        if self.key_decisions:
            sections.append("\n## 关键决策")
            for d in self.key_decisions[-5:]:
                sections.append(f"- [{d.timestamp.strftime('%H:%M')}] {d.topic}")
                sections.append(f"  -> {d.decision}")

        # 3. 代码变更
        if self.code_changes:
            sections.append("\n## 代码变更")
            for c in self.code_changes[-5:]:
                sections.append(f"- [{c.change_type}] {c.file_path}: {c.summary[:60]}")

        # 4. 环境状态
        if self.env_state.git_branch:
            sections.append(f"\n## 环境")
            sections.append(f"分支: {self.env_state.git_branch}")
            if self.env_state.modified_files:
                sections.append(f"修改: {', '.join(self.env_state.modified_files[:5])}")

        # 5. 对话摘要
        if self.conversation_summary:
            sections.append(f"\n## 对话摘要\n{self.conversation_summary[:1500]}")

        # 6. 记忆引用
        if self.memory_refs:
            sections.append(f"\n## 相关记忆: {', '.join(self.memory_refs[:10])}")

        summary = "\n".join(sections)

        # Token估算与裁剪 (1 token ~ 4字符)
        estimated_tokens = len(summary) // 4
        if estimated_tokens > max_tokens:
            ratio = (max_tokens / estimated_tokens) * 0.9
            cut_at = int(len(summary) * ratio)
            last_newline = summary.rfind('\n', 0, cut_at)
            if last_newline > len(summary) * 0.5:
                summary = summary[:last_newline] + "\n\n... [上下文已裁剪]"
            else:
                summary = summary[:cut_at] + "\n... [已裁剪]"

        return summary


@dataclass
class TransferResult:
    """切换结果"""
    success: bool
    task_id: str
    from_agent: str
    to_agent: str
    context_size: int
    duration_seconds: float
    message: str


class ContextNotFoundError(Exception):
    """上下文未找到异常"""
    pass


class ContextBridge:
    """
    上下文桥接 - Agent切换的核心引擎。

    核心流程:
    1. capture: 从原Agent捕获当前上下文
    2. persist: 将上下文持久化到记忆中心
    3. restore: 从记忆中心恢复上下文到新Agent
    """

    def __init__(self, memory_hub: Any, max_concurrent_transfers: int = 5):
        self.memory_hub = memory_hub
        self._active_snapshots: Dict[str, ContextSnapshot] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent_transfers)

    async def capture(self, task_id: str, from_adapter: Any) -> ContextSnapshot:
        """
        从Agent捕获上下文。
        步骤:
        1. 请求Agent导出当前上下文
        2. 补充网关端已知信息
        3. 压缩并保存
        """
        logger.info(f"[ContextBridge] 捕获任务 {task_id} 从 {from_adapter.agent_id}")

        snapshot = self._active_snapshots.get(task_id, ContextSnapshot(
            task_id=task_id,
            primary_agent=from_adapter.agent_id,
            current_agent=from_adapter.agent_id
        ))

        # 从Agent同步上下文
        try:
            sync_result = await asyncio.wait_for(
                from_adapter.context_sync(
                    direction=SyncDirection.DOWNLOAD,
                    snapshot=snapshot
                ),
                timeout=10.0
            )
            if sync_result and sync_result.success:
                logger.info(f"Agent导出上下文: {sync_result.bytes_transferred} bytes")
        except asyncio.TimeoutError:
            logger.warning("Agent上下文导出超时，使用网关端信息")
        except Exception as e:
            logger.warning(f"Agent上下文导出失败: {e}")

        # 更新快照
        snapshot.current_agent = from_adapter.agent_id
        if from_adapter.agent_id not in snapshot.agent_history:
            snapshot.agent_history.append(from_adapter.agent_id)
        snapshot.status = TaskStatus.SWITCHING
        snapshot.updated_at = datetime.now()

        # 添加快捷记录
        snapshot.key_decisions.append(Decision(
            decision_id=f"sw-{datetime.now().timestamp():.0f}",
            topic="Agent切换",
            decision=f"从 {from_adapter.agent_id} 切换",
            reasoning=f"触发切换时的状态: {snapshot.status.value}"
        ))

        self._active_snapshots[task_id] = snapshot
        return snapshot

    async def persist(self, task_id: str, priority: str = "normal") -> bool:
        """持久化上下文"""
        snapshot = self._active_snapshots.get(task_id)
        if not snapshot:
            logger.error(f"任务 {task_id} 没有活动快照")
            return False

        snapshot.updated_at = datetime.now()

        try:
            await self.memory_hub.save_snapshot(snapshot, priority=priority)
            logger.info(f"任务 {task_id} 上下文已持久化 (priority={priority})")
            return True
        except Exception as e:
            logger.error(f"持久化失败: {e}")
            await self._local_backup(snapshot)
            return False

    async def restore(self, task_id: str, to_adapter: Any) -> str:
        """
        恢复上下文到新Agent。
        返回应注入的prompt内容。
        """
        logger.info(f"[ContextBridge] 恢复任务 {task_id} 到 {to_adapter.agent_id}")

        snapshot = await self.memory_hub.load_snapshot(task_id)
        if not snapshot:
            snapshot = await self._load_local_backup(task_id)

        if not snapshot:
            raise ContextNotFoundError(f"任务 {task_id} 的上下文不存在")

        # 获取目标Agent的token限制
        caps = to_adapter.capabilities()
        injection_budget = caps.max_context_tokens // 2  # 预留50%

        # 加载相关记忆
        try:
            related = await self.memory_hub.query_relevant_memories(
                task_description=snapshot.task_description,
                top_k=5
            )
            snapshot.memory_refs = [m.id for m in related]
        except Exception as e:
            logger.warning(f"记忆检索失败: {e}")

        # 生成上下文摘要
        context_prompt = snapshot.get_summary_for_agent(
            target_agent=to_adapter.agent_id,
            max_tokens=injection_budget
        )

        # 通过适配器注入
        try:
            upload_snapshot = ContextSnapshot(
                task_id=task_id,
                conversation_summary=context_prompt,
                memory_refs=snapshot.memory_refs
            )
            await asyncio.wait_for(
                to_adapter.context_sync(
                    direction=SyncDirection.UPLOAD,
                    snapshot=upload_snapshot
                ),
                timeout=15.0
            )
        except asyncio.TimeoutError:
            logger.warning("上下文注入超时，将通过prompt注入")
        except Exception as e:
            logger.warning(f"上下文注入失败: {e}")

        # 更新快照状态
        snapshot.current_agent = to_adapter.agent_id
        snapshot.status = TaskStatus.RUNNING
        snapshot.updated_at = datetime.now()
        snapshot.version += 1
        self._active_snapshots[task_id] = snapshot

        return context_prompt

    async def transfer(self, task_id: str, 
                      from_adapter: Any, 
                      to_adapter: Any) -> TransferResult:
        """
        完整切换流程：捕获 -> 持久化 -> 恢复
        """
        async with self._semaphore:
            start_time = datetime.now()

            try:
                # 1. 捕获
                snapshot = await self.capture(task_id, from_adapter)

                # 2. 持久化
                persisted = await self.persist(task_id, priority="critical")
                if not persisted:
                    raise RuntimeError("上下文持久化失败")

                # 等待确认
                confirmed = await self.memory_hub.wait_for_persistence(task_id, timeout=5.0)
                if not confirmed:
                    logger.warning("MemoryHub持久化确认超时，继续恢复")

                # 3. 恢复
                context_prompt = await self.restore(task_id, to_adapter)

                duration = (datetime.now() - start_time).total_seconds()

                return TransferResult(
                    success=True,
                    task_id=task_id,
                    from_agent=from_adapter.agent_id,
                    to_agent=to_adapter.agent_id,
                    context_size=len(context_prompt),
                    duration_seconds=duration,
                    message=f"OK {from_adapter.agent_id} -> {to_adapter.agent_id} ({duration:.1f}s)"
                )

            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(f"切换失败: {e}")
                return TransferResult(
                    success=False,
                    task_id=task_id,
                    from_agent=from_adapter.agent_id,
                    to_agent=to_adapter.agent_id,
                    context_size=0,
                    duration_seconds=duration,
                    message=f"FAIL: {str(e)}"
                )

    async def _local_backup(self, snapshot: ContextSnapshot):
        """本地文件备份（降级方案）"""
        import os
        backup_dir = os.path.expanduser("~/.agent-gateway/backups")
        os.makedirs(backup_dir, exist_ok=True)
        filepath = f"{backup_dir}/{snapshot.task_id}.json"
        with open(filepath, "w") as f:
            f.write(snapshot.to_json())
        logger.info(f"本地备份已写入: {filepath}")

    async def _load_local_backup(self, task_id: str) -> Optional[ContextSnapshot]:
        """从本地备份加载"""
        import os
        filepath = os.path.expanduser(f"~/.agent-gateway/backups/{task_id}.json")
        if os.path.exists(filepath):
            with open(filepath) as f:
                return ContextSnapshot.from_json(f.read())
        return None
```


### 4.3 MemoryHub（统一记忆中心）

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import asyncio
import json


class MemoryType(Enum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class PrivacyLevel(Enum):
    PUBLIC = "public"
    AGENT_SPECIFIC = "agent"
    PRIVATE = "private"


@dataclass
class MemoryRecord:
    """记忆记录"""
    id: str
    memory_type: MemoryType
    content: str
    source_agent: str = ""
    source_task: str = ""
    privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class MemoryHub:
    """
    统一记忆中心 - 跨Agent记忆共享的核心。
    提供统一的记忆写入、读取、检索和同步接口。
    """

    def __init__(self, redis_url: str = "redis://localhost:6379",
                 pg_url: str = "postgresql://user:pass@localhost/agent_memory",
                 embedding_dim: int = 1536):
        self.redis_url = redis_url
        self.pg_url = pg_url
        self.embedding_dim = embedding_dim
        self._redis = None
        self._pg = None
        self._sync_queue = asyncio.Queue()

    async def initialize(self):
        """初始化存储连接"""
        import aioredis
        import asyncpg
        self._redis = await aioredis.from_url(self.redis_url, decode_responses=True)
        self._pg = await asyncpg.connect(self.pg_url)
        await self._init_tables()
        asyncio.create_task(self._sync_queue_processor())

    async def _init_tables(self):
        """初始化数据库表"""
        # 语义记忆表
        await self._pg.execute("""
            CREATE TABLE IF NOT EXISTS semantic_memories (
                id SERIAL PRIMARY KEY,
                memory_id VARCHAR(64) UNIQUE NOT NULL,
                category VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                context TEXT,
                source_agent VARCHAR(50),
                source_task VARCHAR(100),
                confidence FLOAT DEFAULT 1.0,
                confirmed_by_user BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # 上下文快照表
        await self._pg.execute("""
            CREATE TABLE IF NOT EXISTS context_snapshots (
                task_id VARCHAR(100) PRIMARY KEY,
                snapshot_data JSONB NOT NULL,
                priority VARCHAR(20) DEFAULT 'normal',
                version INTEGER DEFAULT 1,
                saved_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # pgvector扩展
        await self._pg.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        await self._pg.execute(f"""
            CREATE TABLE IF NOT EXISTS episodic_memories (
                id SERIAL PRIMARY KEY,
                memory_id VARCHAR(64) UNIQUE NOT NULL,
                task_description TEXT NOT NULL,
                task_summary TEXT,
                outcome TEXT,
                lessons_learned TEXT,
                embedding vector({self.embedding_dim}),
                source_agent VARCHAR(50),
                tokens_used INTEGER,
                duration_seconds FLOAT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # 向量索引
        await self._pg.execute("""
            CREATE INDEX IF NOT EXISTS idx_episodic_embedding 
            ON episodic_memories 
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """)

    # --- 记忆写入接口 ---

    async def write_working_memory(self, task_id: str, content: Dict[str, Any], 
                                   ttl: int = 86400) -> str:
        """写入工作记忆 - 当前任务的实时状态，24小时过期"""
        memory_id = f"wm:{task_id}"
        data = {
            "content": json.dumps(content),
            "updated_at": datetime.now().isoformat(),
            "version": content.get("version", 1)
        }
        await self._redis.hset(f"memory:{memory_id}", mapping=data)
        await self._redis.expire(f"memory:{memory_id}", ttl)
        return memory_id

    async def write_episodic_memory(self, task_description: str, task_summary: str,
                                     outcome: str, lessons: str, source_agent: str,
                                     embedding: List[float], **kwargs) -> str:
        """写入情景记忆 - 完成的任务记录，支持向量检索"""
        import uuid
        memory_id = f"em:{uuid.uuid4().hex[:12]}"

        await self._pg.execute("""
            INSERT INTO episodic_memories 
            (memory_id, task_description, task_summary, outcome, 
             lessons_learned, embedding, source_agent, tokens_used, duration_seconds)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """, memory_id, task_description, task_summary, outcome,
           lessons, embedding, source_agent,
           kwargs.get("tokens_used"), kwargs.get("duration_seconds"))

        return memory_id

    async def write_semantic_memory(self, category: str, content: str,
                                     context: str = "", source_agent: str = "",
                                     source_task: str = "", confidence: float = 1.0) -> str:
        """写入语义记忆 - 用户偏好、决策和项目规范"""
        import uuid
        memory_id = f"sm:{uuid.uuid4().hex[:12]}"

        await self._pg.execute("""
            INSERT INTO semantic_memories 
            (memory_id, category, content, context, source_agent, source_task, confidence)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, memory_id, category, content, context, source_agent, source_task, confidence)

        return memory_id

    # --- 记忆读取接口 ---

    async def read(self, memory_id: str) -> Optional[MemoryRecord]:
        """读取指定记忆"""
        if memory_id.startswith("wm:"):
            data = await self._redis.hgetall(f"memory:{memory_id}")
            if data:
                return MemoryRecord(
                    id=memory_id,
                    memory_type=MemoryType.WORKING,
                    content=data.get("content", ""),
                    metadata={"version": data.get("version", 1)}
                )

        if memory_id.startswith("em:"):
            row = await self._pg.fetchrow("""
                SELECT * FROM episodic_memories WHERE memory_id = $1
            """, memory_id)
            if row:
                return MemoryRecord(
                    id=memory_id,
                    memory_type=MemoryType.EPISODIC,
                    content=f"{row['task_description']}\n结果: {row['outcome']}",
                    source_agent=row['source_agent'],
                    metadata={"lessons": row['lessons_learned']}
                )

        if memory_id.startswith("sm:"):
            row = await self._pg.fetchrow("""
                SELECT * FROM semantic_memories WHERE memory_id = $1
            """, memory_id)
            if row:
                return MemoryRecord(
                    id=memory_id,
                    memory_type=MemoryType.SEMANTIC,
                    content=row['content'],
                    source_agent=row['source_agent'],
                    metadata={"category": row['category'], "confidence": row['confidence']}
                )

        return None

    # --- 记忆检索接口 ---

    async def query_relevant_memories(self, task_description: str, 
                                       embedding: Optional[List[float]] = None,
                                       top_k: int = 5,
                                       agent_id: Optional[str] = None) -> List[MemoryRecord]:
        """检索与任务相关的记忆"""
        results = []

        # 1. 检索情景记忆（向量相似度）
        if embedding:
            rows = await self._pg.fetch("""
                SELECT memory_id, task_description, task_summary, outcome,
                       lessons_learned, source_agent, created_at,
                       1 - (embedding <=> $1) as similarity
                FROM episodic_memories
                WHERE 1 - (embedding <=> $1) > 0.7
                ORDER BY embedding <=> $1
                LIMIT $2
            """, embedding, top_k)

            for row in rows:
                results.append(MemoryRecord(
                    id=row['memory_id'],
                    memory_type=MemoryType.EPISODIC,
                    content=f"{row['task_description']}\n结果: {row['outcome']}",
                    source_agent=row['source_agent'],
                    metadata={"similarity": row['similarity'], "lessons": row['lessons_learned']}
                ))

        # 2. 检索语义记忆（关键词匹配）
        keywords = task_description.split()[:10]
        pattern = f"%{' '.join(keywords)}%"
        rows = await self._pg.fetch("""
            SELECT memory_id, category, content, context, 
                   source_agent, confidence
            FROM semantic_memories
            WHERE content ILIKE $1 OR context ILIKE $1
            ORDER BY confidence DESC, updated_at DESC
            LIMIT $2
        """, pattern, top_k)

        for row in rows:
            results.append(MemoryRecord(
                id=row['memory_id'],
                memory_type=MemoryType.SEMANTIC,
                content=row['content'],
                source_agent=row['source_agent'],
                metadata={"category": row['category'], "confidence": row['confidence']}
            ))

        # 按相关度排序
        results.sort(key=lambda m: m.metadata.get("similarity", 0.5), reverse=True)
        return results[:top_k]

    async def get_user_preferences(self, category: Optional[str] = None) -> List[MemoryRecord]:
        """获取用户偏好"""
        if category:
            rows = await self._pg.fetch("""
                SELECT * FROM semantic_memories 
                WHERE category = $1 
                AND (confirmed_by_user = TRUE OR confidence > 0.8)
                ORDER BY updated_at DESC
            """, category)
        else:
            rows = await self._pg.fetch("""
                SELECT * FROM semantic_memories 
                WHERE confirmed_by_user = TRUE OR confidence > 0.8
                ORDER BY updated_at DESC
            """)

        return [
            MemoryRecord(
                id=r['memory_id'],
                memory_type=MemoryType.SEMANTIC,
                content=r['content'],
                source_agent=r['source_agent'],
                metadata={"category": r['category']}
            ) for r in rows
        ]

    # --- 快照管理 ---

    async def save_snapshot(self, snapshot: ContextSnapshot, priority: str = "normal"):
        """保存上下文快照"""
        memory_id = f"snap:{snapshot.task_id}"

        if priority == "critical":
            await self._pg.execute("""
                INSERT INTO context_snapshots (task_id, snapshot_data, priority, saved_at, version)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (task_id) DO UPDATE SET
                    snapshot_data = EXCLUDED.snapshot_data,
                    priority = EXCLUDED.priority,
                    saved_at = EXCLUDED.saved_at,
                    version = EXCLUDED.version
            """, snapshot.task_id, snapshot.to_json(), priority,
               datetime.now(), snapshot.version)

        # 同时写入Redis
        await self._redis.hset(f"memory:{memory_id}", mapping={
            "snapshot": snapshot.to_json(),
            "priority": priority,
            "updated_at": datetime.now().isoformat()
        })
        await self._redis.expire(f"memory:{memory_id}", 86400 * 7)

    async def load_snapshot(self, task_id: str) -> Optional[ContextSnapshot]:
        """加载上下文快照"""
        memory_id = f"snap:{task_id}"
        data = await self._redis.hgetall(f"memory:{memory_id}")

        if data and "snapshot" in data:
            try:
                return ContextSnapshot.from_dict(json.loads(data["snapshot"]))
            except (json.JSONDecodeError, KeyError):
                pass

        row = await self._pg.fetchrow("""
            SELECT snapshot_data FROM context_snapshots WHERE task_id = $1
        """, task_id)

        if row:
            try:
                return ContextSnapshot.from_dict(json.loads(row['snapshot_data']))
            except (json.JSONDecodeError, KeyError):
                pass

        return None

    async def wait_for_persistence(self, task_id: str, timeout: float = 5.0) -> bool:
        """等待快照持久化完成"""
        start = datetime.now()
        while (datetime.now() - start).total_seconds() < timeout:
            snapshot = await self.load_snapshot(task_id)
            if snapshot is not None:
                return True
            await asyncio.sleep(0.1)
        return False

    async def _sync_queue_processor(self):
        """后台同步队列处理器"""
        while True:
            try:
                task = await self._sync_queue.get()
                await self._process_sync_task(task)
            except Exception as e:
                print(f"同步队列处理错误: {e}")
            await asyncio.sleep(0.1)

    async def _process_sync_task(self, task: Dict):
        """处理单个同步任务"""
        pass
```


### 4.4 RouterEngine（路由引擎）

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    BEST_SCORE = "best_score"
    ROUND_ROBIN = "round_robin"
    LEAST_LOAD = "least_load"
    COST_FIRST = "cost_first"
    SPEED_FIRST = "speed_first"


@dataclass
class RoutingScore:
    """路由评分详情"""
    agent_id: str
    overall: float = 0.0
    availability: float = 0.0
    cost: float = 0.0
    capability: float = 0.0
    speed: float = 0.0
    memory: float = 0.0
    success_rate: float = 0.0
    explanation: str = ""

    def to_dict(self):
        return {
            "agent_id": self.agent_id,
            "overall": round(self.overall, 3),
            "availability": round(self.availability, 3),
            "cost": round(self.cost, 3),
            "capability": round(self.capability, 3),
            "speed": round(self.speed, 3),
            "memory": round(self.memory, 3),
            "success_rate": round(self.success_rate, 3)
        }


@dataclass
class RouterConfig:
    """路由配置"""
    weights: Dict[str, float] = field(default_factory=lambda: {
        "availability": 0.30,
        "cost": 0.15,
        "capability": 0.25,
        "speed": 0.10,
        "memory": 0.10,
        "success_rate": 0.10
    })
    min_availability: float = 0.3
    max_cost_usd: float = 10.0
    max_latency_ms: float = 30000
    failover_cooldown_sec: int = 300
    health_check_interval_sec: int = 10
    default_strategy: RoutingStrategy = RoutingStrategy.BEST_SCORE


class RouterEngine:
    """
    智能路由引擎

    职责:
    1. 多维度Agent评分
    2. 实时健康监控
    3. 故障转移和冷却
    4. 策略化路由选择
    """

    def __init__(self, agent_pool: Any, memory_hub: Any, 
                 config: Optional[RouterConfig] = None):
        self.agent_pool = agent_pool
        self.memory_hub = memory_hub
        self.config = config or RouterConfig()

        # 运行时状态
        self._failover_log: Dict[str, List[datetime]] = {}
        self._cooling: Dict[str, datetime] = {}
        self._assignment_count: Dict[str, int] = {}
        self._health_cache: Dict[str, Any] = {}
        self._health_cache_time: Dict[str, datetime] = {}

        self._running = False
        self._health_task: Optional[asyncio.Task] = None

    async def start(self):
        """启动路由引擎"""
        self._running = True
        self._health_task = asyncio.create_task(self._health_loop())
        logger.info("RouterEngine 已启动")

    async def stop(self):
        """停止"""
        self._running = False
        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass

    async def route(self, task: Dict[str, Any],
                   preferred: Optional[str] = None,
                   strategy: Optional[RoutingStrategy] = None,
                   exclude: Optional[List[str]] = None) -> str:
        """
        路由决策主入口。

        Args:
            task: {type, description, estimated_tokens, languages, requirements}
            preferred: 用户偏好的Agent ID
            strategy: 路由策略
            exclude: 排除的Agent列表

        Returns:
            选中的Agent ID
        """
        strat = strategy or self.config.default_strategy
        exclude_set = set(exclude or [])

        # 1. 获取候选Agent
        candidates = await self.agent_pool.available_agents()
        if not candidates:
            raise NoAvailableAgentError("没有可用Agent")

        # 2. 排除冷却中和指定排除的
        now = datetime.now()
        candidates = [
            a for a in candidates
            if a.agent_id not in exclude_set
            and (a.agent_id not in self._cooling or self._cooling[a.agent_id] < now)
        ]

        if not candidates:
            if self._cooling:
                oldest = min(self._cooling.items(), key=lambda x: x[1])
                candidates = [a for a in self.agent_pool.list_all() 
                             if a.agent_id == oldest[0]]
            if not candidates:
                raise NoAvailableAgentError("所有Agent都在冷却中")

        # 3. 评分
        scores = []
        for agent in candidates:
            try:
                score = await self._score(agent, task)
                scores.append(score)
            except Exception as e:
                logger.warning(f"评分 {agent.agent_id} 失败: {e}")

        if not scores:
            raise NoAvailableAgentError("没有Agent能通过评分")

        # 4. 按策略选择
        selected = self._select_by_strategy(scores, strat)

        # 5. 用户偏好覆盖
        if preferred:
            pref_score = next((s for s in scores if s.agent_id == preferred), None)
            if pref_score and pref_score.availability >= self.config.min_availability:
                selected = pref_score
                logger.info(f"使用用户偏好Agent: {preferred}")

        # 6. 更新计数
        self._assignment_count[selected.agent_id] =             self._assignment_count.get(selected.agent_id, 0) + 1

        logger.info(f"路由决策: {selected.agent_id} (score={selected.overall:.3f})")

        return selected.agent_id

    async def _score(self, agent: Any, task: Dict[str, Any]) -> RoutingScore:
        """为Agent计算综合评分"""
        w = self.config.weights
        score = RoutingScore(agent_id=agent.agent_id)

        # 获取健康状态（使用缓存）
        health = await self._get_cached_health(agent)

        # 1. 可用性评分
        score.availability = self._score_availability(health)

        # 2. 成本评分
        try:
            cost = await asyncio.wait_for(agent.cost(task), timeout=5.0)
            score.cost = max(0, 1 - (cost.estimated_cost_usd / self.config.max_cost_usd))
        except:
            score.cost = 0.5

        # 3. 能力匹配
        score.capability = self._score_capability(agent, task)

        # 4. 速度
        score.speed = max(0, 1 - (health.get("response_time_ms", 30000) 
                                  / self.config.max_latency_ms))

        # 5. 记忆亲和度
        score.memory = await self._score_memory(agent, task)

        # 6. 成功率
        score.success_rate = self._score_success_rate(agent.agent_id)

        # 综合
        score.overall = (
            w["availability"] * score.availability +
            w["cost"] * score.cost +
            w["capability"] * score.capability +
            w["speed"] * score.speed +
            w["memory"] * score.memory +
            w["success_rate"] * score.success_rate
        )

        score.explanation = (f"a={score.availability:.2f} c={score.cost:.2f} "
                            f"cap={score.capability:.2f} s={score.speed:.2f} "
                            f"m={score.memory:.2f} sr={score.success_rate:.2f}")

        return score

    def _score_availability(self, health: Dict[str, Any]) -> float:
        """可用性评分"""
        if not health.get("is_available", False):
            return 0.0

        score = 1.0

        # Token不足
        remaining = health.get("token_remaining")
        total = health.get("token_total")
        if remaining is not None and total:
            ratio = remaining / total
            if ratio < 0.05:
                score -= 0.6
            elif ratio < 0.15:
                score -= 0.3
            elif ratio < 0.30:
                score -= 0.1

        # 速率限制
        rl = health.get("rate_limit_remaining")
        if rl is not None and rl < 5:
            score -= 0.4

        # 错误率
        err = health.get("error_rate_10min", 0)
        if err > 0.5:
            score -= 0.5
        elif err > 0.2:
            score -= 0.2

        # 健康级别
        level = health.get("level")
        if level == "degraded":
            score -= 0.15
        elif level == "limited":
            score -= 0.4

        return max(0, score)

    def _score_capability(self, agent: Any, task: Dict[str, Any]) -> float:
        """能力匹配评分"""
        caps = agent.capabilities()
        scores = []

        task_type = task.get("type", "")
        if task_type in caps.supported_tasks:
            scores.append(1.0)
        else:
            scores.append(0.2)

        langs = task.get("languages", [])
        if langs:
            matched = sum(1 for l in langs if l in caps.supported_languages)
            scores.append(matched / len(langs))

        est_tokens = task.get("estimated_tokens", 4000)
        if caps.max_context_tokens >= est_tokens * 2:
            scores.append(1.0)
        elif caps.max_context_tokens >= est_tokens:
            scores.append(0.6)
        else:
            scores.append(0.2)

        reqs = task.get("requirements", [])
        if reqs:
            matched = sum(1 for r in reqs if r in caps.special_features)
            scores.append(matched / len(reqs))

        return sum(scores) / len(scores) if scores else 0.5

    async def _score_memory(self, agent: Any, task: Dict[str, Any]) -> float:
        """记忆亲和度"""
        try:
            rows = await self.memory_hub._pg.fetch("""
                SELECT COUNT(*) as cnt FROM episodic_memories 
                WHERE source_agent = $1 
            """, agent.agent_id)
            count = rows[0]["cnt"] if rows else 0
            return min(1.0, 0.2 + count * 0.05)
        except:
            return 0.5

    def _score_success_rate(self, agent_id: str) -> float:
        """成功率评分"""
        failures = self._failover_log.get(agent_id, [])
        if not failures:
            return 0.8

        now = datetime.now()
        recent_10min = [f for f in failures[-10:] if now - f < timedelta(minutes=10)]

        if len(recent_10min) >= 3:
            return 0.1
        elif len(recent_10min) >= 1:
            return 0.5
        return 0.8

    def _select_by_strategy(self, scores: List[RoutingScore], 
                           strategy: RoutingStrategy) -> RoutingScore:
        """按策略选择"""
        if strategy == RoutingStrategy.BEST_SCORE:
            return max(scores, key=lambda s: s.overall)
        elif strategy == RoutingStrategy.ROUND_ROBIN:
            top = [s for s in scores if s.overall > 0.5]
            if not top:
                top = scores
            return min(top, key=lambda s: self._assignment_count.get(s.agent_id, 0))
        elif strategy == RoutingStrategy.LEAST_LOAD:
            return min(scores, key=lambda s: self._assignment_count.get(s.agent_id, 0))
        elif strategy == RoutingStrategy.COST_FIRST:
            return max(scores, key=lambda s: s.cost)
        elif strategy == RoutingStrategy.SPEED_FIRST:
            return max(scores, key=lambda s: s.speed)
        return max(scores, key=lambda s: s.overall)

    async def _get_cached_health(self, agent: Any) -> Dict[str, Any]:
        """获取缓存的健康状态"""
        agent_id = agent.agent_id
        now = datetime.now()

        cached = self._health_cache.get(agent_id)
        cached_time = self._health_cache_time.get(agent_id)

        if cached and cached_time and (now - cached_time).seconds < 5:
            return cached

        try:
            health = await asyncio.wait_for(agent.health(), timeout=10.0)
            h = {
                "is_available": health.is_available,
                "level": getattr(health.level, "value", str(health.level)),
                "response_time_ms": health.response_time_ms,
                "token_remaining": health.token_remaining,
                "token_total": health.token_total,
                "rate_limit_remaining": health.rate_limit_remaining,
                "error_rate_10min": health.error_rate_10min
            }
            self._health_cache[agent_id] = h
            self._health_cache_time[agent_id] = now
            return h
        except:
            return {"is_available": False, "level": "unavailable"}

    async def report_failure(self, agent_id: str, reason: str):
        """报告Agent故障"""
        now = datetime.now()

        if agent_id not in self._failover_log:
            self._failover_log[agent_id] = []
        self._failover_log[agent_id].append(now)

        # 检查是否触发冷却
        recent = [f for f in self._failover_log[agent_id] 
                 if now - f < timedelta(minutes=10)]

        if len(recent) >= 3:
            cooldown = now + timedelta(seconds=self.config.failover_cooldown_sec)
            self._cooling[agent_id] = cooldown
            logger.warning(f"Agent {agent_id} 触发冷却至 {cooldown}")

        self._health_cache.pop(agent_id, None)

    async def _health_loop(self):
        """健康监控循环"""
        while self._running:
            try:
                for agent in self.agent_pool.list_all():
                    try:
                        health = await asyncio.wait_for(
                            agent.health(), timeout=15.0
                        )
                        agent.record_health(health)

                        h = {
                            "is_available": health.is_available,
                            "level": getattr(health.level, "value", str(health.level)),
                            "response_time_ms": health.response_time_ms,
                            "token_remaining": health.token_remaining,
                            "token_total": health.token_total,
                            "error_rate_10min": health.error_rate_10min
                        }
                        self._health_cache[agent.agent_id] = h
                        self._health_cache_time[agent.agent_id] = datetime.now()

                        if not health.is_available:
                            await self.report_failure(agent.agent_id, "健康检查失败")
                    except asyncio.TimeoutError:
                        await self.report_failure(agent.agent_id, "健康检查超时")
                    except Exception as e:
                        logger.debug(f"健康检查 {agent.agent_id} 异常: {e}")

                await asyncio.sleep(self.config.health_check_interval_sec)
            except Exception as e:
                logger.error(f"健康循环异常: {e}")
                await asyncio.sleep(30)

    def get_stats(self) -> Dict[str, Any]:
        """获取路由统计"""
        return {
            "assignment_count": self._assignment_count,
            "cooling_agents": {k: v.isoformat() for k, v in self._cooling.items()},
            "failover_log": {k: len(v) for k, v in self._failover_log.items()},
        }


class NoAvailableAgentError(Exception):
    """没有可用Agent异常"""
    pass
```


---

## 5. 关键场景详细设计

### 5.1 场景1：Claude Code没token -> 自动切换到Codex接续任务

这是用户项目的核心场景，体现"统一入口+记忆增强"的核心价值。

#### 5.1.1 完整时序图

```mermaid
sequenceDiagram
    autonumber
    participant U as 用户
    participant GW as AgentGateway
    participant R as RouterEngine
    participant CB as ContextBridge
    participant MH as MemoryHub
    participant CA as ClaudeCodeAdapter
    participant OA as CodexAdapter
    participant RH as Redis(工作记忆)
    participant PG as PostgreSQL(持久记忆)

    Note over U,PG: === 正常执行阶段 ===

    U->>GW: "优化API性能"
    GW->>R: route(task="optimize_api")
    R->>CA: health() (cached)
    CA-->>R: HEALTHY token: 85%
    R->>R: score=0.92
    R-->>GW: selected=claude-code
    GW->>CA: send("优化API性能...")
    activate CA
    CA-->>GW: [stream] 分析中...
    CA-->>GW: [stream] 发现N+1查询...

    Note over R: 每10秒健康检查
    loop 健康监控
        R->>CA: health()
        CA-->>R: HEALTHY token: 60%->30%->8%
    end

    Note over U,PG: === Token耗尽检测 ===

    CA-->>GW: [429] Rate Limit
    deactivate CA
    GW->>R: report_failure("claude-code", "token耗尽")
    R->>R: 加入冷却队列(5min)

    Note over GW: 触发紧急上下文保存
    GW->>CB: capture(task_id="task-123", from=CA)
    CB->>CA: context_sync(DOWNLOAD)
    CA-->>CB: {对话历史, 工作文件, 决策记录}
    CB->>CB: 构建ContextSnapshot
    CB->>RH: SET memory:snap:task-123 (TTL=24h)
    CB->>PG: INSERT context_snapshots priority=critical
    PG-->>CB: OK 已持久化
    CB-->>GW: snapshot

    Note over U,PG: === 路由重决策 ===

    GW->>R: route(task, exclude=["claude-code"])
    R->>OA: health()
    OA-->>R: HEALTHY token: 92%
    R->>R: score=0.88 (claude冷却中)
    R-->>GW: selected=codex

    Note over U,PG: === 上下文恢复 ===

    GW->>CB: restore(task_id="task-123", to=OA)
    CB->>RH: GET memory:snap:task-123
    RH-->>CB: snapshot_data
    CB->>PG: query_relevant_memories("API优化")
    PG-->>CB: [3条相关历史任务]
    CB->>CB: generate_summary() token_budget=64000
    CB->>OA: context_sync(UPLOAD, summary)
    Note right of OA: system_prompt注入:<br/>"任务接续: 进度45%<br/>已发现N+1查询瓶颈<br/>关键决策: ..."
    OA-->>CB: OK 已注入
    CB-->>GW: context_prompt

    Note over U,PG: === 任务接续 ===

    GW->>OA: send("继续优化...已分析出N+1查询")
    activate OA
    OA-->>GW: [stream] 使用select_related优化...
    OA-->>GW: [stream] 完成！性能提升10x
    deactivate OA

    GW->>OA: context_sync(DOWNLOAD)
    OA-->>GW: {执行结果, 代码变更}
    GW->>MH: save_episodic_memory(任务完成)
    MH->>PG: INSERT episodic_memories (embedding + summary)

    GW-->>U: 完成！Claude Code自动切换至Codex<br/>优化后QPS从120->1800

    Note over U,PG: === 后续: Claude恢复 ===

    Note over CA: 1小时后
    R->>CA: health()
    CA-->>R: HEALTHY token: 100%
    R->>R: 从冷却队列移除
    Note over CA: 下次任务可重新使用
```

#### 5.1.2 上下文保存与恢复细节

**保存阶段（Claude Code -> MemoryHub）**：

```python
async def emergency_save_context(self, task_id: str, claude_adapter: ClaudeCodeAdapter):
    """紧急保存上下文 - 在Agent故障时调用"""

    # 1. 立即停止当前对话
    await claude_adapter.send(AgentMessage(
        content="/pause",
        message_type=MessageType.COMMAND
    ))

    # 2. 捕获当前上下文
    bridge = self.context_bridge
    snapshot = await bridge.capture(task_id, claude_adapter)

    # 3. 关键信息紧急记录
    snapshot.status = TaskStatus.PAUSED
    snapshot.key_decisions.append(Decision(
        decision_id=f"d:{datetime.now().timestamp():.0f}",
        topic="Agent切换触发",
        decision=f"从Claude Code切换到Codex（原因：token耗尽）",
        reasoning=f"Claude Code token余额<5%，无法继续执行任务",
        timestamp=datetime.now()
    ))

    # 4. 强制持久化
    await self.memory_hub.save_snapshot(snapshot, priority="critical")

    # 5. 确认写入
    confirmed = await self.memory_hub.wait_for_persistence(task_id, timeout=5.0)
    if not confirmed:
        await self._local_backup(snapshot)

    return snapshot
```

**恢复阶段（MemoryHub -> Codex）**：

```python
async def restore_context_to_codex(self, task_id: str, codex_adapter: CodexAdapter) -> str:
    """恢复上下文到Codex"""

    # 1. 加载快照
    snapshot = await self.memory_hub.load_snapshot(task_id)
    if not snapshot:
        raise ContextNotFoundError(f"任务 {task_id} 上下文丢失")

    # 2. 获取Codex的token限制
    caps = codex_adapter.capabilities()
    injection_budget = caps.max_context_tokens // 2

    # 3. 生成注入prompt（适配Codex风格）
    context_prompt = f"""
# 任务接续说明

你正在接替另一个AI助手（Claude Code）完成一个被中断的任务。

## 任务概览
- 任务：{snapshot.task_description}
- 进度：{snapshot.progress_percent}%
- 当前阶段：{snapshot.current_phase}

## 之前的关键决策
{self._format_decisions(snapshot.key_decisions)}

## 已完成的代码变更
{self._format_code_changes(snapshot.code_changes)}

## 环境状态
- 分支：{snapshot.environment_state.git_branch}
- 工作文件：{', '.join(snapshot.working_files)}

## 对话摘要
{snapshot.conversation_summary[:2000]}

请基于以上上下文继续工作。注意保持代码风格一致。
"""

    # 4. Token预算控制
    estimated_tokens = len(context_prompt) // 4
    if estimated_tokens > injection_budget:
        context_prompt = self._compress_for_budget(snapshot, injection_budget)

    return context_prompt
```

#### 5.1.3 代码风格差异处理

不同Agent的代码风格可能不同。切换时需要处理：

| 风格维度 | Claude Code风格 | Codex风格 | 处理策略 |
|----------|----------------|-----------|----------|
| 代码注释 | 详细JSDoc | 简洁行注释 | 从记忆加载用户偏好 |
| 错误处理 | try/catch+logger | 直接返回error | 记忆中有项目规范 |
| 命名风格 | camelCase | snake_case(Python) | 按语言标准，非Agent |
| import排序 | 字母顺序 | 分组 | 项目级MEMORY.md规定 |
| 函数长度 | 偏好短小 | 接受较长 | 从用户历史代码推断 |

**处理方式**：统一记忆的语义层中保存"项目代码规范"，切换时作为system prompt注入新Agent。

#### 5.1.4 用户感知设计

切换时用户应得到清晰通知：

```
! 自动切换通知
==================================================
Claude Code token已耗尽，已自动切换至 OpenAI Codex
任务继续执行，上下文已完整保留

切换详情：
  原Agent: Claude Code (token: 2%)
  新Agent: OpenAI Codex (token: 92%)  
  任务进度: 45% (已分析完瓶颈，进入优化阶段)
  记忆加载: 3条关键决策 + 2个文件上下文

您也可以手动选择其他Agent：
[Cursor] [OpenClaw] [稍后重试Claude Code]
==================================================
```

### 5.2 场景2：多Agent协作完成复杂任务

#### 5.2.1 用例描述

**任务**：实现一个用户认证系统（OAuth2 + JWT + Refresh Token）

**协作流程**：

| 阶段 | 负责Agent | 工具 | 输出 |
|------|-----------|------|------|
| 需求分析 | PM Agent | Claude Code | 需求文档+API设计 |
| 技术设计 | Architect Agent | Claude Code | 技术方案+数据模型 |
| 编码实现 | Developer Agent | Codex | 可运行代码+单元测试 |
| 代码审查 | Reviewer Agent | Cursor | 审查报告+修改建议 |
| 测试验证 | QA Agent | Cursor | 测试报告+覆盖率 |
| 部署配置 | DevOps Agent | Claude Code | Dockerfile+CI配置 |

#### 5.2.2 记忆流转设计

```
阶段1: PM Agent (Claude Code)
  执行中 -> 工作记忆实时写入Redis
  完成 -> 情景记忆写入PGVector
    - "需求分析任务：用户认证系统"
    - "决策：使用OAuth2而非SAML（原因：复杂度）"
    - "API设计：POST /auth/token, POST /auth/refresh"
  语义记忆写入PostgreSQL
    - "用户偏好：API设计优先RESTful风格"
         |
         v 记忆同步
阶段2: Architect Agent (Claude Code)
  启动前 -> 加载阶段1的情景记忆
    - "用户认证系统相关历史 -> 找到阶段1记录"
    - "决策：OAuth2（已有结论，直接继承）"
  执行中 -> 工作记忆写入Redis
  完成 -> 情景记忆写入
    - "技术决策：Redis存储refresh token（TTL=7天）"
         |
         v 记忆同步
阶段3: Developer Agent (Codex)
  启动前 -> 加载阶段1+2的情景记忆
    - "找到需求+设计记录"
    - "关键决策：OAuth2 + Redis"
    - "API设计规范：RESTful风格"
  执行中 -> 工作记忆写入Redis
  完成 -> 情景记忆写入
    - "代码实现：Python/FastAPI，含单元测试"
         |
         v 记忆同步
阶段4+: 后续Agent重复上述流程...
```

#### 5.2.3 任务状态传递

每个阶段通过ContextSnapshot传递：

```python
auth_system_pipeline = [
    {
        "phase": "requirements",
        "agent_type": "claude-code",
        "prompt_template": "分析OAuth2认证系统需求...",
        "output_artifacts": ["requirements.md", "api_spec.yaml"],
    },
    {
        "phase": "architecture",
        "agent_type": "claude-code",
        "prompt_template": "基于{previous.requirements}设计技术架构...",
        "input_from_previous": ["requirements.md"],
    },
    {
        "phase": "implementation",
        "agent_type": "codex",
        "prompt_template": "基于{previous.architecture}实现代码...",
        "input_from_previous": ["architecture.md", "data_model.sql"],
    },
    {
        "phase": "review",
        "agent_type": "cursor",
        "prompt_template": "审查{previous.implementation}的代码质量...",
        "human_review": True  # 人工确认节点
    }
]
```

### 5.3 场景3：新Agent接入

#### 5.3.1 接入流程

```
新Agent接入（以Gemini CLI为例）

Step 1: 实现适配器
  - 创建 GeminiCLIAdapter 继承 AgentAdapter
  - 实现 send() - 调用Gemini CLI
  - 实现 health() - 检查进程+token
  - 实现 cost() - Google AI Studio定价
  - 实现 context_sync() - prompt注入
  - 实现 capabilities() - 能力清单

Step 2: 注册Agent
  - 编写配置 YAML
  - 调用 AgentPool.register()
  - 自动健康检查

Step 3: 能力测试
  - 基础功能测试（ping->echo）
  - 上下文同步测试
  - 故障模拟测试
  - 记忆流转测试

Step 4: 路由集成
  - 自动纳入路由决策
  - 权重校准（观察期1周）
  - A/B测试对比
```

#### 5.3.2 适配器开发指南

```python
class NewAgentAdapter(AgentAdapter):
    """新Agent适配器模板"""

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        # 初始化连接

    async def send(self, message: AgentMessage) -> AgentResponse:
        # 1. 转换消息为Agent特定格式
        # 2. 发送请求
        # 3. 转换响应为标准格式
        pass

    async def health(self) -> HealthStatus:
        # 1. 检查进程/API可达性
        # 2. 检查token/配额
        # 3. 返回标准化HealthStatus
        pass

    async def cost(self, task_hint: Dict[str, Any]) -> CostEstimate:
        # 根据Agent定价模型估算
        pass

    async def context_sync(self, direction: SyncDirection,
                          snapshot: ContextSnapshot) -> SyncResult:
        # UPLOAD: 将上下文注入Agent的prompt/system message
        # DOWNLOAD: 从Agent导出当前状态（如支持）
        pass

    def capabilities(self) -> AgentCapabilities:
        # 返回该Agent的完整能力清单
        pass
```


---

## 6. 技术选型

### 6.1 技术选型表

| 组件 | 技术方案 | 备选方案 | 选型理由 |
|------|----------|----------|----------|
| **网关框架** | FastAPI (Python) | Go + Gin | 1. Python生态与AI/ML无缝集成；2. 异步原生支持(async/await)；3. 自动OpenAPI文档；4. 团队招聘Python人才更容易 |
| **记忆存储-工作记忆** | Redis 7+ | Memcached | 1. 支持数据结构（Hash/List）；2. TTL过期机制；3. Pub/Sub支持记忆变更通知；4. Redis Streams做同步队列 |
| **记忆存储-情景记忆** | PostgreSQL + pgvector | ChromaDB/Qdrant | 1. MultiCa已验证pgvector的可靠性；2. SQL生态成熟；3. 向量+关系数据统一查询；4. 事务支持 |
| **记忆存储-语义记忆** | PostgreSQL | SQLite(开发) | 结构化数据存储，与情景记忆同库减少复杂度 |
| **向量嵌入** | OpenAI text-embedding-3-small | 本地BGE-M3 | 1. 1536维度适中；2. 成本低；3. 质量优秀；4. 可切换为本地模型保护隐私 |
| **消息队列** | Redis Streams | RabbitMQ/NATS | 1. 已有Redis依赖，减少组件；2. 支持消费者组；3. 持久化；4. 轻量级 |
| **通信协议** | WebSocket + HTTP REST | gRPC | 1. WebSocket支持实时推送（Agent进度）；2. HTTP REST兼容性好；3. 前端友好；4. gRPC可作为内部优化 |
| **进程管理** | asyncio + subprocess | systemd/Docker | 1. Python原生异步；2. 跨平台；3. 与FastAPI事件循环集成 |
| **配置管理** | Pydantic Settings | YAML/Env | 1. 类型安全；2. 自动验证；3. 环境变量+文件混合 |
| **监控告警** | Prometheus + Grafana | Datadog(付费) | 1. 开源可自托管；2. 与FastAPI集成(metrics中间件)；3. 社区生态丰富 |
| **日志追踪** | structlog + Jaeger | ELK Stack | 1. 结构化日志；2. 分布式追踪；3. 与OpenTelemetry兼容 |
| **部署** | Docker Compose | K8s(后期) | 1. 开发友好；2. 足够支撑早期；3. 后期可平滑迁移K8s |

### 6.2 架构分层技术映射

```
+-------------------------------------------------------+
|  用户界面层                                             |
|  Next.js / React -> 借鉴MultiCa的前端方案              |
+-------------------------------------------------------+
|  网关层（FastAPI）                                      |
|  - API路由 (FastAPI Router)                            |
|  - WebSocket管理 (fastapi.WebSocket)                   |
|  - 依赖注入 (FastAPI DI)                               |
|  - 后台任务 (BackgroundTasks / Celery)                |
+-------------------------------------------------------+
|  核心引擎层（Python asyncio）                            |
|  - AgentAdapter (抽象基类 + 具体实现)                   |
|  - ContextBridge (上下文桥接)                          |
|  - MemoryHub (记忆中心)                                 |
|  - RouterEngine (路由引擎)                              |
+-------------------------------------------------------+
|  存储层                                                 |
|  - Redis (工作记忆 + 队列 + Pub/Sub)                    |
|  - PostgreSQL + pgvector (情景记忆 + 语义记忆)          |
|  - 本地文件 (MEMORY.md 过程记忆)                       |
+-------------------------------------------------------+
|  外部Agent层                                            |
|  - Claude Code (CLI subprocess)                       |
|  - Codex (HTTP API)                                   |
|  - Cursor (Extension API / 文件监控)                  |
|  - OpenClaw (Gateway API)                             |
|  - Hermes (HTTP API + SQLite)                         |
+-------------------------------------------------------+
```

### 6.3 为什么不用Go而用Python

MultiCa后端用Go，我们选Python，理由如下：

| 对比维度 | Go | Python |
|----------|-----|--------|
| AI生态 | 弱（无主流ML库） | 强（LangChain/LlamaIndex/OpenAI SDK） |
| 异步 | goroutine（性能强） | asyncio（够用） |
| 开发速度 | 中等 | 快（动态类型+丰富库） |
| 人才市场 | 较少（偏基础设施） | 多（AI/数据方向） |
| 与Agent集成 | 需额外桥接 | 直接调用SDK |
| 长期演进 | 偏基础设施 | 可扩展ML能力 |

**决策**：Gateway用Python，但性能敏感部分（如向量检索）可委托给专用服务。

---

## 7. 与QClaw/OpenClaw的集成方案

### 7.1 OpenClaw架构回顾

OpenClaw是开源框架（372K stars），包含四个模块：

| 模块 | 功能 | 我们如何利用 |
|------|------|-------------|
| **Gateway** | Agent入口网关 | 作为基础参考，扩展为多Agent路由 |
| **Agent** | Agent执行引擎 | 作为下游Agent之一接入 |
| **Skills** | 技能系统（5000+） | 直接复用SKILL.md标准 |
| **Memory** | MEMORY.md长期记忆 | 作为语义记忆层的实现方式 |

### 7.2 集成策略

#### 7.2.1 利用OpenClaw的Gateway

OpenClaw的Gateway是单体入口，我们的Gateway是多Agent路由。集成方式：

```python
class OpenClawGatewayAdapter(AgentAdapter):
    """将OpenClaw Gateway作为下游Agent接入"""

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        self.openclaw_api = config["gateway_url"]  # http://localhost:3000

    async def send(self, message: AgentMessage) -> AgentResponse:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.openclaw_api}/api/tasks",
                json={
                    "message": message.content,
                    "context": message.context_hint,
                    "mode": "act"  # OpenClaw支持plan/act/boomerang模式
                }
            ) as resp:
                data = await resp.json()
                return AgentResponse(
                    content=data["response"],
                    message_type=MessageType.COMPLETION
                )
```

#### 7.2.2 利用OpenClaw的Skills系统

OpenClaw的Skills是SKILL.md文件，标准化了技能定义。我们可以在记忆层集成：

```yaml
---
name: write_sql_migration
description: 编写数据库迁移脚本
tools: [read_file, write_file, execute_sql]
---

## 执行步骤
1. 读取当前schema
2. 分析变更需求
3. 编写up.sql和down.sql
4. 在测试数据库验证
```

我们的集成方式：
1. Skills作为**过程记忆**的一部分存储
2. Agent执行前检索相关Skills
3. 通过skills_apply标记记录哪些Skill被使用过

#### 7.2.3 利用OpenClaw的Memory机制

OpenClaw的MEMORY.md是优秀的长期记忆实现，我们直接兼容：

```
项目根目录/
  .memory/                    # 我们的统一记忆目录
    episodic/                # 情景记忆（自动生成的任务记录）
    semantic/                # 语义记忆（结构化数据）
    procedural/              # 过程记忆
      MEMORY.md             # 与OpenClaw格式兼容
        - User Preferences
        - Project Conventions
        - Common Pitfalls
        - Known Issues
```

**双向同步**：
- OpenClaw修改MEMORY.md -> 文件系统监控 -> 自动同步到语义记忆
- 我们的系统新增记忆 -> 写入MEMORY.md -> OpenClaw立即可用

### 7.3 QClaw作为本地执行端

QClaw（本地版OpenClaw）可以作为我们的本地执行端：

```
用户请求 -> AgentGateway -> 路由决策 -> QClaw（本地）
                                      -> Codex（云端）
                                      -> Claude Code（本地CLI）
```

QClaw的优势：
- 本地执行，数据不上云（安全）
- 可以访问本地文件系统
- 可以作为fallback（所有云端Agent都不可用时）

---

## 8. 项目里程碑

### 8.1 三阶段规划

#### MVP阶段（4周）—— 证明核心场景

| 周次 | 目标 | 交付物 | 关键验证 |
|------|------|--------|----------|
| W1 | 基础框架搭建 | FastAPI项目骨架 + AgentAdapter接口 | 技术栈可行性 |
| W1-2 | Claude Code适配器 | 完整ClaudeCodeAdapter实现 | 能发消息、能健康检查 |
| W2-3 | Codex适配器 | 完整CodexAdapter实现 | 能发消息、能健康检查 |
| W3 | 基础路由引擎 | RouterEngine + 故障转移 | 能自动切换 |
| W3-4 | 上下文接续 v1 | ContextBridge + TaskState | **Claude->Codex切换不丢上下文** |
| W4 | 记忆层 v1 | Redis工作记忆 + 基础MemoryHub | 记忆能写入和读取 |

**MVP成功标准**：Claude Code token耗尽后，10秒内自动切换到Codex，用户感受不到上下文丢失。

#### 完整版（8周）—— 产品可用

| 周次 | 目标 | 交付物 |
|------|------|--------|
| W5 | 6个Agent适配器 | Cursor + OpenClaw + Hermes + 自定义Agent |
| W5-6 | 四层记忆架构 | 工作+情景+语义+过程记忆全部实现 |
| W6 | 向量检索 | pgvector集成 + 记忆语义检索 |
| W7 | Pipeline编排 | 多阶段任务自动分配Agent |
| W7-8 | Web控制台 | Next.js前端（看板+配置+监控） |

#### 企业版（12周）—— 生产就绪

| 周次 | 目标 | 交付物 |
|------|------|--------|
| W9 | 监控治理 | Prometheus + Grafana + 告警 |
| W9-10 | 安全控制 | 权限管理 + 审计日志 + 敏感信息过滤 |
| W10-11 | 企业级记忆 | 团队共享记忆 + 记忆权限 + 记忆版本 |
| W11-12 | 性能优化 | 连接池 + 缓存 + 批量处理 + 压测 |

### 8.2 学习路线图映射

| 学习阶段 | 对应开发阶段 | 实践内容 |
|----------|-------------|----------|
| FastAPI基础 | W1 | 搭建Gateway框架，理解async/await |
| Agent模式 | W2-3 | 实现Adapter模式，理解不同Agent接口 |
| PostgreSQL+向量 | W5-6 | pgvector集成，理解向量检索原理 |
| Redis+消息队列 | W3-4 | 工作记忆+同步队列实现 |
| 系统设计 | W7 | Pipeline编排+状态机设计 |
| 前端开发 | W7-8 | Next.js Web控制台 |

---

## 9. 代码实现示例

### 9.1 核心模块使用示例

```python
#!/usr/bin/env python3
"""
AgentGateway 完整使用示例
演示：Claude Code没token -> 自动切换到Codex
"""

import asyncio
from datetime import datetime


async def main():
    # 1. 初始化组件
    memory_hub = MemoryHub(
        redis_url="redis://localhost:6379",
        pg_url="postgresql://user:pass@localhost/agent_memory"
    )
    await memory_hub.initialize()

    agent_pool = AgentPool()
    context_bridge = ContextBridge(memory_hub=memory_hub)
    router = RouterEngine(
        agent_pool=agent_pool,
        memory_hub=memory_hub
    )
    await router.start()

    # 2. 注册Agent
    agent_pool.register(ClaudeCodeAdapter("claude-code", {
        "cli_path": "claude",
        "project_dir": "/home/user/myproject",
        "api_key": "sk-ant-xxxxx"
    }))

    agent_pool.register(CodexAdapter("codex", {
        "api_key": "sk-openai-xxxxx",
        "model": "codex-latest"
    }))

    # 3. 模拟任务执行
    task_id = "task-2025-001"
    task = {
        "type": "coding",
        "description": "优化API性能，解决N+1查询问题",
        "estimated_tokens": 8000,
        "languages": ["python"]
    }

    # 4. 路由选择Agent
    selected_agent_id = await router.route(task)
    print(f"[Gateway] 选择Agent: {selected_agent_id}")

    agent = agent_pool.get(selected_agent_id)

    # 5. 执行任务（正常流程）
    print("[Gateway] 开始执行任务...")
    response = await agent.send(AgentMessage(
        content="请分析API性能瓶颈",
        metadata={"system_prompt": "你是一个API优化专家"}
    ))
    print(f"[Claude] {response.content[:200]}...")

    # 6. 模拟token耗尽故障
    print("[Gateway] 模拟Claude Code token耗尽...")
    await router.report_failure("claude-code", "token耗尽模拟")

    # 7. 自动切换流程
    print("[Gateway] 触发紧急上下文保存...")
    snapshot = await context_bridge.capture(task_id, agent)
    persisted = await context_bridge.persist(task_id, priority="critical")
    print(f"[Gateway] 上下文持久化: {'成功' if persisted else '失败'}")

    # 8. 路由重决策（排除claude-code）
    print("[Gateway] 重新路由（排除claude-code）...")
    new_agent_id = await router.route(task, exclude=["claude-code"])
    print(f"[Gateway] 新Agent: {new_agent_id}")

    new_agent = agent_pool.get(new_agent_id)

    # 9. 恢复上下文
    print("[Gateway] 恢复上下文到新Agent...")
    context_prompt = await context_bridge.restore(task_id, new_agent)
    print(f"[Gateway] 上下文大小: {len(context_prompt)} chars")

    # 10. 任务接续
    print("[Gateway] 任务接续执行...")
    response = await new_agent.send(AgentMessage(
        content="请基于之前的分析继续优化",
        metadata={"system_prompt": context_prompt}
    ))
    print(f"[Codex] {response.content[:200]}...")

    # 11. 清理
    await router.stop()
    print("[Gateway] 任务完成!")


if __name__ == "__main__":
    asyncio.run(main())
```

### 9.2 启动脚本

```python
#!/usr/bin/env python3
"""AgentGateway 启动脚本"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def bootstrap():
    """启动AgentGateway"""

    # 初始化记忆中心
    memory_hub = MemoryHub(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        pg_url=os.getenv("DATABASE_URL", "postgresql://localhost/agent_memory")
    )
    await memory_hub.initialize()
    print("[Bootstrap] MemoryHub 初始化完成")

    # 初始化Agent池
    agent_pool = AgentPool()

    # 注册Claude Code（如果配置存在）
    if os.getenv("CLAUDE_CODE_ENABLED") == "true":
        agent_pool.register(ClaudeCodeAdapter("claude-code", {
            "cli_path": os.getenv("CLAUDE_PATH", "claude"),
            "api_key": os.getenv("ANTHROPIC_API_KEY")
        }))
        print("[Bootstrap] Claude Code 已注册")

    # 注册Codex（如果配置存在）
    if os.getenv("CODEX_ENABLED") == "true":
        agent_pool.register(CodexAdapter("codex", {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "model": os.getenv("CODEX_MODEL", "codex-latest")
        }))
        print("[Bootstrap] Codex 已注册")

    # 注册Cursor（如果配置存在）
    if os.getenv("CURSOR_ENABLED") == "true":
        agent_pool.register(CursorAdapter("cursor", {
            "extension_port": int(os.getenv("CURSOR_PORT", "37182"))
        }))
        print("[Bootstrap] Cursor 已注册")

    # 初始化路由引擎
    router = RouterEngine(
        agent_pool=agent_pool,
        memory_hub=memory_hub,
        config=RouterConfig(
            weights={
                "availability": 0.30,
                "cost": 0.15,
                "capability": 0.25,
                "speed": 0.10,
                "memory": 0.10,
                "success_rate": 0.10
            }
        )
    )
    await router.start()
    print("[Bootstrap] RouterEngine 已启动")

    # 启动健康检查
    healthy_agents = await agent_pool.available_agents()
    print(f"[Bootstrap] 可用Agent: {[a.agent_id for a in healthy_agents]}")

    return {
        "memory_hub": memory_hub,
        "agent_pool": agent_pool,
        "router": router,
        "context_bridge": ContextBridge(memory_hub=memory_hub)
    }


if __name__ == "__main__":
    components = asyncio.run(bootstrap())
    print("[Bootstrap] AgentGateway 启动完成!")
```


---

## 10. 面试话术

### 10.1 项目介绍（3分钟版本）

> "我正在设计一个**基于记忆增强的Agent统一入口框架**，对标MultiCa但做差异化。
>
> **痛点**：开发者现在用AI编程时要在Claude Code、Codex、Cursor之间切来切去，每个Agent各管一段，记忆完全不共享。比如你在Claude Code里讨论了半小时的架构方案，切换到Codex后要重新说一遍。
>
> **我们的方案**：做一个Agent Gateway，统一接入所有Agent，核心能力是**跨Agent记忆共享和任务接续**。比如Claude Code突然没token了，我们能在10秒内自动切换到Codex，把完整的上下文（对话摘要、代码变更、关键决策）全部带过去，用户几乎感知不到切换。
>
> **技术亮点**：
> 1. **适配器模式**——每个Agent一个Adapter，统一接口屏蔽差异
> 2. **四层记忆架构**——工作记忆(REDIS) + 情景记忆(向量检索) + 语义记忆(结构化) + 过程记忆(MEMORY.md)
> 3. **ContextBridge**——上下文捕获->压缩->传输->恢复的全流程，这是技术核心
> 4. **智能路由**——多维度评分（可用性、成本、能力、记忆亲和度），自动故障转移
>
> **对标MultiCa**：MultiCa管'人'（Agent身份和任务分配），我们管'脑'（跨Agent记忆和上下文连续性）。记忆层的护城河更深，因为记忆资产有复利效应——用得越久，Agent越懂你，迁移成本越高。"

### 10.2 竞品分析话术

**关于MultiCa**：

> "MultiCa是26K stars的开源Agent管理平台，作者Jiayuan Zhang，字节背景。它的定位是AI版Linear/Jira——把Agent当成团队成员管理，有看板、Squads、Skills沉淀。
>
> **MultiCa做得好的地方**：
> - Agent身份系统设计成熟（名字、档案、专长标签）
> - Daemon架构实现云端管理+本地执行混合模式
> - Skills向量检索实现经验复用
> - 看板式UI直观管理多Agent任务
>
> **MultiCa的短板（我们的机会）**：
> - **没有持久记忆**：Agent每次执行任务都是无状态的，上下文随进程退出丢失
> - **不支持Agent切换**：没有故障转移机制，一个Agent挂了任务就断了
> - **记忆只是项目级Skills**：没有用户级、跨Agent的个人记忆
>
> 我们的差异化是**以记忆为核心抽象**（MultiCa以任务为核心），解决Agent切换时的上下文连续性问题。"

### 10.3 技术难点话术

**上下文接续的难点**：

> "上下文接续是项目的核心难点，主要挑战有三：
>
> **第一，上下文压缩**。不同Agent的token限制不同（Claude Code 200K, Codex 128K），切换时需要在有限token内传递最关键的信息。我们的策略是分层摘要——决策层保留全部，对话层保留摘要，代码层保留文件列表+变更摘要。
>
> **第二，状态一致性**。切换过程中如果新Agent也失败了怎么办？我们采用'先持久化再切换'的策略——上下文先同步写入Redis+PostgreSQL双重确认，再启动新Agent。最坏情况也能从持久化存储恢复。
>
> **第三，Agent行为差异**。不同Agent的代码风格、输出格式不同。我们通过语义记忆层存储用户偏好的代码规范，切换时作为system prompt注入，保证风格一致性。"

**跨Agent记忆共享的难点**：

> "跨Agent记忆共享涉及两个问题：格式统一和隐私控制。
>
> **格式统一**：Claude Code用ANSI文本，Codex用JSON，Cursor用结构化数据。我们的方案是在网关层做统一抽象——每个Agent通过Adapter转换为标准格式（AgentMessage/AgentResponse），记忆层只处理标准格式。
>
> **隐私控制**：哪些记忆可以跨Agent共享？我们设计了三级隐私——Public（项目规范，所有Agent可见）、Agent-Specific（API Key等敏感信息不共享）、Private（仅用户可见）。默认代码风格和架构决策是Public的。"

**记忆存储设计**：

> "我们采用四层记忆架构，每层对应不同的存储和检索需求：
>
> - **工作记忆**用Redis，24小时TTL，存当前任务的实时状态
> - **情景记忆**用PostgreSQL+pgvector，永久保存，向量相似度检索找相关历史任务
> - **语义记忆**用PostgreSQL结构化表，存用户偏好和项目决策
> - **过程记忆**用MEMORY.md文件，与OpenClaw生态兼容
>
> 这种分层设计的优势是各层独立扩展——工作内存要求高吞吐用Redis，情景记忆要求语义检索用向量库，语义记忆要求精确查询用SQL。"

**技术亮点总结（一句话）**：

> "这个项目的本质是**给碎片化的Agent生态加一层分布式记忆系统**，让AI Agent从'用完即走'变成'越用越懂你'。"

---

## 附录A：核心数据流图

```
+----------+     send()      +--------------+     adapter.send()     +----------+
|          | ---------------> |              | --------------------> |          |
|   用户    |                  |   Gateway    |                        | Claude   |
|          | <--------------- |              | <-------------------- | Code     |
+----------+     响应          +------+-------+     adapter.recv()     +----------+
                                 |
                                 | 故障检测
                                 v
                          +--------------+
                          |   Router     | -- health() --> 所有Agent监控
                          |   Engine     |
                          +------+-------+
                                 |
                                 | 切换决策
                                 v
                          +--------------+
                          |  Context     | -- capture() --> 原Agent导出
                          |  Bridge      | -- persist() --> MemoryHub保存
                          |              | -- restore() --> 新Agent注入
                          +------+-------+
                                 |
                                 v
                +-------------------------------+
                |       MemoryHub                |
                |  +----+  +----+  +----+       |
                |  |工作|  |情景|  |语义|       |
                |  |记忆|  |记忆|  |记忆|       |
                |  |Redis| |PG+ | |PG  |       |
                |  |     | |vctr| |    |       |
                |  +----+  +----+  +----+       |
                +-------------------------------+
```

## 附录B：术语表

| 术语 | 英文 | 定义 |
|------|------|------|
| Agent适配器 | AgentAdapter | 统一Agent接入的抽象接口 |
| 上下文桥接 | ContextBridge | Agent切换时的上下文传输组件 |
| 上下文快照 | ContextSnapshot | 任务执行状态的完整快照 |
| 记忆中心 | MemoryHub | 统一记忆管理组件 |
| 路由引擎 | RouterEngine | 智能选择Agent的决策组件 |
| 工作记忆 | Working Memory | 当前任务的实时状态（Redis） |
| 情景记忆 | Episodic Memory | 过往任务记录（向量检索） |
| 语义记忆 | Semantic Memory | 用户偏好和项目规范（结构化） |
| 过程记忆 | Procedural Memory | 工作流模板和最佳实践 |
| 任务接续 | Task Continuation | 跨Agent保持任务上下文连续 |

## 附录C：文件清单

```
agent-gateway/
├── gateway/                    # FastAPI网关
│   ├── __init__.py
│   ├── main.py                 # 应用入口
│   ├── routers/                # API路由
│   │   ├── tasks.py            # 任务管理
│   │   ├── agents.py           # Agent管理
│   │   └── memory.py           # 记忆查询
│   └── websocket.py            # WebSocket实时推送
├── core/                       # 核心引擎
│   ├── __init__.py
│   ├── adapter.py              # AgentAdapter抽象基类
│   ├── adapters/               # 具体适配器
│   │   ├── __init__.py
│   │   ├── claude_code.py      # Claude Code适配器
│   │   ├── codex.py            # Codex适配器
│   │   ├── cursor.py           # Cursor适配器
│   │   └── openclaw.py         # OpenClaw适配器
│   ├── context_bridge.py       # 上下文桥接
│   ├── memory_hub.py           # 记忆中心
│   ├── router_engine.py        # 路由引擎
│   └── pipeline.py             # Pipeline编排
├── models/                     # 数据模型
│   ├── __init__.py
│   ├── message.py              # 消息模型
│   ├── snapshot.py             # 上下文快照
│   ├── memory.py               # 记忆模型
│   └── health.py               # 健康状态模型
├── storage/                    # 存储层
│   ├── __init__.py
│   ├── redis_store.py          # Redis工作记忆
│   ├── pg_store.py             # PostgreSQL持久记忆
│   └── vector_store.py         # pgvector向量检索
├── config/                     # 配置
│   ├── __init__.py
│   └── settings.py             # Pydantic Settings
├── tests/                      # 测试
│   ├── test_adapter.py
│   ├── test_context_bridge.py
│   ├── test_router.py
│   └── test_memory_hub.py
├── docker-compose.yml          # Docker部署
├── requirements.txt            # Python依赖
└── README.md                   # 项目说明
```

---

## 附录D：与MultiCa的全面对比

| 维度 | MultiCa | 本项目（记忆增强框架） | 优劣分析 |
|------|---------|---------------------|----------|
| **定位** | AI版Linear/Jira | 分布式Agent记忆系统 | 互补定位 |
| **目标用户** | 开发团队管理者 | 个人开发者 | 更大用户基数 |
| **核心能力** | Agent管理+任务看板 | 记忆增强+上下文接续 | 差异化竞争 |
| **技术栈** | Go+Next.js+PostgreSQL | Python+Next.js+PostgreSQL | Python AI生态更强 |
| **架构模式** | Daemon轮询 | 事件驱动+WebSocket | 更实时 |
| **Agent数量** | 最多20个 | 理论上无限 | 可扩展性更强 |
| **记忆能力** | 无持久记忆 | 四层记忆架构 | **核心优势** |
| **故障转移** | 不支持 | 自动切换+任务接续 | **核心优势** |
| **Skills** | 向量检索复用 | 集成OpenClaw+自学习 | 生态兼容 |
| **开源协议** | 开源 | 开源 | 共同推动生态 |
| **商业化路径** | 托管SaaS | 个人免费+企业版 | 类似路径 |

---

> **文档结束**
>
> 本文档为《软件工程全生命周期Agent实战项目设计》的重要补充，聚焦Agent统一入口与记忆增强的技术架构。
>
> 核心定位：**基于记忆增强的Agent统一入口框架，对标MultiCa，解决Agent碎片化与记忆断层痛点。**
>
> 关键场景：Claude Code没token -> 10秒内自动切换到Codex -> 完整上下文保留 -> 任务无缝接续。
