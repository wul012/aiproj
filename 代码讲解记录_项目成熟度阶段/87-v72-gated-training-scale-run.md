# 第七十二版代码讲解：Gated Training Scale Run

## 本版目标、来源和边界

v72 的目标是把 v70 的 `training_scale_plan.json`、v71 的 training scale gate 和 v69 的 training portfolio batch runner 串成一个受控启动入口。前两版已经能“生成计划”和“判断计划”，但还缺一个真正执行链路上的协调层：只有 gate 允许时，才把 variants 交给 batch runner。

本版解决的问题是：后续跑真实更大中文语料时，不应该手动跳过 gate 去执行 batch。v72 提供 `run_training_scale_plan.py`，默认只做 dry-run；如果 gate fail 就阻止 batch；如果 gate warn 则默认允许但保留 warning 证据；如果用户希望更严格，可以用 `--no-allow-warn` 阻止 warned plan。

本版不做这些事情：

- 不下载新语料。
- 不改变 v69 `run_training_portfolio_batch.py` 的默认行为。
- 不默认执行真实训练；`--execute` 仍然需要显式传入。
- 不把结果写入 registry；本版只生成一次 gated run 的证据。

## 本版接在哪条链路后面

已有链路是：

```text
v70: text sources -> training_scale_plan.json -> training_scale_variants.json
v71: training_scale_plan.json -> training_scale_gate.*
v69: variants.json -> training_portfolio_batch.*
```

v72 把三者变成一个受控入口：

```text
training_scale_plan.json
 -> gate/training_scale_gate.*
 -> if allowed:
      training_scale_variants.json
      batch/training_portfolio_batch.*
 -> training_scale_run.*
```

`training_scale_run.*` 是本版新增的总控证据，记录 gate 是否允许、是否启动 batch、batch 输出在哪里，以及后续建议。

## 关键新增文件

### `src/minigpt/training_scale_run.py`

这是 v72 的核心模块。

关键函数：

- `run_training_scale_plan(...)`：读取 v70 plan，执行 v71 gate，写 gate outputs，判断是否允许 batch，允许时加载 variants 并调用 v69 batch plan/run/write。
- `write_training_scale_run_outputs(...)`：写出 `training_scale_run.json/csv/md/html`。
- `render_training_scale_run_markdown(...)` / `render_training_scale_run_html(...)`：把总控结果渲染为人审阅报告。

核心字段：

- `status`：本次 gated run 的总状态，可能是 `blocked`、`planned`、`planned_with_warnings`、`completed` 或 `failed`。
- `allowed`：gate 是否允许进入 batch。
- `blocked_reason`：被阻止时说明原因，例如 `gate failed` 或 `gate warned and allow_warn is false`。
- `gate`：v71 gate 摘要，包含 overall status、pass/warn/fail 数量和 profile。
- `gate_outputs`：gate JSON/CSV/Markdown/HTML 路径。
- `variants_path`：从 v70 plan 导出的 batch variants JSON。
- `batch_outputs`：v69 batch 输出路径；如果 blocked，则为空。
- `batch_summary`：batch 执行摘要，blocked 时为 `skipped`。

### `scripts/run_training_scale_plan.py`

这是命令行入口。典型用法：

```powershell
python scripts/run_training_scale_plan.py --plan runs/training-scale-plan/training_scale_plan.json --out-root runs/training-scale-run --gate-profile review
```

默认是 dry-run，只有传入 `--execute` 才执行真实训练。关键参数：

- `--gate-profile review|standard|strict`：选择 gate 策略。
- `--no-allow-warn`：warn 也阻止 batch。
- `--allow-fail`：即使 fail 也允许继续，只适合刻意的 report-only 实验。
- `--no-compare`：透传给 batch 层，跳过 portfolio comparison。

CLI 如果最终状态是 `blocked` 或 `failed`，会返回非零退出码。

### `tests/test_training_scale_run.py`

测试覆盖：

- review profile 下 tiny plan 会 warn，但默认允许 batch dry-run。
- `allow_warn=False` 时 warned plan 会被阻止，且不会写 batch 产物。
- standard profile 下 fail plan 会被阻止。
- `allow_fail=True` 可以强制交给 batch dry-run，但报告中保留 gate fail。
- HTML 渲染会显示 dataset 名并转义 `<demo>`。
- `training_scale_run.json/csv` 是机器可读产物。

这些测试保护 v70 -> v71 -> v69 的真实衔接，而不是只测单个模块内部逻辑。

### `c/72`

本版截图和解释写入：

```text
c/72/图片
c/72/解释/说明.md
```

截图覆盖单测、允许路径、阻止路径、结构检查、Playwright HTML 和文档一致性检查。

## 输入输出格式

输入是 v70 的 `training_scale_plan.json`：

```powershell
python scripts/run_training_scale_plan.py --plan runs/training-scale-plan/training_scale_plan.json --out-root runs/training-scale-run --gate-profile review
```

输出目录结构：

```text
runs/training-scale-run/
  training_scale_run.json
  training_scale_run.csv
  training_scale_run.md
  training_scale_run.html
  training_scale_variants.json
  gate/
    training_scale_gate.*
  batch/
    training_portfolio_batch.*
    variants/<name>/training_portfolio.*
    comparison/training_portfolio_comparison.*
```

如果 gate 阻止执行，则 `gate/` 和 `training_scale_run.*` 仍会写出，但 `batch/` 不会写 batch 产物。

## 为什么这是合理推进

v70 和 v71 分别是“计划”和“准入”，v72 才把它们接到真实 batch runner。这样后续继续推进到真实大语料时，可以统一走一个入口，减少手动绕过 gate 的风险。

## 测试如何保护链路

测试明确保护三条关键路径：

- allow：gate warn 但允许时，batch dry-run 真的写出。
- block：gate fail 或 warn 被禁止时，batch 不写出。
- force：用户显式 `allow_fail=True` 时，报告保留 fail 但仍能跑 dry-run。

这能防止未来改动时把 gate 变成“只展示不控制”的假门禁。

## 一句话总结

v72 把 MiniGPT 从“能计划和检查训练矩阵”推进到“能按 gate 决策受控启动 batch dry-run 或训练”的层次。
