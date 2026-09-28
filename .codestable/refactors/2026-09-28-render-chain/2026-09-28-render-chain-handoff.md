# render-chain 重构 · 交接简报（中断续传用）

- 日期: 2026-09-28
- 当前阶段: 已完成刻画测试、前端渲染链架构 backfill，并已确认显式 UI 组合原则。原始大范围任务仍按模块级范围拆分推进。
  **rules-notifications 已完成。** 规则页与浏览器通知已从隐式 `renderRules` 覆盖切换为显式规则页扩展注册，自动验证和用户确认均已完成。
- 用户已确认范围: 4 个测试文件（render 链 / detail 链 / rules UI / project UI），带上 eventCard / openAdd 接管。
  测试只固化现状、不改产品代码；目标是在当前代码上先跑绿。
- 审计原文: `.codestable/audits/2026-09-28-project-wide/finding-07.md`（已关闭）。

## 接线缝清单（刻画对象）

| 全局函数 | 基座 | 接管/覆盖点 |
| --- | --- | --- |
| render | live.js | live.js、project.js、charts.js、preferences.js、reading-updates.js（5 层包装） |
| openDetail | live.js | live.js（质量证据）、project.js（本地化标题 / 关联报道）、reading-updates.js（版本记录 / 时间线） |
| renderRules / openRule | live.js | rules.js 覆盖；notifications.js 再包 renderRules |
| eventCard / openAdd | live.js | project.js 覆盖（本地化、候选标签、表单） |
| filteredEvents | live.js | reading-updates.js、live.js 的 news 过滤叠加 |

load 顺序（dist/index.html，scripts 解析自 index.html）:
source-status → live → project → rules → reorder → watchlist → charts → notifications → preferences → reading-updates

## 已完成

- dist 全部 10 个 js + index.html + 现有 6 个测试已通读（2026-09-28）。
- 可复用模式: `test_live_refresh.cjs`（elementStub + vm + pending fetch + settle）、`test_reading_updates.cjs`（ctx stub + 收集 handlers 手动触发点击）。
- 新增 `chain-harness.cjs`：按 `dist/index.html` 解析并断言 10 个脚本的加载顺序，在共享 VM 中提供 DOM、fetch、localStorage 与事件分发桩。
- 新增 4 组刻画测试：`test_render_chain.cjs`、`test_detail_chain.cjs`、`test_rules_ui.cjs`、`test_project_ui.cjs`。覆盖 feed / 项目页 / 图表 / 规则页 / 通知面板、详情质量证据与时间线、规则表单、原文切换与新增项目表单。
- 回归结果（当前工作区）：Node 21/21、Python 97/97 全部通过；`git diff --check` 通过。
- 已新增 `.codestable/architecture/ui-render-chain.md`，并更新 `.codestable/architecture/ARCHITECTURE.md` 索引；架构文档的 frontmatter 校验通过。
- 已新增 active decision：`.codestable/compound/2026-09-28-decision-explicit-ui-composition.md`。
- 已完成 rules-notifications 模块的前置检查和 scan；`test_notifications.cjs` 与 `test_rules_ui.cjs` 共 4 项通过。
- 已完成 rules-notifications 的 design、checklist 与 3 个实现步骤：规则页渲染拆分、通知控制器、显式规则页扩展注册；当前全量回归为 Node 21/21 与 Python 97/97。
- rules-notifications checklist 已 complete，用户在目视验收请求后确认继续；本模块未单独提交。
- render-orchestration 已完成：live 基座按固定顺序运行实时状态、项目页、偏好状态和阅读回顾四个 render 扩展；render-chain 测试同时断言扩展数量与名称顺序。当前全量回归 Node 21/21、Python 97/97 与 git diff --check 已通过，用户已确认浏览器全流程验收。

## 待做（严格按序）

1. detail-reading 已完成：详情扩展通过显式 beforeOpen / afterOpen 阶段组合，自动验证和用户目视确认均已完成。
2. project-charts 已完成：项目页扩展注册承接关联图表，charts 不再覆盖 `render`；自动验证和用户目视确认均已完成。
3. render-orchestration 已完成，checklist 已 complete，finding-07 已关闭。

## harness 设计要点（别丢）

- 脚本顺序从 `dist/index.html` 正则解析 `<script src="...">`，并断言等于当前 10 文件顺序（order 契约本身就是刻画对象）。
- document stub: selector → 稳定 stub 注册表（同一 selector 多次 querySelector 返回同一对象）；querySelectorAll 特判:
  `'.rail-block'`→2 个、`'[data-view]'`→3、`'[data-filter]'`→4、`'dialog'`→2；`'#detail-content .quality-evidence'`、`'.alert-history details'` 等查"created 注册表"（按 className 过滤，textContent 可由 innerHTML 去标签派生，用于模拟 remove 语义）。
- element stub 必备: innerHTML / textContent / hidden / value / checked / className / open / disabled / dataset / classList(add/remove/toggle/contains) / style / addEventListener / removeEventListener / append / prepend / before / remove（标记 removed）/ insertAdjacentHTML（记录到 calls）/ setAttribute / getAttribute / hasAttribute / focus / close / showModal / matches / closest / getBoundingClientRect / offsetHeight / scrollIntoView / contains / setPointerCapture / querySelector(子 stub 缓存) / querySelectorAll(特判) / outerHTML（可写，记录）。
- 特判 stub:
  - `'#rule-form'`: 需带 `elements:{type:{value:'ema',addEventListener(){}},threshold:{},period:{},...}` + addEventListener（rules.js openRule 会立刻读 form.elements.type.value）。
  - `'#detail-content .modal-footer'`: 记录 before() / insertAdjacentHTML() 调用供断言。
  - `'#detail-content h1'` / `'.dialog-inner > p'`: project.js 会设 textContent，断言本地化标题用。
- fetch 路由（全部同步 resolve ok，测试用 settle() 等 2-3 次 setImmediate）:
  `/api/live`→liveData fixture；`/api/chart`→chart fixture；`/api/preferences` GET→`{values:{}}`，POST→ok；其余→`{ok:false}`。
- fixture 硬性要求:
  - `markets.near.errors = {}`（marketEvents 会读 `Object.keys(m.errors)`）。
  - news 事件 id 形如 `'news_0123456789ab'`（refreshLive: `parseInt(e.id.slice(5,17),16)`）。
  - `publishedAt = Date.now() - 1h` 量级（catchup 的 24h 窗口用真实 now）。
  - 带 `clusterSize:2`、`relatedItems`、`progressCandidates`、`sourcesList`、`translationStatus:'ready'`（如想刻画 translation-note 就不设 ready）。
- 行为时序: load 期 render 被调用多次（live / project / rules / watchlist / charts / reading-updates 末尾各一次）；preferences 的 `sync()` 异步落地后还会再 render 一次 → **断言前必须 settle**。
- notifications: `Notification` 未定义 → `supported()=false`；panel 只在 `state.view==='rules' && !state.project` 时 prepend 到 `#feed`（文案"当前浏览器不支持此功能。"）。
- reading-updates: catchup 面板在 feed 且无项目时 `insertAdjacentHTML('afterbegin')` 到 `#feed`；openDetail 会写 `versions` 并落 localStorage `signal-reading-v2`。
- 真实 DOM 语义（outerHTML 真替换、textContent/innerHTML 联动）stub 不完整模拟——只断言 stub 侧可观察行为；浏览器目视验证留给 apply 阶段（技能要求 HUMAN 验证）。

## 各测试断言草稿

- render_chain: `.demo-status`=真实数据测试 / `.demo-banner` 含 LIVE BETA / `.brief` 含 DATA COVERAGE / rail[0] 标题 / `#market-watch` 含 data-project / `#feed` 含 catchup-panel + translation-note + "已合并"标签 / `footer span` 偏好状态 / 切项目视图后 `#project-overview` 含 project-head 且 `.project-section` outerHTML 变为 linked-chart / rules 视图 → 后台规则 + 通知面板。
- detail_chain: news → quality-evidence（"为什么出现在这里"）+ h1=titleZh + cluster 区块被时间线替换 + 版本落盘；market → 仅基座内容、无 quality 区、不崩。
- rules_ui: renderRules 覆盖（尚无后台规则 / 列表项 / 触发记录）+ notifications 面板叠加 + openRule 表单（新建/编辑）+ 描述文案。
- project_ui: eventCard 组合（language-toggle、"后续进展候选"、"已合并"、"已读事件有新增进展"、原文/中文切换）+ openAdd（"新增关注项目"）+ compactAccounts 不崩。

## 恢复方式

- 本会话: 说"继续，写 chain-harness.cjs"。
- 新会话: 读本简报 + `dist/*.js`（10 个文件全读）+ 参考测试 `test_live_refresh.cjs`、`test_reading_updates.cjs` 即可无缝接手。
- 全量复测命令（run_command 无 glob，需显式列文件）:
  `node --test test_notifications.cjs test_preferences_ui.cjs test_reading_updates.cjs test_reorder.cjs test_source_status.cjs test_live_refresh.cjs test_render_chain.cjs test_detail_chain.cjs test_rules_ui.cjs test_project_ui.cjs`
  Python 侧不涉及，保持 92 项不动。
