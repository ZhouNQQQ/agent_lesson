# 阶段三：Multi-Agent 与任务编排 — 完整学习资料

> 文档来源：基于 OpenClaw 官方文档（multi-agent、session、session-tool、taskflow、agents、flows、tasks、acp）整理
> 适用对象：已完成阶段一 + 阶段二模块一的开发者
> 学习周期：2–3 周

---

## 目录

1. [为什么需要 Multi-Agent](#1-为什么需要-multi-agent)
2. [OpenClaw 多 Agent 核心架构](#2-openclaw-多-agent-核心架构)
3. [四种协作模式详解](#3-四种协作模式详解)
4. [核心 API：跨会话工具](#4-核心-api跨会话工具)
5. [Agent 隔离与路由](#5-agent-隔离与路由)
6. [TaskFlow：工作流编排](#6-taskflow工作流编排)
7. [后台任务与生命周期](#7-后台任务与生命周期)
8. [ACP Harness：外部编码代理](#8-acp-harness外部编码代理)
9. [实战演练：构建一个多 Agent 系统](#9-实战演练构建一个多-agent-系统)
10. [配置参考](#10-配置参考)
11. [常见问题与调试](#11-常见问题与调试)
12. [与 Manus / Claude Code / Cursor / OpenHuman 的关系](#12-与-manus--claude-code--cursor--openhuman-的关系)

---

## 1. 为什么需要 Multi-Agent

### 1.1 单 Agent 的瓶颈

一个 Agent 可以处理简单任务，但遇到复杂任务时会遇到：

| 问题 | 表现 |
|------|------|
| 上下文爆炸 | 长期任务导致 token 消耗过高，推理质量下降 |
| 工具冲突 | 不同任务需要不同的工具权限，混在一起容易出错 |
| 专业分工不足 | 代码审查、文案写作、数据分析混在一起，每个都不精 |
| 并发低效 | 串行处理多个子任务，浪费时间 |
| 故障扩散 | 一个子任务失败，整个会话崩溃 |

### 1.2 Multi-Agent 的解决思路

把复杂任务拆成多个子任务，每个子任务交给专门的 Agent 处理：

- **Supervisor（监督者）**：中央调度，拆解任务 → 分配给 Worker
- **Worker（工作者）**：各自专注一个领域（代码、文案、数据）
- **Router（路由器）**：根据任务类型自动分发到对应 Agent
- **Pipeline（流水线）**：串行处理，每个阶段一个 Agent
- **Parallel（并行）**：多个 Agent 同时处理不同子任务

### 1.3 类比

想象一个餐厅：
- 单 Agent = 一个人既要接待、又要做菜、又要洗碗、又要收银
- Multi-Agent = 前台（接待）、厨师（做菜）、洗碗工（洗碗）、收银员（收银），各干各的，通过订单单（message）协调

---

## 2. OpenClaw 多 Agent 核心架构

### 2.1 核心概念

| 概念 | 含义 | 对应文件/命令 |
|------|------|--------------|
| **Agent** | 一个独立的智能体，有自己的工具集、配置、记忆 | `~/.openclaw/agents/<agentId>/` |
| **Session** | 一次对话上下文，是 Agent 的"运行时实例" | `~/.openclaw/agents/<agentId>/sessions/` |
| **Session Key** | 会话标识符，格式 `agent:<agentId>:<sessionId>` | `agent:main:main`, `agent:code:session-1` |
| **Binding** | 把会话固定到某个 Agent 的特定工具集 | 自动根据 agentId 绑定 |
| **Workspace** | 每个 Agent 的独立工作目录（文件隔离） | `agents.defaults.workspace` |
| **Sub-agent** | 由父 Agent 通过 `sessions_spawn` 创建的子会话 | 运行时创建，非持久化 |
| **ACP Harness** | 外部编码代理（Codex、Claude Code、Cursor） | `sessions_spawn runtime="acp"` |
| **TaskFlow** | 持久化工作流编排层，协调多个任务 | `~/.openclaw/tasks/` |
| **Task** | 后台任务记录（跟踪 detached work 的状态） | `openclaw tasks list` |

### 2.2 架构图（逻辑关系）

```
┌─────────────────────────────────────────────────────────┐
│                    Gateway（网关）                        │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │
│  │ Agent A │  │ Agent B │  │ Agent C │  │ Agent D │    │
│  │ (main)  │  │ (code)  │  │ (write) │  │ (data)  │    │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘    │
│       │            │            │            │         │
│  ┌────┴────┐  ┌────┴────┐  ┌────┴────┐  ┌────┴────┐   │
│  │ Session │  │ Session │  │ Session │  │ Session │   │
│  │ main    │  │ main    │  │ main    │  │ main    │   │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘   │
│       │            │            │            │         │
│       └────────────┴────────────┴────────────┘         │
│                        ↑                               │
│                   sessions_send / sessions_spawn        │
│                    （跨会话通信）                        │
└─────────────────────────────────────────────────────────┘
```

### 2.3 与 Microservices 的类比

| 微服务 | Multi-Agent |
|--------|-------------|
| 服务发现 | Agent 列表 + bindings |
| 服务间通信 | `sessions_send`（异步消息） |
| 负载均衡 | 手动分配 or Router 模式 |
| 熔断/隔离 | 每个子 Agent 独立 session，失败不影响父级 |
| 日志/监控 | `tasks list` + `sessions_history` |
| 部署 | `agents add` + `agents bind` |

---

## 3. 四种协作模式详解

### 3.1 Supervisor（监督者模式）

**核心思想**：一个中央 Agent 接收任务，拆解后分配给 Worker Agent，收集结果后汇总。

```
用户请求 → Supervisor Agent → 拆解任务
                              ↓
                    ┌────────┼────────┐
                    ↓        ↓        ↓
                 Worker1  Worker2  Worker3
                 (编码)   (文案)   (数据)
                    └────────┼────────┘
                              ↓
                        收集结果 → 汇总 → 返回用户
```

**OpenClaw 实现**：

```javascript
// Supervisor Agent 中
// 1. 分析任务，决定需要哪些 Worker
const tasks = analyzeTask(userRequest); // [{type: 'code', desc: '...'}, {type: 'write', desc: '...'}]

// 2. 并行 spawn 多个 Worker
const spawns = await Promise.all(tasks.map(t => 
  sessions_spawn({
    runtime: 'subagent',
    task: t.desc,
    model: t.type === 'code' ? 'kimi-k2p6' : 'kimi-k2p6'
  })
));

// 3. 等待结果（通过 sessions_yield 避免轮询）
sessions_yield();
// 结果会在下一个消息中到达

// 4. 汇总结果
const results = collectResults(spawns);
return summarize(results);
```

**适用场景**：复杂任务需要多个领域协作，如"开发一个带数据分析的 Web 应用"。

---

### 3.2 Router（路由模式）

**核心思想**：根据任务类型自动路由到对应专业 Agent。

```
用户请求 → Router Agent（分析意图）
              ↓
    ┌─────────┼─────────┐
    ↓         ↓         ↓
  CodeAgent WriteAgent  DataAgent
  代码任务   文案任务    数据任务
```

**OpenClaw 实现**：

```javascript
// Router Agent 中
function routeTask(request) {
  if (request.includes('代码') || request.includes('bug') || request.includes('PR')) {
    return 'agent:code:main';
  } else if (request.includes('文案') || request.includes('文章') || request.includes('翻译')) {
    return 'agent:write:main';
  } else if (request.includes('数据') || request.includes('分析') || request.includes('报表')) {
    return 'agent:data:main';
  } else {
    return 'agent:main:main'; // fallback
  }
}

const targetSession = routeTask(userRequest);
const result = await sessions_send({
  sessionKey: targetSession,
  message: userRequest,
  timeoutSeconds: 60
});
return result;
```

**适用场景**：用户请求类型多样，需要自动分发到专业 Agent，如客服系统、支持平台。

---

### 3.3 Pipeline（流水线模式）

**核心思想**：任务按阶段串行处理，每个阶段由一个 Agent 负责，输出作为下一个阶段的输入。

```
Stage 1 → Stage 2 → Stage 3 → Stage 4
(需求分析) (设计)   (编码)   (测试)
```

**OpenClaw 实现**：

```javascript
// Pipeline Agent 中
async function runPipeline(task) {
  // Stage 1: 需求分析
  const requirements = await sessions_send({
    sessionKey: 'agent:analysis:main',
    message: `分析需求：${task}`,
    timeoutSeconds: 30
  });

  // Stage 2: 设计
  const design = await sessions_send({
    sessionKey: 'agent:design:main',
    message: `基于以下需求进行设计：${requirements}`,
    timeoutSeconds: 30
  });

  // Stage 3: 编码
  const code = await sessions_send({
    sessionKey: 'agent:code:main',
    message: `基于以下设计实现代码：${design}`,
    timeoutSeconds: 60
  });

  // Stage 4: 测试
  const testResult = await sessions_send({
    sessionKey: 'agent:qa:main',
    message: `测试以下代码：${code}`,
    timeoutSeconds: 30
  });

  return { requirements, design, code, testResult };
}
```

**适用场景**：软件开发流程、内容生产流程（选题→大纲→写作→编辑→发布）。

**关键注意事项**：
- 每个 Stage 必须等前一个完成，不能并行
- 中间结果过大时要考虑截断或摘要
- 错误处理：任一 Stage 失败，Pipeline 中断或重试

---

### 3.4 Parallel（并行模式）

**核心思想**：多个 Agent 同时处理同一个任务的不同维度，结果汇总。

```
用户请求
    ↓
┌───┼───┐
↓   ↓   ↓
A1  A2  A3
(安全审计) (性能分析) (代码风格)
    ↓
  汇总报告
```

**OpenClaw 实现**：

```javascript
// Parallel Agent 中
async function runParallel(task) {
  const workers = [
    { key: 'agent:security:main', prompt: `安全审计：${task}` },
    { key: 'agent:performance:main', prompt: `性能分析：${task}` },
    { key: 'agent:style:main', prompt: `代码风格检查：${task}` }
  ];

  // 同时 spawn，不等待
  const spawns = workers.map(w => sessions_send({
    sessionKey: w.key,
    message: w.prompt,
    timeoutSeconds: 60
  }));

  // Promise.all 等待全部完成
  const results = await Promise.all(spawns);

  return mergeResults(results);
}
```

**适用场景**：代码审查（多维度同时检查）、数据报表（多维度同时分析）、A/B 测试方案生成。

---

### 3.5 模式对比总结

| 模式 | 并发性 | 复杂度 | 容错性 | 适用场景 |
|------|--------|--------|--------|----------|
| Supervisor | 并行 | 高 | 中（Worker 失败可重试） | 复杂项目拆解 |
| Router | 串行 | 低 | 高（单一 Agent 处理） | 请求分发 |
| Pipeline | 串行 | 中 | 低（任一阶段失败全断） | 流程化任务 |
| Parallel | 并行 | 中 | 高（部分失败可忽略） | 多维度分析 |

---

## 4. 核心 API：跨会话工具

### 4.1 工具总览

| 工具 | 用途 | 是否阻塞 | 典型场景 |
|------|------|----------|----------|
| `sessions_list` | 列出所有可见会话 | 是 | 查看有哪些 Agent 在运行 |
| `sessions_history` | 读取某个会话的历史 | 是 | 检查 Worker 做了什么 |
| `sessions_send` | 向另一个会话发消息 | 可选等待 | 请求其他 Agent 处理任务 |
| `sessions_spawn` | 创建子 Agent 会话 | 否（立即返回） | 启动后台 Worker |
| `sessions_yield` | 结束当前 turn，等待后续 | 是 | spawn 后等待子 Agent 完成 |
| `subagents` | 管理已 spawn 的子 Agent | 是 | 查看/终止/干预子 Agent |
| `session_status` | 查看会话状态 | 是 | 检查 token 消耗、模型等 |

### 4.2 sessions_spawn（创建子 Agent）

```typescript
// 完整参数签名
sessions_spawn({
  runtime: 'subagent' | 'acp',      // 默认 subagent，acp 用于外部编码代理
  task: string,                      // 任务描述（必填）
  mode: 'run' | 'session',           // run=一次性，session=持久（默认 run）
  model: string,                     // 覆盖模型，如 'kimi-k2p6'
  thinking: string,                 // 覆盖思考级别
  sandbox: 'inherit' | 'require',    // 是否强制沙箱
  thread: boolean,                   // 绑定到聊天线程（Discord/Slack 等）
  timeoutSeconds: number,            // 超时时间
  attachments: Array<{name, content, mimeType}>, // 初始附件
  cwd: string,                      // 工作目录
  label: string,                     // 会话标签
});
```

**返回**：`{ runId, childSessionKey }`

**示例**：

```javascript
// 基础用法：启动一个后台任务
const result = await sessions_spawn({
  runtime: 'subagent',
  task: '分析这个 Python 项目的依赖安全性',
  timeoutSeconds: 120
});
// result: { runId: 'run-abc123', childSessionKey: 'agent:main:sub-xyz' }

// 使用 sessions_yield 等待结果
await sessions_yield();
// 子 Agent 完成后，结果会以新消息到达
```

**关键注意事项**：
- `sessions_spawn` 永远是**非阻塞**的，立即返回
- 不要创建轮询循环（`while` + `sleep`），用 `sessions_yield` 等待
- 完成时系统会**自动推送**结果到父会话（或指定频道）
- `mode: 'session'` 用于需要多轮对话的持久子 Agent
- `thread: true` 在 Discord/Slack 等频道中创建线程绑定

---

### 4.3 sessions_send（跨会话通信）

```typescript
sessions_send({
  sessionKey: string,        // 目标会话 key（如 'agent:code:main'）
  message: string,           // 发送的消息内容
  timeoutSeconds: number,    // 0=fire-and-forget，>0=等待回复
  label: string,             // 替代 sessionKey 的标签定位
});
```

**示例**：

```javascript
// 同步等待回复（阻塞式）
const result = await sessions_send({
  sessionKey: 'agent:code:main',
  message: '帮我 review 这个函数的并发安全性',
  timeoutSeconds: 60
});
// result 包含目标 Agent 的回复文本

// 异步发送（fire-and-forget）
await sessions_send({
  sessionKey: 'agent:write:main',
  message: '写一篇关于 Redis 缓存穿透的文章',
  timeoutSeconds: 0
});
// 不等待，立即返回
```

**Reply-back loop**：
- 目标 Agent 回复后，父 Agent 可以再次回复（最多 5 轮交替）
- 目标 Agent 回复 `REPLY_SKIP` 可提前终止循环

---

### 4.4 subagents（子 Agent 管理）

```typescript
subagents({
  action: 'list' | 'steer' | 'kill',
  target: string,            // 子 Agent 的 runId 或 sessionKey（kill/steer 时用）
  message: string,            // steer 时发送的干预消息
});
```

**示例**：

```javascript
// 列出当前会话的所有子 Agent
const active = await subagents({ action: 'list' });
// 返回：[{ runId, childSessionKey, status, startTime, ... }]

// 终止一个子 Agent
await subagents({ action: 'kill', target: 'run-abc123' });

// 给运行中的子 Agent 发送干预指令
await subagents({
  action: 'steer',
  target: 'run-abc123',
  message: '注意：用户要求改成 REST API 而不是 GraphQL'
});
```

---

### 4.5 sessions_yield（避免轮询）

```typescript
sessions_yield({ message?: string });
```

**核心作用**：主动结束当前 turn，让后续消息（如子 Agent 完成通知）作为下一轮输入。

**正确用法**：

```javascript
// ❌ 错误：轮询循环
while (true) {
  const status = await subagents({ action: 'list' });
  if (status.find(s => s.runId === runId)?.status === 'succeeded') break;
  await sleep(5000); // 浪费 API 调用
}

// ✅ 正确：yield 等待
const { runId } = await sessions_spawn({ task: '...' });
await sessions_yield();
// 子 Agent 完成后，系统会自动唤醒当前会话，结果作为下一条消息到达
```

---

## 5. Agent 隔离与路由

### 5.1 文件系统隔离

每个 Agent 有独立的 `agentDir`：

```
~/.openclaw/
├── agents/
│   ├── main/                 # 主 Agent
│   │   ├── sessions/         # 会话存储
│   │   ├── agent/
│   │   │   └── auth-profiles.json
│   │   └── ...
│   ├── code/                 # 代码专用 Agent
│   │   ├── sessions/
│   │   └── ...
│   └── write/                # 文案专用 Agent
│       ├── sessions/
│       └── ...
```

配置：

```json
// ~/.openclaw/config.json 或 gateway.config.json
{
  "agents": {
    "defaults": {
      "workspace": "~/.openclaw/agents/{agentId}/workspace",
      "skills": ["feishu-task", "feishu-calendar"]
    },
    "list": [
      {
        "id": "code",
        "name": "Code Reviewer",
        "skills": ["code-reviewer"],
        "workspace": "~/.openclaw/agents/code/workspace",
        "sandbox": {
          "workspaceRoot": "~/.openclaw/agents/code/sandbox"
        }
      }
    ]
  }
}
```

### 5.2 工具集隔离

每个 Agent 可以绑定不同的 skills：

```json
{
  "agents": {
    "list": [
      {
        "id": "main",
        "skills": ["feishu-calendar", "feishu-task", "feishu-im-read"]
      },
      {
        "id": "code",
        "skills": ["code-reviewer", "file-organizer"]
      },
      {
        "id": "write",
        "skills": ["copywriting", "content-research-writer"]
      }
    ]
  }
}
```

### 5.3 会话绑定（Bindings）

把消息路由到特定 Agent 的机制：

```javascript
// 通过 sessions_spawn 创建时自动绑定
// 或者通过 label 绑定到已有会话
await sessions_send({
  label: 'code-reviewer-session',
  message: 'review this PR'
});
```

### 5.4 可见性范围（Scope）

| Scope | 可见范围 |
|-------|----------|
| `self` | 仅当前会话 |
| `tree` | 当前会话 + 子 Agent（默认） |
| `agent` | 该 Agent 的所有会话 |
| `all` | 所有会话（跨 Agent，需配置） |

沙箱会话被强制限制为 `tree`。

---

## 6. TaskFlow：工作流编排

### 6.1 什么是 TaskFlow

TaskFlow 是 OpenClaw 的**持久化工作流编排层**，位于后台任务之上：

```
TaskFlow（编排层）
    ↓ 协调多个
Task（后台任务）
    ↓ 对应
Agent Run（实际执行）
```

### 6.2 两种同步模式

| 模式 | 说明 |
|------|------|
| **Managed** | TaskFlow 主动管理子任务生命周期，父任务等待子任务完成 |
| **Mirrored** | 子任务镜像父任务状态，适合需要状态同步的场景 |

### 6.3 CLI 操作

```bash
# 查看所有工作流
openclaw tasks flow list

# 查看具体工作流
openclaw tasks flow show <flowId>

# 取消工作流
openclaw tasks flow cancel <flowId>
```

### 6.4 何时使用 TaskFlow

| 场景 | 是否用 TaskFlow |
|------|----------------|
| 简单的单次子 Agent 调用 | 否，直接用 sessions_spawn |
| 需要多步骤、状态持久化的流程 | 是 |
| 需要跨会话协调多个任务 | 是 |
| 需要等待外部事件/人工审批 | 是 |
| 任务需要修订检查（revision-checked mutations） | 是 |

---

## 7. 后台任务与生命周期

### 7.1 任务生命周期

```
queued → running → succeeded / failed / timed_out / cancelled / lost
```

### 7.2 什么会创建任务

| 来源 | Runtime | 默认通知策略 |
|------|---------|-------------|
| `sessions_spawn` (subagent) | `subagent` | `done_only` |
| `sessions_spawn` (acp) | `acp` | `done_only` |
| Cron 执行 | `cron` | `silent` |
| CLI 命令 | `cli` | `silent` |

### 7.3 CLI 查看任务

```bash
# 列出所有任务
openclaw tasks list

# 按状态过滤
openclaw tasks list --status running
openclaw tasks list --runtime subagent

# 查看详情
openclaw tasks show <taskId>

# 取消任务
openclaw tasks cancel <taskId>

# 修改通知策略
openclaw tasks notify <taskId> state_changes

# 健康审计
openclaw tasks audit
```

### 7.4 通知策略

| 策略 | 效果 |
|------|------|
| `done_only` | 只通知终态（默认） |
| `state_changes` | 每次状态变化都通知 |
| `silent` | 完全不通知 |

### 7.5 推送驱动 vs 轮询

**正确方式（推送驱动）**：
```javascript
// 启动子 Agent
await sessions_spawn({ task: '...' });
// yield 等待，系统会在完成时自动唤醒
await sessions_yield();
```

**错误方式（轮询）**：
```javascript
// ❌ 不要这样做
while (true) {
  const tasks = await subagents({ action: 'list' });
  if (allDone(tasks)) break;
  await sleep(5000);
}
```

---

## 8. ACP Harness：外部编码代理

### 8.1 什么是 ACP Harness

OpenClaw 可以通过 `sessions_spawn runtime="acp"` 调用外部编码代理：

| Harness | 说明 | 用途 |
|---------|------|------|
| **Codex** | OpenAI 的 CLI 编码代理 | 代码生成、重构 |
| **Claude Code** | Anthropic 的 ACP 编码代理 | 代码审查、复杂修改 |
| **Cursor** | AI 代码编辑器（通过 CLI） | 代码编辑、项目级修改 |
| **Gemini CLI** | Google 的编码代理 | 代码生成、文档 |

### 8.2 调用方式

```javascript
// 调用外部编码代理
const result = await sessions_spawn({
  runtime: 'acp',
  task: '重构这个函数，添加类型注解',
  agentId: 'codex',  // 或 'claude-code', 'cursor'
  timeoutSeconds: 300
});

await sessions_yield();
// 编码代理完成后，修改后的代码会返回
```

### 8.3 与 OpenClaw 的关系

```
用户请求 → OpenClaw Agent（主控）
              ↓
         分析：需要编码？
              ↓
         sessions_spawn runtime="acp"
              ↓
         ┌──────────┬──────────┐
         ↓          ↓          ↓
      Codex    Claude Code   Cursor
      (编码)    (审查)      (重构)
         └──────────┴──────────┘
              ↓
         结果返回 OpenClaw
              ↓
         汇总 → 用户
```

OpenClaw 是**编排层**，ACP Harness 是**专业工具**。OpenClaw 决定"什么时候调用谁"，Harness 负责"具体怎么改代码"。

---

## 9. 实战演练：构建一个多 Agent 系统

### 9.1 目标

构建一个"软件开发团队"多 Agent 系统：
- `supervisor`：中央调度
- `analyst`：需求分析
- `coder`：编码实现
- `reviewer`：代码审查
- `qa`：测试

### 9.2 步骤

#### Step 1：创建 Agent

```bash
# 创建各个 Agent
openclaw agents add analyst --name "需求分析师"
openclaw agents add coder --name "代码工程师" --skills code-reviewer
openclaw agents add reviewer --name "代码审查员" --skills code-reviewer
openclaw agents add qa --name "测试工程师"
```

#### Step 2：配置绑定

```json
// ~/.openclaw/config.json
{
  "agents": {
    "list": [
      { "id": "main", "skills": ["feishu-task"] },
      { "id": "analyst", "skills": [] },
      { "id": "coder", "skills": ["code-reviewer"] },
      { "id": "reviewer", "skills": ["code-reviewer"] },
      { "id": "qa", "skills": [] }
    ]
  }
}
```

#### Step 3：编写 Supervisor 逻辑

```python
# 在 supervisor Agent 的会话中
async def develop_feature(requirement):
    # Phase 1: 需求分析
    analysis = await sessions_send({
        sessionKey: 'agent:analyst:main',
        message: f'分析需求：{requirement}',
        timeoutSeconds: 60
    })
    
    # Phase 2: 编码（并行）
    # 可以拆成多个模块并行编码
    code_tasks = [
        { module: 'api', desc: f'实现API层：{analysis}' },
        { module: 'db', desc: f'实现数据层：{analysis}' },
        { module: 'ui', desc: f'实现UI层：{analysis}' }
    ]
    
    const code_spawns = code_tasks.map(t => sessions_spawn({
        runtime: 'subagent',
        task: t.desc,
        label: f'coder-{t.module}'
    }))
    
    await sessions_yield()
    # 等待所有 coder 完成
    
    # Phase 3: 代码审查（Parallel 模式）
    const review_results = await Promise.all([
        sessions_send({ sessionKey: 'agent:reviewer:main', message: f'审查API代码：{api_code}' }),
        sessions_send({ sessionKey: 'agent:reviewer:main', message: f'审查数据层代码：{db_code}' }),
        sessions_send({ sessionKey: 'agent:reviewer:main', message: f'审查UI代码：{ui_code}' })
    ])
    
    # Phase 4: 测试
    const test = await sessions_send({
        sessionKey: 'agent:qa:main',
        message: f'测试完整功能：{merged_code}',
        timeoutSeconds: 120
    })
    
    return {
        analysis,
        code: { api: api_code, db: db_code, ui: ui_code },
        reviews: review_results,
        test
    }
```

#### Step 4：测试运行

```bash
# 在 main Agent 中发送请求
openclaw agent main
# 然后输入：
# "开发一个用户登录功能，包括注册、登录、JWT token"
```

---

## 10. 配置参考

### 10.1 多 Agent 配置模板

```json
{
  "agents": {
    "defaults": {
      "skills": ["feishu-task"],
      "workspace": "~/.openclaw/agents/{agentId}/workspace",
      "sandbox": {
        "workspaceRoot": "~/.openclaw/agents/{agentId}/sandbox"
      }
    },
    "list": [
      {
        "id": "main",
        "name": "主控Agent",
        "skills": ["feishu-task", "feishu-calendar", "feishu-im-read"]
      },
      {
        "id": "code",
        "name": "代码专家",
        "skills": ["code-reviewer", "file-organizer"],
        "model": "kimi-k2p6"
      },
      {
        "id": "write",
        "name": "文案专家",
        "skills": ["copywriting", "content-research-writer"]
      }
    ]
  },
  "session": {
    "dmScope": "per-channel-peer",
    "identityLinks": ["main"],
    "reset": {
      "idleMinutes": 60
    }
  }
}
```

### 10.2 会话工具可见性配置

```json
{
  "session": {
    "tools": {
      "scope": "tree"
    }
  }
}
```

可选值：`self` | `tree` | `agent` | `all`

---

## 11. 常见问题与调试

### Q1: 子 Agent 失败怎么办？

```javascript
// 在 Supervisor 中处理失败
async function spawnWithRetry(task, maxRetries = 2) {
  for (let i = 0; i <= maxRetries; i++) {
    try {
      const result = await sessions_spawn({ task, timeoutSeconds: 120 });
      await sessions_yield();
      return result;
    } catch (e) {
      if (i === maxRetries) throw e;
      // 重试，可能调整任务描述
    }
  }
}
```

### Q2: 子 Agent 结果太大怎么办？

- 要求子 Agent 返回摘要而非完整内容
- 使用 `sessions_history` 按需读取历史而非完整传输
- 子 Agent 把结果写入文件，父 Agent 读取文件

### Q3: 如何避免死锁？

- 不要循环 `sessions_send`（A 调 B，B 调 A）
- 使用单向通信：Supervisor → Worker
- 超时设置合理（`timeoutSeconds`）

### Q4: 如何查看子 Agent 在做什么？

```bash
# 查看子 Agent 的历史对话
openclaw tasks list --runtime subagent
openclaw tasks show <taskId>

# 或者直接读取会话历史
# 在父 Agent 中
const history = await sessions_history({
  sessionKey: childSessionKey,
  includeTools: true,
  limit: 50
});
```

### Q5: 子 Agent 的 token 消耗如何控制？

- 设置 `timeoutSeconds` 限制时间
- 在子 Agent 配置中设置 `model` 使用轻量级模型
- 使用 `sandbox: 'require'` 限制子 Agent 权限

---

## 12. 与 Manus / Claude Code / Cursor / OpenHuman 的关系

### 12.1 各工具定位

| 工具 | 类型 | 核心能力 | 与 OpenClaw 的关系 |
|------|------|----------|-------------------|
| **OpenClaw** | 开源 Agent 编排框架 | 多 Agent 协作、IM 集成、Memory、Skills、Cron、TaskFlow | 你正在学的核心框架 |
| **Manus** | 通用 AI Agent 平台（闭源） | 自主浏览器操作、代码执行、文件处理、任务自动化 | 类似"产品形态"，OpenClaw 可以编排出类似能力 |
| **Claude Code** | 编码专用 ACP Harness | 终端内代码编辑、重构、测试、Git 操作 | OpenClaw 可通过 `runtime="acp"` 调用它 |
| **Cursor** | AI 代码编辑器 | IDE 内代码生成、编辑、聊天、代码库理解 | 可作为 ACP Harness 被 OpenClaw 调用，或独立使用 |
| **OpenHuman** | 桌面个人 AI 助手 | 118+ 集成、本地记忆树、桌面 UI、语音、背景处理 | 与 OpenClaw 是**同类产品**，架构理念高度相似 |

### 12.2 概念互通性分析

学了 OpenClaw 后，迁移到其他平台的**概念迁移成本**：

| 概念 | OpenClaw | Manus | Claude Code | Cursor | OpenHuman |
|------|----------|-------|-------------|--------|-----------|
| Agent | ✅ Agent | ✅ Agent | ✅ Agent | ✅ Agent | ✅ Agent |
| Tool Use | ✅ Skills | ✅ Built-in Tools | ✅ Tool Use | ✅ Composer | ✅ Integrations |
| Memory | ✅ MEMORY.md + dreaming | ✅ Memory | ✅ Context Window | ✅ Context + Chat | ✅ Memory Tree |
| Multi-Agent | ✅ sessions_spawn | ✅ Multi-Agent | ❌ Single | ❌ Single | ✅ Multi-Agent |
| Planning | ✅ TaskFlow | ✅ Auto-planning | ✅ Planning | ✅ Planning | ✅ Subconscious |
| Scheduling | ✅ Cron + Heartbeat | ❌ | ❌ | ❌ | ✅ Background sync |
| IM 集成 | ✅ 10+ 渠道 | ❌ | ❌ | ❌ | ✅ Slack/Discord |

**结论**：

1. **核心概念高度互通**：Agent、Tool Use、Memory、Planning 这些概念在所有平台都通用。你学了 OpenClaw，理解这些概念后，切换到任何其他平台都很快。

2. **OpenClaw 的独特优势**：
   - **Multi-Agent 编排**：这是 OpenClaw 最强的能力，Manus 和 OpenHuman 也支持，但 OpenClaw 的 `sessions_spawn` + `sessions_send` + `subagents` 提供了非常灵活的 API
   - **渠道集成**：OpenClaw 原生支持 10+ 即时通讯渠道（Telegram、Discord、Slack、飞书、微信、QQ 等），这是其他平台不具备的
   - **开源 + 自托管**：完全可控，数据本地化

3. **需要单独学习的部分**：
   - **Manus**：如果你需要"通用任务自动化"（如自动订机票、写研究报告、做 PPT），可以学习它的使用方式，但不需要重新学 Agent 概念
   - **Claude Code / Cursor**：如果你需要"深度代码工作"（重构大型代码库、写测试、Git 操作），可以学习它们作为 ACP Harness 被 OpenClaw 调用，或者独立使用
   - **OpenHuman**：它是与 OpenClaw 最接近的竞品，理念相似（本地优先、持久记忆、个人助手）。如果你需要桌面 UI 和开箱即用的集成，可以了解它。但学了一个，另一个上手很快。

4. **建议的学习路径**：

   ```
   现在：OpenClaw（Multi-Agent + Memory + Skills）→ 打牢基础概念
   以后：
     ├─ 需要编码深度 → 学 Claude Code / Cursor（作为 ACP Harness 调用）
     ├─ 需要通用自动化 → 学 Manus（产品使用，非开发）
     └─ 需要桌面体验 → 学 OpenHuman（对比了解）
   ```

   关键：**不要重复学概念，只学差异**。Agent、Memory、Tool Use 这些概念学会了就是学会了，换平台只是 API 不同。

### 12.3 OpenClaw 作为"中心枢纽"

最理想的架构是：

```
          用户
           ↓
      ┌────────┐
      │ OpenClaw │  ← 主控 + 编排 + 记忆 + 渠道集成
      │ (主 Agent)│
      └────┬───┘
           │ sessions_spawn / sessions_send
      ┌────┼────┬────────┐
      ↓    ↓    ↓        ↓
   Code  Write Data  External
  ┌────┐┌────┐┌────┐  ┌────┐
  │Codex││Claude││Self│  │Manus│
  │Code ││Code ││逻辑│  │API  │
  └────┘└────┘└────┘  └────┘
```

OpenClaw 作为**编排层**，可以调用任何外部工具：
- 需要编码 → 调用 Claude Code / Codex（ACP Harness）
- 需要写文案 → 调用专门写文案的 Agent
- 需要数据分析 → 调用数据分析 Agent
- 需要自动化浏览器任务 → 可以集成 Manus 的能力（如果有 API）

---

## 附录：参考文档索引

| 文档 | 路径 | 内容 |
|------|------|------|
| Multi-Agent 概念 | `/usr/lib/node_modules/openclaw/docs/concepts/multi-agent.md` | 架构、路由、隔离、绑定 |
| Session 管理 | `/usr/lib/node_modules/openclaw/docs/concepts/session.md` | 生命周期、可见性、作用域 |
| Session 工具 | `/usr/lib/node_modules/openclaw/docs/concepts/session-tool.md` | API 详解、权限范围 |
| Agent 概念 | `/usr/lib/node_modules/openclaw/docs/concepts/agent.md` | Agent 定义、配置、会话 |
| Agents CLI | `/usr/lib/node_modules/openclaw/docs/cli/agents.md` | CLI 命令参考 |
| Flows CLI | `/usr/lib/node_modules/openclaw/docs/cli/flows.md` | TaskFlow CLI 参考 |
| TaskFlow Skill | `/usr/lib/node_modules/openclaw/skills/taskflow/SKILL.md` | 工作流编排指南 |
| ACP 桥接 | `/usr/lib/node_modules/openclaw/docs/cli/acp.md` | ACP 配置、IDE 集成 |
| 后台任务 | `/usr/lib/node_modules/openclaw/docs/automation/tasks.md` | 任务跟踪、生命周期 |

---

> 文档生成时间：2026-06-03
> 基于 OpenClaw 官方文档整理，适合作为阶段三学习教材
