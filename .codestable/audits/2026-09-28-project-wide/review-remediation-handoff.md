---
doc_type: handoff
date: 2026-09-28
project: crypto-project-tracker
purpose: 修复本轮未提交改动审查发现的 P1 缺陷，并完成复审。
baseline: 0eb3bcaffcd7e7f7c8bda79d75aaeb2e86d31a5f
status: complete
---

# 未提交改动审查 · 修复交接

## 目标

基于当前工作区修复本轮审查的 P1 缺陷，并保留既有修复与显式 UI 组合改造。不要重置、覆盖或提交现有未提交改动；本轮没有创建 git commit。

## 当前状态

- 审查基线：HEAD 0eb3bcaffcd7e7f7c8bda79d75aaeb2e86d31a5f；范围包含已跟踪 diff 和未跟踪的 CodeStable 文档、harness 与测试文件。
- 已验证：git diff --check 通过；Node 21/21、Python 97/97 通过；最终双轴复审未发现剩余 P1。
- 已完成的功能/重构与原始验收资料见下方“参考资料”；不要重复改写这些设计文档，除非修复改变了既有契约。

## 必修 P1

### 1. 认证重定向仍可降级或换端口泄露 Token

- 位置：server.py CrossHostRedirectBlocked，约 77-82 行；现状只比较 hostname。
- 风险：https://ai.6551.io 可重定向到 http://ai.6551.io 或 https://ai.6551.io:444，Authorization 可能继续随请求发送。
- 修复目标：认证请求仅允许同一 HTTPS origin（scheme、hostname、有效端口均一致），或拒绝所有认证重定向；公开来源保持默认重定向逻辑。
- 必增测试：HTTPS→HTTP 同主机、HTTPS 默认端口→同主机非默认端口均被拒；同 origin HTTPS 重定向的既有行为明确且可测试。
- 规格依据：.codestable/audits/2026-09-28-project-wide/finding-01.md。

### 2. providerMismatch 的后续进展仍能触发新闻提醒

- 位置：alerts.py 约 36-48 行、event_clusters.py 约 120-126 行。
- 风险：alerts 仅检查聚类锚点的 providerMismatch；带冲突映射的 related item 生成 progressCandidates 后，仍可触发“项目事件出现后续进展候选”。
- 修复目标：来自 providerMismatch 记录的锚点、后续进展或整组事件均不得产生新闻提醒，并保留普通低优先级锚点的可信进展提醒能力。
- 必增测试：正常锚点 + providerMismatch 的“暂停/金额变化”后续报道共享原文时，不生成触发记录；可信后续报道仍照常触发一次。
- 规格依据：.codestable/audits/2026-09-28-project-wide/finding-02.md 与 finding-03.md。

### 3. 事件归并索引可能漏掉原算法应合并的事件

- 位置：event_clusters.py _sample_words / cluster，约 41-47、68-116 行。
- 风险：SAMPLE_SIZE、SAMPLE_HITS 与 MAX_POSTING 过滤候选时会产生 false negative；实现注释也承认 missed merge。
- 修复目标：保持 finding-04 要求的归并判定与原因文案不变，并与 naive 基准的分组结果一致；性能优化不得用漏合并作为可接受退化。
- 必增测试：构造超过 posting 上限的共同词语料，其中同一数字且正文高度重合的事件必须归为同组；继续保留 1600 条独立事件的比较数/性能保护。
- 规格依据：.codestable/audits/2026-09-28-project-wide/finding-04.md。

## P2/P3 收尾项

- Checklist 元数据：render-orchestration checklist 已 complete，但 checks 状态为 done；按 .codestable/reference/shared-conventions.md 的 checklist 生命周期，应在验收后使用 passed 或 failed。
- 测试资源：redirect 与翻译限流测试都会关闭构造的 HTTPError；完整 Python 回归已无 ResourceWarning。
- 范围卫生：本次新增大量 .codestable/reference、tools 与骨架目录。若不属于既定审计/重构工作，单独归档为治理初始化或从本次交付中拆出。

## 实施更新（2026-09-28）

- P1-1：认证重定向现在比较完整 HTTPS origin；已覆盖跨主机、HTTPS→HTTP、非默认端口和同 origin 行为。
- P1-2：含 providerMismatch 成员的聚类组会继承该标记并被 alerts.evaluate 整组跳过；不可信 related item 不再生成 progressCandidate，可信组的后续进展仍可触发一次新闻提醒。
- P1-3：归并候选改为覆盖完整 token 集的固定语料频率 Jaccard 前缀索引，并按项目与数字签名分区；高密度 posting、停用词重合、跨项目相似语料与现有性能/naive 等价测试通过。
- P2：render-orchestration 的五项验收状态已改为 passed；RedirectSecurityTests 已在 ResourceWarning 视为错误时通过。
- 验证：Python 97/97、Node 21/21、git diff --check 通过；HTTP 429 模拟异常现在由翻译错误处理关闭，不再产生 ResourceWarning。
- 最终复审：认证 origin、错配来源信任传播、归并候选完整性和 UI 显式组合均无剩余硬缺陷；范围卫生继续作为独立治理事项。
- 范围卫生保留为后续独立治理事项，未删除任何既有 CodeStable 文档或骨架。

## 修复顺序

1. 先修认证重定向边界并跑对应 Python 单测。
2. 修 providerMismatch 在聚类/提醒间的信任传播，再补端到端 alert 测试。
3. 调整归并候选策略，先证明与 naive 分组等价，再恢复性能回归。
4. 清理 checklist 状态、测试 warning 和范围归档。
5. 运行全套回归，再以 review 技能复审未提交 diff。

## 验证命令

```bash
python3 -m unittest discover -q
node --test test_notifications.cjs test_preferences_ui.cjs test_reading_updates.cjs test_reorder.cjs test_source_status.cjs test_live_refresh.cjs test_render_chain.cjs test_detail_chain.cjs test_rules_ui.cjs test_project_ui.cjs
git diff --check
```

## 参考资料

- 审计发现：.codestable/audits/2026-09-28-project-wide/finding-01.md 至 finding-07.md。
- UI 重构：.codestable/refactors/2026-09-28-rules-notifications/、detail-reading/、project-charts/、render-orchestration/。
- 显式组合决策：.codestable/compound/2026-09-28-decision-explicit-ui-composition.md。
- UI 当前结构：.codestable/architecture/ui-render-chain.md。
- 审查输出已在当前对话中；不要将任何 Token、个人数据或本地 data/ 内容写入后续文档。

## Suggested Skills

- cs-issue：将三项 P1 分成可复现、可追溯的修复条目。
- cs-issue-fix：在根因和修复方案确认后定点修改并补回归测试。
- diagnosing-bugs：验证归并候选索引的对抗输入与提醒信任传播。
- review：修复完成后，以 HEAD 为基线做一次双轴复审。
