# 学习资料：Cursor 普及 — AI 编辑器的 Agent 模式

> 定位：普及知识面，理解 Cursor 是什么、三种模式、Composer Agent 的工作流、和 LangGraph 的关系
> 来源：综合多个使用经验整理，去掉了实现细节，保留核心概念
> 修正：2026-06-16 修正了关于"Plan-and-Execute"的过度断言，承认 Cursor 是闭源产品，无法确认内部范式

---

## 一、Cursor 是什么

**一句话：** Cursor 是**基于 VS Code 的 AI 编辑器**，核心能力是把 AI 集成到代码编辑器的每个环节。

**为什么不是"又一个 Copilot"？**

| 工具 | 定位 | 能力 |
|------|------|------|
| **GitHub Copilot** | 代码补全插件 | 你写代码时它补全，被动 |
| **Cursor** | 完整的 AI 编辑器 | 可以主动帮你改代码、理解项目、执行操作 |
| **Claude Code** | 命令行 AI 助手 | 纯命令行，没有编辑器界面 |

**Cursor 的核心区别：** 它不只是"帮你写代码"，而是**能主动理解你的项目、规划修改、执行多文件操作**。

---

## 二、三种模式（使用场景）

### 1. Chat（聊天）

**场景：** 你写代码时遇到报错，按 `Cmd+K` 弹出对话窗口，问"这个报错是什么意思？"

**特点：**
- 和代码上下文关联：Cursor 会自动把当前文件的代码、报错信息、光标位置传给 AI
- AI 回答时可以直接引用代码片段
- 你可以让 AI "修改这段代码"，它会直接改到文件里

**类比：** 像有一个编程导师坐在你旁边，你指着代码问，他直接帮你改。

```
用户：
  光标在第 15 行，报错 "TypeError: undefined is not a function"
  
Chat 输入："这个报错是什么意思？"

Cursor 自动传给 AI 的上下文：
  - 当前文件前 50 行代码
  - 光标位置（第 15 行）
  - 报错信息
  - 项目类型（React/Node/Python）

AI 回答：
  "第 15 行的 `data.map()` 中，`data` 可能是 undefined。
  建议先检查：`if (!data) return null;`"
  
用户："帮我加上检查"
→ AI 直接修改第 15 行前后的代码
```

---

### 2. Tab（代码补全）

**场景：** 你写代码时，Cursor 预测你接下来要写什么，按 `Tab` 接受。

**特点：**
- 比 Copilot 更智能：能跨文件理解（比如你在 A 文件定义了函数，在 B 文件使用，Tab 能补全正确的函数名）
- 能补全大块代码（不只是单行，可以补全整个函数）
- 能根据注释生成代码（你写注释描述功能，Tab 生成实现）

**类比：** 像有一个非常了解你项目的高级程序员，知道你接下来要写什么。

---

### 3. Composer（多文件 Agent）

**这是 Cursor 的核心 Agent 模式。**

**场景：** 你说"帮我重构这个项目的认证模块，把 JWT 改成 Session"，Composer 会：
1. 分析哪些文件需要改（auth.js、middleware.js、routes.js）
2. 逐个文件修改
3. 检查修改后是否有报错
4. 如果有问题，修复后再验证

**这就是 Agent：** 不是被动回答你的问题，而是**主动分析、修改、验证**。

---

## 三、Composer 的 Agent 工作流（不确定内部实现）

**重要前提：Cursor 是闭源产品，没有公开源码。下面的描述是基于用户观察到的行为推断，不是内部实现。**

**用户观察到的行为：**

```
用户输入："重构认证模块"
    │
    ▼
┌─────────────────────────────────────────┐
│ 阶段 1：分析（可能是 LLM 的 think）      │
│ 分析项目结构，列出要修改的文件列表          │
│ 输出：["auth.js", "middleware.js", "routes.js"] │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 阶段 2：逐个文件修改                       │
│ 读取文件 → 修改 → 保存 → 展示 diff       │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 阶段 3：验证（可能是编译器/测试）          │
│ 检查语法错误、类型检查、测试              │
│ 不通过 → 回到阶段 2 修复                  │
│ 通过 → 用户审批（Accept/Reject/Modify）   │
└─────────────────────────────────────────┘
```

**关键不确定点：**
- 这个"阶段 1"是**真正的先制定完整计划**（Plan-and-Execute）？
- 还是**第一轮 think**（ReAct 的第一个思考步骤）？
- 还是**混合模式**（先列出思路，后续迭代）？

**没有源码，无法确认。** 可以确认的是：Claude Code 开源代码（claw-code）是 ReAct 循环（有 state/iteration loop 源码证据）。

---

## 四、Cursor 和 LangGraph 的关系

### 关系1：不确定内部是否用 LangGraph

**Cursor 没有公开源码。** 从用户行为观察：
- 有"分析→修改→验证"的循环
- 支持循环重试
- 支持人在中间审批
- 支持撤销/回滚

这些特征**和 LangGraph 的图编排思想一致**，但无法确认是否实际使用 LangGraph。可能内部用了 LangGraph，也可能自己实现了类似架构，或者完全是不同的实现方式。

### 关系2：Cursor 的 Chat 上下文 ≈ LangGraph 的 State

```
Cursor Chat 的上下文：
  - 当前文件代码
  - 光标位置
  - 报错信息
  - 项目类型
  - 最近的操作历史

≈ LangGraph 的 State（全局共享数据）
```

### 关系3：Cursor 的 Agent 模式 ≈ 图编排的执行模式

```
Cursor Composer：
  用户输入 → 分析 → 修改 → 验证 → （循环）

≈ LangGraph 的图编排：
  START → 节点 → 节点 → 条件边 → 结束/重试
```

**注意：以上只是行为类比，不是内部实现的确认。**

---

## 五、Cursor 和 Claude Code / KimiClaw 的关系

| 工具 | 界面 | Agent 能力 | 记忆系统 |
|------|------|-----------|----------|
| **Cursor** | 编辑器 GUI | Composer 多文件 Agent | 项目上下文（代码文件） |
| **Claude Code** | 命令行 | 代码生成、文件操作 | 有上下文记忆（但有限） |
| **KimiClaw** | 命令行 | 目前无 Agent 模式 | 只有 USER.md（无向量库） |

**Cursor 的优势：**
- 可视化：代码修改直接在编辑器里展示，diff 一目了然
- 集成：和代码编辑器深度集成，不需要切换窗口
- 人介入：每个修改都可以 Accept/Reject/Modify

**Claude Code 的优势：**
- 命令行：适合自动化脚本、CI/CD 集成
- 灵活：可以操作任何文件系统，不限于代码项目

---

## 六、真实使用案例

### 案例：重构 React 组件

```
用户输入：
  "把 UserProfile 组件从 Class 组件改成 Function 组件，
   用 React Hooks 替代生命周期"

Composer Agent 工作流：

[分析阶段]
  分析：找到 UserProfile.js
  列出：
    1. 改写 Class 为 Function
    2. componentDidMount → useEffect
    3. this.state → useState
    4. 检查 props 类型是否需要改

[修改阶段]
  读取 UserProfile.js
  生成修改后的代码
  保存到 UserProfile.js
  → 展示 diff（红线删除，绿线新增）

[验证阶段]
  检查语法错误
  检查 TypeScript 类型（如果有）
  检查 ESLint 规则
  
[用户审批]
  通过？→ 用户看到"Accept / Reject / Modify"按钮
  用户点击 "Accept"
  修改生效，文件保存

[撤销]
  这次操作被记录，可以撤销
```

---

## 七、面试考点（普及阶段）

| 问题 | 一句话答案 |
|------|----------|
| "Cursor 是什么？" | 基于 VS Code 的 AI 编辑器，核心是多文件 Agent（Composer） |
| "Cursor 和 Copilot 的区别？" | Copilot 是被动补全，Cursor 能主动分析、修改、验证多文件 |
| "Cursor 的 Composer 怎么体现 Agent 概念？" | 分析→修改→验证→循环，有完整的工作流程 |
| "Cursor 和 LangGraph 的关系？" | 行为上和图编排思想一致（节点→边→循环），但 Cursor 闭源，无法确认内部实现 |
| "Cursor 的 Chat 上下文对应 LangGraph 的什么？" | 对应 State（全局共享数据） |
| "Cursor 支持人在中间审批，对应 LangGraph 的什么？" | Human-in-the-loop（人在节点间介入） |
| "Cursor 和 Claude Code 的区别？" | Cursor 是编辑器 GUI，Claude Code 是命令行。Cursor 适合可视化代码修改，Claude Code 适合自动化脚本 |
| **"Cursor 是 Plan-and-Execute 吗？"** | **不能确定。** 闭源产品，没有公开源码。Claude Code 可以确认是 ReAct（有源码）。 |

---

## 八、一句话总结

> **Cursor 是 AI 编辑器，核心能力是 Composer 多文件 Agent。用户观察到它有"分析→修改→验证"的循环流程，行为上和图编排思想一致。但 Cursor 是闭源产品，没有公开源码，无法确认内部是 Plan-and-Execute、ReAct 还是混合模式。可以确认的是 Claude Code 开源代码是 ReAct（有源码证据）。**

---

> 延伸阅读：
> - 官网：`https://www.cursor.com/`
> - Composer 文档：`https://docs.cursor.com/composer`
