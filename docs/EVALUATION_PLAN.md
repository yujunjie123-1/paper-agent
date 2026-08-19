# V2 评测与演进证据

## 1. 要回答的问题

V2 不是要证明“多 Agent 必然更好”，而是回答：

1. 哪些任务的错误来自检索、生成、工具、编排还是权限层；
2. LangGraph 迁移是否降低恢复错误和维护成本；
3. 混合检索与条件重排是否比 dense-only 更值得；
4. 哪些 Agent 分工提高缺陷召回/任务成功，哪些只带来额外 token 和 P95；
5. 模型、prompt、Skill、workflow 或工具升级后是否发生回归。

## 2. 固定数据集

起步使用 30–100 个 case，每条包含：

- `case_id`、任务类型、领域、难度、风险级别；
- 输入 ResearchBrief 和可用 artifact/tool snapshot；
- 预期的必需产物、不可接受行为和 blocker；
- 人工标注的证据/引用/工具期望；
- 固定 model snapshot、prompt version、skill commit、workflow version 和 budget；
- 拆分标签：normal、synonym、multi-turn、no-answer、conflict、permission、injection、tool-failure、recovery、external-review。

bad case 从 trace 回流数据集时，先去隐私并由人确认 reference；不直接把生产输出当成真值。

## 3. 对比变体

| 变体 | 用途 |
|---|---|
| `native-single` | V1 native workflow + 单 Agent 基线 |
| `native-multi` | 分离“多 Agent”本身的收益 |
| `langgraph-single` | 分离 runtime 迁移的恢复/可观测收益 |
| `langgraph-multi` | V2 受控多 Agent 目标版 |
| `request-multi-stage` | 仅对独立搜索/评审阶段试验 Responses Multi-agent beta |

公平性条件：相同 case、模型家族、证据快照、工具权限和最大预算。如果多 Agent 使用了更多 token，必须同时报告“等成本”与“开放成本”结果。

## 4. 分层指标

### Retrieval

- Recall@K、MRR、NDCG、Context Precision；
- ACL leakage rate（必须为 0）；
- stale/conflict detection recall；
- dense-only / BM25-only / RRF / RRF+rerank 的 P95 和效果对比。

### Generation and evidence

- claim correctness、faithfulness、citation precision/recall；
- unsupported claim rate、no-answer precision/recall；
- 数字到 artifact 的反向解析成功率。

### Agent and tools

- task success、tool selection/argument accuracy、loop termination；
- transient retry success、non-retryable error misclassification；
- duplicate side-effect rate（必须为 0）；
- human handoff precision/recall。

### Review

- blocker/major defect recall、false positive rate；
- 不同 rubric 专家的边际收益；
- 仲裁后 blocker 被“平均分淹没”的次数（必须为 0）；
- 返修意见到修改位置/验证证据的覆盖率。

### Engineering and business

- P50/P95/P99、error rate、availability；
- input/output/cached/reasoning tokens、tool calls、成本；
- crash-resume success、已完成节点重复率；
- 人工审批时长、一次通过率、每个论文项目的有效人工时间。

## 5. 评分策略

1. 确定性 code grader 优先：schema、hash、citation ID、工具调用和权限。
2. 检索使用有标注 relevant IDs 的 ranking metrics。
3. LLM-as-judge 只评估难以编码的方法/写作维度，并用小规模人工双标定期校准。
4. 结果报告均值、分布、置信区间与实际 bad case，不只报一个总分。
5. 每次主要只改一层；若同时改 model + prompt + retrieval，结论不能归因。

## 6. 保留/回退门槛

- 多 Agent 仅在 blocker recall、任务成功或可维护性有显著收益，且成本/P95 在预算内时保留。
- reranker 仅在对失败集的排名/答案收益超过时延预算时保留。
- 高 reasoning/pro 仅用于经 eval 证明收益的高价值节点。
- 任何版本发生 ACL leakage、重复副作用或 blocker 被掩盖，直接禁止发布，不用平均分抵消。

## 7. 结果文件格式

每次 experiment 必须保存：

- dataset/version/split；
- git commit、workflow/prompt/skill/model/tool versions；
- budget 与并发参数；
- 逐 case result 与 trace ID；
- 汇总 metrics、方差/区间、失败分类；
- 发布/回退建议和人工签字。

当前仓库不填任何虚构提升百分比。
