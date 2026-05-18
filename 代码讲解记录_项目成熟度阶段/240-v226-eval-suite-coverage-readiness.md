# v226 eval suite coverage readiness 代码讲解

## 本版目标

v226 的目标是给固定 prompt eval suite 增加覆盖度 readiness 证据。

前面 v198-v205 已经把 `standard-zh` suite 接入训练 portfolio、training scale、promotion 和 handoff 链路；v226 回到 eval suite 本身，补上一个更早、更底层的判断：这个 suite 到底只是“能跑”，还是已经足够代表 MiniGPT 的多任务评估边界。

## 不做什么

本版不训练模型。

本版不改变 prompt 生成、采样参数、tokenizer、checkpoint 加载或 `scripts/eval_suite.py` 的调用方式。

本版也不改变 `eval_suite.json`、`eval_suite.csv`、`eval_suite.svg`、`eval_suite.html` 的文件名，只在报告 schema 里追加向后兼容字段。

## 关键文件

### `src/minigpt/eval_suite.py`

这里新增了 coverage readiness 的核心逻辑。

新增常量包括：

```python
RECOMMENDED_TASK_TYPES
RECOMMENDED_DIFFICULTIES
COMPARISON_RECOMMENDED_DIFFICULTIES
MIN_RECOMMENDED_CASES
MIN_RECOMMENDED_TAGS
MIN_COMPARISON_CASES
MIN_COMPARISON_TASK_TYPES
MIN_COMPARISON_TAGS
```

这些常量把“代表性 suite”和“可比较 suite”的边界显式写出来：

- 代表性 suite 至少要覆盖 continuation、qa、summary、structured、factual-consistency。
- 基础难度至少要有 easy 和 medium。
- 标签数量不能太少，否则说明 prompt 维度过窄。
- 可用于 checkpoint comparison 的 suite 还需要 hard 难度、更多 case、更多 task type 和更宽 tag。

核心函数是 `_coverage_summary()`。

它读取 `PromptResult` 列表和已有的 task/difficulty 计数，输出一个 `coverage` 字典：

```text
status
comparison_status
decision
comparison_decision
case_count
task_type_count
difficulty_count
tag_count
observed_task_types
observed_difficulties
observed_tags
missing_recommended_task_types
missing_recommended_difficulties
missing_comparison_difficulties
blockers
comparison_blockers
```

其中 `status` 判断这个 suite 是否具有基础代表性；`comparison_status` 判断它是否适合支撑跨 checkpoint 的质量比较。

### `build_eval_suite_report()`

`build_eval_suite_report()` 现在会在生成 task/difficulty summary 后构建 coverage：

```python
coverage = _coverage_summary(results, task_type_counts, difficulty_counts)
```

然后同时写到两个位置：

```text
report["coverage"]
report["benchmark"]["coverage"]
```

这样做是为了兼容两类消费者：

- 直接读取顶层 report 的脚本。
- 已经把 benchmark 元数据当成入口的后续报告模块。

### `src/minigpt/eval_suite_artifacts.py`

HTML 报告新增 Coverage 和 Comparison 两个统计卡片，并新增 `Coverage Readiness` 面板。

面板展示：

- 基础 readiness 状态。
- checkpoint comparison 状态。
- 决策字符串。
- 覆盖到的 task、difficulty、tag 数。
- 缺失的推荐任务、推荐难度和比较难度。
- 基础 blockers 和 comparison blockers。

这部分是最终可视证据，不参与模型推理，但会被截图和 README 引用。

### `tests/test_eval_suite.py`

测试新增两层保护。

第一层是小型 demo suite：

```text
qa + summary，2 个 case
```

它可以生成报告，但 coverage 必须是 `warn`，comparison 也必须是 `warn`。这个断言保护的是“不要把小样本评估误认为模型质量证据”。

第二层是 `builtin:standard-zh`：

```text
10 个 case
10 种 task_type
easy / medium / hard
21 个 tag
```

它必须得到：

```text
coverage.status = pass
coverage.comparison_status = pass
```

这个断言保护的是 v198 以来推荐的标准中文 benchmark 确实能作为重复 checkpoint 比较的默认套件。

## 输入输出

输入仍然是 eval suite 的 `PromptResult` 列表。

输出新增一个向后兼容字段：

```json
{
  "coverage": {
    "status": "pass",
    "comparison_status": "pass",
    "decision": "suite_has_representative_prompt_coverage",
    "comparison_decision": "suite_ready_for_repeated_checkpoint_comparison"
  }
}
```

旧消费者如果只读 `results`、`task_type_counts`、`difficulty_counts` 不受影响。

新消费者可以直接读 `coverage.comparison_status`，判断某个 eval run 是否适合放进严肃的模型质量对比。

## 运行证据

本版运行证据归档在 `c/226`：

- `图片/01-eval-suite-coverage-readiness.png`

截图来自 `builtin:standard-zh` 的 eval suite HTML 报告，证明页面上已经展示 Coverage Readiness，并且标准中文 suite 的 coverage/comparison 都是 `pass`。

Playwright CLI wrapper 在当前 Windows 会话里因为 bash/WSL 入口不可用而无法直接执行；本版改用同一 Playwright 浏览器能力打开临时本地 HTTP 服务截图。临时 HTTP 服务已在截图后停止。

## 测试覆盖

本版会运行：

```text
python -B -m unittest tests.test_eval_suite -q
python -B -m unittest discover -s tests -q
python -B scripts/check_source_encoding.py
```

重点断言包括：

- 小型临时 suite 生成 `warn`，避免误报为强 benchmark。
- `builtin:standard-zh` 生成 `pass/pass`，证明标准 suite 能支撑重复 checkpoint comparison。
- HTML 输出包含 `Coverage Readiness`。
- 全量测试确认新增 coverage 字段不破坏训练、scorecard、release gate、portfolio、server 和文档链路。

## 证据链角色

v226 不直接提升模型能力，但提升了模型能力证据的可信度。

它把 eval suite 的适用边界写入机器可读报告，使后续 training portfolio、benchmark scorecard、promotion decision 和 maturity summary 在读取 eval artifact 时，可以区分：

```text
可运行评估
代表性评估
适合 checkpoint 对比的评估
```

这比继续堆 report helper 更有价值，因为它约束的是“模型质量说法”的入口。

## 一句话总结

v226 让 MiniGPT 的固定 prompt benchmark 带上覆盖度和可比较性 verdict，为后续真实 checkpoint 质量对比补上更清楚的评估边界。
