# v181 CI workflow hygiene artifact split 代码讲解

## 本版目标

v181 的目标是把 `ci_workflow_hygiene.py` 中的 JSON、CSV、Markdown 和 HTML artifact 输出层拆到专用模块。v180 已经把 training scale workflow 的输出层拆出；本版继续沿用“最大模块优先、契约保持、低风险收束”的路线，处理当前 module pressure 里靠前的 CI workflow hygiene 模块。

本版明确不做这些事：不改变 `build_ci_workflow_hygiene_report()` 的输入参数，不改变 TypedDict report schema，不改变 `actions/checkout@v6` 与 `actions/setup-python@v6` 的策略，不改变 required command fragments，不改变 `scripts/check_ci_workflow_hygiene.py` 用法，也不改变旧代码从 `minigpt.ci_workflow_hygiene` 导入 writer/renderer 的方式。

## 前置路线

CI workflow hygiene 是 v145 引入的可运行 CI 策略门禁，v152 又补了 TypedDict schema 和 action tag 宽松解析。它后来被 project audit、release bundle、release readiness、readiness comparison、registry 和 maturity summary 消费，成为项目治理链路里“CI 配置是否健康”的证据来源。

由于这个模块同时负责 policy 检查和 JSON/CSV/Markdown/HTML 输出，随着证据链消费范围扩大，它变成了一个职责偏宽的模块。v181 的拆分把“检查 workflow 是否符合策略”和“把检查结果渲染成证据文件”分开。

## 关键文件

- `src/minigpt/ci_workflow_hygiene_artifacts.py`：新增 artifact 模块，负责 CI workflow hygiene JSON、CSV、Markdown、HTML 的渲染和写出。
- `src/minigpt/ci_workflow_hygiene.py`：保留 `build_ci_workflow_hygiene_report()`、action 收集、required checks、summary 和 recommendations。
- `tests/test_ci_workflow.py`：新增 facade identity 测试，确认旧入口导出的 HTML renderer 和 output writer 就是新 artifact 模块里的函数。
- `README.md`、`c/181/解释/说明.md`、`代码讲解记录_项目成熟度阶段/README.md`、`c/README.md`：记录 v181 的能力边界、运行证据和讲解索引。

## Artifact 模块

`ci_workflow_hygiene_artifacts.py` 承接四类输出：

- `write_ci_workflow_hygiene_json()`：写出完整 CI workflow hygiene report JSON。
- `write_ci_workflow_hygiene_csv()`：把每条 check 的 id、category、target、expected、actual、status 和 detail 写成表格。
- `render_ci_workflow_hygiene_markdown()` 和 `write_ci_workflow_hygiene_markdown()`：输出面向交接阅读的 Markdown。
- `render_ci_workflow_hygiene_html()` 和 `write_ci_workflow_hygiene_html()`：输出带 stats、checks table、actions table 和 recommendations 的 HTML。

`write_ci_workflow_hygiene_outputs()` 仍是统一出口，会一次性写出 `ci_workflow_hygiene.json`、`ci_workflow_hygiene.csv`、`ci_workflow_hygiene.md` 和 `ci_workflow_hygiene.html`。这些文件是最终证据，可被 project audit、release bundle、release readiness 和 maturity summary 消费。

## 主入口

`ci_workflow_hygiene.py` 现在聚焦五件事：

1. 读取 workflow YAML 文本。
2. 收集 `uses:` action 和版本信息。
3. 生成 action version、forbidden env、required command 和 Python version checks。
4. 组装 TypedDict summary 和 recommendations。
5. 返回 `CiWorkflowReport`，并从 artifact 模块 re-export 旧 writer/renderer 名称。

主模块仍然保留 `__all__` 里的旧导出，所以脚本和下游模块不需要修改导入路径。

## 数据结构和字段语义

CI workflow hygiene report 的关键字段保持不变：

- `policy`：required actions、forbidden env vars、required command fragments 和 required Python version。
- `summary`：status、decision、check/action 计数、required action 命中数、Node 24 native action 数、forbidden env 数、missing step 数和 Python version。
- `actions`：每个 `uses:` action 的 repository、version、raw、line 和 node24_native。
- `checks`：每个检查项的 id、category、target、expected、actual、status 和 detail。
- `recommendations`：根据失败原因生成的修复建议。

v181 不改变这些字段，只把它们如何被渲染成 JSON/CSV/Markdown/HTML 的代码移动到 artifact 模块。

## 测试覆盖

`tests.test_ci_workflow` 覆盖以下链路：

- 当前 `.github/workflows/ci.yml` 使用 Node 24 native action 版本。
- 当前 workflow 的 CI hygiene report 为 pass。
- 旧 runtime policy、旧 action major、错误 Python version 和缺失命令会进入 fail。
- `v6.0.0` 与 `6` 可以被识别为 Node 24 native major，但仍会按 required exact version 做 action version 检查。
- JSON/CSV/Markdown/HTML 输出可读且 HTML 正确 escape。
- 新增 facade identity 测试确认旧入口导出的 `render_ci_workflow_hygiene_html()` 和 `write_ci_workflow_hygiene_outputs()` 与 artifact 模块同源。

## 运行证据

v181 的运行截图归档在 `c/181`：

- `01-ci-workflow-tests.png`：CI workflow hygiene 定向测试通过。
- `02-ci-workflow-artifact-smoke.png`：旧 facade 和新 artifact 模块函数 identity 以及模块行数检查。
- `03-maintenance-smoke.png`：module pressure 为 `pass`，没有 warn/critical 模块。
- `04-source-encoding-smoke.png`：源码编码、BOM、语法和 Python 3.11 兼容检查通过。
- `05-full-unittest.png`：全量 405 个测试通过。
- `06-docs-check.png`：README、`c/181`、讲解索引、source/test 关键词对齐。

临时 `tmp_v181_*` 日志和 `runs/*v181*` 输出会在提交前按 AGENTS 清理门禁删除，`c/181` 是保留的正式证据。

## 边界说明

`ci_workflow_hygiene_artifacts.py` 不是新的策略入口，也不会重新解析 workflow。它只消费已经组装好的 CI workflow hygiene report dict，把同一份证据写成多种可读格式。策略检查仍在 `build_ci_workflow_hygiene_report()` 内完成，CLI 仍使用 `scripts/check_ci_workflow_hygiene.py`。

## 一句话总结

v181 把 CI workflow hygiene 的 artifact 输出层从策略检查里拆出来，让 CI 质量门禁主模块从 470 行降到 263 行，同时保持 report schema、CLI 和旧 facade 导入全部不变。
