---
doc_type: decision
category: architecture
date: 2026-09-28
slug: explicit-ui-composition
status: active
area: frontend-rendering
tags: [frontend, rendering, refactor]
---

## 背景

当前前端在同一全局作用域内按 `dist/index.html` 的固定顺序加载脚本。后加载脚本通过保存并重赋 `render`、`renderRules`、`openDetail` 等全局函数来追加行为。该模式使原始渲染链任务命中跨模块前置检查，且脚本顺序成为隐式依赖。

## 决定

后续新增或拆分 UI 行为时，使用模块拥有的显式组合入口；不再新增依赖脚本加载顺序的同名全局函数覆盖。

现有覆盖链按行为等价的模块级步骤迁移。迁移期间保留现有脚本顺序和对外页面行为，直到对应模块已经由显式入口承接。

第一个迁移切口是规则页与浏览器通知：将通知面板与通知交付接入规则 UI 的明确入口，而非继续包装 `renderRules`。

## 理由

该决定基于已确认的前端渲染链架构图和刻画测试：`renderRules` 当前由 `rules.js` 定义后再由 `notifications.js` 覆盖，正确行为依赖两份脚本的先后顺序。用户于 2026-09-28 确认采用显式组合方向，并同意优先从规则页与浏览器通知开始。

## 考虑过的替代方案

- 继续沿用同名全局函数覆盖：保留现有隐式依赖，不能解除该类耦合。
- 一次性重写全部前端脚本：改动范围过大，无法在每一步用现有刻画测试验证行为等价。

## 后果

- 新的 UI 扩展必须在所属模块的组合入口注册，并由该模块负责调用顺序。
- 规则页与通知重构必须保持规则列表、触发记录、通知授权状态和前台通知去重语义不变。
- 其他渲染链模块在各自范围内逐步迁移；本决定不要求一次性改变全部脚本。

## 相关文档

- `.codestable/architecture/ui-render-chain.md`
- `.codestable/refactors/2026-09-28-render-chain/2026-09-28-render-chain-handoff.md`
- `.codestable/audits/2026-09-28-project-wide/finding-07.md`
