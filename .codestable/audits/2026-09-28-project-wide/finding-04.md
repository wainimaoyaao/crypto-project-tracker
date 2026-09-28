---
doc_type: audit-finding
audit: 2026-09-28-project-wide
finding_id: "performance-04"
nature: performance
severity: P1
confidence: high
suggested_action: cs-issue
status: fixed
---

# Finding 04：事件归并二次复杂度阻塞采集与页面请求

## 速答

每条资讯都倒序扫描已有事件组；相互独立的资讯达到较大数量时，归并耗时近似平方增长，而调用方在全局数据锁内完成归并。

## 关键证据

- event_clusters.py:47–55 — 对每条输入扫描 reversed(groups)，直到匹配或遍历全部已有组。
- server.py:297–301 — 后台提醒线程在 LOCK 内运行 cluster(curate(...))，每 20 秒执行一次。
- server.py:395–396 — 每次 /api/live 请求也在 LOCK 内运行同一归并与序列化；浏览器在 dist/live.js:65 每 15 秒轮询。
- 本机合成 400 条互不归并事件耗时约 0.735 秒；1600 条耗时约 11.911 秒。输入扩大 4 倍，时间约增 16 倍。collection_state.py:22 每项目最多保留 400 条，因此默认四项目即可达到 1600 条上限量级。

## 影响

消息积累后，页面刷新延迟、后台提醒延迟和采集线程取得 LOCK 的等待时间会一同增加。基准是同时间窗、互不归并的合成数据，不是线上固定耗时。

## 修复方向

按项目和时间窗建立候选索引或预计算稳定归并结果，并把昂贵计算移出全局数据锁；用 400/1600 条回归基准检验增长。

## 建议动作

cs-issue：已有可复现的响应性能退化，并影响采集调度。

## 修复记录

- event_clusters.cluster 改为候选索引：按项目的锚点引用倒排 + 覆盖完整 token 集的固定语料频率 Jaccard 前缀索引（按数字签名分区）、48 小时窗口单调剪枝；归并判定规则与原因文案不变。
- server.py 新增 clustered_news()：(事件版本号, 项目签名, 15 分钟时间桶) 键控缓存；/api/live 与 alert_loop 的归并计算移出 LOCK，锁内只做快照。
- 回归测试：test_event_clusters.py 覆盖 1600 条互不归并、共享词库、随机语料与 naive 等价、高密度 posting、停用词重合和跨项目相似语料；test_server.py 覆盖缓存复用/失效。
- 同型合成基准：400→0.011s、1600→0.041s（增长 ≈3.8×；原 0.735s / 11.911s，增长 ≈16×）。
