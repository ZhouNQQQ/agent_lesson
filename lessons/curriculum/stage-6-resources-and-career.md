## 7. 学习资源清单

### 7.1 官方文档（必读）

| 文档 | 链接 | 说明 |
|------|------|------|
| QClaw官网 | https://qclaw.qq.com/ | 产品主页、下载、基础文档 |
| OpenClaw GitHub | 搜索openclaw | 开源框架源码、Wiki文档 |
| OpenClaw安装指南 | GitHub Wiki | 详细安装和配置步骤 |
| SKILL.md规范 | GitHub Wiki | Skill开发完整规范 |
| AGENTS.md规范 | GitHub Wiki | Agent行为定义文档 |
| ADP文档 | 腾讯云平台 | 企业级开发平台文档 |

### 7.2 社区资源

| 资源 | 说明 |
|------|------|
| QClaw Discord/微信群 | 实时交流、问题求助 |
| OpenClaw GitHub Issues | Bug反馈、功能讨论 |
| 腾讯技术公众号 | 官方技术文章和案例 |
| V2EX/知乎Agent话题 | 中文社区讨论 |
| Twitter/X #AgentDev | 国际社区动态 |

### 7.3 推荐书籍

| 书名 | 作者 | 重点章节 |
|------|------|----------|
| 《LLM应用开发实践》 | 国内外多作者合集 | Agent架构、工具调用、记忆设计 |
| 《Building LLM Apps》 | Valentina Alto | LLM应用工程化实践 |
| 《Designing Machine Learning Systems》 | Chip Huyen | ML系统设计模式（可借鉴到Agent） |
| 《凤凰架构：构建可靠的大型分布式系统》 | 周志明 | 分布式一致性、容错设计 |

### 7.4 推荐论文

| 论文 | 作者/年份 | 重点 |
|------|-----------|------|
| "MemGPT: Towards LLMs as Operating Systems" | 2023 | 记忆分层管理、虚拟上下文 |
| "Generative Agents" (Stanford) | 2023 | Agent记忆、反射、规划 |
| "Chain-of-Thought Prompting" | Wei et al. 2022 | 推理链、Agent思维过程 |
| "ReAct: Synergizing Reasoning and Acting" | 2023 | 推理+行动结合范式 |
| "RAG Survey" | 2023 | 检索增强生成完整综述 |
| Mem0相关论文 | mem0.ai | 企业级记忆架构 |

### 7.5 实践项目库

| 项目 | 链接 | 适合阶段 |
|------|------|----------|
| OpenClaw示例Skills | GitHub | 阶段二 |
| Mem0开源实现 | github.com/mem0ai | 阶段四 |
| AutoGen（Microsoft） | github.com/microsoft/autogen | 阶段三 |
| LangGraph（LangChain） | github.com/langchain-ai | 阶段三 |
| Honcho | github.com/trycackle/honcho | 阶段四 |
| Cackle | github.com/trycackle | 阶段四 |

---

## 8. 求职准备建议

### 8.1 项目经验包装

#### 核心项目结构（STAR法则）

**项目：企业级Agent系统（基于QClaw）**

**Situation（背景）**：
> 随着LLM技术发展，企业对智能助手的需求从简单问答升级为复杂任务处理。传统单Agent架构在处理多步骤、多领域任务时表现不佳，记忆能力薄弱，无法满足企业级要求。

**Task（任务）**：
> 基于腾讯QClaw平台，独立设计并实现了一套企业级Multi-Agent系统，核心解决三个问题：复杂任务的多Agent协作、企业级记忆管理（MemoryManager）、知识库的智能检索。

**Action（行动）**：
> 1. 架构设计：采用QClaw+ADP组合方案，设计Router+Worker多Agent协作架构，支持Supervisor/Router/Pipeline/Parallel四种模式
> 2. Skills开发：独立开发12个自定义Skills（文件处理、数据分析、代码审查、日程管理等），覆盖企业常见场景
> 3. MemoryManager实现：完整实现Mem0架构的两阶段流水线（Extraction+Update），CQRS+双水位一致性（延迟从秒级降到200ms），Rolling summary分层摘要，自演化长期记忆（Observer-Reflector-Promotion循环）
> 4. 召回治理：设计规则路由+重排+门控+fail-open的召回治理流水线，召回准确率>90%
> 5. 可观测性：集成TCOP/CLS实现全链路监控和日志追踪

**Result（成果）**：
> - 系统支持5+Agent并行协作，任务完成率95%+
> - MemoryManager 99分位延迟<200ms，记忆准确率>90%
> - 完整开源在GitHub，获得XXX Stars（如有）
> - 作为个人作品在XXX场景实际使用（如有）

#### 简历亮点提炼

**标题建议**：
- "独立构建企业级Multi-Agent系统（基于QClaw/OpenClaw）"
- "MemoryManager设计与实现：企业级Agent记忆管理"
- "Multi-Agent协作框架：复杂任务自动化"

**关键词**（用于ATS简历筛选）：
> LLM、Agent、Multi-Agent、RAG、Memory、QClaw、OpenClaw、Mem0、CQRS、Vector Database、FTS5、Rolling Summary、Prompt Engineering、Python、TypeScript、Docker、Git

**技术栈呈现**：
```
核心技术：LLM应用开发 / Agent架构设计 / RAG / 记忆系统
开发平台：QClaw / OpenClaw / ADP
协作框架：Supervisor / Router / Pipeline / Parallel
记忆系统：Mem0 / CQRS / 双水位一致性 / Rolling Summary
开发语言：Python / TypeScript / YAML
基础设施：Docker / Git / RESTful API / SQLite / Chroma
```

### 8.2 面试要点

#### 高频面试题及回答框架

**Q1：什么是Agent？和普通LLM应用有什么区别？**

> Agent = LLM + 工具调用 + 记忆 + 规划 + 自主决策
> 
> 普通LLM应用是"你问我答"的单轮交互，Agent具备：
> 1. 自主性：能自主分解任务、选择工具、执行步骤
> 2. 记忆性：能记住用户偏好和历史交互，越用越懂你
> 3. 工具性：能调用外部工具（搜索、代码执行、API调用）完成复杂任务
> 4. 规划性：能制定多步骤计划并动态调整
> 
> 我在QClaw中实现的Agent包含四层架构：Gateway（入口）+ Agent（推理）+ Skills（工具）+ Memory（记忆），每个Agent通过AGENTS.md/SOUL.md/USER.md三层定义行为。

**Q2：多Agent协作有哪些模式？各适用于什么场景？**

> 四种核心模式：
> 1. **Supervisor**：中央统筹者分配任务，适合需要复杂决策和资源协调的场景（如项目管理）
> 2. **Router**：按任务类型路由，适合领域明确的场景（如客服按问题类型分配）
> 3. **Pipeline**：任务按阶段串行处理，适合有明确依赖关系的流程（如数据ETL）
> 4. **Parallel**：多Agent并行处理子任务，适合可分解的独立任务（如多源信息收集）
> 
> 我的项目中使用了Supervisor+Parallel的组合模式：Router先识别任务类型，Supervisor拆解任务，多个Worker并行执行，最后汇总结果。

**Q3：如何实现企业级Agent记忆系统？Mem0架构的核心是什么？**

> 企业级记忆需要解决三个核心问题：记忆什么（提取）、怎么存（存储）、怎么取（召回）。
> 
> Mem0架构的核心是两阶段流水线：
> 1. **Extraction**：从对话中提取结构化记忆（事实、偏好、关系），使用LLM+Prompt工程
> 2. **Update**：将新记忆与已有记忆合并，四种操作：ADD/UPDATE/DELETE/NOOP
> 
> 我的MemoryManager在此基础上增加了：
> - **CQRS+双水位**：读写分离，低水位<50ms快速响应，高水位200ms最终一致
> - **Rolling Summary**：热路径精确记录+冷路径分层摘要，API耗时和Token双下降
> - **自演化记忆**：Observer-Reflector-Promotion循环，记忆质量持续提升
> - **召回治理**：规则路由+重排+门控+fail-open，召回准确率>90%

**Q4：Agent系统中如何处理错误和异常？**

> 多层容错设计：
> 1. **工具层**：Skill调用失败时重试（指数退避）+ 降级（备用工具）
> 2. **Agent层**：子Agent无响应时超时回收 + 任务重新分配
> 3. **记忆层**：Compensator补偿重放保证幂等 + fail-open降级
> 4. **系统层**：网关健康检查 + 限流熔断 + 日志追踪（CLS）
>
> 具体例子：在我的MemoryManager中，双水位不一致时Compensator会自动补偿重放，即使写操作失败，读视图最终也能达到一致状态。

**Q5：如何评估Agent系统的好坏？**

> 多维度评估体系：
> 1. **任务完成率**：Agent能成功完成任务的比例（目标>95%）
> 2. **延迟指标**：端到端响应时间、Memory召回延迟（目标P99<200ms）
> 3. **记忆质量**：召回率（该记的记了）、精确率（记的都对）
> 4. **用户体验**：对话轮次（越少越好）、用户满意度
> 5. **系统稳定性**：可用性（目标>99.9%）、错误率
> 6. **成本效率**：Token消耗、计算资源使用

#### 编码面试准备

可能遇到的编码题类型：
1. **实现一个简单的Agent**：LLM调用 + 工具选择 + 结果解析
2. **记忆存储设计**：设计一个支持CRUD和向量搜索的记忆存储类
3. **多Agent任务分配**：给定任务列表和Agent能力，实现最优分配算法
4. **Rolling Summary**：实现一个带分层摘要的对话历史管理器
5. **CQRS模式实现**：用代码展示命令端和查询端的分离

建议提前准备：
- 用Python实现一个简化版MemoryManager（200行以内）
- 熟悉Prompt Engineering的基本技巧
- 了解常见向量数据库的基本操作

### 8.3 求职时间线建议

| 阶段 | 时间 | 行动 |
|------|------|------|
| 学习期 | 第1-14周 | 按路线图学习，积累项目经验 |
| 准备期 | 第12-14周 | 整理项目、写简历、刷面试题 |
| 投递期 | 第14-16周 | 投递简历、参加笔试 |
| 面试期 | 第16-20周 | 面试、复盘、调整 |
| 收获期 | 第20-22周 | 比较Offer、做出选择 |

### 8.4 目标公司与岗位

| 公司类型 | 目标岗位 | 匹配度 |
|----------|----------|--------|
| 互联网大厂（腾讯/阿里/字节） | AI应用工程师、Agent开发工程师 | 高 |
| AI创业公司（智谱/Moonshot/Minimax） | LLM应用工程师、AI infra工程师 | 高 |
| 外企（Microsoft/Google/Meta） | Applied Scientist、ML Engineer | 中高 |
| 传统企业（银行/保险） | AI解决方案架构师 | 中 |
| 独立开发者/创业 | AI产品创业 | 自主 |

---

