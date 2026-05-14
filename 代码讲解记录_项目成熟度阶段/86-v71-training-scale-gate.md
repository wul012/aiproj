# 第七十一版代码讲解：Training Scale Gate

## 本版目标、来源和边界

v71 的目标是在 v70 `training_scale_plan.json` 和 v69 batch runner 之间加一层执行前准入检查。v70 已经能扫描语料规模并生成 batch-compatible variants，但“能生成矩阵”不等于“应该执行矩阵”。v71 负责读取这份 plan，按照 `review`、`standard`、`strict` 三种 profile 输出 pass/warn/fail gate 证据。

它解决的问题是：tiny 语料、质量 warning、baseline 缺失、variant 数量异常、token budget 过高、语料重复训练轮次过高时，项目应该先给出明确判断，而不是直接进入 batch 训练。

本版不做这些事情：

- 不重新扫描原始语料；原始语料扫描仍由 v70 完成。
- 不执行训练；真正执行仍由 v69 `run_training_portfolio_batch.py` 负责。
- 不替代 release gate；它只检查 training scale plan 是否适合进入训练 batch。
- 不把 gate 结果写入 registry；后续如果要做跨 run 索引，可以再接入 registry 或 maturity summary。

## 本版接在哪条链路后面

v70 形成训练前规划：

```text
text sources -> training_scale_plan.json -> training_scale_variants.json
```

v69 负责执行或 dry-run 多组 portfolio：

```text
training_scale_variants.json -> run_training_portfolio_batch.py -> training_portfolio_batch.*
```

v71 放在两者之间：

```text
training_scale_plan.json
 -> training_scale_gate.json/csv/md/html
 -> pass/warn/fail
 -> 决定是否继续执行 batch
```

这让“更大语料训练”多了一道工程上的刹车：先看计划是否健康，再决定是否开跑。

## 关键新增文件

### `src/minigpt/training_scale_gate.py`

这是 v71 的核心模块。

关键函数：

- `load_training_scale_plan(path)`：读取 v70 生成的 `training_scale_plan.json`。
- `build_training_scale_gate(plan, profile=...)`：根据选定 profile 生成 gate 报告。
- `write_training_scale_gate_outputs(...)`：写出 JSON、CSV、Markdown 和 HTML。
- `render_training_scale_gate_markdown(...)` / `render_training_scale_gate_html(...)`：渲染人审阅报告。

核心字段：

- `profile`：当前策略，取值为 `review`、`standard` 或 `strict`。
- `policy`：profile 展开后的阈值，例如 `min_char_count`、`max_warning_count`、`max_token_budget`、`max_corpus_pass_estimate`。
- `plan_summary`：从 v70 plan 抽取的数据集名、版本前缀、scale tier、字符数、source 数、warning 数、variant 数和 baseline。
- `checks`：逐项检查结果，每项包含 `code`、`status`、`message`、`recommendation` 和 `details`。
- `overall_status`：只要有 fail 就是 `fail`；没有 fail 但有 warn 就是 `warn`；全部通过才是 `pass`。
- `batch`：原样保留 v70 plan 中的 batch handoff 信息，方便 gate 通过后继续执行。

当前检查项包括：

- `plan_schema`：plan 是否有支持的 schema 和 dataset block。
- `source_count`：是否至少有一个 source。
- `dataset_fingerprint`：是否存在 fingerprint。
- `min_char_count`：字符数是否达到 profile 阈值。
- `tiny_corpus`：tiny 语料在不同 profile 下是 warn 还是 fail。
- `quality_warnings`：质量 warning 是否超过阈值。
- `variant_count`：variant 数量是否落在允许范围。
- `baseline_variant`：baseline 是否存在于 variant names 中。
- `batch_handoff`：是否有 variants path 和 batch command。
- `variant_dataset_versions`：每个 variant 是否有 dataset version。
- `token_budget`：最大 token budget 是否超过阈值。
- `corpus_pass_estimate`：最大语料重复训练轮次是否超过阈值。

### `scripts/check_training_scale_gate.py`

这是命令行入口。典型用法：

```powershell
python scripts/check_training_scale_gate.py --plan runs/training-scale-plan/training_scale_plan.json --out-dir runs/training-scale-gate --profile review
```

CLI 输出 `status`、`profile`、`pass_count`、`warn_count`、`fail_count`、`plan_summary` 和输出文件路径。默认情况下，只要 selected profile 产生 `fail`，命令退出码就是 1；如果只是想生成报告，可以加 `--no-fail`。

### `tests/test_training_scale_gate.py`

测试覆盖 v71 的关键风险：

- `review` profile 对 tiny plan 给出 warn，但不 fail。
- `standard` profile 对 tiny 或 warning plan 给出 fail。
- gate 能读取 v70 写出的 JSON，并写出 gate JSON/CSV/HTML。
- baseline 指向不存在的 variant 时会 fail。
- token budget 超过阈值时会 fail。
- Markdown/HTML 报告包含 checks，且 HTML 会转义 `<demo>`。
- 未知 profile 会快速报错。

这些测试直接保护 v70 -> v71 -> v69 的边界：v70 产物可读，v71 能决策，v69 batch command 仍保留在报告中。

### `c/71`

本版截图和解释写入：

```text
c/71/图片
c/71/解释/说明.md
```

截图包含单测、review smoke、standard smoke、结构检查、Playwright HTML 截图和文档检查。

## 输入输出格式

输入是 v70 的 `training_scale_plan.json`：

```powershell
python scripts/check_training_scale_gate.py --plan runs/training-scale-plan/training_scale_plan.json --profile review
```

输出目录默认是：

```text
runs/training-scale-gate
```

关键输出：

- `training_scale_gate.json`：完整机器可读 gate 报告。
- `training_scale_gate.csv`：每个 check 一行，适合 CI 或表格审阅。
- `training_scale_gate.md`：人审阅说明。
- `training_scale_gate.html`：浏览器报告。

`training_scale_gate.json` 是执行前证据，不是训练结果证据。它回答“这份计划是否适合执行”；真正训练效果仍要看 v69 batch 和 v67 portfolio 输出。

## 为什么这是合理推进

v70 已经把训练前计划生成出来，但缺少“是否允许继续”的判断。v71 不是继续做展示层，而是给训练链路加准入控制。这样后续跑真实更大中文语料时，可以先用 gate 审查计划，避免把 tiny 语料或异常 budget 当成模型能力实验。

## 测试如何保护链路

测试重点不是覆盖所有阈值组合，而是保护最容易出错的边界：

- profile 策略是否真的改变 warn/fail 结果。
- v70 写出的 plan JSON 是否能被 v71 读取。
- gate 输出是否完整可审阅。
- baseline 和 budget 这类执行前高风险字段是否会被拦住。
- HTML 报告是否安全转义。

如果这些测试失败，说明训练 batch 前置准入失效，项目可能会把不合格计划交给后续训练链路。

## 一句话总结

v71 把 MiniGPT 从“能根据语料规模生成训练矩阵”推进到“能在执行训练矩阵前做准入检查并给出 pass/warn/fail 证据”。
