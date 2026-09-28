---
doc_type: audit-finding
audit: 2026-09-28-project-wide
finding_id: "performance-05"
nature: performance
severity: P1
confidence: high
suggested_action: cs-issue
status: fixed
---

# Finding 05：图表全局锁覆盖网络请求

## 速答

图表缓存使用一把全局锁，且在锁内等待 Binance API；不同项目和周期的图表请求因此串行。

## 关键证据

- server.py:30–31 — CHART_CACHE 和 CHART_LOCK 均为进程级全局对象。
- server.py:365–374 — chart_data 在 with CHART_LOCK 内完成缓存检查、api 网络请求、K 线计算和写缓存。
- server.py:302–305 — 后台提醒对每个非 4h 周期逐一调用 chart_data；server.py:385–389 的用户图表请求也使用同一路径。
- 本地用每次睡眠 0.2 秒的假 API 并发请求 NEAR 和 PHA 的 1h 图表，合计耗时约 0.406 秒，符合串行等待。

## 影响

一个慢请求会让其他项目的图表和依赖图表的提醒等待。代码设置的单次上游超时为 18 秒且可能重试，极端情况下等待更明显。

## 修复方向

锁内只检查和更新缓存；按缓存键协调重复请求，不在全局锁内执行网络 I/O 与计算。

## 建议动作

cs-issue：请求相互阻塞可在当前代码中直接复现。

## 修复记录

- chart_data 锁内只做缓存检查与 in-flight 登记；网络请求与 K 线计算在锁外执行；同 key 单飞（waiters 等 Event 后重查缓存），失败通过短时错误标记向 waiters 传播；TTL 60 秒语义不变。
- 回归测试：test_server.py ChartConcurrencyTests 3 项（不同项目并发 <0.55s 对比串行 0.6s；同 key 3 并发只调 1 次上游；TTL 内复用）。
