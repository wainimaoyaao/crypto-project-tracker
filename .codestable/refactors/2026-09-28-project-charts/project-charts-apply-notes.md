---
doc_type: refactor-apply-notes
refactor: 2026-09-28-project-charts
---

# project-charts apply notes

## 步骤 1：拆分项目页的结构化渲染片段

- 完成时间：2026-09-28
- 改动文件：`dist/project.js`。
- 验证结果：`node --check dist/project.js` 通过；`node --test test_render_chain.cjs test_project_ui.cjs` 2/2 通过；`git diff --check` 通过。
- 偏离：无。

## 步骤 2：形成关联图表控制器

- 完成时间：2026-09-28
- 改动文件：`dist/charts.js`。
- 验证结果：`node --check dist/charts.js` 通过；`node --test test_render_chain.cjs test_project_ui.cjs` 2/2 通过；`git diff --check` 通过。
- 偏离：无。

## 步骤 3：以项目页扩展注册替换图表 render 覆盖

- 完成时间：2026-09-28
- 改动文件：`dist/project.js`、`dist/charts.js`、`test_render_chain.cjs`。
- 验证结果：两个脚本的 `node --check` 通过；Node 21/21、Python 92/92 通过；`rg` 确认 charts.js 不含 `beforeLinkedChartRender` 或 `render=function`；`git diff --check` 通过。
- 偏离：无。charts.js 保留为显式关联图表控制器，通过项目页扩展注册挂载。

## 最终人工验收

- 完成时间：2026-09-28
- 验证结果：用户确认项目切换、周期切换、刷新与新闻标记的目视验收通过。
- 收尾：project-charts 模块级 refactor 已完成；未创建 git commit。
