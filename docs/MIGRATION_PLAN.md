# V1 → V2 可回滚迁移计划

## 原则

不将 V1 一次性重写为 LangGraph。V1 是已验证的 reference runtime，V2 通过相同 domain contracts 做阶段性替换，每个阶段都可回退。

## 阶段

1. **契约冻结**：冻结 `ResearchBrief / AgentTask / AgentResult / Artifact / Approval`，建立 schema-version 兼容测试。
2. **绘制等价图**：使用 `StageExecutor` port 在 LangGraph 表达 V1 拓扑，先用 fake executor 验证两次 gate、revision loop 和 max-round 路由。
3. **单节点影子运行**：先迁移无副作用的 venue/topic stage，新旧 runtime 读同一输入，只有 V1 结果对用户可见。
4. **artifact 对比**：比较 schema、排序、引用、成本与 trace；差异必须解释，不用模糊文本相似度代替业务校验。
5. **迁移 HITL**：切换研究方案 gate，验证 interrupt 后跨进程恢复和审批哈希绑定。
6. **迁移读操作**：检索、评审先切；工具调用经 `ToolExecutor` 统一超时/重试。
7. **最后迁移写副作用**：实验、下载、上传和投稿只在 idempotency/receipt/failure-injection 测试通过后切换。
8. **灰度**：按 run ID 稳定分流，不在一个 run 中随机切 runtime；保留 V1 读取兼容期。

## 回滚条件

任何一项触发即停止扩量：

- checkpoint 无法恢复或已完成节点重复；
- approval artifact hashes 不一致；
- duplicate side effect > 0；
- ACL leakage > 0；
- blocker 被路由/仲裁丢失；
- 在质量无改善时 P95/成本超预算；
- 新 runtime 的故障无法由 trace 定位。

回滚时对新 run 恢复 V1 路由；已在 V2 执行的 run 根据 checkpoint 停在安全点，不粗暴地把中间 state 塞回 V1。
