---
doc_type: refactor-design
refactor: 2026-09-28-render-orchestration
status: approved
scope: 将 live、项目、偏好和阅读回顾的残余 render 包装迁移为 live 基座的有序命名扩展，保持完整页面行为与异步刷新时机。
summary: live.js 先建立 render 扩展注册并迁移实时状态，项目、偏好和阅读层按脚本加载顺序注册后置行为，移除全部 original/prior/old render 包装。
---

# render-orchestration refactor design

## 1. 本次范围

- 采纳 scan 条目：#1、#2、#3、#4。
- 改动文件：`dist/live.js`、`dist/project.js`、`dist/preferences.js`、`dist/reading-updates.js`、`test_render_chain.cjs`、`test_preferences_ui.cjs`、`test_reading_updates.cjs`，必要时调整 `chain-harness.cjs` 的最小测试桩。
- 不改基础收件箱/规则页/项目页内容、实时刷新 API、偏好同步协议、阅读 ledger、catchup/提醒上下文、项目图表扩展或服务端 API。
- 总风险：高。render 是全部 UI 的共同入口；错误顺序可能导致项目图表没有挂载、footer 状态滞后或阅读面板插入错误位置。

## 2. 前置依赖

- `test_render_chain.cjs` 覆盖基础收件箱、实时状态、项目页、关联图表、规则页和通知面板。
- `test_preferences_ui.cjs` 覆盖本机编辑与远端偏好轮询的合并行为。
- `test_reading_updates.cjs` 覆盖阅读进展、历史新闻过滤与提醒上下文。
- `.codestable/compound/2026-09-28-decision-explicit-ui-composition.md` 规定不新增同名全局函数覆盖。
- 当前脚本顺序为 live → project → … → preferences → reading-updates；该顺序也将成为 render 扩展的注册顺序。

## 3. 执行顺序

### 步骤 1：在 live 基座建立 render 扩展注册

- **引用方法**：M-L1-01 Parallel Change。
- **具体操作**：在基础 `render` 中增加命名扩展注册与按注册顺序运行的阶段；把 live 自身的实时状态、数据覆盖和新闻筛选界面逻辑抽为第一个扩展，移除 `originalRender` 包装。
- **退出信号**：收件箱、实时状态、来源筛选和项目占位输出保持当前测试结果；扩展入口在 project 脚本加载前可用。
- **验证责任**：AI 自证。
- **回滚**：回退本步骤对 `dist/live.js` 与 render-chain 测试的单步修改。

### 步骤 2：将项目页登记为 render 扩展

- **引用方法**：M-L1-01 Parallel Change。
- **具体操作**：将项目页写入、账户压缩和项目页扩展执行抽为命名函数，注册到 live render 基座；移除 `priorProjectRender` 与 project.js 对 `render` 的赋值。
- **退出信号**：项目页在实时状态扩展后写入，关联图表仍由项目页扩展挂载；无项目时不出现项目页或图表请求。
- **验证责任**：AI 自证。
- **回滚**：回退本步骤对 `dist/project.js` 与项目/render 测试的单步修改。

### 步骤 3：将偏好状态更新登记为 render 扩展

- **引用方法**：M-L2-04 Move Function。
- **具体操作**：保留 `persist` 覆盖与同步逻辑，把 footer 状态更新注册为命名 render 扩展；移除 `priorRender` 与 preferences.js 对 `render` 的赋值；独立偏好测试提供扩展注册桩。
- **退出信号**：状态文本继续随本地编辑、同步、冲突和失败变化；远端偏好合并结果不变。
- **验证责任**：AI 自证。
- **回滚**：回退本步骤对 `dist/preferences.js` 与偏好测试的单步修改。

### 步骤 4：将阅读回顾登记为 render 扩展

- **引用方法**：M-L3-07 Single Responsibility Split。
- **具体操作**：形成阅读页面控制器，封装已读版本初始化、catchup 面板、规则触发记录上下文和提醒回看上下文；控制器注册为最后一个 render 扩展，移除 `oldRender` 与 reading-updates.js 对 `render` 的赋值。
- **退出信号**：阅读扩展在偏好状态之后运行；catchup 仍位于 feed 开头，规则记录补充内容和提醒上下文均保持。
- **验证责任**：AI 自证 + HUMAN。
- **回滚**：回退本步骤；恢复原有阅读 render 包装。

## 4. 风险与看点

- **扩展顺序**：实时状态 → 项目页（含图表）→ 偏好 footer → 阅读回顾。该顺序必须由注册顺序和测试共同守护。
- **递归渲染**：图表请求、偏好同步和阅读操作都会调用 `render()`；扩展必须无额外状态写入循环，依赖既有缓存、busy 和 ledger 防护。
- **独立测试环境**：偏好与阅读的现有独立 VM 测试未加载 live.js，必须提供 `registerRenderExtension` 测试桩并验证各自注册一次。
- **最终目视范围**：收件箱、规则页、项目页、偏好同步状态、catchup 面板和提醒回看都必须走一遍。
