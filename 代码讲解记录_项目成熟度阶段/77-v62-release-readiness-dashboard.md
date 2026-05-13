# 第六十二版代码讲解：release readiness dashboard

## 本版目标、来源和边界

v61 已经让 request history summary 进入 project audit、release bundle 和 release gate policy。到这里，发布治理链路已经比较完整，但审阅时仍然需要分别打开 registry、audit、bundle、gate、request history summary、maturity summary 多份报告。v62 的目标是新增一个总览层：把这些证据读取进来，汇总成一份 release readiness dashboard。

本版解决的问题是“证据散落”。它不改变 release gate 的判定规则，不重新计算 audit score，也不修改已有 release bundle 结构。它只做聚合和解释：告诉使用者这个 release 当前是 `ready`、`review`、`blocked` 还是 `incomplete`，并列出每个 panel 的状态和需要处理的 action。

## 路线位置

v62 接在两条路线之后：

- v25-v34 的发布治理路线：project audit、release bundle、release gate、policy profile。
- v57-v61 的本地推理请求历史路线：request history view、filters、detail JSON、summary、audit gate。

前面版本已经能生成证据，v62 把证据放到同一个 review surface 里。这个动作不是继续拆小功能，而是对现有治理链路做一次收口。

## 关键文件

- `src/minigpt/release_readiness.py`：核心模块，负责读取输入、构建 summary、panels、actions、evidence，并导出 JSON/Markdown/HTML。
- `scripts/build_release_readiness.py`：命令行入口，默认读取 `runs/release-bundle/release_bundle.json`，输出到 `runs/release-readiness`。
- `tests/test_release_readiness.py`：新增单元测试，覆盖 ready、incomplete、blocked 和 HTML escaping。
- `README.md`：记录 v62 能力、tag、截图清单、学习地图和下一步方向。
- `b/62/解释/说明.md` 与 `b/62/图片/`：运行证据归档。

## 核心输入

dashboard 的主输入是 release bundle：

```text
runs/release-bundle/release_bundle.json
```

release bundle 是主入口，因为它已经记录 registry、model card、audit、request history summary 等 evidence path。v62 也会自动寻找：

```text
runs/release-gate/gate_report.json
runs/audit/project_audit.json
runs/request-history-summary/request_history_summary.json
runs/maturity-summary/maturity_summary.json
```

CLI 仍然允许显式传参：

```text
--gate
--audit
--request-history-summary
--maturity
```

显式参数用于 smoke、CI 或临时目录；默认路径用于常规项目运行。

## 核心数据结构

dashboard 输出的 JSON 有五个主要部分。

第一是 `summary`：

```json
{
  "readiness_status": "ready",
  "decision": "ship",
  "release_status": "release-ready",
  "gate_status": "pass",
  "audit_status": "pass",
  "request_history_status": "pass",
  "maturity_status": "pass"
}
```

`readiness_status` 是 v62 的总览判断。它不替代 gate，而是读取各 panel 后做一个可读摘要：有 fail panel 就是 `blocked`，缺 gate 是 `incomplete`，有 warn panel 是 `review`，全部 pass 才是 `ready`。

第二是 `panels`：

```json
{
  "key": "release_gate",
  "title": "Release Gate",
  "status": "pass",
  "detail": "gate=pass; decision=approved; checks=12 pass/0 warn/0 fail",
  "source_path": "runs/release-gate/gate_report.json"
}
```

panel 是 dashboard 的核心显示单元。它把每份证据变成同一种结构，便于 Markdown/HTML 统一展示。

第三是 `actions`。它来自失败或警告 panel、gate failed/warned checks、audit recommendations 和 bundle recommendations。这样 dashboard 不只展示状态，也告诉下一步应该修什么。

第四是 `evidence`。它复用 release bundle 的 artifact 列表，说明哪些 JSON/Markdown/HTML/SVG 证据存在，哪些缺失。

第五是 `warnings`。它记录读取可选 JSON 时出现的问题，例如 maturity summary 不存在、gate report 不是合法 JSON 等。

## readiness 判定逻辑

v62 的判定逻辑很克制：

```text
没有 gate report -> incomplete
任意 panel 为 fail -> blocked
任意 panel 为 warn -> review
全部 panel pass -> ready
```

这个逻辑有意不重新发明 release policy。真正的发布门禁仍然是 release gate；dashboard 只是把 gate 和其它上下文放在一起。

## 输出格式

`write_release_readiness_outputs` 会生成：

```text
release_readiness.json
release_readiness.md
release_readiness.html
```

JSON 是机器可读证据；Markdown 适合提交记录、报告和代码讲解引用；HTML 是浏览器审阅面板，也是 Playwright 截图的对象。

## 测试覆盖

`test_build_release_readiness_dashboard_ready` 构造完整证据链，确认 dashboard 输出 `ready`、`ship`，并且所有 panel 都是 pass。

`test_build_release_readiness_dashboard_incomplete_without_gate` 删除 gate report，确认 dashboard 不会假装 ready，而是进入 `incomplete`。

`test_build_release_readiness_dashboard_blocks_failed_gate` 构造 failed gate，确认 dashboard 总览为 `blocked`，action 能指出 `request_history_summary_audit_check`。

`test_write_release_readiness_outputs_and_escape_html` 确认 JSON/Markdown/HTML 都能写出，并且 HTML 对标题里的特殊字符做了转义。

## 与截图和归档的关系

`b/62/图片/02-release-readiness-ready-smoke.png` 证明完整证据链能汇总为 ready。`03-release-readiness-blocked-smoke.png` 证明 request history gate 缺失时能被 dashboard 捕获。`05-playwright-release-readiness-html.png` 证明 HTML 不是只写文件，而是能被真实 Chrome 打开审阅。

## 一句话总结

v62 把分散的发布治理证据收束成一个 release readiness dashboard，让 MiniGPT 的发布状态从“多份报告分开看”推进到“一份总览直接判断”。
