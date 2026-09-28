---
doc_type: refactor-scan
refactor: 2026-09-28-project-charts
status: user-reviewed
scope: dist/project.js、dist/charts.js，以及 test_render_chain.cjs 与 test_project_ui.cjs
summary: 发现 3 条结构优化点；低风险 1 条、中风险 2 条。
---

# project-charts scan

## 总览

- 扫描范围：`dist/project.js`、`dist/charts.js`、`test_render_chain.cjs`、`test_project_ui.cjs`。
- 发现 3 条优化点：结构 3 / 性能 0 / 可读性 0。
- 按风险：低 1 条 / 中 2 条。
- 建议先做：#2、#3；先收敛项目页 HTML 与图表状态，再替换图表对 `render` 的覆盖。
- 建议慎做 / 后做：#1 改变项目页和图表的组合入口，需要保持项目概览、关联图表、图表请求和新闻标记的触发时机。
- 前置检查 7 条全过：✓。本次按 `explicit-ui-composition` 决定把 project-charts 视为受控模块；不修改 `live.js` 的基础 `render`、共享 `state` 或 API 数据格式。

## 条目

### #1 以项目页扩展注册替换图表 render 覆盖 ✓

- **位置**：`dist/project.js:13-14`、`dist/charts.js:22-23`
- **分类**：结构
- **现状**：`project.js` 先包装全局 `render`，写入完整项目页；`charts.js` 再保存该函数、以同名覆盖，并将项目页第一块 `.project-section` 替换为关联图表。
- **问题**：图表正确渲染依赖项目页已经写入目标节点；`render` 在该接线缝被同名赋值 2 次，图表请求也在每次项目渲染后由覆盖函数触发。
- **建议**：在项目页模块建立命名的项目页扩展注册入口；项目页渲染完成且项目存在时调用扩展，图表模块注册“替换首个行情区块并确保图表数据”的扩展，移除 `charts.js` 对 `render` 的同名覆盖。
- **建议映射的方法**：M-L1-01（Parallel Change 并行变更）
- **风险**：中——改变图表请求与 DOM 替换的调用时机，须防止无项目时请求、重复请求和首屏图表缺失。
- **验证**：AI 自证（`node --test test_render_chain.cjs test_project_ui.cjs`；检查 charts.js 不含 `beforeLinkedChartRender` 或 `render=function`）｜HUMAN（切换项目、改变周期和刷新图表，确认图表、新闻标记和项目概览正常）。
- **范围**：约 45 行 / 2 个产品文件。

### #2 拆分项目页的结构化渲染片段 ✓

- **位置**：`dist/project.js:12`
- **分类**：结构
- **现状**：`projectPage` 在一个模板字符串内生成项目头、价格区、团队账号、讨论者和动态分隔符，共 5 个 UI 区块。
- **问题**：单个函数包含 5 类展示职责，修改团队、讨论者或行情区都需要触碰同一模板；图表扩展只能依赖该大模板中第一个 `.project-section` 的位置。
- **建议**：提取命名的项目头、行情、团队账号和讨论者渲染函数；`projectPage` 只按既有顺序组装这些片段，并保留现有 HTML 结构与 class 名。
- **建议映射的方法**：M-L2-01（Extract Function 提取函数）
- **风险**：低——纯字符串渲染，项目 UI 与 render-chain 测试已覆盖关键输出。
- **验证**：AI 自证（`node --test test_project_ui.cjs test_render_chain.cjs`，断言项目头、账户网格、关联图表和新闻标记）｜HUMAN（打开项目页，确认官方链接、团队区和讨论者区仍显示）。
- **范围**：约 60 行 / 1 个产品文件。

### #3 封装关联图表的数据与呈现状态 ✓

- **位置**：`dist/charts.js:1-23`
- **分类**：结构
- **现状**：`charts.js` 在模块全局同时管理缓存、请求去重、错误、周期设置、图表 SVG、新闻弹窗和项目页替换逻辑。
- **问题**：缓存/请求状态、可见设置、图表 HTML 和项目页副作用同处；`fetchChart` 的 finally 分支直接调用全局 `render`，导致图表数据状态与页面组合路径难以分开验证。
- **建议**：形成关联图表控制器，内部拥有缓存和请求状态，显式提供“确保数据”和“渲染项目区块”入口；保留现有 60 秒缓存、单飞请求和当前项目/周期检查。
- **建议映射的方法**：M-L3-07（Single Responsibility Split 职责分离）
- **风险**：中——控制器迁移时不得改变缓存 TTL、错误保留、强制刷新或图表请求完成后的重渲染条件。
- **验证**：AI 自证（`node --test test_render_chain.cjs`，并新增/扩展缓存与当前项目切换断言）｜HUMAN（依次切换 15m/1h/4h/1d，刷新图表并点击新闻标记）。
- **范围**：约 27 行 / 1 个产品文件。
