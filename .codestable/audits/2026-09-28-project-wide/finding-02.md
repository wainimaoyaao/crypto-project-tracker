---
doc_type: audit-finding
audit: 2026-09-28-project-wide
finding_id: "bug-02"
nature: bug
severity: P1
confidence: high
suggested_action: cs-issue
status: fixed
---

# Finding 02：OpenNews 币种映射被读取却未参与过滤

## 速答

OpenNews 返回的 coins 字段被提取后未使用；仅凭正文关键词即可把映射到其他币种的资讯归入当前项目。

## 关键证据

- server.py:202–204 — coins 列表已从 row.coins 生成，下一行却只检查 HTTPS 链接和 relevant(...)；紧邻注释声称提供方币种映射是必要条件。
- news_quality.py:44–49 — 后续 curate 只再次检查正文相关性，不复核提供方的币种映射。
- 本地模拟 OpenNews 返回 coins=[BTC]、正文为“NEAR Protocol announces a new upgrade”的记录；对 NEAR 调用 provider_news 后，币种检索与关键词检索各接收一条，均标记为该项目资讯。

## 影响

提供方把内容归到其他币种、但正文顺带提到关注项目时，系统仍可能展示为该项目资讯，并进入后续重点判断与提醒。触发量取决于上游数据，不代表每条多币种报道都一定误归属。

## 修复方向

明确币种检索与关键词补充检索各自的接收条件；对提供方映射与正文匹配不一致的记录设独立处理，并补反例测试。

## 建议动作

cs-issue：信息归属会影响用户阅读和提醒判断。

## 修复记录

- 币种检索：提供方 coins 存在时要求包含项目 symbol，缺失时回退正文匹配并注明；关键词补充检索以正文相关性接收，但提供方映射冲突时标记 providerMismatch，matchReason 注明需核对原文（server.py）。
- news_quality.annotate 对 providerMismatch 记录强制 high=False；cluster 会将任一成员的 providerMismatch 传播到聚类组，alerts.evaluate 对该组不产生提醒。
- 回归测试：test_server.py ProviderNewsFilterTests 3 项（coins=[BTC] 反例：币种检索拒绝、关键词检索带标记；coins=[NEAR] 与缺失映射正常接收；标记记录不进入 high）。
