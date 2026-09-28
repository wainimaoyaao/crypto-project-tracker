---
doc_type: refactor-apply-notes
refactor: 2026-09-28-detail-reading
---

# detail-reading apply notes

## 步骤 1：拆出项目详情增强函数

- 完成时间：2026-09-28
- 改动文件：`dist/project.js`。
- 验证结果：`node --check dist/project.js` 通过；`node --test test_detail_chain.cjs test_reading_updates.cjs` 5/5 通过；`git diff --check` 通过。
- 偏离：无。

## 步骤 2：形成阅读详情控制器

- 完成时间：2026-09-28
- 改动文件：`dist/reading-updates.js`。
- 验证结果：`node --check dist/reading-updates.js` 通过；`node --test test_detail_chain.cjs test_reading_updates.cjs` 5/5 通过；`git diff --check` 通过。
- 偏离：无。

## 步骤 3：以详情扩展注册替换 openDetail 覆盖

- 完成时间：2026-09-28
- 改动文件：`dist/live.js`、`dist/project.js`、`dist/reading-updates.js`、`test_detail_chain.cjs`、`test_reading_updates.cjs`。
- 验证结果：三个脚本的 `node --check` 通过；Node 21/21、Python 92/92 通过；`rg` 确认项目与阅读层不含 `priorDetail`、`beforeClusterDetail`、`oldDetail` 或 `openDetail=function`；`git diff --check` 通过。
- 偏离：独立阅读测试增加 `registerDetailExtension` 测试桩并断言阅读控制器注册一次，以匹配新显式组合依赖；产品行为未变。

## 最终人工验收

- 完成时间：2026-09-28
- 验证结果：用户确认普通新闻、关联报道新闻和行情详情的目视验收通过。
- 收尾：detail-reading 模块级 refactor 已完成；未创建 git commit。
