# ADR-001：采用混合、可恢复编排

- 状态：Accepted
- 日期：2026-08-18

## 决策

使用确定性状态图控制 venue → topic → literature → design → experiment → writing → review → revision → submission；只在独立调研和独立评审处并行。每个 Agent 使用有界微循环并只返回结构化 artifact。

## 原因

研究任务是长周期、有人工等待、有昂贵或不可逆步骤的流程。纯模型编排无法保证恢复后不重复实验，也难以稳定解释状态、责任和失败层。2026 年 Robin 的实际实现同样从 Agent 工具循环收敛到稳定的确定性工作流。

## 后果

- 优点：可恢复、可测试、可审计、易做单 Agent / 多 Agent A/B。
- 代价：需要显式 state/schema；不允许 Agent 任意改变宏观阶段。
- 退出条件：若固定评测证明某阶段完全 Agentic 的成功率收益显著且风险可控，可只替换该 stage，而不重写全系统。

