# v405 eval suite design report

## 本版目标和边界

v405 的目标是把 v402 新增的 prompt-suite design summary 从 tiny standard benchmark smoke 扩展到通用 eval suite 报告层。这样只要调用 `build_eval_suite_report()`，JSON 和 HTML 报告就能同时说明“生成结果是什么”和“这套 prompt 的设计是否足够用于比较”。

本版不训练新模型，不声称模型质量提升，也不新增新的治理链。它只是把已有设计检查接入 eval suite 的常规产物，让后续标准套件、训练组合和人工复核都能复用同一份设计证据。

## 前置能力

本版承接 v402 的 `eval_suite_design.py`：

- v402 已经能读取 prompt suite 定义并输出 case 数量、任务类型、难度、标签、token budget、seed 重复和 expected behavior 完整性。
- v405 让 eval suite 实际运行后的 `PromptResult` 也能重建同样的 suite 设计输入，再生成同一套 summary。
- 因为 tiny smoke 和普通 eval suite 都用同一套设计判断，后续比较多个 checkpoint 时不需要再为不同入口解释两套口径。

## 关键文件

### `src/minigpt/eval_suite.py`

`build_eval_suite_report()` 现在在原有 `coverage` 之外计算 `design_summary`。

核心流程是：

```text
PromptResult 列表
  -> 统计 task_type / difficulty
  -> 生成 coverage summary
  -> 从 PromptResult 重建 suite cases
  -> 调用 summarize_prompt_suite_design()
  -> 写入 benchmark.design_summary 和 top-level design_summary
```

`_design_summary()` 是本版新增的内部桥接函数。它从每个 `PromptResult` 取出：

- `name`
- `prompt`
- `max_new_tokens`
- `temperature`
- `top_k`
- `seed`
- `task_type`
- `difficulty`
- `expected_behavior`
- `tags`

这些字段被组装成与 prompt suite 定义兼容的 `cases` 列表，然后交给 `summarize_prompt_suite_design()`。这样 eval suite 运行结果不需要知道设计检查的内部规则，只需要提供完整的 case 元数据。

`design_summary` 同时放在两个位置：

- `report["design_summary"]`
- `report["benchmark"]["design_summary"]`

这样老消费者可以从 top-level 读取，新消费者也可以把它看成 benchmark 元数据的一部分。

### `src/minigpt/eval_suite_artifacts.py`

HTML 渲染器新增 `Suite Design` 面板，展示：

- design coverage 状态
- design comparison 状态
- task type / difficulty / tag 数量
- token budget 范围
- duplicate seed 数量
- expected behavior 是否完整
- tags 是否完整
- design blockers
- design comparison blockers

顶部 stats 区也新增 `Design coverage` 和 `Design comparison`，让打开 HTML 的人不用翻 JSON 就能先看到这套 prompt 是否适合作为比较证据。

`_range_text()` 是一个小的显示辅助函数，只负责把最小和最大 token budget 显示成 `min / max`。它不参与判断逻辑。

### `tests/test_eval_suite.py`

测试覆盖三类边界：

- 窄套件会得到 `coverage_status=warn`，并保留 token budget 和 duplicate seed 信息。
- 内置 `standard-zh` 套件的 design coverage 和 comparison status 都是 `pass`。
- `write_eval_suite_outputs()` 写出的 HTML 包含 `Suite Design` 和 `Design comparison` 文本。

这些断言保护的是报告契约：如果后续改 eval suite 或 HTML 渲染，不能悄悄丢失 suite-design 证据。

## 输入输出

输入仍然是 eval suite 的 prompt 运行结果，不需要新增命令参数。

输出增加两个字段：

```text
eval_suite.json
  design_summary
  benchmark.design_summary

eval_suite.html
  Suite Design panel
  Design coverage / Design comparison stats
```

这些产物是只读证据，用于人工复核、后续 benchmark scorecard 或训练治理链消费；它们不是训练数据，也不是模型质量结论。

## 运行证据

运行归档在 `d/405`：

- `d/405/解释/说明.md`：说明本版改动、测试和截图含义。
- `d/405/解释/v405-eval-suite-design-report-evidence.html`：可浏览的证据页。
- `d/405/图片/01-eval-suite-design-report-evidence.png`：Playwright MCP 打开的证据页截图。

## 测试覆盖

本版先跑定向测试：

```text
python -m pytest tests\test_eval_suite.py tests\test_benchmark_scorecard.py tests\test_tiny_standard_benchmark_smoke.py -q
```

定向测试确认 eval suite、scorecard 和 tiny standard benchmark smoke 都能理解新的 design summary。

收口时再跑全量测试、源码编码检查和 `git diff --check`，确认本版没有引入语法、编码或空白错误。

## 一句话总结

v405 把 prompt 套件设计质量从 tiny smoke 的局部证据提升为通用 eval suite 报告契约，让后续 checkpoint 比较先能判断“这套题是否够用”。
