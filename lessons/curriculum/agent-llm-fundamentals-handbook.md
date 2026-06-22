# Agent开发与LLM基础能力速查手册

> **文档定位**：本文档是QClaw Agent学习路线图的补充参考资料，覆盖Agent安全约束、LLM参数调优、模型部署三大核心知识板块。面向有编程基础的开发者，强调可操作的实践指导。
>
> **版本**：v1.0 | **适用模型**：Claude 3.5/3.7 Sonnet、GPT-4o/o1/o3、Llama 3.x、Qwen 2.5等主流LLM

---

## 第一部分：Agent操作的强制约束机制（安全与合规）

### 1.1 核心洞察：为什么"光写禁止没用"

一位有经验的Agent开发者指出："skill里明确写清楚检查项，有可验证的校验点才有用，光写'禁止XXX'没用。当上下文过长，模型产生上下文焦虑时，会自行压缩执行步骤，可能绕过自检。"

这个观察完全正确，且触及了LLM安全工程的核心难点。LLM作为概率模型，其本质是**预测下一个最可能的token**，而非执行严格的逻辑程序。这导致以下行为特性：

#### 1.1.1 LLM的"抗禁止"行为特性

| 特性 | 说明 | 实例 |
|------|------|------|
| **上下文稀释效应** | 长上下文中，早期指令的概率权重被后续内容稀释 | System Prompt中的"禁止删除文件"在长对话后被遗忘 |
| **上下文焦虑**（准确洞察） | 面对长任务时，模型倾向于压缩步骤以"节省"上下文空间 | 自行跳过自检步骤，直接执行操作 |
| **指令层级冲突** | 不同来源的指令（System/User/Tool）优先级竞争 | User说"帮我清理磁盘"与System说"禁止删除"冲突 |
| **过度优化倾向** | 模型为追求"高效"而绕过看似冗余的安全步骤 | 跳过确认弹窗，直接执行删除 |
| **否定指令理解弱** | "不要XXX"的遵守率远低于"必须YYY" | "不要输出密码"vs"输出时必须将密码字段替换为[REDACTED]" |

**关键结论**：对LLM而言，**结构性约束**远比**行为禁止**有效。与其告诉模型"不要做什么"，不如设计"只能这样做"的架构。

### 1.2 五层纵深防御体系（Defense in Depth）

有效的Agent安全需要五层防护，每层独立生效，多层叠加形成纵深防御。

#### 第一层：模型层约束（Model-Level Constraints）

这是最直接但也是最薄弱的一层——完全依赖模型的指令遵循能力。

**System Prompt工程**：
```markdown
# 有效的System Prompt设计原则

## 1. 使用肯定性指令替代否定性指令
- ❌ "不要删除用户的任何文件"
- ✅ "所有文件操作必须通过SafeFileTool执行，该工具会自动创建备份"

## 2. 结构化输出强制
- ❌ "请以JSON格式输出"
- ✅ 使用response_format={"type": "json_object"} 或 JSON Schema约束

## 3. 强制思考链（Chain of Thought）
在执行任何操作前，你必须：
1. 输出[CHECKLIST]标签包裹的检查清单
2. 逐项确认每个校验点
3. 输出[CONFIRM]标签表示所有检查通过
4. 最后执行操作
```

**输出格式约束（JSON Schema）**：
```json
{
  "type": "object",
  "required": ["checklist_completed", "safety_verified", "action"],
  "properties": {
    "checklist_completed": {
      "type": "boolean",
      "description": "是否已完成所有检查项"
    },
    "safety_verified": {
      "type": "boolean", 
      "description": "安全校验是否通过"
    },
    "action": {
      "type": "string",
      "enum": ["read", "write", "delete", "none"],
      "description": "仅限枚举值，none表示不执行操作"
    }
  }
}
```

**Function Calling约束**：通过tools定义严格限定模型可调用的功能范围。模型只能调用你提供的工具，这是**架构级**的硬约束。

```python
# OpenAI API示例：严格限制工具选择
response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=safe_tools_only,  # 只提供安全工具
    tool_choice="auto",     # 或强制特定工具
    # tool_choice={"type": "function", "function": {"name": "safe_read_only"}}
)
```

#### 第二层：Agent层约束（Agent-Level Constraints）

**Claude Code Hooks系统**（业界最佳实践）：

Claude Code提供了26个生命周期事件钩子，允许开发者在关键节点插入自定义逻辑。

```typescript
// Claude Code Hooks系统 - 26个生命周期事件
// 完整事件列表：

// === 工具使用相关 ===
// PreToolUse      - 工具调用前（权限控制的关键节点）
// PostToolUse     - 工具调用后（结果校验、审计日志）
// ToolError       - 工具调用错误

// === 消息处理相关 ===
// PreMessageSend  - 发送消息给模型前
// PostMessageReceive - 接收到模型响应后
// PreToolOutput   - 工具输出返回给模型前

// === 文件操作相关 ===
// PreFileRead     - 读取文件前
// PostFileRead    - 读取文件后
// PreFileWrite    - 写入文件前（关键：可拦截危险写入）
// PostFileWrite   - 写入文件后
// PreFileDelete   - 删除文件前（关键：必须人工确认）
// PostFileDelete  - 删除文件后

// === 命令执行相关 ===
// PreCommandRun   - 执行终端命令前（关键：可拦截rm -rf等）
// PostCommandRun  - 执行终端命令后
// CommandOutput   - 命令输出处理

// === 网络请求相关 ===
// PreRequest      - 发起HTTP请求前
// PostRequest     - 收到HTTP响应后

// === 会话生命周期 ===
// SessionStart    - 会话开始
// SessionEnd      - 会话结束
// ConversationTurn - 每轮对话

// === 用户交互 ===
// PreUserPrompt   - 用户输入处理前
// UserApproval    - 需要用户确认时

// === 其他 ===
// OnError         - 错误处理
// OnWarning       - 警告处理
// ToolValidation  - 工具参数校验
// ContextLoad     - 上下文加载
// ContextCompress - 上下文压缩时（关键：防止压缩掉安全指令）
```

**Hooks实现强制确认机制的完整示例**：

```typescript
// claude-code-hooks.ts - 生产级权限控制实现
import { HookSystem, ToolCall } from '@anthropic-ai/claude-code';

const hooks = new HookSystem();

// === 危险操作白名单 ===
const DANGEROUS_PATTERNS = [
  /rm\s+-rf/i,
  /DROP\s+TABLE/i,
  /DELETE\s+FROM/i,
];

// === 1. PreToolUse：所有工具调用前的权限检查 ===
hooks.on('PreToolUse', async (toolCall: ToolCall) => {
  // 所有操作都需要通过安全检查
  const result = await securityCheck(toolCall);
  
  if (!result.passed) {
    // 拒绝执行，返回错误信息给模型
    return {
      allowed: false,
      reason: result.reason,
      // 关键：将拒绝原因返回给模型，让它知道为什么被拒绝
      feedback: `操作被拒绝：${result.reason}。请尝试替代方案或请求人工授权。`
    };
  }
  
  // 高敏感操作强制人工确认
  if (isHighSensitivityOperation(toolCall)) {
    const approved = await requestHumanApproval(toolCall);
    return { allowed: approved };
  }
  
  return { allowed: true };
});

// === 2. PostToolUse：操作审计日志 ===
hooks.on('PostToolUse', async (toolCall: ToolCall, result: any) => {
  await auditLog.record({
    timestamp: new Date(),
    tool: toolCall.name,
    parameters: toolCall.arguments,
    result_summary: truncate(result, 500),
    session_id: context.sessionId,
    user_id: context.userId,
  });
});

// === 3. PreCommandRun：命令执行前的危险模式检测 ===
hooks.on('PreCommandRun', async (command: string) => {
  // 自动拦截危险命令模式
  for (const pattern of DANGEROUS_PATTERNS) {
    if (pattern.test(command)) {
      // 记录安全事件
      await securityAlert({
        level: 'critical',
        message: `拦截危险命令: ${command}`,
      });
      return { 
        allowed: false, 
        reason: '危险命令模式被安全策略拦截' 
      };
    }
  }
  
  // 写入类命令需要额外确认
  if (isWriteCommand(command)) {
    return { allowed: await requestHumanApproval(command) };
  }
  
  return { allowed: true };
});

// === 4. ContextCompress：防止安全指令被压缩掉 ===
hooks.on('ContextCompress', async (context: Context) => {
  // 安全指令永远不能被压缩
  const SAFETY_PRIORITY = Infinity;
  return context.markImmutable('system.safety_rules', SAFETY_PRIORITY);
});
```

**OpenClaw/QClaw的权限控制**：

```yaml
# QClaw Agent权限配置文件 agent-permissions.yaml
agent:
  name: "code-assistant"
  
  # 权限范围定义
  permissions:
    filesystem:
      read: ["./src/**", "./docs/**", "./config/**"]
      write: ["./src/**", "./temp/**"]  # 明确允许写入的范围
      delete: []  # 空数组 = 禁止删除
      
    network:
      allowed_hosts: ["api.github.com", "registry.npmjs.org"]
      blocked_hosts: ["*.*.*.*"]  # 默认禁止IP直连
      
    commands:
      allowed: ["git", "npm", "node", "python"]
      blocked_patterns: ["rm -rf /", "sudo", "> /dev/null"]
      require_confirmation: ["git push", "npm publish"]
      
  # 敏感操作确认配置
  confirmation_rules:
    - operation: "file_delete"
      always_confirm: true
      
    - operation: "git_push"
      confirm_message: "即将推送代码到远程仓库，确认？"
      
    - operation: "npm_publish"
      confirm_message: "即将发布npm包，此操作不可逆，确认？"
```

#### 第三层：Skill层约束（Skill-Level Constraints）

这是用户原回答的核心内容，也是大多数开发者能直接接触到的层面。

**SKILL.md中的可验证检查项设计**：

```markdown
# SKILL.md - 安全可验证检查项设计模板

## 文件操作Skill的安全检查项

### 前置条件检查（Pre-conditions）
- [ ] 目标路径在允许的操作范围内（通过path_allowlist校验）
- [ ] 操作前已创建备份（backup_exists == true）
- [ ] 目标文件未被其他进程锁定

### 参数校验（Input Validation）
- [ ] file_path: 必须为绝对路径，不能包含".."序列
- [ ] content: 大小不超过max_file_size（默认1MB）
- [ ] encoding: 必须为"utf-8"或"utf-16"

### 执行中校验（Runtime Checks）
- [ ] 写入前磁盘空间充足（disk_free > content_size * 2）
- [ ] 写入后校验MD5哈希（hash_match == true）

### 后置条件检查（Post-conditions）
- [ ] 文件可读（read_verify == true）
- [ ] 文件权限设置正确（mode == expected_mode）
```

**为什么这种结构有效**：
1. **可自动化验证**：每个检查项都对应一个布尔表达式，可以代码自动判断
2. **可审计**：检查失败会留下明确记录
3. **可组合**：不同Skill可以复用相同的检查框架

**将"禁止"转化为"结构性约束"的对比**：

| ❌ 禁止性指令（低效） | ✅ 结构性约束（高效） |
|---------------------|---------------------|
| "禁止删除系统文件" | 文件系统挂载为只读，删除操作需要sudo权限 |
| "不要泄露API密钥" | API密钥存储在环境变量，模型上下文永不包含.env内容 |
| "不要生成恶意代码" | 代码执行在沙箱容器，网络访问被隔离 |
| "不要超出预算调用" | API调用通过中间层计数，达到限额自动熔断 |

#### 第四层：架构层约束（Architecture-Level Constraints）

**沙箱隔离**（以OpenAI Codex沙箱为例）：

```yaml
# Codex沙箱安全架构
sandbox:
  # 文件系统隔离
  filesystem:
    type: overlay    # OverlayFS，所有写入在临时层
    persist: false   # 会话结束后丢弃所有变更
    whitelist:
      - "/workspace" # 只有/workspace可读写
      
  # 网络隔离  
  network:
    mode: none       # 默认无网络访问
    egress_rules:
      - allow: "*.openai.com"
      - allow: "*.github.com"
        rate_limit: "100/min"
        
  # 资源限制
  resources:
    cpu_quota: 1.0      # 最多1核
    memory_limit: 512M  # 最多512MB内存
    max_processes: 10   # 最多10个进程
    
  # 系统调用过滤
  seccomp:
    mode: whitelist
    allowed_syscalls:
      - read, write, open, close
      - mmap, brk
      # 明确禁止: execve, fork, clone, ptrace...
```

**RBAC权限模型**：

```yaml
# Agent RBAC权限矩阵
roles:
  code_assistant:
    description: "代码辅助Agent"
    permissions:
      - filesystem:read
      - filesystem:write:scoped     # 仅在项目目录内
      - command:execute:safe        # 只允许安全命令白名单
      - network:none                # 无网络权限
      
  devops_agent:
    description: "运维Agent"
    inherits: [code_assistant]
    permissions:
      - command:execute:all         # 可执行更多命令
      - network:egress:limited      # 有限网络访问
      - docker:container:manage
    requires:
      - mfa_verified: true          # 需要多因素认证
      
  admin_agent:
    description: "管理Agent"
    permissions:
      - all:*
    requires:
      - human_approval: every_operation  # 每个操作都需要人工确认
```

**操作审计日志规范**：

```json
{
  "event_id": "uuid",
  "timestamp": "2024-01-15T09:30:00Z",
  "event_type": "tool_execution",
  "severity": "info|warning|critical",
  "agent": {
    "id": "agent-123",
    "name": "code-assistant",
    "version": "1.2.0"
  },
  "context": {
    "session_id": "sess-456",
    "conversation_length": 42,
    "tool_chain": ["read_file", "edit_file", "write_file"]
  },
  "tool_call": {
    "name": "write_file",
    "arguments_hash": "sha256:abc...",
    "arguments_preview": "{\"path\":\"/src/app.js\",\"content\":\"...\"}"
  },
  "security_checks": {
    "path_allowed": true,
    "backup_created": true,
    "human_approved": false,
    "auto_approved_reason": "path_in_safe_list"
  },
  "result": {
    "status": "success",
    "bytes_written": 1024
  }
}
```

#### 第五层：人工层约束（Human-in-the-Loop）

这是最后一道防线，适用于不可逆或高影响操作。

```yaml
# 人工确认节点配置
human_approval_gates:
  # 文件删除：总是确认
  - trigger: "file_delete"
    condition: "always"
    confirmation_dialog:
      title: "确认文件删除"
      description: "Agent请求删除文件: {file_path}"
      show_preview: true
      
  # 敏感数据访问：当涉及密钥等
  - trigger: "file_read"
    condition: "path contains '.env' or path contains 'secret'"
    confirmation_dialog:
      title: "敏感文件访问请求"
      risk_level: "high"
      
  # 外部通信：首次访问新域名
  - trigger: "http_request"
    condition: "host not in approved_hosts"
    confirmation_dialog:
      title: "新域名访问请求"
      description: "Agent请求访问: {url}"
      options: ["allow_once", "allow_always", "deny"]
      
  # 成本告警：接近预算上限
  - trigger: "token_usage"
    condition: "usage > budget * 0.8"
    alert:
      channels: ["slack", "email"]
      message: "Agent {agent_id} 接近预算上限: {usage}/{budget}"
```

### 1.3 有效约束实践总结

| 实践原则 | 具体操作 | 优先级 |
|---------|---------|--------|
| **肯定 > 否定** | 用"必须检查X"替代"不要忽略X" | P0 |
| **结构 > 提示** | 用JSON Schema/枚举值限定输出，而非文字描述 | P0 |
| **强制自检** | 要求模型先输出检查清单，逐项确认后再执行 | P0 |
| **分层验证** | 每层防御独立生效，多层叠加 | P1 |
| **审计追溯** | 所有操作有日志、可回放、可追责 | P1 |
| **最小权限** | Agent只能访问完成任务必需的最小资源集 | P0 |
| **人工兜底** | 不可逆操作必须有最终确认节点 | P0 |

---

## 第二部分：LLM可调参数大全

### 2.A 推理参数（Inference Parameters）

#### temperature — 随机性控制的核心旋钮

```yaml
参数: temperature
取值范围: 0.0 - 2.0（不同模型上限不同，OpenAI最高2.0，Claude最高1.0）
默认值: 1.0（OpenAI），0.7（部分模型），1.0（Claude）
推荐类型: float
```

**作用机制**：temperature控制采样分布的"平坦度"。在LLM解码的softmax步骤中，温度参数T对logits进行缩放：

```
P(token_i) = exp(logit_i / T) / Σ_j exp(logit_j / T)
```

- **T→0**：分布趋于尖锐，总是选择概率最高的token（贪婪解码，确定性输出）
- **T=1**：标准softmax，自然概率分布
- **T>1**：分布趋于平坦，低概率token也有机会被选中（更具创造性/随机性）

**对Agent行为的具体影响**：

| temperature值 | 效果 | Agent场景 |
|-------------|------|----------|
| 0.0 - 0.2 | 几乎确定性输出，每次调用结果高度一致 | 工具调用Agent、代码生成、数据提取 |
| 0.3 - 0.5 | 低随机性，偶尔有措辞变化 | 结构化输出、分类任务、格式化回复 |
| 0.6 - 0.8 | 中等随机性，平衡创造性和一致性 | 对话Agent、内容生成、头脑风暴 |
| 0.9 - 1.2 | 高随机性，输出多样化 | 创意写作、营销文案 |
| 1.3+ | 很高随机性，可能出现不连贯 | 探索性任务、角色扮演 |

**调优建议**：
- **代码生成Agent**：0.1-0.3。代码需要确定性，temperature>0.5可能导致语法错误。
- **工具调用Agent**：0.0-0.2。工具参数必须精确，随机性是敌人。
- **需求分析Agent**：0.5-0.7。需要一定创造性来理解模糊需求。
- **面试常问**："为什么代码生成要用低temperature？" → "因为代码是结构化输出，高temperature会引入语法错误和不一致的变量命名。"

**常见陷阱**：
- ❌ temperature=0 也不能保证完全确定性（GPU浮点运算有非确定性因素，除非设置seed）
- ❌ 不同模型对temperature的敏感度不同（Claude 3.5 Sonnet在T=0.5时已经很稳定，GPT-4o在T=0.7依然稳定）
- ✅ 结合top_p使用效果更佳（建议temperature×top_p协同调参）

#### top_p — 核采样（Nucleus Sampling）

```yaml
参数: top_p
取值范围: 0.0 - 1.0
默认值: 1.0（不启用核采样）
别名: nucleus sampling parameter
```

**作用机制**：top_p采样不是取固定数量的top-k token，而是动态选择累积概率达到p的最小token集合。

```python
# top_p采样算法示意
def top_p_sampling(logits, p=0.9):
    probs = softmax(logits)
    sorted_probs, sorted_indices = torch.sort(probs, descending=True)
    cumulative_probs = torch.cumsum(sorted_probs, dim=-1)
    
    # 找到累积概率首次超过p的截断点
    cutoff_index = torch.searchsorted(cumulative_probs, p)
    
    # 只保留前cutoff_index个token
    filtered_logits = logits.clone()
    filtered_logits[sorted_indices[cutoff_index+1:]] = -float('inf')
    
    return filtered_logits
```

**与temperature的关系和选择策略**：

| 策略 | 设置方式 | 适用场景 |
|------|---------|---------|
| **Temperature-only** | top_p=1.0, 调节temperature | 需要平滑控制随机性 |
| **Top-p-only** | temperature=1.0, 调节top_p | 需要动态调整候选集 |
| **协同调节（推荐）** | temperature=0.7, top_p=0.9 | 大多数Agent场景 |
| **严格确定性** | temperature=0.0, top_p=0.0 | 需要完全一致的输出 |

**面试常问**："top_p和top_k的区别？"
- top_k：固定保留k个候选token（如k=50），不考虑概率分布形状
- top_p：动态保留累积概率达到p的最小集合（如p=0.9），适应不同上下文
- **top_p更优的原因**：在模型"确定"的上下文（概率分布尖锐）中保留少量token即可；在"不确定"的上下文中自动扩大候选集

**Agent调优建议**：
- 结构化输出：top_p=0.1-0.3 + temperature=0.1-0.3
- 对话Agent：top_p=0.9-0.95 + temperature=0.7-0.8
- 创意任务：top_p=0.95-1.0 + temperature=0.9-1.1

#### top_k — Top-K采样

```yaml
参数: top_k
取值范围: 0 - 无穷大（通常1-100有效）
默认值: 不设置（即禁用）或不一致（不同提供商）
支持情况: Anthropic原生支持，OpenAI API不直接支持
```

**作用机制**：只保留概率最高的k个token，其余概率置零后重新归一化。

**何时需要设置**：
- 使用本地模型（llama.cpp、vLLM）时可以直接设置
- 需要严格限制输出多样性时（如k=1就是贪婪解码）
- 与top_p联合使用：先top_k过滤，再top_p过滤

**实际影响**：top_k=50是最常见的设置，能在保持输出多样性的同时排除真正低概率的"垃圾"token。

#### max_tokens / max_completion_tokens

```yaml
参数: max_tokens (OpenAI legacy) / max_completion_tokens (OpenAI new) / max_tokens (Anthropic)
取值范围: 1 - 模型上下文上限（如128K、200K）
默认值: 因模型而异（GPT-4o默认无限制直到上下文满，Claude默认4096）
```

**关键区别**：
- `max_tokens`（旧）：包含所有生成的token（包括推理过程的 reasoning tokens）
- `max_completion_tokens`（新OpenAI API）：明确区分completion和reasoning token预算

**对Agent行为的具体影响**：
- 设置过低：Agent输出被截断，可能导致JSON格式不完整、代码未完成
- 设置过高：浪费token（如果模型不需要那么多），但不影响输出质量

**Agent场景推荐值**：

| Agent类型 | 推荐max_tokens | 理由 |
|----------|--------------|------|
| 简单分类/判断 | 50-100 | 只需要yes/no或标签 |
| 结构化数据提取 | 500-1000 | JSON对象大小 |
| 代码生成 | 2000-4000 | 函数级代码块 |
| 长文本生成 | 4000-8000 | 文章、报告 |
| 复杂推理链 | 8000-16000 | 多步骤推理+最终答案 |
| 工具调用链 | 4000-8000 | 多轮工具调用的累积输出 |

**陷阱**：Claude 3.5 Sonnet默认max_tokens=4096，如果要生成长内容必须显式设置更高值！

#### presence_penalty — 新话题促进

```yaml
参数: presence_penalty
取值范围: -2.0 到 2.0（OpenAI）；Anthropic不支持此参数
默认值: 0.0
作用: 惩罚已出现过的token，促进话题多样性
```

**作用机制**：对已经生成过的token施加惩罚，降低它们再次出现的概率。

```
adjusted_logit = logit - presence_penalty * (token_has_appeared ? 1 : 0)
```

注意：**只关心是否出现过（presence），不关心出现频率**。

**对Agent行为的影响**：
- 正值（>0）：鼓励模型引入新词汇、新话题，避免重复
- 负值（<0）：鼓励模型使用已提及的内容，保持一致性
- 对话Agent：设置0.3-0.6可以让对话更自然，避免反复说同样的客套话
- 代码Agent：建议0.0，代码需要一致的变量命名

#### frequency_penalty — 重复抑制

```yaml
参数: frequency_penalty
取值范围: -2.0 到 2.0（OpenAI）
默认值: 0.0
作用: 基于出现频率惩罚token
```

**与presence_penalty的区别**：

```
# presence_penalty: 出现1次就惩罚，惩罚力度不变
# frequency_penalty: 出现次数越多，惩罚越重
adjusted_logit = logit - frequency_penalty * token_appearance_count
```

**对Agent行为的影响**：
- **代码生成**：设置0.1-0.3可以有效减少重复代码块（如连续输出多行相似代码）
- **长文本生成**：0.3-0.5避免重复论述同一个观点
- **对话Agent**：配合presence_penalty使用，0.3-0.6

**两个penalty的协同使用**：

| 场景 | presence | frequency | 效果 |
|------|----------|-----------|------|
| 代码生成 | 0.0 | 0.1-0.2 | 保持命名一致，减少冗余代码 |
| 创意写作 | 0.5 | 0.5 | 最大化话题和词汇多样性 |
| 技术文档 | 0.0 | 0.0-0.1 | 术语一致性优先 |
| 对话Agent | 0.3 | 0.3 | 自然对话，适度变化 |

#### repetition_penalty

```yaml
参数: repetition_penalty（HuggingFace Transformers）/ penalty_score（部分框架）
取值范围: 1.0 - 通常2.0（HuggingFace实现）
默认值: 1.0（不惩罚）
注意: 不同框架参数名和范围可能不同！
```

**框架差异对照表**：

| 框架 | 参数名 | 取值范围 | 默认值 |
|------|--------|---------|--------|
| HuggingFace Transformers | `repetition_penalty` | 1.0 - 2.0+ | 1.0 |
| vLLM | `repetition_penalty` | 1.0 - 2.0 | 1.0 |
| llama.cpp | `--repeat-penalty` | 0.0 - 2.0+ | 1.1 |
| Ollama | `repeat_penalty` | 0.0 - 2.0 | 1.1 |
| OpenAI API | 无直接参数，用frequency_penalty替代 | - | - |

**作用机制**：对重复token的概率进行除法缩放（不同于加减法的penalty）。

```
P'(token) = P(token) / repetition_penalty  (如果token已出现过)
```

#### stop_sequences — 控制输出边界

```yaml
参数: stop（OpenAI）/ stop_sequences（Anthropic）
取值范围: 最多4个字符串（OpenAI）/ 最多4个字符串（Anthropic）
类型: string[]
默认值: 无
```

**作用机制**：当模型生成内容中出现指定的停止序列时，立即停止生成，且**不输出**该停止序列。

**Agent场景中的关键用途**：

```python
# 1. 控制多轮工具调用的边界
# 模型输出工具调用后应该停止，等待工具结果
response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=available_tools,
    stop=["<END_TOOL_CALL>"]  # 工具调用结束后停止
)

# 2. 结构化输出的分隔
# 要求模型按格式输出，在特定标记处停止
stop=["\n\n---", "###", "<DONE>"]

# 3. 防止模型过度生成
# 告诉模型"输出到XXX为止"，并把XXX设为stop序列
```

**面试常问**："stop_sequences和max_tokens的区别？"
- max_tokens是硬性截断（可能截断到句子中间）
- stop_sequences是语义截断（在指定边界停止，更优雅）
- 两者可以同时使用，先触发生效

#### seed — 结果复现

```yaml
参数: seed
取值范围: 整数（通常-2^31 到 2^31-1）
默认值: 随机（每次不同）
支持情况: OpenAI GPT-4o支持，Anthropic部分支持
```

**作用机制**：固定随机数生成器的种子，使相同输入产生相同输出。

**对Agent开发的价值**：
- **单元测试**：固定seed后，可以编写确定性测试
- **调试**：复现"奇怪的输出"以便分析
- **A/B对比**：固定seed对比不同prompt的效果

**重要限制**：
- seed只在temperature=0时才能保证完全一致性
- 即使seed相同，如果模型版本更新，输出可能变化
- 不同硬件/GPU可能产生微小差异

#### logit_bias — 令牌级偏见控制

```yaml
参数: logit_bias（OpenAI）
取值范围: -100 到 +100（整数），映射token_id到偏见值
类型: dict[int, int]
默认值: {}
```

**作用机制**：在采样前，直接修改指定token的logit值。

```python
# 强制模型生成"positive"而非"negative"
import tiktoken
enc = tiktoken.encoding_for_model("gpt-4o")

# 获取"positive"和"negative"的token ID
positive_tokens = enc.encode("positive")  # 如 [12345]
negative_tokens = enc.encode("negative")  # 如 [67890]

logit_bias = {
    positive_tokens[0]: +10,   # 大幅增加"positive"的概率
    negative_tokens[0]: -100   # 完全禁止"negative"（-100 = 概率趋近0）
}

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Sentiment of 'great product':"}],
    logit_bias=logit_bias,
    max_tokens=1  # 只生成一个token
)
```

**Agent场景中的高级用途**：
- **强制输出格式**：为JSON key的token增加偏见，确保格式一致性
- **安全过滤**：为敏感词的token设置-100偏见，完全阻止生成
- **多语言控制**：为非目标语言的token设置负偏见

**面试常问**："如何用logit_bias做内容安全过滤？"
- 构建敏感词表，获取对应的token ID
- 在API调用中设置这些token的logit_bias=-100
- 在应用层做二次校验（因为tokenization可能产生变体）

#### response_format / json_schema — 结构化输出

```yaml
参数: response_format（OpenAI）/ 无直接参数（Anthropic通过tools或prompt）
支持格式: "json_object", "json_schema"
```

**OpenAI结构化输出（GPT-4o支持json_schema）**：

```python
from pydantic import BaseModel
from typing import Literal

class TaskResult(BaseModel):
    status: Literal["success", "failure", "needs_human"]
    checklist_completed: bool
    safety_verified: bool
    output: str
    error_message: str | None

# 使用strict=True强制模型严格遵守schema
response = client.beta.chat.completions.parse(
    model="gpt-4o-2024-08-06",
    messages=[
        {"role": "system", "content": "Execute the task and report results."},
        {"role": "user", "content": task_description}
    ],
    response_format=TaskResult,  # Pydantic模型直接作为schema
)

result: TaskResult = response.choices[0].message.parsed
```

**对Agent行为的关键影响**：
- **消除了"格式解析失败"的问题**：模型被强制按schema输出
- **类型安全**：布尔值就是布尔值，不会变成字符串"true"
- **枚举约束**：`Literal["a", "b"]`确保只能取允许值
- **面试重点**：这是Agent可靠性的基础设施——如果模型输出无法可靠解析，整个Agent工作流就会崩溃

#### tools / tool_choice — 工具选择与控制

```yaml
参数: tools（OpenAI）/ tools（Anthropic）
tool_choice: "auto" | "required" | "none" | {type: "function", function: {name: "xxx"}}
```

**tool_choice选项详解**：

| 值 | 效果 | Agent场景 |
|----|------|----------|
| `"auto"` | 模型决定是否使用工具 | 通用对话Agent |
| `"required"` | 模型**必须**调用至少一个工具 | 强制工具使用场景 |
| `"none"` | 模型不能调用任何工具 | 纯文本回复场景 |
| `{type: "function", function: {name: "xxx"}}` | 强制调用指定工具 | 确定性工作流 |

**Agent开发中的关键实践**：

```python
# 1. 强制工具调用（确定性工作流）
# 当明确需要某个操作时，强制模型调用对应工具
response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=[search_tool, calculator_tool],
    tool_choice={"type": "function", "function": {"name": "search"}}
    # 注意：OpenAI API格式，Anthropic略有不同
)

# 2. Anthropic的tool_choice格式
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    messages=messages,
    tools=[search_tool, calculator_tool],
    tool_choice={"type": "tool", "name": "search"}
)

# 3. 动态tool_choice切换
# 在Agent循环中，根据当前状态决定下一步必须调用什么工具
async def agent_loop(state: AgentState):
    if state.step == "validate":
        tool_choice = {"type": "function", "function": {"name": "validate_input"}}
    elif state.step == "execute":
        tool_choice = {"type": "function", "function": {"name": "execute_task"}}
    else:
        tool_choice = "auto"
    # ...
```

#### reasoning_effort — 推理深度控制（OpenAI o系列）

```yaml
参数: reasoning_effort
取值范围: "low" | "medium" | "high"
默认值: "medium"
适用模型: o1, o1-mini, o3-mini 等推理模型
```

**作用机制**：控制模型在生成最终答案前进行"思考"的token预算。

| 级别 | 思考token预算 | 适用场景 |
|-----|-------------|---------|
| low | ~1/3 of max | 简单分类、快速回答 |
| medium | ~2/3 of max | 标准推理任务 |
| high | ~max | 复杂数学证明、深度分析 |

**对Agent行为的影响**：
- reasoning_effort="high"时，Agent会展示更详细的思考过程，减少推理错误
- 但消耗更多token和延迟时间
- **关键**：思考过程不计入output tokens收费（OpenAI的定价策略）

#### thinking / budget_tokens — Anthropic扩展思考模式

```yaml
参数: thinking（Anthropic Messages API）
类型: {"type": "enabled", "budget_tokens": int}
budget_tokens范围: 1024 - 模型输出上限（如32000）
适用模型: Claude 3.7 Sonnet（及后续支持扩展思考的模型）
```

**作用机制**：启用后，模型会在`<thinking>`标签内输出内部推理过程。

```python
# Anthropic扩展思考模式
response = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=20000,  # 总输出预算
    thinking={
        "type": "enabled",
        "budget_tokens": 16000  # 其中16000用于思考过程
    },
    messages=[{"role": "user", "content": complex_task}]
)

# 响应包含两部分：
# 1. thinking内容（budget_tokens分配的预算）
# 2. 最终输出（剩余预算）
for block in response.content:
    if block.type == "thinking":
        print(f"思考过程: {block.thinking}")
    elif block.type == "text":
        print(f"最终答案: {block.text}")
```

**对Agent开发的价值**：
- 可以检查模型的"思考过程"来调试Agent行为
- 思考预算不足时，模型会直接输出，质量可能下降
- 建议：复杂任务budget_tokens设为max_tokens的70-80%



---

### 2.B 微调参数（Fine-tuning Parameters）

微调是将预训练模型适配到特定任务的关键手段。对于Agent开发，微调可以提升模型在特定领域的决策能力、工具使用熟练度和输出格式一致性。

#### 全量微调（Full Fine-tuning）

全量微调更新模型的所有参数，效果最强但成本最高。

```yaml
核心超参数:
  learning_rate:        # 学习率
    取值: 1e-6 到 1e-4
    默认值: 通常 1e-5 到 2e-5
    影响: 过高导致灾难性遗忘，过低收敛太慢
    Agent场景: 建议从 1e-5 开始，使用cosine衰减
    
  batch_size:           # 批大小
    取值: 1 到 256（受显存限制）
    默认值: 8 或 16
    影响: 大批量更稳定但需要更多显存
    Agent场景: 显存允许时用较大batch（32+），配合gradient_accumulation
    
  epochs:               # 训练轮数
    取值: 1 到 10
    默认值: 3
    影响: 过多导致过拟合和灾难性遗忘
    Agent场景: 通常1-3轮即可，Agent任务不需要太多通用知识调整
    
  warmup_steps:         # 预热步数
    取值: 0 到 总步数的20%
    默认值: 总步数的 5-10%
    影响: 防止训练初期大学习率破坏预训练权重
    Agent场景: 设为总步数的 5%
    
  weight_decay:         # 权重衰减（L2正则化）
    取值: 0.0 到 0.1
    默认值: 0.01
    影响: 防止过拟合
    Agent场景: 0.01-0.05，Agent数据量通常不大，适当正则化
    
  gradient_accumulation_steps:  # 梯度累积
    取值: 1 到 64
    默认值: 1
    影响: 用时间换空间，模拟大批量训练
    Agent场景: 显存不足时的必选项
    
  max_grad_norm:        # 梯度裁剪
    取值: 0.1 到 10.0
    默认值: 1.0
    影响: 防止梯度爆炸
    
  lr_scheduler_type:    # 学习率调度器
    取值: "linear", "cosine", "cosine_with_restarts", "polynomial", "constant"
    默认值: "linear"
    Agent场景推荐: "cosine" 平滑衰减，配合warmup
```

**全量微调的适用场景和成本分析**：

| 因素 | 分析 |
|-----|------|
| **适用场景** | 需要深度调整模型行为；训练数据>10K条；团队有充足GPU资源 |
| **不适用场景** | 快速迭代实验；资源受限；只需轻量级调整 |
| **7B模型成本** | 单张A100 80GB即可全量微调，batch_size=4-8 |
| **70B模型成本** | 需要8×A100 80GB或分布式训练框架（DeepSpeed FSDP） |
| **灾难性遗忘** | 全量微调最大风险——模型丧失通用能力，只保留微调任务能力 |
| **建议** | Agent开发优先考虑LoRA/QLoRA，除非效果不达预期 |

**HuggingFace Trainer全量微调示例**：

```python
from transformers import (
    AutoModelForCausalLM, AutoTokenizer,
    TrainingArguments, Trainer
)
from datasets import load_dataset

# 1. 加载模型和tokenizer
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-8B-Instruct",
    torch_dtype="auto",
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B-Instruct")

# 2. 准备训练数据
dataset = load_dataset("json", data_files="agent_training_data.jsonl")

def format_example(example):
    # 将Agent交互数据格式化为对话格式
    messages = [
        {"role": "system", "content": example["system_prompt"]},
        {"role": "user", "content": example["user_input"]},
        {"role": "assistant", "content": example["expected_output"]}
    ]
    text = tokenizer.apply_chat_template(messages, tokenize=False)
    return {"text": text}

dataset = dataset.map(format_example)

# 3. 训练参数
training_args = TrainingArguments(
    output_dir="./agent-model-full",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,      # 等效batch_size=16
    learning_rate=1e-5,
    warmup_ratio=0.05,
    weight_decay=0.01,
    lr_scheduler_type="cosine",
    logging_steps=10,
    save_strategy="epoch",
    fp16=True,                          # 混合精度训练
    gradient_checkpointing=True,        # 梯度检查点节省显存
)

# 4. 开始训练
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
)
trainer.train()
```

#### LoRA微调（Parameter-Efficient Fine-Tuning）

LoRA（Low-Rank Adaptation）只训练少量"适配器"参数，冻结原始模型权重，是Agent微调的**首选方案**。

```yaml
核心超参数:
  lora_rank (r):        # LoRA秩
    取值: 1, 2, 4, 8, 16, 32, 64, 128
    默认值: 8 或 16
    影响: 秩越高，表达能力越强，但参数量也越大
    Agent场景: 
      - 简单任务（分类、格式化）: r=4-8
      - 复杂任务（推理、决策）: r=16-32
      - 需要学习新知识: r=32-64
    面试重点: "r=8和r=64的区别？" → "r=64的LoRA矩阵更大，可以学更复杂的变换，
              但参数量是r=8的8倍。不是越大越好，要看任务复杂度。"
    
  lora_alpha:           # LoRA缩放参数
    取值: 通常等于rank或rank的2倍
    默认值: 16（当r=8时）
    影响: 控制LoRA适配器的输出缩放，实际缩放因子 = alpha / rank
    Agent场景: alpha/rank 比值通常在 1-2 之间
    计算公式: scaling = lora_alpha / lora_rank
    
  lora_dropout:         # LoRA层的dropout率
    取值: 0.0 到 0.5
    默认值: 0.05 或 0.1
    影响: 防止LoRA适配器过拟合
    Agent场景: 0.05-0.1，数据量小（<1K）时可提高到0.2
    
  target_modules:       # 应用LoRA的目标模块
    默认值: 因模型架构而异
    常见值:
      - LLaMA/Qwen: ["q_proj", "v_proj"]  # 最轻量
      - 更全面: ["q_proj", "k_proj", "v_proj", "o_proj"]  # 推荐
      - 最全: ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    影响: 覆盖越多模块，微调效果越好，参数量也越大
    Agent场景: 建议至少覆盖注意力层 ["q_proj", "k_proj", "v_proj", "o_proj"]
    
  bias:                 # 是否微调偏置项
    取值: "none", "all", "lora_only"
    默认值: "none"
    影响: "none"最省参数，"all"效果可能略好
    Agent场景: "none"即可
    
  modules_to_save:      # 除了LoRA外，完整训练某些模块
    取值: ["embed_tokens", "lm_head"] 等
    默认值: null
    影响: 如果任务需要新词汇，需要训练embedding层
    Agent场景: 如果微调数据包含特殊token，设为 ["embed_tokens", "lm_head"]
```

**LoRA rank的选择策略**：

| rank | 参数量（7B模型） | 适用场景 | 微调效果 |
|------|----------------|---------|---------|
| 4 | ~2M (0.03%) | 极简任务、快速实验 | 轻微调整风格 |
| 8 | ~4M (0.06%) | 格式化输出、简单分类 | 明显风格适配 |
| 16 | ~8M (0.12%) | 工具调用、决策逻辑 | 较强任务适配 |
| 32 | ~16M (0.24%) | 复杂推理、新知识 | 深度能力调整 |
| 64 | ~32M (0.48%) | 需要学习大量新内容 | 接近全量微调效果 |
| 128 | ~64M (0.96%) | 接近全量微调的场景 | 效果接近但速度更快 |

**LoRA微调完整示例**：

```python
from peft import LoraConfig, get_peft_model, TaskType
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments

# 1. 加载基础模型（可加载4bit量化版进一步节省显存）
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-8B-Instruct",
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

# 2. 配置LoRA
lora_config = LoraConfig(
    r=16,                          # 秩
    lora_alpha=32,                 # alpha = 2 * r
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    bias="none",
    task_type=TaskType.CAUSAL_LM,
    # 如果需要学习新token
    modules_to_save=["embed_tokens", "lm_head"]
)

# 3. 应用LoRA适配器
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# 输出示例: trainable params: 16,785,408 || all params: 8,050,147,328 
#           || trainable%: 0.2085

# 4. 训练（与全量微调相同流程，但只训练LoRA参数）
trainer = Trainer(model=model, args=training_args, train_dataset=dataset)
trainer.train()

# 5. 保存和加载LoRA适配器
model.save_pretrained("./lora-adapter-r16")  # 只保存适配器（~30MB）

# 加载时使用
from peft import PeftModel
base_model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.1-8B-Instruct")
model = PeftModel.from_pretrained(base_model, "./lora-adapter-r16")
model = model.merge_and_unload()  # 合并到基础模型（可选）
```

**面试常问**："LoRA的原理是什么？为什么比全量微调省参数？"
- LoRA假设权重更新的增量 ΔW 是低秩的，即 ΔW = BA，其中B是d×r，A是r×d，r << d
- 原始参数量：d×d；LoRA参数量：d×r + r×d = 2dr
- 当r=16, d=4096时，LoRA参数量只有全量的 2×16/4096 = 0.78%

#### QLoRA微调（量化 + LoRA）

QLoRA使用4-bit量化加载基础模型，大幅降低显存需求，是**单卡消费级GPU微调大模型**的解决方案。

```yaml
核心配置参数:
  load_in_4bit:         # 使用4-bit量化加载
    取值: true / false
    效果: 7B模型从14GB显存降至~4GB
    
  bnb_4bit_compute_dtype:  # 4-bit计算的中间类型
    取值: "float16", "bfloat16", "float32"
    默认值: "float16"
    影响: 计算精度，bfloat16更稳定但需Ampere+ GPU
    
  bnb_4bit_quant_type:  # 量化类型
    取值: "nf4", "fp4"
    默认值: "nf4"
    影响: nf4（Normal Float 4）通常比fp4效果更好
    
  bnb_4bit_use_double_quant:  # 嵌套量化
    取值: true / false
    默认值: true
    影响: 对量化常数进行二次量化，进一步节省显存
    
  bnb_4bit_quant_storage:  # 量化参数存储类型
    取值: "uint8"
    影响: 量化参数的存储精度
    
  # 分页优化器（QLoRA关键创新）
  gradient_checkpointing: true
    效果: 以计算换显存
  optim: "paged_adamw_8bit"  # 分页优化器
    效果: 当显存不足时，优化器状态自动分页到CPU内存
    关键: 这是QLoRA能在单卡24GB显存上微调65B模型的核心
```

**量化级别的取舍**：

| 量化级别 | 显存节省 | 精度损失 | 适用场景 |
|---------|---------|---------|---------|
| FP16（无量化） | 基准 | 无 | 全精度推理、微调 |
| BF16 | 与FP16相同 | 极小 | 推荐替代FP16，训练更稳定 |
| INT8 | ~50% | 很小 | 精度敏感场景的快速推理 |
| NF4（QLoRA默认） | ~75% | 小 | 4-bit微调的最佳实践 |
| FP4 | ~75% | 中等 | 不太推荐 |
| GGUF Q4_K_M | ~75% | 小-中等 | llama.cpp推理推荐 |
| GGUF Q5_K_M | ~69% | 很小 | 质量优先的本地推理 |
| GGUF Q8_0 | ~50% | 极小 | 几乎无损的本地推理 |

**QLoRA完整微调示例**：

```python
from transformers import (
    AutoModelForCausalLM, AutoTokenizer,
    BitsAndBytesConfig, TrainingArguments
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# 1. 4-bit量化配置
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

# 2. 量化加载模型（7B模型只需~4GB显存）
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-8B-Instruct",
    quantization_config=bnb_config,
    device_map="auto",  # 自动分配层到GPU/CPU
)
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B-Instruct")

# 3. 为量化模型准备训练
model = prepare_model_for_kbit_training(model)
# 这做了：
# - 冻结所有4-bit参数
# - 添加LoRA适配器时启用梯度检查点
# - 处理输入嵌入的归一化

# 4. LoRA配置
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, lora_config)

# 5. 分页优化器配置
training_args = TrainingArguments(
    output_dir="./qlora-agent-model",
    num_train_epochs=3,
    per_device_train_batch_size=1,      # QLoRA通常batch_size=1
    gradient_accumulation_steps=8,       # 累积达到等效batch=8
    learning_rate=2e-4,                  # QLoRA可用稍大学习率
    warmup_ratio=0.05,
    lr_scheduler_type="cosine",
    optim="paged_adamw_8bit",           # 分页优化器！
    gradient_checkpointing=True,
    logging_steps=10,
    save_strategy="epoch",
    fp16=False,
    bf16=True,                           # bfloat16更稳定
)

trainer = Trainer(model=model, args=training_args, train_dataset=dataset)
trainer.train()

# 保存适配器
model.save_pretrained("./qlora-adapter")
```

#### 微调对Agent能力的影响

**何时需要微调而非提示工程**：

| 场景 | 提示工程 | 微调 | 理由 |
|-----|---------|------|------|
| 输出格式不稳定 | ✅ 先尝试 | 备选 | JSON Schema/结构化输出通常足够 |
| 需要特定领域知识 | ❌ 效果有限 | ✅ 推荐 | RAG+微调协同 |
| 工具调用格式不兼容 | ✅ 先用函数定义 | ✅ 严重时微调 | 教会模型特定工具格式 |
| 长程规划能力差 | ⚠️ 部分有效 | ✅ 推荐 | 用规划数据微调 |
| 安全行为不遵守 | ❌ 不可靠 | ✅ 推荐 | 需要内化安全准则 |
| 响应速度慢 | ❌ 无关 | ✅ 小模型+微调 | 用小模型微调达到大模型效果 |

**微调Agent的决策能力 vs 通用知识**：

```
微调的主要价值在于改变模型的行为模式，而非注入新知识：

✅ 微调擅长：
   - 教会模型特定输出格式
   - 调整模型的"风格"和"语气"
   - 强化特定类型的推理模式（如Agent的规划链）
   - 让模型更"听话"（遵循指令的能力）

⚠️ 微调不擅长：
   - 注入大量新的事实知识（用RAG更好）
   - 完全改变模型的基础能力（如从不会编程到会编程）
   - 纠正模型的根本性偏见

最佳实践：RAG提供知识 + 微调调整行为
```

**微调和RAG的协同架构**：

```
用户查询
  │
  ▼
┌──────────────────┐
│   RAG检索层       │  ← 注入实时知识（文档、代码库、API文档）
│  （向量数据库）    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   微调后的LLM     │  ← 行为调整（输出格式、决策逻辑、工具使用）
│  （LoRA适配器）   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   工具执行层      │  ← 实际调用API/执行代码
│  （Agent Loop）   │
└──────────────────┘
```

---

### 2.C Agent场景参数调优决策表

#### 代码生成Agent

```yaml
推荐参数:
  model: "claude-3-5-sonnet-20241022"  # 或 "gpt-4o"
  temperature: 0.1                      # 低随机性，代码需要确定性
  top_p: 0.9                           
  max_tokens: 4096                      # 足够生成完整函数
  frequency_penalty: 0.1                # 轻微抑制重复
  presence_penalty: 0.0                 # 代码命名需要一致性
  stop_sequences: []                    # 让模型决定结束位置
  
QClaw/OpenClaw配置:
  response_format:
    type: "json_schema"
    schema:
      type: object
      required: [code, explanation, test_cases]
      properties:
        code: {type: string, description: "生成的代码"}
        language: {type: string, enum: [python, javascript, typescript]}
        explanation: {type: string}
        test_cases: {type: array, items: {type: string}}
  tool_choice: "auto"  # 允许使用代码执行工具验证
  
面试考点:
  Q: "代码生成的temperature为什么要低？"
  A: "代码是结构化输出，高temperature会引入语法错误、不一致的变量名、
      甚至幻觉API。temperature=0.1-0.2能在保持一致性的同时有微小变化。"
```

#### 需求分析Agent

```yaml
推荐参数:
  model: "claude-3-5-sonnet-20241022"  # 长上下文+强理解能力
  temperature: 0.5-0.7                  # 需要一定创造性理解模糊需求
  top_p: 0.9
  max_tokens: 8000                      # 输出结构化需求文档
  frequency_penalty: 0.2
  presence_penalty: 0.2                 # 鼓励多角度分析
  
QClaw/OpenClaw配置:
  system_prompt: |
    你是一个需求分析师。你的任务是将用户的模糊描述转化为结构化的PRD。
    你必须：
    1. 先输出[UNDERSTANDING]你对用户需求的理解
    2. 列出[ASSUMPTIONS]你的假设（让用户确认）
    3. 输出[PRD]结构化的需求文档
    4. 最后列出[QUESTIONS]需要用户澄清的问题
    
  tools:
    - name: search_similar_requirements
    - name: generate_user_stories
```

#### 创意写作Agent

```yaml
推荐参数:
  model: "claude-3-5-sonnet-20241022"  # 或 "gpt-4o"
  temperature: 0.9-1.0                  # 高随机性促进创意
  top_p: 0.95
  top_k: 50                             # 如果使用本地模型
  max_tokens: 4000
  frequency_penalty: 0.4                # 抑制重复词汇
  presence_penalty: 0.4                 # 促进话题多样性
  
注意事项:
  - temperature>1.0时可能导致输出不连贯
  - 创意写作是唯一推荐temperature>0.8的场景
```

#### 工具调用Agent（确定性最强）

```yaml
推荐参数:
  model: "gpt-4o"  # 或 "claude-3-5-sonnet"
  temperature: 0.0                     # 工具参数必须精确
  top_p: 0.0                           # 贪婪解码
  max_tokens: 4000                     # 多轮工具调用
  frequency_penalty: 0.0
  presence_penalty: 0.0
  tool_choice: "auto"                  # 模型自主选择工具
  response_format: null                # 工具调用有专用格式
  
QClaw/OpenClaw配置（高安全场景）:
  # 强制每次工具调用前输出自检清单
  system_prompt: |
    你是一个安全的工具执行Agent。在每次调用工具前，你必须：
    1. 在<thinking>标签中分析任务
    2. 在<checklist>标签中输出安全检查清单：
       - [ ] 工具参数已通过schema验证
       - [ ] 操作在权限范围内
       - [ ] 如果是写操作，已确认备份存在
    3. 只有所有检查项勾选后才能调用工具
    
  hooks:
    PreToolUse:
      - validate_parameters
      - check_permissions
      - log_audit_trail
```

#### 通用Agent参数调优速查表

| Agent类型 | temperature | top_p | max_tokens | frequency_penalty | presence_penalty | 特殊配置 |
|----------|-------------|-------|-----------|-------------------|------------------|---------|
| **代码生成** | 0.1-0.2 | 0.9 | 2048-4096 | 0.1 | 0.0 | json_schema约束输出 |
| **代码审查** | 0.2-0.3 | 0.9 | 4000-8000 | 0.0 | 0.1 | 长上下文模型 |
| **工具调用** | 0.0-0.1 | 0.1 | 2048-4096 | 0.0 | 0.0 | tool_choice控制 |
| **需求分析** | 0.5-0.7 | 0.9 | 4000-8000 | 0.2 | 0.2 | 结构化输出模板 |
| **文档生成** | 0.3-0.5 | 0.9 | 4000-8000 | 0.1 | 0.1 | markdown格式 |
| **创意写作** | 0.8-1.0 | 0.95 | 2048-4000 | 0.4 | 0.4 | 高penalty防重复 |
| **分类/判断** | 0.0-0.2 | 0.1 | 50-100 | 0.0 | 0.0 | logit_bias强制输出 |
| **对话Agent** | 0.7-0.8 | 0.9 | 1024-2048 | 0.3 | 0.3 | 多轮上下文管理 |
| **数据分析** | 0.1-0.3 | 0.9 | 2048-4000 | 0.0 | 0.0 | 代码执行工具 |
| **安全审查** | 0.0-0.1 | 0.1 | 1024-2048 | 0.0 | 0.0 | 确定性判断 |

#### 参数调优常见陷阱

```yaml
陷阱1: "temperature=0就万无一失"
  真相: GPU浮点运算有非确定性，即使T=0也可能有微小差异
  解决: 同时设置seed，或使用确定性采样模式
  
陷阱2: "top_p和temperature重复控制，只用一个就行"
  真相: 两者作用不同，协同使用效果更好
  解决: temperature控制分布形状，top_p控制候选集范围
  
陷阱3: "max_tokens设很大不会有害"
  真相: 过大的max_tokens可能导致模型"填充"无意义内容
  解决: 根据任务合理设置，配合stop_sequences使用
  
陷阱4: "penalty值越大越好"
  真相: penalty>1.0可能导致输出不自然、用词怪异
  解决: 从0.1开始逐步调整，观察效果
  
陷阱5: "所有模型对这些参数的响应相同"
  真相: 不同模型家族（GPT/Claude/Llama）对参数敏感度差异很大
  解决: 针对具体模型微调参数，不要跨模型照搬
  
陷阱6: "Agent用最高级模型总是最好"
  真相: 简单任务用小模型更快更便宜，且可能更可控
  解决: 多模型路由，任务分发给合适的模型
```


---

## 第三部分：模型部署方案

### 3.A 本地轻量部署（开发测试用）

本地部署是Agent开发的第一步。开发阶段需要快速迭代、离线可用、零成本运行，以下方案满足这些需求。

#### Ollama（最推荐的本地开发方案）

Ollama是目前本地运行LLM最简单的方案，一条命令即可运行模型，提供REST API兼容OpenAI格式。

**安装与启动**：

```bash
# macOS/Linux - 一键安装
curl -fsSL https://ollama.com/install.sh | sh

# Windows - 下载安装包 https://ollama.com/download

# 验证安装
ollama --version
# ollama version 0.3.x

# 拉取并运行模型（自动下载，首次需要下载时间）
ollama run llama3.1:8b          # Meta Llama 3.1 8B
ollama run qwen2.5:14b          # 阿里Qwen 2.5 14B（中文优秀）
ollama run deepseek-coder:6.7b  # 代码专用模型
ollama run nomic-embed-text     # 嵌入模型（用于RAG）

# 查看本地模型列表
ollama list

# 删除模型释放空间
ollama rm llama3.1:70b
```

**REST API调用（OpenAI兼容）**：

```python
import requests

# Ollama原生API
response = requests.post('http://localhost:11434/api/generate', json={
    "model": "llama3.1:8b",
    "prompt": "用Python写一个快速排序",
    "stream": False,
    "options": {
        "temperature": 0.2,
        "num_predict": 1024,    # 等价于max_tokens
        "top_p": 0.9,
    }
})
print(response.json()["response"])

# OpenAI兼容API（推荐，代码迁移零成本）
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",  # 关键：/v1路径
    api_key="ollama"  # 任意值，Ollama不验证
)

response = client.chat.completions.create(
    model="llama3.1:8b",  # Ollama中的模型名
    messages=[
        {"role": "system", "content": "你是一个Python专家。"},
        {"role": "user", "content": "写一个快速排序"}
    ],
    temperature=0.2,
    max_tokens=1024,
)
print(response.choices[0].message.content)

# 流式输出
for chunk in client.chat.completions.create(
    model="llama3.1:8b",
    messages=[{"role": "user", "content": "讲个故事"}],
    stream=True,
):
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

**自定义Modelfile（SYSTEM提示词和参数配置）**：

Modelfile是Ollama的"Dockerfile"，可以自定义模型的系统提示词、参数等。

```dockerfile
# Modelfile - 自定义Agent专用模型
FROM llama3.1:8b

# 系统提示词（相当于永久注入的System Prompt）
SYSTEM """你是一个专业的代码审查Agent。你的职责是：
1. 检查代码的安全漏洞（SQL注入、XSS、路径遍历等）
2. 检查代码风格和最佳实践
3. 提供具体的改进建议，附带修正后的代码

你必须以JSON格式输出审查结果：
{
  "severity": "high|medium|low|info",
  "issues": [
    {
      "type": "security|performance|style",
      "location": "行号范围",
      "description": "问题描述",
      "suggestion": "修正代码",
      "references": ["OWASP链接或文档链接"]
    }
  ]
}"""

# 参数配置
PARAMETER temperature 0.1        # 低随机性，审查需要确定性
PARAMETER top_p 0.9
PARAMETER num_ctx 8192           # 上下文窗口大小
PARAMETER num_predict 4096       # 最大输出长度

# 停止序列
PARAMETER stop "</review>"

# 许可证
LICENSE "MIT"
```

```bash
# 构建自定义模型
ollama create code-reviewer -f ./Modelfile

# 运行自定义模型
ollama run code-reviewer

# 查看模型详情
ollama show code-reviewer
```

**Ollama常用模型速查表**：

| 模型 | 参数 | 量化 | 显存需求 | 适用场景 |
|-----|------|------|---------|---------|
| llama3.1:8b | 8B | Q4 | ~5GB | 通用对话、代码辅助 |
| llama3.1:70b | 70B | Q4 | ~40GB | 复杂推理、深度分析 |
| qwen2.5:7b | 7B | Q4 | ~5GB | 中文任务优秀 |
| qwen2.5:14b | 14B | Q4 | ~9GB | 中文+代码综合 |
| qwen2.5:32b | 32B | Q4 | ~20GB | 接近GPT-4质量 |
| deepseek-coder:6.7b | 6.7B | Q4 | ~4GB | 代码生成专用 |
| codellama:7b-code | 7B | Q4 | ~5GB | 代码补全 |
| mistral:7b | 7B | Q4 | ~5GB | 通用任务 |
| nomic-embed-text | - | - | ~1GB | 文本嵌入（RAG） |

**与QClaw/OpenClaw集成**：

```yaml
# QClaw配置 - 使用本地Ollama模型
model:
  provider: "ollama"
  base_url: "http://localhost:11434/v1"
  models:
    default: "qwen2.5:14b"
    code: "deepseek-coder:6.7b"
    fast: "qwen2.5:7b"       # 简单任务用小模型
    embedding: "nomic-embed-text"
  
  # 参数覆盖
  parameters:
    temperature: 0.2
    max_tokens: 4096
    
  # 降级策略
  fallback:
    - "qwen2.5:7b"           # 首选模型不可用时降级
    - "llama3.1:8b"
```

```python
# OpenClaw集成示例
from openclaw import Agent

agent = Agent(
    model="ollama:qwen2.5:14b",  # 使用Ollama本地模型
    base_url="http://localhost:11434/v1"
)

# 所有OpenClaw功能（工具调用、RAG等）正常工作
result = agent.run("分析这个日志文件", tools=[file_tool])
```

#### llama.cpp（极致性能优化方案）

llama.cpp是Georgi Gerganov开发的C/C++推理引擎，以极高的CPU推理效率和广泛的量化支持著称。它是Ollama的底层引擎之一。

**GGUF量化模型获取**：

GGUF是llama.cpp的专用模型格式，经过量化后体积大幅缩小。

```bash
# 方式1：从HuggingFace下载预量化模型
# 推荐源: https://huggingface.co/TheBloke  (社区量化专家)
# 推荐源: https://huggingface.co/bartowski  (更新的量化)

# 下载示例
wget https://huggingface.co/bartowski/Llama-3.1-8B-Instruct-GGUF/resolve/main/Llama-3.1-8B-Instruct-Q4_K_M.gguf

# 方式2：自己转换（如果有原始PyTorch模型）
python convert_hf_to_gguf.py \
  --outfile model.gguf \
  --outtype q4_k_m \
  /path/to/huggingface/model
```

**量化级别详细对比**：

| 量化类型 | 每权重位数 | 文件大小(7B) | 质量 | 速度 | 推荐使用场景 |
|---------|-----------|-------------|------|------|------------|
| F16 | 16 | 13.5GB | 基准 | 基准 | 无需量化的场景 |
| Q8_0 | 8 | 7.0GB | 几乎无损 | 快 | 质量优先的生产环境 |
| Q6_K | 6 | 5.3GB | 极微小损失 | 快 | 平衡质量与速度 |
| Q5_K_M | 5 | 4.7GB | 微小损失 | 很快 | **推荐的生产选择** |
| Q5_K_S | 5 | 4.5GB | 较小损失 | 很快 | 速度优先 |
| **Q4_K_M** | **4** | **4.1GB** | **可接受损失** | **很快** | **最常用推荐** |
| Q4_K_S | 4 | 3.9GB | 中等损失 | 极快 | 资源受限 |
| Q3_K_M | 3 | 3.2GB | 明显损失 | 极快 | 仅CPU推理 |
| Q2_K | 2 | 2.5GB | 较大损失 | 最快 | 仅测试用 |

> **选择建议**：日常开发用Q4_K_M，追求质量用Q5_K_M或Q8_0，极端资源受限用Q3_K_M，绝不用Q2_K。

**启动命令和API服务**：

```bash
# 基本交互模式
./main -m Llama-3.1-8B-Instruct-Q4_K_M.gguf \
  --color \
  --ctx-size 4096 \
  -p "You are a helpful assistant."

# 启动API服务器（OpenAI兼容）
./server \
  -m Llama-3.1-8B-Instruct-Q4_K_M.gguf \
  --ctx-size 8192 \              # 上下文长度
  --port 8080 \                   # API端口
  --host 0.0.0.0 \               # 监听地址
  --n-gpu-layers 35 \             # 卸载到GPU的层数（0=纯CPU）
  --threads 8 \                   # CPU线程数
  --batch-size 512 \              # 批大小
  --ubatch-size 512

# 关键参数说明：
# --n-gpu-layers: 越大GPU利用率越高，设为999尝试全部加载到GPU
# --threads: 通常设为物理核心数，超线程帮助不大
# --ctx-size: 根据可用显存/内存设置，8192需约1-2GB额外显存

# API调用示例
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.1-8b",
    "messages": [{"role": "user", "content": "Hello"}],
    "temperature": 0.7,
    "max_tokens": 256
  }'
```

**Python绑定（llama-cpp-python）**：

```bash
# 安装（带CUDA支持）
CMAKE_ARGS="-DLLAMA_CUDA=on" pip install llama-cpp-python

# 纯CPU版本
pip install llama-cpp-python

# Apple Silicon（Metal加速）
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python
```

```python
from llama_cpp import Llama

# 加载模型
llm = Llama(
    model_path="./Llama-3.1-8B-Instruct-Q4_K_M.gguf",
    n_ctx=8192,              # 上下文窗口
    n_gpu_layers=-1,         # -1 = 尽可能多的层放到GPU
    verbose=True,
    # 性能调优参数
    n_threads=8,             # CPU线程
    n_batch=512,             # 批处理大小
    use_mmap=True,           # 内存映射（推荐）
    use_mlock=False,         # 锁定内存（root权限时需要）
)

# 生成
output = llm(
    prompt="<|user|>\n写一个快速排序<|assistant|>\n",
    max_tokens=1024,
    temperature=0.7,
    top_p=0.9,
    top_k=40,
    repeat_penalty=1.1,       # llama.cpp使用repeat_penalty
    stop=["<|user|>", "</s>"],
    stream=False,
)
print(output["choices"][0]["text"])

# 释放资源
llm.close()
```

#### LM Studio（图形化方案）

LM Studio提供图形化界面，适合不熟悉命令行的开发者。

```
下载: https://lmstudio.ai/
支持: macOS, Windows, Linux

核心功能:
1. 模型浏览器 - 内置HuggingFace模型搜索和一键下载
2. 聊天界面 - 直接对话测试
3. 本地推理服务器 - 启动OpenAI兼容API
4. 模型管理 - 量化级别选择、加载参数配置

启动本地服务器:
1. 打开LM Studio
2. 下载模型（如Llama-3.1-8B-Instruct）
3. 右侧"Developer"标签 → "Start Server"
4. 默认地址: http://localhost:1234/v1

API调用（与Ollama完全相同）:
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
```

**三种本地部署方案对比**：

| 特性 | Ollama | llama.cpp | LM Studio |
|------|--------|-----------|-----------|
| 安装难度 | ⭐ 最简单 | ⭐⭐⭐ 需编译 | ⭐ 图形安装 |
| 命令行操作 | ✅ 完善 | ✅ 完善 | ❌ 无 |
| 图形界面 | ❌ 无 | ❌ 无 | ✅ 完善 |
| API兼容性 | ✅ OpenAI兼容 | ✅ OpenAI兼容 | ✅ OpenAI兼容 |
| 模型管理 | ✅ pull/rm/list | 手动管理 | ✅ 图形管理 |
| 量化选项 | 有限 | 最全面 | 中等 |
| 性能调优 | 中等 | 最精细 | 图形化调参 |
| 多GPU支持 | 有限 | ✅ 完善 | 有限 |
| 适用人群 | 开发者首选 | 性能极致追求者 | 初学者/非技术用户 |
| **推荐度** | **⭐⭐⭐⭐⭐** | ⭐⭐⭐⭐ | ⭐⭐⭐ |

### 3.B 生产级服务部署（高并发用）

生产环境需要处理高并发请求、低延迟、高吞吐量，以下方案专为生产设计。

#### vLLM（生产部署首选方案）

vLLM是UC Berkeley开发的高性能推理引擎，核心创新是**PagedAttention**，能显著提升GPU利用率。

**PagedAttention技术原理**：

传统LLM推理中，KV Cache（注意力键值缓存）使用连续内存分配，导致大量内存碎片和浪费。PagedAttention借鉴操作系统虚拟内存的页式管理思想：

```
传统方式（连续分配）:
┌─────────────────────────────────────────┐
│ Request A: [████████████    ] 60%利用率 │  ← 预分配max_tokens，实际用不完
│ Request B: [██████          ] 40%利用率 │  ← 碎片浪费
│ Request C: [████████        ] 50%利用率 │
└─────────────────────────────────────────┘
实际利用率: ~30-50%

PagedAttention（分页管理）:
┌─────────────────────────────────────────┐
│ 物理KV Cache块: [Block0][Block1][Block2][Block3][Block4][Block5]... │
│ Request A: 映射 → [Block0][Block2][Block5]  （非连续，按需分配）│
│ Request B: 映射 → [Block1][Block3]                              │
│ Request C: 映射 → [Block4][Block6]                              │
└─────────────────────────────────────────┘
实际利用率: >90%
```

关键优势：
1. **内存效率**：KV Cache利用率从30-50%提升到90%+
2. **连续批处理**：请求动态加入批次，无需等待整批完成
3. **高并发**：相同GPU可同时服务更多请求

**连续批处理（Continuous Batching）**：

```
静态批处理（传统）:
时间轴: |====Batch 1====|====Batch 2====|====Batch 3====|
        Request A 先完成也要等整个批次完成

连续批处理（vLLM）:
时间轴: |==A==|  ← A完成立即返回
              |==B==|==C==|==D==|  ← 新请求D在C运行时加入
                        |==E==|  ← E在D运行时加入
```

**安装与启动**：

```bash
# 安装（需要CUDA 11.8+或12.1+）
pip install vllm

# 启动API服务器
python -m vllm.entrypoints.openai.api_server \
  --model "meta-llama/Llama-3.1-8B-Instruct" \
  --tensor-parallel-size 1 \            # GPU数量（多卡推理）
  --gpu-memory-utilization 0.90 \        # GPU显存利用率上限
  --max-model-len 8192 \                 # 最大上下文长度
  --max-num-seqs 256 \                   # 最大并发序列数
  --port 8000 \
  --host 0.0.0.0 \
  --dtype bfloat16 \                     # 数据类型
  --quantization None                    # 量化方式（awq/gptq/fp8）

# 使用AWQ量化模型（4bit，显存减半）
python -m vllm.entrypoints.openai.api_server \
  --model "TheBloke/Llama-3.1-8B-Instruct-AWQ" \
  --quantization awq \
  --gpu-memory-utilization 0.90

# 多GPU并行（张量并行）
python -m vllm.entrypoints.openai.api_server \
  --model "meta-llama/Llama-3.1-70B-Instruct" \
  --tensor-parallel-size 4               # 4张GPU同时服务

# 后台运行（systemd服务示例）
# /etc/systemd/system/vllm.service
[Unit]
Description=vLLM Inference Server
After=network.target

[Service]
Type=simple
User=vllm
Environment="CUDA_VISIBLE_DEVICES=0,1"
ExecStart=/opt/venv/bin/python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --tensor-parallel-size 2 \
  --gpu-memory-utilization 0.85 \
  --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**vLLM关键性能参数**：

```yaml
参数详解:
  tensor_parallel_size: 
    说明: 张量并行GPU数量
    设置: 1（单卡）, 2, 4, 8
    注意: 必须≤物理GPU数，且能被注意力头数整除
    
  gpu_memory_utilization:
    说明: KV Cache可用显存比例
    设置: 0.85-0.95
    影响: 越高并发能力越强，但留太少会OOM
    建议: 0.90（留10%余量）
    
  max_model_len:
    说明: 最大上下文长度
    设置: 按模型支持设置（如8192, 32768, 128000）
    影响: 越长KV Cache越大，并发数越少
    权衡: 如果大部分请求<4K，设为8192而非128K
    
  max_num_seqs:
    说明: 最大并发序列数
    设置: 256, 512
    影响: 越大并发越高，但每个序列的KV Cache越小
    
  dtype:
    说明: 模型加载数据类型
    设置: float16, bfloat16, float32
    建议: bfloat16（动态范围更好，训练稳定）
    注意: Ampere+ GPU才支持bfloat16
    
  quantization:
    说明: 加载量化模型
    选项: awq, gptq, squeezellm, fp8
    AWQ: 4bit，精度最好，推荐
    GPTQ: 4bit，速度快但精度稍差
    FP8: 需要Hopper架构GPU（H100）
    
  pipeline_parallel_size:
    说明: 流水线并行（层间分布到不同GPU）
    与张量并行区别: 张量并行是层内拆分（通信多，适合单节点）
                     流水线并行是层间拆分（通信少，适合多节点）
```

**vLLM API调用**：

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy"  # vLLM不验证API key
)

# 标准对话
response = client.chat.completions.create(
    model="meta-llama/Llama-3.1-8B-Instruct",  # 必须与服务启动时一致
    messages=[{"role": "user", "content": "Hello"}],
    temperature=0.7,
    max_tokens=512,
)

# vLLM特有参数
response = client.chat.completions.create(
    model="meta-llama/Llama-3.1-8B-Instruct",
    messages=messages,
    # 额外参数（通过extra_body传递vLLM特定参数）
    extra_body={
        "top_k": 50,                    # vLLM支持top_k
        "repetition_penalty": 1.05,     # vLLM支持重复惩罚
        "min_p": 0.05,                  # 最小概率阈值
        "guided_json": {                # 结构化输出（JSON模式）
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "score": {"type": "number"}
            }
        }
    }
)

# 批量推理（vLLM优势场景）
import asyncio

async def batch_inference(prompts):
    tasks = [
        client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=[{"role": "user", "content": p}],
        )
        for p in prompts
    ]
    results = await asyncio.gather(*tasks)
    return results

# 100个并发请求
prompts = [f"Summarize: {text}" for text in documents]
results = asyncio.run(batch_inference(prompts))
```

#### Text Generation Inference（TGI）

TGI是HuggingFace官方出品的高性能推理服务，特点是多语言支持和与HuggingFace生态深度集成。

```bash
# Docker一键启动
docker run --gpus all \
  -p 8080:80 \
  -v $(pwd)/data:/data \
  ghcr.io/huggingface/text-generation-inference:2.0 \
  --model-id meta-llama/Llama-3.1-8B-Instruct \
  --quantize awq \
  --max-input-length 8192 \
  --max-total-tokens 16384 \
  --max-batch-prefill-tokens 8192

# 关键参数
# --quantize: awq, eetq, gptq, bitsandbytes
# --sharded: true（多卡）
# --num-shard: 2（分片数）
```

**vLLM vs TGI 选型对比**：

| 特性 | vLLM | TGI |
|-----|------|-----|
| 核心创新 | PagedAttention | FlashAttention + Safetensors |
| 性能 | 并发吞吐量更高 | 首token延迟更低 |
| 量化支持 | AWQ, GPTQ, FP8 | AWQ, GPTQ, bitsandbytes |
| 多语言 | 良好 | **更优**（原生HuggingFace） |
| 部署难度 | 简单 | 中等（Docker为主） |
| 与HF生态集成 | 良好 | **深度集成** |
| 功能特性 | 结构化生成(Outlines) | 流式生成优化、消息API |
| 维护活跃 | ⭐⭐⭐ 非常活跃 | ⭐⭐⭐ 非常活跃 |
| **选型建议** | **高并发首选** | **HF生态首选、多语言首选** |

#### Triton Inference Server（NVIDIA企业级方案）

NVIDIA出品的多模型并发推理服务器，适合企业级部署。

```bash
# 使用TensorRT-LLM后端（最快推理速度）
docker run --gpus all --rm -p 8000:8000 \
  -v $(pwd)/models:/models:ro \
  nvcr.io/nvidia/tritonserver:24.01-trtllm-python-py3 \
  tritonserver --model-repository=/models

# models/目录结构
# models/
#   llama3.1_8b/
#     config.pbtxt       # 模型配置
#     1/
#       model.engine     # TensorRT引擎（预编译）

# config.pbtxt示例
name: "llama3.1_8b"
platform: "tensorrt_llm"
max_batch_size: 64
input [
  {
    name: "input_ids"
    data_type: TYPE_INT32
    dims: [-1]
  }
]
output [
  {
    name: "output_ids"
    data_type: TYPE_INT32
    dims: [-1]
  }
]
instance_group [
  {
    count: 2  # 2个模型实例并发
    kind: KIND_GPU
    gpus: [0, 1]
  }
]
```

**TensorRT-LLM预编译（离线优化）**：

```bash
# 将HuggingFace模型编译为TensorRT引擎（需NVIDIA GPU）
python convert_checkpoint.py \
  --model_dir ./Llama-3.1-8B-Instruct \
  --output_dir ./trt_engines/8B \
  --dtype bfloat16 \
  --tp_size 1  # 张量并行数

# 编译引擎
trllm-build \
  --checkpoint_dir ./trt_engines/8B \
  --output_dir ./trt_engines/8B/compiled \
  --gemm_plugin bfloat16 \
  --gpt_attention_plugin bfloat16
```

**适用场景**：
- 需要**极致推理速度**（TensorRT-LLM是业界最快之一）
- 多模型同时服务（如一个Agent用多个不同模型）
- 企业级需求（监控、日志、ACL）
- 需要与NVIDIA生态（Triton, TensorRT）深度集成

#### SGLang（结构化生成优化）

SGLang是UC Berkeley的新项目，专注于**高效结构化生成**和**RadixAttention缓存**。

**RadixAttention — 自动KV Cache复用**：

```python
# SGLang的核心创新：RadixAttention
# 自动检测和复用共享前缀的KV Cache

# 场景：100个请求都共享相同的system prompt
# 传统方式：每个请求独立计算system prompt的KV Cache（100次重复计算）
# RadixAttention：只计算1次，自动复用给所有请求

from sglang import function, system, user, assistant, gen, RuntimeEndpoint

@function
def multi_turn(s, question):
    s += system("你是一个专业助手。")  # ← 自动缓存
    s += user(question)
    s += assistant(gen("answer", max_tokens=256))

runtime = RuntimeEndpoint("http://localhost:30000")

# 并行处理100个问题（system prompt KV Cache自动共享）
states = multi_turn.run_batch(
    [{"question": q} for q in questions],
    runtime
)
```

**SGLang与Agent开发的结合**：

SGLang特别适合有**固定交互模板**的Agent场景，因为：
1. System Prompt KV Cache自动复用
2. 多轮对话中前缀自动缓存
3. 结构化输出（JSON、代码块）生成更快

```bash
# 启动SGLang服务
python -m sglang.launch_server \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --tp 1 \
  --port 30000

# 支持的量化: AWQ, GPTQ, FP8
# 需要FlashInfer加速（自动安装）
```

**四种生产级方案对比总结**：

| 特性 | vLLM | TGI | Triton+TRT-LLM | SGLang |
|-----|------|-----|---------------|--------|
| 吞吐量 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 首token延迟 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 部署复杂度 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 多模型并发 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 结构化生成 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 量化支持 | AWQ/GPTQ/FP8 | AWQ/GPTQ | FP8/INT8/INT4 | AWQ/GPTQ/FP8 |
| 与HF生态 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **推荐场景** | **通用首选** | **HF生态** | **企业级极速** | **结构化Agent** |

### 3.C 云端部署方案

#### vLLM on Kubernetes

```yaml
# vllm-deployment.yaml - Kubernetes部署
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-llama3-8b
spec:
  replicas: 2  # 2个副本，负载均衡
  selector:
    matchLabels:
      app: vllm-llama3-8b
  template:
    metadata:
      labels:
        app: vllm-llama3-8b
    spec:
      nodeSelector:
        node-type: gpu  # 调度到GPU节点
      containers:
      - name: vllm
        image: vllm/vllm-openai:latest
        resources:
          limits:
            nvidia.com/gpu: "1"  # 每个Pod 1张GPU
        env:
        - name: MODEL_NAME
          value: "meta-llama/Llama-3.1-8B-Instruct"
        args:
        - --model
        - $(MODEL_NAME)
        - --gpu-memory-utilization
        - "0.90"
        - --max-model-len
        - "8192"
        ports:
        - containerPort: 8000
---
apiVersion: v1
kind: Service
metadata:
  name: vllm-service
spec:
  selector:
    app: vllm-llama3-8b
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
---
# HPA自动扩缩容
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: vllm-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vllm-llama3-8b
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: nvidia.com/gpu
      target:
        type: Utilization
        averageUtilization: 80
```

#### 云服务商方案

| 云服务商 | 服务名称 | 特点 | 适用场景 |
|---------|---------|------|---------|
| **阿里云PAI** | PAI-EAS | 国内访问快，支持主流模型一键部署 | 国内业务 |
| **阿里云** | 百炼 | 托管API，无需自建 | 快速上线 |
| **AWS SageMaker** | JumpStart | 与AWS生态深度集成 | AWS用户 |
| **AWS** | Bedrock | 托管多模型API（Claude/Llama等） | 无需维护基础设施 |
| **Google Vertex AI** | Model Garden | Gemini原生支持 | GCP用户 |
| **Azure** | Azure ML | 企业级MLOps | Azure生态 |
| **NVIDIA** | NIM | 优化的模型容器，一键部署 | NVIDIA GPU环境 |
| **Groq** | API服务 | LPU硬件，极速推理（首token<100ms） | 低延迟需求 |
| **Fireworks** | API服务 | 快速推理，价格竞争力 | 成本敏感 |
| **Together** | API服务 | 开源模型API，微调支持 | 开源模型需求 |

#### Serverless方案

```yaml
# 云函数按需推理 - 适合低频Agent任务

# 1. 阿里云函数计算 + 镜像部署
# 将vLLM打包为容器镜像，函数计算按需冷启动

# 2. AWS Lambda + ONNX Runtime
# 小模型(<7B)用ONNX导出，Lambda直接运行
# 限制: Lambda最大10GB内存，适合小模型

# 3. Cloudflare Workers AI
# 边缘AI推理，全球低延迟
# 支持模型: Llama 2/3, Mistral, BERT等
# 代码示例:
curl https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/meta/llama-3-8b-instruct \
  -H "Authorization: Bearer {api_token}" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'
```

### 3.D Agent系统的模型部署策略

#### 多模型路由策略

生产级Agent系统通常需要多个模型协同工作：

```yaml
# QClaw多模型路由配置
model_gateway:
  # 路由策略：按任务类型分发到不同模型
  routers:
    # 简单任务 → 小模型（快、便宜）
    - match:
        task_type: ["greeting", "simple_qa", "classification"]
        estimated_tokens: "< 100"
      target: "qwen2.5:7b"  # 或 "gpt-4o-mini"
      priority: cost        # 成本优先
      
    # 代码任务 → 代码专用模型
    - match:
        task_type: ["code_generation", "code_review", "debug"]
      target: "deepseek-coder:33b"
      priority: quality
      
    # 复杂推理 → 大模型
    - match:
        task_type: ["planning", "analysis", "complex_reasoning"]
        estimated_tokens: "> 1000"
      target: "claude-3-5-sonnet"
      priority: quality
      
    # 安全审查 → 专用安全模型
    - match:
        task_type: ["security_check"]
      target: "llama-guard-3"
      priority: safety
      
  # 降级策略
  fallback:
    - if: "primary_model.unavailable"
      then: "use_secondary"
    - if: "all_local.unavailable"
      then: "use_cloud_api"
    - if: "rate_limit_exceeded"
      then: "queue_and_retry"
      
  # 成本预算
  budget:
    daily_limit: "$100"
    alert_threshold: "80%"
    hard_limit_action: "switch_to_local_model"
```

#### 模型热加载

```python
# 不停机切换模型版本
class HotSwapModelServer:
    def __init__(self):
        self.current_model = None
        self.new_model = None
        self.request_count = 0
        
    async def load_new_model(self, model_path: str):
        """后台加载新模型"""
        self.new_model = await load_model_async(model_path)
        # 新模型预热
        await self.warmup(self.new_model)
        
    async def swap(self):
        """原子切换"""
        # 等待当前请求完成
        while self.request_count > 0:
            await asyncio.sleep(0.1)
        # 原子交换
        self.current_model, self.new_model = self.new_model, None
        
    async def handle_request(self, request):
        self.request_count += 1
        try:
            return await self.current_model.generate(request)
        finally:
            self.request_count -= 1

# Kubernetes滚动更新策略
# deployment.yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0      # 零停机
      maxSurge: 1            # 先启动新Pod
```

#### 量化策略矩阵

| 阶段 | 推荐量化 | 理由 |
|-----|---------|------|
| **开发** | FP16 / BF16 | 最大精度，调试友好 |
| **测试** | Q4_K_M / Q5_K_M | 接近生产环境 |
| **生产（GPU）** | AWQ 4bit / GPTQ 4bit | 速度+精度平衡 |
| **生产（CPU）** | Q4_K_M / Q5_K_M | llama.cpp优化 |
| **边缘设备** | Q4_K_S / Q3_K_M | 极致压缩 |

#### 成本优化策略

```yaml
# Agent系统成本优化配置
optimization:
  # 策略1: 缓存常用响应
  response_cache:
    enabled: true
    ttl_seconds: 3600
    cache_keys: ["system_prompt_hash", "messages_hash"]
    # 相同输入直接返回缓存，节省API调用
    
  # 策略2: 小模型预处理
  prefilter:
    enabled: true
    model: "qwen2.5:7b"  # 小模型判断任务复杂度
    logic: |
      if complexity == "low":
        route_to_small_model()
      elif complexity == "medium":
        route_to_medium_model()
      else:
        route_to_large_model()
        
  # 策略3: 批处理聚合
  batching:
    enabled: true
    max_wait_ms: 50          # 最多等50ms聚合请求
    max_batch_size: 32       # 最大批大小
    
  # 策略4: 非高峰降级
  off_peak:
    enabled: true
    schedule: "0 2-6 * * *"  # 凌晨2-6点
    action: "switch_to_cheaper_model"
    
  # 策略5: Token使用监控
  monitoring:
    track_input_tokens: true
    track_output_tokens: true
    alert_on_spike: "> 2x average"
```

#### 与QClaw/OpenClaw的集成

```python
# QClaw模型选择器 - 自动选择最佳模型
from qclaw import Agent, ModelSelector

# 配置多模型后端
selector = ModelSelector({
    "local": {
        "provider": "ollama",
        "base_url": "http://localhost:11434/v1",
        "models": ["qwen2.5:14b", "deepseek-coder:6.7b"],
        "cost_per_1k_tokens": 0,  # 本地零成本
        "latency_ms": 500,
    },
    "cloud": {
        "provider": "openai",
        "models": ["gpt-4o", "gpt-4o-mini"],
        "cost_per_1k_tokens": {"gpt-4o": 0.005, "gpt-4o-mini": 0.0006},
        "latency_ms": 800,
    },
    "enterprise": {
        "provider": "vllm",
        "base_url": "http://vllm-cluster:8000/v1",
        "models": ["Llama-3.1-70B-Instruct"],
        "cost_per_1k_tokens": 0.001,  # 自托管成本
        "latency_ms": 300,
    }
})

agent = Agent(
    model_selector=selector,
    routing_policy="cost_aware",  # 或 "quality_first", "latency_first"
    budget_limit_per_day=50,       # 每日预算$50
)

# Agent自动选择模型：
# - 简单任务 → 本地小模型（免费）
# - 代码任务 → 本地代码模型（免费）
# - 复杂任务 → 企业vLLM（$0.001/1K tokens）
# - 紧急任务 → 云端API（最贵但最可靠）

result = agent.run("分析这个代码库的安全漏洞")
# → 自动选择 deepseek-coder:6.7b（本地，代码专用）

result = agent.run("设计一个微服务架构")
# → 自动选择 Llama-3.1-70B-Instruct（企业级，复杂推理）
```

#### 部署策略面试速查

```yaml
常见面试问题:
  Q1: "vLLM的PagedAttention是什么？解决了什么问题？"
  A1: "传统LLM推理中KV Cache连续分配导致内存碎片和浪费，利用率仅30-50%。
       PagedAttention借鉴OS虚拟内存的页式管理，将KV Cache分成固定大小的块，
       非连续分配并通过页表映射。这使GPU显存利用率提升到90%以上，
       相同硬件可服务更多并发请求。"
       
  Q2: "生产环境怎么选量化方案？"
  A2: "GPU环境推荐AWQ 4bit（速度+精度平衡），CPU环境推荐Q4_K_M GGUF格式。
       如果追求极致速度且有H100，用FP8。不建议用低于4bit的量化用于生产，
       精度损失会导致Agent行为不稳定。"
       
  Q3: "为什么Agent系统需要多模型路由？"
  A3: "三个原因：1）成本优化——简单任务用小模型，只有复杂任务用大模型；
       2） specialization——代码任务用代码模型，安全审查用安全模型；
       3）可靠性——多模型互为备份，避免单点故障。"
       
  Q4: "Ollama和vLLM的区别？什么时候用哪个？"
  A4: "Ollama面向开发者和本地使用，安装简单但并发能力有限；
       vLLM面向生产环境，基于PagedAttention实现高并发。
       开发阶段用Ollama快速验证，生产环境用vLLM部署服务。"
       
  Q5: "如何实现模型热更新而不影响线上服务？"
  A5: "Kubernetes滚动更新是最简单方案（maxUnavailable=0）。
       自托管服务可以实现请求计数+原子切换：新模型后台加载并预热，
       等待当前请求完成后原子切换引用。更复杂场景可用蓝绿部署或金丝雀发布。"
```

---

## 附录：快速参考

### A. 参数速查卡（面试背诵版）

```
╔════════════════════════════════════════════════════════════════╗
║                 LLM推理参数速查卡                              ║
╠════════════════════════════════════════════════════════════════╣
║ temperature(0-2): 随机性控制                                  ║
║   → 代码/工具: 0.0-0.2 | 对话: 0.7-0.8 | 创意: 0.9-1.0      ║
║                                                                ║
║ top_p(0-1): 核采样，动态候选集                                ║
║   → 与temperature协同：结构化0.1-0.3，通用0.9-0.95           ║
║                                                                ║
║ top_k: Top-K采样（本地模型常用）                               ║
║   → k=50通用，k=1=贪婪解码                                    ║
║                                                                ║
║ max_tokens: 输出长度上限                                       ║
║   → 分类50，代码2048，文档4000+                               ║
║                                                                ║
║ frequency/presence_penalty(-2~2): 重复抑制/话题多样性          ║
║   → 代码: 0/0.1 | 对话: 0.3/0.3 | 创意: 0.4/0.4              ║
║                                                                ║
║ stop_sequences: 停止序列控制输出边界                           ║
║   → 工具调用后停止，结构化输出分隔                             ║
║                                                                ║
║ tool_choice: 工具选择控制                                     ║
║   → auto(自由选) | required(必须调) | none(禁止调)             ║
║   → {type:"function",name:"xxx"}(强制指定)                     ║
║                                                                ║
║ seed: 结果复现，配合temperature=0使用                         ║
║                                                                ║
║ response_format/json_schema: 结构化输出强制                    ║
║   → Agent可靠性基础设施，消除格式解析失败                       ║
╚════════════════════════════════════════════════════════════════╝
```

### B. 部署方案决策树

```
开始部署LLM
│
├─ 开发/测试阶段？
│  ├─ 是 → Ollama（最简单）或 LM Studio（图形化）
│  └─ 否 → 继续
│
├─ 生产环境？
│  ├─ 高并发(>100 req/s) → vLLM（首选）或 TGI
│  ├─ 极致延迟要求 → Triton+TensorRT-LLM 或 Groq
│  ├─ 结构化生成密集 → SGLang
│  ├─ 多模型并发 → Triton Inference Server
│  └─ 不想自运维 → 云API（Bedrock/Vertex/百炼）
│
├─ 硬件条件？
│  ├─ 消费级GPU(8-16GB) → Q4_K_M量化 + QLoRA微调
│  ├─ 专业GPU(24-48GB) → QLoRA微调，vLLM推理
│  ├─ 多GPU服务器 → vLLM张量并行
│  └─ 纯CPU → llama.cpp Q4_K_M
│
└─ 模型来源？
   ├─ 开源模型(HuggingFace) → vLLM/TGI直接加载
   ├─ 自训练模型 → 导出为safetensors再部署
   └─ 闭源API → 无需部署，直接调用
```

### C. 五层约束检查清单

```yaml
部署Agent前的安全检查清单:

模型层:
  - [ ] System Prompt使用肯定性指令
  - [ ] 输出格式用JSON Schema约束（非文字描述）
  - [ ] 工具调用范围严格限定
  - [ ] 思考链（CoT）强制自检步骤

Agent层:
  - [ ] Hooks系统拦截危险操作（PreToolUse/PreCommandRun）
  - [ ] 工具调用参数自动校验
  - [ ] 异常操作自动告警

Skill层:
  - [ ] 每个Skill有可验证的前置/后置条件
  - [ ] 输入参数有schema校验
  - [ ] "禁止"转化为"结构性约束"

架构层:
  - [ ] 沙箱隔离（文件系统/网络/资源）
  - [ ] RBAC权限矩阵定义清晰
  - [ ] 所有操作记录审计日志
  - [ ] 敏感数据加密存储

人工层:
  - [ ] 不可逆操作强制人工确认
  - [ ] 异常行为实时告警
  - [ ] 定期人工审计Agent行为
```

---

> **文档结束**
>
> 本文档覆盖Agent安全约束、LLM参数调优、模型部署三大核心知识板块。建议结合实际项目逐步实践，而非一次性全部掌握。重点关注：
> 1. **安全约束**：五层防御体系中，Skill层和Agent层是开发者最能直接控制的
> 2. **参数调优**：temperature + top_p + max_tokens 是三个最核心的参数
> 3. **部署方案**：开发用Ollama，生产用vLLM，这是最简单有效的选型策略
