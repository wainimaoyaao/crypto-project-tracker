---
doc_type: audit-finding
audit: 2026-09-28-project-wide
finding_id: "maintainability-07"
nature: maintainability
severity: P2
confidence: high
suggested_action: cs-refactor
status: closed
closed_on: 2026-09-28
---

# Finding 07：全局渲染函数层层覆盖并依赖脚本顺序

## 速答

多个前端脚本通过保存旧函数、重赋值全局函数的方式扩展同一渲染路径；行为依赖 index.html 的脚本排列，修改某个页面模块时难以判断最终调用链。

## 修复前证据

- dist/index.html:5 — live、project、rules、charts、notifications、preferences、reading-updates 以固定顺序加载为普通脚本。
- dist/live.js:54–55、dist/project.js:12–13、dist/charts.js:22–23、dist/preferences.js:21、dist/reading-updates.js:40–41 — render 被先后包装五次，后者通过捕获前者继续调用。
- dist/project.js:5–6、59–60 与 dist/reading-updates.js:30–31 — openDetail 也被多次重赋值；dist/rules.js:3、9 覆盖 renderRules 和 openRule。

## 影响

添加模块或调整脚本顺序容易改变最终调用路径；局部测试即使覆盖单个函数，也不能自动说明整条包装链正确。当前代码尚未证实由此造成的具体线上故障。

## 修复方向

把扩展点改为显式注册或由一个组合入口按既定顺序调用，保留现有交互行为并测试组合后的主要页面路径。

## 实施状态

2026-09-28 已完成显式组合迁移。live 基座提供有序 render 扩展注册；实时状态、项目页、footer 偏好状态和阅读回顾依次登记。项目图表、浏览器通知与详情增强继续使用各自的命名扩展入口。

自动验证已确认完整链路、项目页、偏好同步和阅读回顾保持行为，且旧的 render 包装标识已不存在。用户已确认浏览器全流程验收，finding-07 关闭。

## 建议动作

cs-refactor：属于结构性维护成本，适合独立于故障修复处理。
