---
doc_type: refactor-apply-notes
refactor: 2026-09-28-rules-notifications
---

# rules-notifications apply notes

## 步骤 1：拆出规则页的命名渲染片段

- 完成时间：2026-09-28
- 改动文件：`dist/rules.js`。
- 验证结果：`node --check dist/rules.js` 通过；`node --test test_rules_ui.cjs test_notifications.cjs` 4/4 通过；`git diff --check` 通过。
- 偏离：无。

## 步骤 2：将浏览器通知封装为显式控制器

- 完成时间：2026-09-28
- 改动文件：`dist/notifications.js`。
- 验证结果：`node --check dist/notifications.js` 通过；`node --test test_rules_ui.cjs test_notifications.cjs` 4/4 通过；`git diff --check` 通过。
- 偏离：无。

## 步骤 3：以规则页扩展注册替换 renderRules 覆盖

- 完成时间：2026-09-28
- 改动文件：`dist/rules.js`、`dist/notifications.js`、`test_rules_ui.cjs`。
- 验证结果：`node --check dist/rules.js` 与 `node --check dist/notifications.js` 通过；Node 21/21、Python 92/92 通过；`rg` 确认 `notifications.js` 不含 `const prior=renderRules` 或 `renderRules=function`；`git diff --check` 通过。
- 偏离：无。独立 `notifications.js` 保留为显式通知控制器，符合已批准 design 的收敛说明。

## 最终人工验收

- 完成时间：2026-09-28
- 验证结果：用户在规则页目视确认请求后回复“继续吧”；`visual-rules-page` 标记为 passed。
- 收尾：本模块级 refactor 已完成；未创建 git commit。
