---
doc_type: refactor-scan
refactor: 2026-09-28-detail-reading
status: user-reviewed
scope: dist/live.js、dist/project.js、dist/reading-updates.js，以及 test_detail_chain.cjs 与 test_reading_updates.cjs
summary: 发现 3 条结构优化点；低风险 1 条、中风险 1 条、高风险 1 条。
---

# detail-reading scan

## 总览

- 扫描范围：`dist/live.js`、`dist/project.js`、`dist/reading-updates.js`、`test_detail_chain.cjs`、`test_reading_updates.cjs`。
- 发现 3 条优化点：结构 3 / 性能 0 / 可读性 0。
- 按风险：低 1 条 / 中 1 条 / 高 1 条。
- 建议先做：#2、#3；二者分别收敛项目详情和阅读状态。#1 应在两个局部增强器稳定后再做。
- 建议慎做 / 后做：#1 替换横跨 3 个脚本的 `openDetail` 组合，需要确保质量证据、语言切换、时间线替换和阅读版本落盘的先后顺序不变。
- 前置检查 7 条全过：✓。本次按 `explicit-ui-composition` 决定把 detail-reading 视为一个受控模块；现有 `events`、`state`、`originalSelections` 和基础 `openDetail` 的对外可观察行为保持不变。

## 条目

### #1 以详情扩展注册替换 openDetail 覆盖 ✓

- **位置**：`dist/live.js:33,73-74`、`dist/project.js:5-6,59-60`、`dist/reading-updates.js:30-39`
- **分类**：结构
- **现状**：基础 `openDetail` 之后又被质量证据、项目本地化、聚类报告和阅读时间线连续覆盖；后续实现通过保存前一函数并调用它来维持组合。
- **问题**：`openDetail` 在基座之外被同名赋值 4 次，跨 3 个脚本形成隐式调用链；阅读层依赖先前层已经创建的 `.modal-footer` 和 `quality-evidence`，脚本顺序或任一调用遗漏都会改变详情内容。
- **建议**：在详情基座建立命名的扩展注册入口，以稳定顺序执行质量、项目和阅读增强器；先并行保留现有输出断言，再逐个把包装逻辑迁为注册的扩展函数。
- **建议映射的方法**：M-L1-01（Parallel Change 并行变更）
- **风险**：高——详情打开会同步更新已读状态、持久化阅读版本并插入/替换多个 DOM 区块，错误顺序会直接改变用户可见内容。
- **验证**：AI 自证（`node --test test_detail_chain.cjs test_reading_updates.cjs test_render_chain.cjs`；检查不再出现项目或阅读层对 `openDetail` 的同名赋值）｜HUMAN（依次打开新闻、带关联报道的新闻和行情快照，确认原文切换、时间线与质量证据）。
- **范围**：约 120 行 / 3 个产品文件。

### #2 将项目详情增强拆成命名函数 ✓

- **位置**：`dist/project.js:5-6,59-60`
- **分类**：结构
- **现状**：`project.js` 通过两次 `openDetail` 覆盖分别处理中文标题/原文按钮与关联报道/进展候选；两段逻辑都直接查找同一详情 DOM。
- **问题**：同一文件为详情行为保存前一函数并重赋两次；语言、本地化、团队身份提示、关联报道和进展候选共有 5 类职责，无法单独定位或复用。
- **建议**：提取命名的“项目详情本地化”和“关联报道增强”函数，显式接收事件与详情容器；在保留当前包装方式的过渡期先让这两个函数承担全部 DOM 修改。
- **建议映射的方法**：M-L2-01（Extract Function 提取函数）
- **风险**：低——逻辑仅改写或插入详情 DOM，现有 detail-chain 测试已覆盖新闻与行情的分支。
- **验证**：AI 自证（`node --test test_detail_chain.cjs`，确认新闻有质量证据/时间线，行情不新增新闻质量区）｜HUMAN（打开新闻详情并切换原文/中文）。
- **范围**：约 35 行 / 1 个产品文件。

### #3 封装阅读详情的版本与时间线增强 ✓

- **位置**：`dist/reading-updates.js:9-39`
- **分类**：结构
- **现状**：阅读层的闭包同时维护 ledger、事件版本、翻译提示、详情时间线、旧聚类区块删除和详情打开时的版本落盘。
- **问题**：一个闭包承担 6 类职责；`openDetail` 包装既写 `localStorage`，又依赖先前层插入的 `quality-evidence`，再根据其文字内容删除旧区块，测试与维护都必须了解整个链条。
- **建议**：抽出阅读详情控制器，显式暴露“记录已打开版本”和“增强新闻详情”两个入口；控制器内部保留 ledger 与版本状态，并在详情模块注册时调用。
- **建议映射的方法**：M-L3-07（Single Responsibility Split 职责分离）
- **风险**：中——迁移时不得改变已读事件复活、翻译未就绪提示和同一事件时间线的顺序。
- **验证**：AI 自证（`node --test test_detail_chain.cjs test_reading_updates.cjs`，覆盖版本落盘、进展复活、历史新闻过滤和提醒上下文链接）｜HUMAN（打开一条有后续进展的新闻，刷新后确认“已读事件有新增进展”语义不变）。
- **范围**：约 45 行 / 1 个产品文件。
