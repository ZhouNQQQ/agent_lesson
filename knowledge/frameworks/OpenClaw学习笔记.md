# OpenClaw 学习笔记：个人 AI 助手框架（修正版）

> 学习日期：2026-06-16
> 来源：OpenClaw GitHub 源码（github.com/openclaw/openclaw）
> 修正说明：之前版本基于假设，未看源码，存在错误。本版基于真实信息重写。

---

## 一、OpenClaw 是什么（修正）

**一句话：** OpenClaw 是**个人 AI 助手框架**，运行在本地设备上，支持多消息通道（微信/QQ/Telegram/Slack 等），有**多 Agent 路由**、**工具系统**、**记忆系统**和**会话管理**。

**之前错误：** 我误以为 OpenClaw 是简单的工具框架，没有 Agent 能力。
**真相：** OpenClaw 是完整的 Agent 框架，有感知、决策、行动、记忆。

---

## 二、核心架构

```
用户消息（来自任何通道：微信/QQ/Telegram/Slack...）
    │
    ▼
┌─────────────────────────────────────────┐
│ Gateway（控制平面）                        │
│ 管理：sessions, channels, tools, events   │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ Multi-agent Routing（多 Agent 路由）       │
│ 根据消息路由到不同 Agent（workspace + session）│
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ Agent（智能体）                           │
│ - 有 Session Model（会话循环）              │
│ - 有 First-class Tools（工具调用）          │
│   browser, canvas, nodes, cron, sessions  │
│ - 有记忆注入（AGENTS.md / SOUL.md / TOOLS.md）│
│ - 有 Skills（技能系统）                     │
└─────────────────────────────────────────┘
    │
    ▼
  回复用户（通过原通道）
```

---

## 三、记忆系统（之前完全遗漏）

| 组件 | 位置 | 作用 |
|------|------|------|
| **Workspace** | `~/.openclaw/workspace` | 持久化存储根目录 |
| **AGENTS.md** | `~/.openclaw/workspace/AGENTS.md` | Agent 配置、人格定义 |
| **SOUL.md** | `~/.openclaw/workspace/SOUL.md` | 助手灵魂/偏好/记忆 |
| **TOOLS.md** | `~/.openclaw/workspace/TOOLS.md` | 工具定义和权限 |
| **Skills** | `~/.openclaw/workspace/skills/<skill>/SKILL.md` | 技能模块 |

**关键：** OpenClaw 通过注入文件（AGENTS.md/SOUL.md/TOOLS.md）将记忆和配置注入到 LLM 上下文中，这是它的记忆机制。

---

## 四、工具系统

| 工具 | 功能 |
|------|------|
| **browser** | 浏览器操作（搜索、抓取） |
| **canvas** | 可视化画布（A2UI） |
| **nodes** | 节点操作 |
| **cron** | 定时任务 |
| **sessions** | 会话管理 |

---

## 五、安全模型

- 默认在主机会话运行工具（有完整访问权限）
- 支持沙箱：Docker / SSH / OpenShell
- 非主会话可以在沙箱中运行（限制权限）
- 默认安全：DM 需要配对码（pairing code）

---

## 六、和 KimiClaw / Qclaw 的关系

**KimiClaw（现在叫 Qclaw）基于 OpenClaw 构建。**

Qclaw 可能是 OpenClaw 的一个具体实例/定制版本：
- OpenClaw 是通用框架
- Qclaw 是特定场景的应用（聚焦在本地开发辅助）

---

## 七、和 LangGraph / Manus / AutoGen 的对比

| | OpenClaw | LangGraph | Manus | AutoGen |
|--|----------|-----------|-------|---------|
| **定位** | 个人 AI 助手 | 图编排框架 | 通用 Agent | 多 Agent 对话 |
| **运行环境** | 本地设备 | 本地/服务器 | 云端虚拟机 | 本地/服务器 |
| **通道** | 多消息通道（微信/QQ/Slack） | 无（应用层） | 无（任务输入） | 无（API） |
| **Agent 能力** | ✅ 有 | 需要外接 | ✅ 有 | ✅ 有 |
| **记忆** | ✅ Workspace + 注入文件 | 需要外接 | ✅ 有 | 需要外接 |
| **工具** | ✅ browser/canvas/nodes/cron | 需要定义 | ✅ 有 | 需要定义 |
| **编排** | Gateway + Multi-agent routing | Node + Edge | 自主规划 | 对话驱动 |

---

## 八、一句话总结（修正）

> **OpenClaw 是本地优先的个人 AI 助手框架，有完整的 Agent 能力：多通道接入、多 Agent 路由、工具系统、记忆系统（Workspace + AGENTS.md/SOUL.md/TOOLS.md + Skills）。不是简单的工具框架，而是功能丰富的 Personal AI Assistant。**

---

## 九、面试考点（修正版）

| 问题 | 答案 |
|------|------|
| OpenClaw 是什么？ | 本地优先的个人 AI 助手框架，支持多通道（微信/QQ/Slack 等） |
| OpenClaw 有 Agent 能力吗？ | ✅ 有，有 Multi-agent routing、Session Model、工具调用 |
| OpenClaw 的记忆系统是什么？ | Workspace + AGENTS.md/SOUL.md/TOOLS.md 注入文件 + Skills 系统 |
| OpenClaw 和 LangGraph 的区别？ | OpenClaw 是完整的个人助手产品，LangGraph 是图编排框架 |
| OpenClaw 和 Qclaw 的关系？ | Qclaw 基于 OpenClaw 构建，是 OpenClaw 的定制应用 |
| OpenClaw 的工具有哪些？ | browser, canvas, nodes, cron, sessions |

---

> 来源：
> - GitHub：`https://github.com/openclaw/openclaw`
> - 官网：`https://openclaw.ai/`
> - 修正说明：之前版本错误，本版基于真实源码重写
