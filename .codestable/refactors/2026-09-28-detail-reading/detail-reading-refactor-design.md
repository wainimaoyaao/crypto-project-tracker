---
doc_type: refactor-design
refactor: 2026-09-28-detail-reading
status: approved
scope: 将详情页的质量、项目和阅读增强从多层 openDetail 覆盖迁移为带前置/后置阶段的显式详情扩展入口，保持既有页面和阅读状态行为。
summary: 先提取项目详情增强，再封装阅读详情控制器，最后在 live.js 建立详情扩展注册与前置/后置执行阶段，移除 project.js 与 reading-updates.js 对 openDetail 的同名覆盖。
---

# detail-reading refactor design

## 1. 本次范围

- 采纳 scan 条目：#1、#2、#3。
- 改动文件：`dist/live.js`、`dist/project.js`、`dist/reading-updates.js`、`test_detail_chain.cjs`、`test_reading_updates.cjs`，必要时调整 `chain-harness.cjs` 的最小测试桩。
- 不改变基础事件详情文案、已读状态、收藏行为、翻译状态、关联报道时间线、阅读 ledger、规则提醒上下文或服务端 API。
- 总风险：高。详情打开同时影响 DOM、已读状态、`localStorage` 阅读版本和后续重渲染；扩展顺序必须与当前覆盖链一致。

## 2. 前置依赖

- `test_detail_chain.cjs` 已覆盖新闻的质量证据、时间线替换与阅读版本落盘，以及行情详情不应出现新闻质量区。
- `test_reading_updates.cjs` 已覆盖进展版本、历史新闻过滤和提醒上下文导航。
- `.codestable/compound/2026-09-28-decision-explicit-ui-composition.md` 规定新 UI 组合采用显式入口，不新增同名全局函数覆盖。
- 当前组合顺序为：基础详情 → 质量解释 → 项目本地化 → 聚类证据 → 阅读版本落盘/时间线。阅读版本必须在基础详情写入已读状态之前记录，因此需要单独的 `beforeOpen` 阶段。

## 3. 执行顺序

### 步骤 1：拆出项目详情增强函数

- **引用方法**：M-L2-01 Extract Function。
- **具体操作**：从 `project.js` 的两个 `openDetail` 包装中提取“项目详情本地化”和“关联报道增强”函数，函数显式接收事件和详情容器；在过渡期仍由现有包装按原顺序调用。
- **退出信号**：新闻标题/摘要本地化、原文切换按钮、团队身份提示、进展候选和关联报道输出保持当前测试结果；行情详情不进入新闻增强。
- **验证责任**：AI 自证。
- **回滚**：回退本步骤对 `dist/project.js` 与 detail 测试的单步修改。

### 步骤 2：形成阅读详情控制器

- **引用方法**：M-L3-07 Single Responsibility Split。
- **具体操作**：从 `reading-updates.js` 的闭包中形成阅读详情控制器；它拥有 ledger 和 versions，并暴露 `beforeOpen(event)` 与 `afterOpen(event, detailContext)`。前者记录版本，后者追加翻译提示、替换聚类区块并插入时间线。过渡期仍由现有 `openDetail` 包装调用这两个入口。
- **退出信号**：打开新闻仍将版本写入 `signal-reading-v2`；进展候选仍替换旧聚类区块；已读事件复活与提醒上下文行为保持不变。
- **验证责任**：AI 自证。
- **回滚**：回退本步骤对 `dist/reading-updates.js` 与阅读测试的单步修改。

### 步骤 3：以详情扩展注册替换 openDetail 覆盖

- **引用方法**：M-L1-01 Parallel Change。
- **具体操作**：在 `live.js` 建立命名的详情扩展注册入口，按注册顺序运行 `beforeOpen` 和 `afterOpen` 钩子。质量解释注册为后置扩展；项目本地化和关联报道增强按原顺序注册为后置扩展；阅读控制器注册为前置记录和后置时间线扩展。移除 `project.js` 与 `reading-updates.js` 对 `openDetail` 的同名赋值。
- **退出信号**：全仓除基础实现外不再有项目或阅读层 `openDetail=function`；扩展注册顺序、新闻详情、行情详情、版本落盘和时间线测试全绿。
- **验证责任**：AI 自证 + HUMAN。
- **回滚**：回退本步骤；恢复原有详情包装函数。

## 4. 风险与看点

- **阶段顺序**：阅读版本必须在基础 `openDetail` 的 `persist()` 和 `render()` 之前记录；质量、项目和阅读 DOM 增强必须在基础详情写入 `.modal-footer` 之后执行。
- **时间线替换**：阅读增强只删除包含“相关报道与各方表述”的聚类区块，不能删除质量解释区块。
- **原文选择**：项目本地化、关联报道和阅读时间线都读取 `originalSelections`；注册后必须共享同一个集合并在重新打开详情时反映最新状态。
- **测试桩边界**：harness 模拟 DOM 插入与 remove 语义，最终步骤仍需要人工依次打开新闻、带关联报道的新闻与行情详情。
