# 关键决策记录

## DR-01：确定性宏观图 + Agent 微循环

**决策**：宏观阶段、权限、审批、预算和副作用用确定性代码；专业搜索、综合和评审允许有界 Agent 循环。

**为什么**：论文流程长、含实验和投稿副作用，自由群聊很难保证重放安全。Nature 2026 Robin 也报告了工具调用顺序趋于固定后转成确定性 Jupyter workflow 的实践。

**舍弃**：全自治 supervisor/group-chat。

**重评条件**：固定数据集证明自治路由在不增加 blocker/成本的前提下显著提高成功率。

## DR-02：V2 选 LangGraph 作为控制面

**决策**：使用 LangGraph 1.2.x 的 StateGraph/checkpointer/interrupt，但 domain model 和 artifact store 保持框架无关。

**候选比较**：

| 方案 | 优势 | 当前问题 | 结论 |
|---|---|---|---|
| 自研 async workflow | 最透明、V1 已跑通 | 中断/时间旅行/子图会继续自建 | V1 参考基线，V2 不继续扩建 |
| LangGraph | Python、低层状态图、checkpoint、interrupt、pending writes | 需正确理解节点 replay 与幂等 | 当前选择 |
| Microsoft Agent Framework | 类型化 workflow、Durable Task、Azure 生态、可靠 streaming | 当前项目并非 Azure/.NET 主导，引入面大 | 保留 provider/runtime 适配边界 |
| Temporal | 成熟分布式持久执行 | 与 Agent graph 形成双工作流心智模型 | 严格 SLA/多区域 worker 时重评 |
| AutoGen/CrewAI | 多 Agent 原型快 | 对话/团队抽象不是本场景核心风险 | 不作控制面 |

## DR-03：直接 OpenAI Responses SDK，不绑定 model wrapper

**决策**：业务代码依赖 `ModelGateway`；OpenAI adapter 直接使用 Responses structured parsing。

**为什么**：新模型特性上线快，可明确管理 reasoning、prompt cache、PTC 和 request-scoped multi-agent；又不会将上层绑死到单 provider。

**舍弃**：全部经由 LangChain ChatModel；完全写死 OpenAI SDK 类型。

**重评条件**：多 provider 成为常态且自建 adapter 的维护成本超过框架封装收益。

## DR-04：Postgres + pgvector 作为生产默认

**决策**：run state、ACL、文档版本、评测和中小规模 vector 先放在同一 Postgres 边界；原始大文件进 object storage。

**为什么**：权限与版本过滤必须尽可能在检索前完成，共用事务和运维面比过早拆专用向量库更有价值。

**舍弃**：V2 起步即使用 Milvus/Weaviate；向量库作为唯一文档真相源。

**重评条件**：数据量、QPS、索引更新或检索延迟超过预先设定 SLO。

## DR-05：BM25 + dense + RRF，rerank 按条件触发

**决策**：先使用可解释混合基线；不让 cross-encoder 成为每次请求的固定税。

**为什么**：论文 DOI、模型名、方法缩写适合 sparse，语义问题适合 dense；RRF 不要求分数校准。重排只在测试证明其 NDCG/答案质量收益大于 P95 代价时保留。

## DR-06：Ego Browser 是 provider，不是框架前提

**决策**：`AuthenticatedBrowser` 契约是稳定边界；macOS 选 Ego Lite，Windows 选现有 Chrome session provider。

**为什么**：平台限制不应污染研究流程，也不能为了“使用新技术”在 Windows 上冒充 Ego 已运行。

**不可妥协**：密码/cookie 不进 prompt；域名 allowlist；MFA/CAPTCHA/付款/新条款转人；投稿前核对 package hash。

## DR-07：可观测与评测解耦

**决策**：使用 OpenTelemetry 语义的 trace/span/metric 作为底层契约，可选输出到 LangSmith 进行 Agent trace/dataset 分析。

**为什么**：只使用平台专属 trace 会让运维指标、HTTP/数据库 span 与 Agent eval 割裂；但 LangSmith 的 dataset/trajectory 能力作为上层分析仍然有价值。

## DR-08：不在 V2 做微调和知识图谱

**决策**：当前 `rejected-now`。

**理由**：面试 JD 对 RAG、工具、稳定性、评测和部署的权重更高；目前也没有证据表明失败来自模型行为而非数据/检索/工具。

**重评条件**：有足够高质量标注数据，且固定 eval 证明 prompt/RAG/tool 不能解决的稳定行为差距；或文献实体关系查询明确成为瓶颈。
