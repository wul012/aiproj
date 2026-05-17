# v179 maturity narrative summary section split 代码讲解

## 本版目标

v179 的目标是把 `maturity_narrative.py` 中的 summary 计算、recommendations/warnings 判断、human-readable sections 和 evidence matrix 构造拆到专用模块。v178 已经把 server POST route 从 HTTP handler 中抽出；本版继续沿用“最大模块优先、低风险、契约保持”的节奏，处理当前 module pressure 报告中的最大模块 `maturity_narrative.py`。

本版明确不做这些事：不改变 `build_maturity_narrative()` 的参数，不改变 narrative JSON schema，不改变 `recommendations` 和 `warnings` 的判断语义，不改变 Markdown/HTML artifact writers，不改变 `scripts/build_maturity_narrative.py` 用法，也不改变旧的 `minigpt.maturity_narrative` 导入入口。

## 前置路线

maturity narrative 是 v66 引入的 portfolio-facing review surface，后来 v134 把 JSON/Markdown/HTML artifact writer 拆到 `maturity_narrative_artifacts.py`，v141 又把 benchmark scorecard decision 纳入 maturity narrative。经过这些版本后，`maturity_narrative.py` 已经不再只是读几个输入并组装输出，还承担了 portfolio status、benchmark scorecard 汇总、scorecard decision 汇总、dataset card 汇总、release/request claim、section 文案和 evidence matrix 构造。

v179 的拆分方向是把它分成三层：

- `maturity_narrative.py`：输入发现、JSON 读取、组装 narrative。
- `maturity_narrative_summary.py`：机器可读 summary、recommendations、warnings。
- `maturity_narrative_sections.py`：面向人的 sections、claim 文案和 evidence matrix。

## 关键文件

- `src/minigpt/maturity_narrative_summary.py`：新增 summary helper 模块，接收 maturity、registry、request history、scorecards、scorecard decisions 和 dataset cards，输出 portfolio summary、recommendations 和 warnings。
- `src/minigpt/maturity_narrative_sections.py`：新增 section/evidence helper 模块，接收 summary 和输入路径，输出 human-readable sections 与 evidence matrix。
- `src/minigpt/maturity_narrative.py`：保留 `build_maturity_narrative()` 入口和 artifact writer re-export，只负责读取输入、调用 helper、组装最终 narrative dict。
- `tests/test_maturity_narrative.py`：新增 split helper identity 和直接 helper behavior 断言，原有 ready/review/incomplete、artifact output、HTML escape 测试继续保留。

## Summary 模块

`build_maturity_narrative_summary()` 负责把多个上游证据压缩成一个统一 summary。它读取：

- maturity summary：当前版本、overall status、average maturity level、release readiness context。
- registry：run count。
- request history summary：local inference request status、records 和 timeout rate。
- benchmark scorecards：overall status、score、rubric weakest case。
- benchmark scorecard decisions：decision status、selected run、review items、blockers 和 generation-quality flag delta。
- dataset cards：quality status、warning count 和 fingerprint。

`portfolio_status` 仍保持旧语义：缺 maturity/benchmark/dataset 或缺 release/request context 时为 `incomplete`；maturity warn/fail、release regression、request warn/fail、benchmark warn/fail 或 dataset warn/fail 时为 `review`；其他完整且健康的证据为 `ready`。

`build_maturity_narrative_recommendations()` 和 `build_maturity_narrative_warnings()` 也放在 summary 模块里，因为它们消费的是机器可读状态，而不是 HTML/Markdown 渲染细节。

## Sections 模块

`build_maturity_narrative_sections()` 负责构造面向人的七个 narrative sections：

- Project Maturity
- Release Quality Trend
- Local Serving Stability
- Benchmark Quality
- Benchmark Promotion Decision
- Data Governance
- Portfolio Boundary

每个 section 都保留 `key`、`title`、`status`、`claim`、`evidence`、`boundary` 和 `next_step` 字段。这里的重点是把“给人看的解释文本”和“机器可读 summary 计算”分开。后续如果要调整文案、增加 section 或改变 evidence note，不需要回到主入口里翻计算逻辑。

`build_maturity_narrative_evidence_matrix()` 负责把 maturity、registry、request history、benchmark scorecards、scorecard decisions 和 dataset cards 的路径映射成 evidence rows。它只记录 path、exists、signal 和 section claim，不读取文件内容。

## 主入口

`build_maturity_narrative()` 现在只做五件事：

1. 解析 project root 和可选输入路径。
2. 发现默认 scorecard、scorecard decision 和 dataset card 文件。
3. 用 `_read_json()` 读取 JSON 输入。
4. 调用 summary、sections、evidence helper 生成 narrative 部件。
5. 返回原有 narrative dict。

这让主模块从 488 行降到 109 行。主入口仍然保留 artifact writer 导入和 re-export，所以旧代码可以继续从 `minigpt.maturity_narrative` 里导入 `render_maturity_narrative_html()` 或 `write_maturity_narrative_outputs()`。

## 测试覆盖

v179 的测试覆盖四层：

- `tests.test_maturity_narrative`：覆盖 ready portfolio、release regression review、missing request history incomplete、artifact outputs、HTML escape 和新 helper identity。
- full unittest discovery：确认 summary/section helper 拆分没有破坏 dashboard、server、release、registry、training-scale 和 benchmark 链路。
- source encoding hygiene：确认新增模块没有 BOM、语法错误或 Python 3.11 兼容问题。
- maintenance batching：确认 module pressure 继续为 `pass`，并且最大模块已经从 maturity narrative 转移到 `training_scale_workflow.py`。

新增测试里的 direct helper 调用不是新业务入口，而是为了保护两件事：主入口确实消费新 helper；helper 单独也能从最小证据生成 ready summary 和 Benchmark Promotion Decision section。

## 运行证据

v179 的运行截图归档在 `c/179`：

- `01-maturity-narrative-tests.png`：maturity narrative 定向测试通过。
- `02-maturity-narrative-split-smoke.png`：主模块和两个 helper 模块的行数、入口 identity 和 helper 使用关系。
- `03-maintenance-smoke.png`：module pressure 为 `pass`。
- `04-source-encoding-smoke.png`：编码、语法和 Python 3.11 兼容检查通过。
- `05-full-unittest.png`：全量 403 个测试通过。
- `06-docs-check.png`：README、`c/179`、讲解索引和 source/test 关键词对齐。

临时 `tmp_v179_*` 日志和 `runs/*v179*` 输出会在提交前按 AGENTS 清理门禁删除，`c/179` 是保留的正式证据。

## 边界说明

`maturity_narrative_summary.py` 和 `maturity_narrative_sections.py` 不是新的报告格式，也不是新的 artifact writer。JSON/Markdown/HTML 输出仍由 `maturity_narrative_artifacts.py` 负责，CLI 仍调用 `build_maturity_narrative()`，外部消费者仍看到同一个 narrative dict。新模块只是把计算和叙事构造边界分开。

## 一句话总结

v179 把 maturity narrative 的 portfolio summary/recommendation/warning 计算与 human-readable section/evidence matrix 构造拆成两个专用模块，让成熟度叙事主入口从 488 行降到 109 行，同时保持 narrative schema、artifact writers、CLI 和旧导入契约不变。
