---
doc_type: audit-finding
audit: 2026-09-28-project-wide
finding_id: "security-01"
nature: security
severity: P1
confidence: medium
suggested_action: cs-issue
status: fixed
---

# Finding 01：认证请求跨主机重定向透传 Token

## 速答

向 ai.6551.io 发送的认证请求使用默认重定向处理；若上游返回跨主机 301、302 或 303，Bearer Token 会随重定向请求发往新主机。

## 关键证据

- server.py:74–76 — URL 以 https://ai.6551.io/ 开头时，代码将 OPENNEWS_TOKEN 放入 Authorization 请求头。
- server.py:79–81 — 请求交由 urllib.request.urlopen 执行，没有限制重定向目标，也没有在跨主机时移除认证头。
- 本地探针用占位 Token 调用 Python 的 HTTPRedirectHandler.redirect_request：301、302、303 指向 https://redirect.example/collect 时，返回请求的 Authorization 均为 Bearer audit-placeholder；307、308 对此 POST 请求被拒绝。未调用真实服务。

## 影响

触发前提是认证上游返回跨主机重定向，例如服务端配置错误、开放重定向或上游被控制。出现时，凭证会泄露给重定向目标；正常 JSON 响应不会触发该路径。

## 修复方向

认证请求禁用跨主机重定向，或在跟随前核对目标主机并剥离 Authorization；为该边界增加本地回归测试。

## 建议动作

cs-issue：属于可定位的凭证边界缺陷，先修复再复测。

## 修复记录

- 认证请求改用专用 opener：跨主机 301/302/303 抛 HTTPError 阻断；同主机重定向保留 Authorization 正常跟随；公开来源仍用默认处理（server.py CrossHostRedirectBlocked / _OPENERS）。
- 回归测试：test_server.py RedirectSecurityTests 5 项（跨主机阻断、同主机保留凭证、307/308 仍被拒、plain/auth opener 绑定、request() 走认证 opener 并携带 Bearer）。
