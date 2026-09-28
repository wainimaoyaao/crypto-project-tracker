---
doc_type: audit-finding
audit: 2026-09-28-project-wide
finding_id: "bug-03"
nature: bug
severity: P1
confidence: high
suggested_action: cs-issue
status: fixed
---

# Finding 03：普通事件的重大后续进展不会触发新闻提醒

## 速答

新闻提醒在读取 progressCandidates 前先要求事件锚点 high=true；原始报道普通、后续出现暂停或金额变化时，进展候选会被整组跳过。

## 关键证据

- event_clusters.py:38–44、58–63 — 归并以最早条目为锚点，并在后续条目新增金额、比例或状态时生成 progressCandidates。
- alerts.py:36–45 — 循环在访问 progressCandidates 之前执行 if e['p']!=rule['p'] or not e.get('high'):continue，因此只看锚点的 high。
- 本地端到端探针：普通“NEAR Protocol product notice”与后续“NEAR Protocol has paused withdrawals”共享原文链接；curate + cluster 得到 1 组、锚点 high=False、1 个进展候选，evaluate 返回 0 条提醒。

## 影响

用户为项目开启新闻规则后，原先低优先级事件的实质后续进展即使被系统识别，也不会进入站内触发记录。

## 修复方向

将锚点重点消息判定与后续进展候选判定分开，避免用锚点 high 直接筛掉进展；补普通锚点后续升级的回归测试。

## 建议动作

cs-issue：已有确定的漏报路径和可重复输入。

## 修复记录

- alerts.evaluate 的进展候选遍历不再依赖锚点 high；锚点消息自身的发射条件不变（high + 时间窗）。
- 回归测试：test_alerts.py 新增 3 项（普通锚点+进展候选触发、无进展普通锚点不触发、providerMismatch 记录不提醒）。
