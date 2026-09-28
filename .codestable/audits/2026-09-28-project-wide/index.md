---
doc_type: audit-index
audit: 2026-09-28-project-wide
scope: Python 服务与采集、dist 前端、部署配置和自动测试
created: 2026-09-28
status: active
total_findings: 7
---

# Signal 项目审计报告

## 范围

检查根目录 Python 服务、采集与规则模块，`dist/` 前端脚本，`Dockerfile`、`compose.yaml`、`deploy/Caddyfile` 和现有测试。执行 73 项 Python 测试、14 项 Node 测试，均通过；另用无外部请求的定向探针验证关键路径。审计只记录发现，不修改业务代码。

## 总评

共 7 条：P1 五条、P2 两条。最优先处理跨主机重定向时凭证透传，以及新闻归属和进展提醒的错误；事件归并在高消息量下会明显拖慢服务。测试覆盖了常规流程，但未覆盖上述边界。默认本地监听与 Compose 的反向代理配置提供了合理的部署边界。本次新建的架构文档仍是骨架，缺少可供对照的现状基线，因此不判定架构偏离。

## 发现清单

| # | 性质 | 严重度 | 置信度 | 标题 | 详情 |
|---|---|---|---|---|---|
| 01 | security | P1 | medium | 认证请求跨主机重定向透传 Token | [finding-01.md](finding-01.md) |
| 02 | bug | P1 | high | OpenNews 币种映射被读取却未参与过滤 | [finding-02.md](finding-02.md) |
| 03 | bug | P1 | high | 普通事件的重大后续进展不会触发新闻提醒 | [finding-03.md](finding-03.md) |
| 04 | performance | P1 | high | 事件归并二次复杂度阻塞采集与页面请求 | [finding-04.md](finding-04.md) |
| 05 | performance | P1 | high | 图表全局锁覆盖网络请求，串行化不同图表 | [finding-05.md](finding-05.md) |
| 06 | bug | P2 | medium | 并发刷新可能让旧响应覆盖较新页面状态 | [finding-06.md](finding-06.md) |
| 07 | maintainability | P2 | high | 全局渲染函数层层覆盖并依赖脚本加载顺序（已关闭） | [finding-07.md](finding-07.md) |

## 按维度分布

| 性质 | P0 | P1 | P2 | 合计 |
|---|---:|---:|---:|---:|
| bug | 0 | 2 | 1 | 3 |
| security | 0 | 1 | 0 | 1 |
| performance | 0 | 2 | 0 | 2 |
| maintainability | 0 | 0 | 1 | 1 |
| arch-drift | 0 | 0 | 0 | 0 |
| **合计** | **0** | **5** | **2** | **7** |

## 验证边界

- 性能数字来自本机合成输入，不代表实际部署的固定耗时；用于证明增长趋势与锁的串行行为。
- 凭证泄露路径以 Python 标准库重定向处理器和占位 Token 验证；需要上游返回跨主机 301/302/303 才会触发，未向真实上游发请求。
- 架构偏离维度没有现状文档可比对，不把缺失基线误记为代码偏离。

## 下一步建议

- **P1 优先修**：先阻断认证请求的跨主机重定向，再补 OpenNews 币种过滤与后续进展提醒回归测试；随后优化事件归并和图表缓存锁。
- **P2 已完成**：刷新请求的版本顺序控制（finding-06）与渲染扩展显式注册（finding-07）均已完成。
- 后续可用 `cs-issue` 处理 bug、安全与性能问题，用 `cs-refactor` 处理渲染链的结构债务。
- **修复进展（本轮）**：finding-01～07 已修复并带回归测试。finding-07 的 render 编排由显式注册组合；复测：97 项 Python + 21 项 Node 测试全部通过。
