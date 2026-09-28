---
doc_type: refactor-scan
refactor: 2026-09-28-rules-notifications
status: user-reviewed
scope: dist/rules.js、dist/notifications.js、dist/index.html，以及 test_rules_ui.cjs 与 test_notifications.cjs
summary: 发现 3 条结构优化点；低风险 1 条、中风险 2 条。
---

# rules-notifications scan

## 总览

- 扫描范围：`dist/rules.js`、`dist/notifications.js`、`dist/index.html`、`test_rules_ui.cjs`、`test_notifications.cjs`。
- 发现 3 条优化点：结构 3 / 性能 0 / 可读性 0。
- 按风险：低 1 条 / 中 2 条。
- 建议先做：#1、#2、#3；三项均有 Node 组合或单元测试可自证。
- 建议慎做 / 后做：#1 会改变脚本责任归属和 `index.html` 加载列表，须保留规则页、通知面板和前台通知的全部现有行为。
- 前置检查 7 条全过：✓。本次以已确认的 `explicit-ui-composition` 决定划定 rules-notifications 模块；不修改 `live.js` 对 `renderRules`、共享状态和实时事件的既有接口。

## 条目

### #1 将通知组合入口迁入规则模块 ✓

- **位置**：`dist/notifications.js:12-50`、`dist/rules.js:3-7`、`dist/index.html:5`
- **分类**：结构
- **现状**：`notifications.js` 先保存 `renderRules`，再以同名赋值包装它；规则页每次渲染后由该隐式包装插入通知面板。
- **问题**：规则页渲染完成后要追加通知面板这一职责分散在两个脚本中，且正确组合依赖 `rules.js` 必须早于 `notifications.js` 加载；同名 `renderRules` 的定义与覆盖各 1 次。
- **建议**：在规则模块建立命名的通知组合入口，由规则页渲染在生成规则内容后显式调用；通过并行入口逐步迁入通知面板、`signal-live` 交付与 storage 刷新逻辑，再移除独立通知脚本及其 `<script>` 标签。
- **建议映射的方法**：M-L1-01（Parallel Change 并行变更）
- **风险**：中——涉及页面渲染时机、前台通知初始去重和 `localStorage` 状态，必须逐项保持。
- **验证**：AI 自证（`node --test test_notifications.cjs test_rules_ui.cjs`，并检查 `dist/index.html` 不再加载旧通知脚本）｜HUMAN（打开规则页，确认通知面板、授权按钮与提醒记录仍可见）。
- **范围**：约 74 行 / 3 个产品文件。

### #2 拆出浏览器通知控制器的状态与副作用 ✓

- **位置**：`dist/notifications.js:7-46`
- **分类**：结构
- **现状**：同一闭包同时维护通知授权、`localStorage` 读写、通知面板 DOM、跨标签刷新、`signal-live` 事件交付和错误文案。
- **问题**：一个闭包承担 6 类可独立变化的职责；面板刷新同时被规则渲染、storage 事件和授权按钮调用，交付逻辑又依赖 `initialized`、`startedAt`、`problem` 三个闭包状态。
- **建议**：抽出命名的浏览器通知控制器，显式暴露“渲染面板”和“处理实时载荷”两个入口；把授权/已见提醒状态保留在控制器内部，由规则模块在自己的组合入口调用它。
- **建议映射的方法**：M-L3-07（Single Responsibility Split 职责分离）
- **风险**：中——闭包状态迁移可能改变首次加载不补发历史提醒的语义。
- **验证**：AI 自证（`node --test test_notifications.cjs test_rules_ui.cjs`；新增或扩展测试覆盖初始载荷、已授权和跨标签刷新）｜HUMAN（安全上下文中开启一次浏览器提醒，确认不会补发旧记录）。
- **范围**：约 45 行 / 2 个产品文件。

### #3 拆分规则页的列表与触发记录渲染 ✓

- **位置**：`dist/rules.js:3-7`
- **分类**：结构
- **现状**：`renderRules` 在一个模板字符串中同时筛选规则、构建工具栏、渲染规则卡片、映射证据字段并渲染触发记录。
- **问题**：同一函数包含 4 个独立 UI 区块和 1 个证据字段映射；修改某一块需要触碰整段模板，且通知组合入口只能在整个函数返回后追加。
- **建议**：提取命名的规则列表、触发记录和证据展示函数；`renderRules` 只负责读取 `liveData`、组装三个区块并调用通知组合入口。
- **建议映射的方法**：M-L2-01（Extract Function 提取函数）
- **风险**：低——纯字符串生成，输入和输出可以由现有规则 UI 测试刻画。
- **验证**：AI 自证（`node --test test_rules_ui.cjs`，断言规则数、规则卡片、触发记录、通知面板与新建/编辑表单）｜HUMAN（规则页切换、编辑、删除和暂停各一次）。
- **范围**：约 20 行 / 1 个产品文件。
