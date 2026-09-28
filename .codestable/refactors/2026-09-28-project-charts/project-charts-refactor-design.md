---
doc_type: refactor-design
refactor: 2026-09-28-project-charts
status: approved
scope: 将项目页与关联图表从多层 render 覆盖迁移为项目页扩展注册，保持项目概览、图表缓存、请求与交互行为。
summary: 先拆项目页 HTML 片段，再形成关联图表控制器，最后让 charts.js 通过项目页扩展注册挂载图表并移除对 render 的同名覆盖。
---

# project-charts refactor design

## 1. 本次范围

- 采纳 scan 条目：#1、#2、#3。
- 改动文件：`dist/project.js`、`dist/charts.js`、`test_render_chain.cjs`、`test_project_ui.cjs`，必要时调整 `chain-harness.cjs` 的最小测试桩。
- 不改 `live.js` 的基础 `render`、项目数据格式、图表 API、缓存 TTL、强制刷新语义、图表周期/开关、新闻标记或项目页的现有 CSS class。
- 总风险：中。图表请求与项目页写入目前依赖 render 覆盖顺序，迁移必须保持无项目时不请求、项目切换时正确加载、当前周期完成后重渲染。

## 2. 前置依赖

- `test_render_chain.cjs` 已覆盖项目选择后的 project head、关联图表与新闻标记。
- `test_project_ui.cjs` 已覆盖项目页结构、账户网格和事件卡交互。
- `.codestable/compound/2026-09-28-decision-explicit-ui-composition.md` 规定新增组合必须经命名入口注册，不新增同名 `render` 覆盖。
- `project.js` 在 `charts.js` 之前加载；项目页扩展入口必须在 charts 注册前创建。

## 3. 执行顺序

### 步骤 1：拆分项目页的结构化渲染片段

- **引用方法**：M-L2-01 Extract Function。
- **具体操作**：从 `projectPage` 提取项目头、基础行情、团队账号和讨论者渲染函数；`projectPage` 只按当前顺序组装片段，保留 HTML、class、文案和 `compactAccounts` 调用位置。
- **退出信号**：项目页继续含项目头、官方链接、行情区、账户网格和讨论者区；现有项目 UI 与 render-chain 测试不变。
- **验证责任**：AI 自证。
- **回滚**：回退本步骤对 `dist/project.js` 与项目 UI 测试的单步修改。

### 步骤 2：形成关联图表控制器

- **引用方法**：M-L3-07 Single Responsibility Split。
- **具体操作**：在 `charts.js` 形成命名的关联图表控制器，内部拥有缓存、请求中集合、错误和显示设置；对外提供“确保当前项目图表数据”“渲染关联图表区块”“打开图表新闻”入口。保留现有 60 秒缓存、单飞、强制刷新和当前项目/周期完成后重渲染。
- **退出信号**：图表缓存、错误、周期和新闻标记的可观察行为不变；图表按钮与周期开关仍通过控制器入口工作。
- **验证责任**：AI 自证。
- **回滚**：回退本步骤对 `dist/charts.js` 与图表测试的单步修改。

### 步骤 3：以项目页扩展注册替换图表 render 覆盖

- **引用方法**：M-L1-01 Parallel Change。
- **具体操作**：在 `project.js` 建立命名的项目页扩展注册入口。项目页在写入 `projectPage` 并运行 `compactAccounts` 后，按注册顺序调用扩展；charts 控制器注册“替换行情区块并确保图表数据”的扩展，移除 `beforeLinkedChartRender` 与 `charts.js` 对 `render` 的同名赋值。
- **退出信号**：charts.js 不含 `beforeLinkedChartRender` 或 `render=function`；项目选择后关联图表与新闻标记仍显示；没有项目时不请求图表。
- **验证责任**：AI 自证 + HUMAN。
- **回滚**：回退本步骤；恢复原有 charts render 包装。

## 4. 风险与看点

- **图表请求时机**：项目扩展只能在项目页已经存在、`state.project` 与扩展项目一致时请求；否则会出现无项目请求或旧项目响应覆盖。
- **递归渲染**：图表请求完成会触发 `render()`；扩展必须依赖现有缓存/单飞检查，避免形成重复请求或无限循环。
- **DOM 替换目标**：图表仍只替换项目页首个行情 `.project-section`，不能误替换团队或讨论者区。
- **测试桩边界**：harness 以 `outerHTML` 记录替换行为；最终步骤仍需要人工切换项目、周期、刷新图表并点击新闻标记。
