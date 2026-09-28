---
doc_type: refactor-scan
refactor: 2026-09-28-render-orchestration
status: user-reviewed
scope: dist/live.js、dist/project.js、dist/preferences.js、dist/reading-updates.js，以及 test_render_chain.cjs、test_preferences_ui.cjs、test_reading_updates.cjs
summary: 发现 4 条结构优化点；低风险 1 条、中风险 2 条、高风险 1 条。
---

# render-orchestration scan

## 总览

- 扫描范围：`dist/live.js`、`dist/project.js`、`dist/preferences.js`、`dist/reading-updates.js` 及 3 组组合/状态测试。
- 发现 4 条优化点：结构 4 / 性能 0 / 可读性 0。
- 按风险：低 1 条 / 中 2 条 / 高 1 条。
- 建议顺序：#1 → #2 → #3 → #4；先由基座提供命名扩展入口，再逐个迁移项目、偏好与阅读行为。
- 建议慎做 / 后做：#4 依赖阅读 ledger 与 catchup 面板的插入时机，须在基座和项目页扩展稳定后实施。
- 前置检查 7 条全过：✓。本次按 `explicit-ui-composition` 决定收敛整个残余 render 链；现有事件、项目、偏好和阅读页面行为保持不变。

## 条目

### #1 在 live 基座建立 render 扩展注册 ✓

- **位置**：`dist/live.js:24-34,57-64`
- **分类**：结构
- **现状**：基础 `render` 完成通用页面后，`live.js` 自身保存并重赋 `render` 来写实时状态、数据覆盖和新闻筛选。
- **问题**：实时状态行为依赖同名函数覆盖，后续项目、偏好和阅读模块只能继续保存并覆盖 `render`；当前链条共有 4 个跨脚本包装。
- **建议**：在基础 `render` 中加入按注册顺序执行的命名扩展入口；把实时状态、数据覆盖和新闻筛选 UI 迁为第一个注册扩展，并保留基础页面与刷新行为。
- **建议映射的方法**：M-L1-01（Parallel Change 并行变更）
- **风险**：高——基座渲染处理收件箱、项目选择、规则页和所有后续扩展；错误注册顺序会影响整个页面。
- **验证**：AI 自证（`node --test test_render_chain.cjs test_preferences_ui.cjs test_reading_updates.cjs`；确认 live.js 外无 `originalRender` 覆盖）｜HUMAN（打开收件箱、规则页与任一项目，确认实时状态与来源筛选正常）。
- **范围**：约 80 行 / 1 个产品文件。

### #2 将项目页渲染登记为 render 扩展 ✓

- **位置**：`dist/project.js:19-21`
- **分类**：结构
- **现状**：项目页在 `priorProjectRender()` 之后写入项目概览、压缩账户，并调用已注册的项目页扩展。
- **问题**：项目页本身已拥有命名的项目页扩展入口，但进入该入口仍依赖对全局 `render` 的一次包装。
- **建议**：把项目页写入与账户压缩移为一个命名 render 扩展，注册到 live 基座；保持项目页扩展注册的既有顺序和图表挂载位置。
- **建议映射的方法**：M-L1-01（Parallel Change 并行变更）
- **风险**：中——项目页必须在图表扩展前写入首个行情区块；项目为空时不得写入或触发图表请求。
- **验证**：AI 自证（`node --test test_render_chain.cjs test_project_ui.cjs`；确认 project.js 不含 `priorProjectRender` 或 `render=function`）｜HUMAN（切换项目并确认项目页、团队、讨论者和关联图表）。
- **范围**：约 12 行 / 1 个产品文件。

### #3 将偏好状态更新登记为 render 扩展 ✓

- **位置**：`dist/preferences.js:7-21`
- **分类**：结构
- **现状**：偏好同步层保存 `priorRender`，每次渲染后更新 footer 同步状态；它也会在合并远端偏好时调用 `render()`。
- **问题**：同步状态这一单一后置 UI 职责通过全局 `render` 覆盖实现；独立测试必须提供假的 `render` 才能加载偏好逻辑。
- **建议**：将 footer 状态更新暴露为命名 render 扩展，保持 `persist` 覆盖和 `sync` 写路径不变；独立偏好测试改为提供扩展注册测试桩。
- **建议映射的方法**：M-L2-04（Move Function 搬移函数）
- **风险**：低——只移动 footer 文案的调用位置，远端合并、冲突处理和请求逻辑不变。
- **验证**：AI 自证（`node --test test_preferences_ui.cjs test_render_chain.cjs`，确认本地编辑与远端轮询行为不变）｜HUMAN（修改关注/已读状态，确认 footer 显示同步状态）。
- **范围**：约 8 行 / 1 个产品文件。

### #4 将阅读回顾渲染登记为 render 扩展 ✓

- **位置**：`dist/reading-updates.js:45-62`
- **分类**：结构
- **现状**：阅读层在 `oldRender()` 后初始化已读事件版本、插入 catchup 面板、补充规则触发记录上下文，并在提醒回看时写入项目页上下文。
- **问题**：阅读层的 4 类后置页面职责通过最终 `render` 覆盖串联；其插入顺序依赖偏好层已经完成渲染，且 ledger 初始化隐含在该包装中。
- **建议**：形成阅读页面扩展控制器，显式注册到 render 基座；控制器保留 ledger、catchup、规则记录和提醒上下文逻辑，在基础/项目/偏好扩展完成后运行。
- **建议映射的方法**：M-L3-07（Single Responsibility Split 职责分离）
- **风险**：中——迁移时不得改变已读事件版本初始化、catchup 面板位置、规则记录附加内容或提醒回看的项目上下文。
- **验证**：AI 自证（`node --test test_reading_updates.cjs test_render_chain.cjs`；确认 reading-updates.js 不含 `oldRender` 或 `render=function`）｜HUMAN（打开收件箱与规则页，确认 catchup、提醒上下文和返回操作）。
- **范围**：约 30 行 / 1 个产品文件。
