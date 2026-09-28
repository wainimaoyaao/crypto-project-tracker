---
doc_type: audit-finding
audit: 2026-09-28-project-wide
finding_id: "bug-06"
nature: bug
severity: P2
confidence: medium
suggested_action: cs-issue
status: fixed
---

# Finding 06：并发刷新可能让旧响应覆盖较新页面状态

## 速答

前端允许多个 /api/live 请求同时进行；较早发出的慢请求若最后返回，会覆盖较新请求的 liveData、catalog 和 events。

## 关键证据

- dist/live.js:63 — refreshLive 在 await fetch 后直接替换 liveData、catalog、events 并调用 render，没有请求序号或响应时间检查。
- dist/live.js:64–65 — 用户点击“刷新视图”和 15 秒定时器都可以调用 refreshLive，也在首次加载时调用；没有共享的进行中标记。
- server.py:395–397 — 响应已有 serverTime 字段，但客户端未用它决定新旧。

## 影响

当两次请求重叠且返回顺序与发出顺序相反时，较旧快照会暂时显示为最新页面状态；下一轮成功刷新通常会纠正。是否实际发生取决于网络和服务耗时。

## 修复方向

用单飞请求、递增请求序号或 serverTime 比较来拒绝过期响应，并覆盖反序返回场景。

## 建议动作

cs-issue：状态覆盖是明确的异步时序风险。

## 修复记录

- dist/live.js refreshLive 增加递增请求序号；响应返回后 seq 非最新则丢弃（成功与失败路径都丢弃），不再覆盖 liveData/catalog/events。
- 回归测试：新增 test_live_refresh.cjs 3 项（反序成功响应被丢弃、迟到的失败不覆盖新状态、顺序返回仍生效）；另做去守卫变异检验，确认测试能捕获原缺陷。
