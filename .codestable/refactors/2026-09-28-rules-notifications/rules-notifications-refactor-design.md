---
doc_type: refactor-design
refactor: 2026-09-28-rules-notifications
status: approved
scope: 将规则页渲染和浏览器通知从隐式 renderRules 覆盖迁移为显式扩展入口，保持当前页面和通知行为。
summary: 先拆规则页的纯字符串渲染，再形成通知控制器，最后用规则页扩展注册替换 notifications.js 对 renderRules 的同名覆盖。
---

# rules-notifications refactor design

## 1. 本次范围

- 采纳 scan 条目：#1、#2、#3。
- 改动文件：`dist/rules.js`、`dist/notifications.js`、`test_rules_ui.cjs`、`test_notifications.cjs`，必要时调整 `chain-harness.cjs` 的最小测试桩。
- 不改 `live.js` 中既有 `renderRules` 调用点、共享 `state` / `liveData` 的结构、服务端 API、通知授权语义或 `dist/index.html` 的脚本列表。
- 总风险：中。规则页 DOM 和浏览器通知均为外部可观察行为；现有刻画测试与人工规则页回归共同守护。

## 2. 前置依赖

- 已有 `test_rules_ui.cjs` 断言规则页、通知面板和规则表单组合；`test_notifications.cjs` 断言提醒的新鲜度、去重和启用后不补发历史。
- 已归档的 `.codestable/compound/2026-09-28-decision-explicit-ui-composition.md` 规定新增组合不得依赖同名全局函数覆盖。
- `dist/index.html` 的加载顺序保持不变：`rules.js` 在 `notifications.js` 之前，使通知脚本能够调用规则模块公开的命名注册入口。

## 3. 执行顺序

### 步骤 1：拆出规则页的命名渲染片段

- **引用方法**：M-L2-01 Extract Function。
- **具体操作**：从 `renderRules` 提取规则工具栏/规则卡片、触发记录和证据字段展示函数；保留 `renderRules` 负责读取 `liveData`、拼接页面并调用后续扩展。
- **退出信号**：规则数量、规则卡片、触发记录、创建与编辑规则表单的输出均与刻画测试一致。
- **验证责任**：AI 自证。
- **回滚**：回退本步骤对 `dist/rules.js` 与 `test_rules_ui.cjs` 的单步修改。

### 步骤 2：将浏览器通知封装为显式控制器

- **引用方法**：M-L3-07 Single Responsibility Split。
- **具体操作**：在 `notifications.js` 形成命名的浏览器通知控制器；控制器内部保留授权、已见提醒、面板刷新、storage 事件和 `signal-live` 交付状态，对外只提供面板渲染与实时载荷处理入口。`freshNotifications` 保持可直接测试。
- **退出信号**：旧的去重、过期过滤和启用后不补发历史断言全部通过；规则页仍能渲染通知面板。
- **验证责任**：AI 自证。
- **回滚**：回退本步骤对 `dist/notifications.js` 与通知测试的单步修改。

### 步骤 3：以规则页扩展注册替换 renderRules 覆盖

- **引用方法**：M-L1-01 Parallel Change。
- **具体操作**：在 `rules.js` 增加命名的规则页扩展注册入口；`renderRules` 完成基础 DOM 输出后调用已注册扩展。`notifications.js` 注册通知面板渲染入口，并移除 `const prior=renderRules; renderRules=function(){...}` 这一同名覆盖。保留现有 `signal-live` 和 storage 监听。
- **退出信号**：全仓不存在 notifications.js 对 `renderRules` 的同名赋值；规则页、通知面板和通知新鲜度测试全绿。
- **验证责任**：AI 自证 + HUMAN。
- **回滚**：回退本步骤；恢复原有通知包装函数。

## 4. 风险与看点

- **首屏/规则页时机**：通知脚本加载后才完成注册。注册后若当前正在规则页，必须触发一次不改变状态的规则页刷新，确保面板不等待下一次数据刷新。
- **前台通知去重**：`initialized`、`startedAt`、`seen`、`enabledAt` 仍由同一控制器保有；不能在注册或刷新面板时重置。
- **测试桩语义**：harness 只验证可观察调用与 DOM 结果，最终步骤仍需要在浏览器中验证规则页的授权按钮和通知行为。
- **设计偏离说明**：scan #1 最初包含移除独立通知脚本；本设计保留 `notifications.js` 作为可测试的通知控制器，仅移除隐式 `renderRules` 覆盖。这保留现有脚本列表和纯函数测试接缝，同时满足已确认的显式组合原则。
