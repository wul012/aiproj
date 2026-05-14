# 第七十三版代码讲解：Training Scale Run Comparison

## 本版目标、来源和边界

v73 的目标是比较多次 v72 `training_scale_run.json`，解释哪些 gated scale run 被 gate 放行、哪些被阻止、哪些只是 warning，以及哪些真正进入了 batch dry-run。v72 解决的是单次受控启动，v73 解决的是多次受控启动之间怎么横向审阅。

它解决的问题是：当同一份 scale plan 用 `review`、`standard`、`strict` profile 跑出不同结果时，不能只打开多个 HTML 手工看。项目需要一个专门的 comparison 产物，总结 allowed/blocked、gate pass/warn/fail、batch started/skipped、readiness score delta 和建议。

本版不做这些事情：

- 不替代 run registry；registry 面向训练实验目录，v73 只比较 gated scale run 总控产物。
- 不重新执行 gate 或 batch；它只读取已有 `training_scale_run.json`。
- 不评价模型能力；它评价训练启动计划是否健康、是否进入 batch 层。
- 不改 v72 runner 的行为。

## 本版接在哪条链路后面

已有链路：

```text
v70: training_scale_plan.json
v71: training_scale_gate.*
v72: training_scale_run.json
```

v73 新增：

```text
training_scale_run.json x N
 -> training_scale_run_comparison.json/csv/md/html
```

这让 profile 对比、准入差异和 batch handoff 差异可以用同一份报告审阅。

## 关键新增文件

### `src/minigpt/training_scale_run_comparison.py`

这是 v73 的核心模块。

关键函数：

- `load_training_scale_run(path)`：读取 `training_scale_run.json`，也支持传入 run 目录。
- `build_training_scale_run_comparison(...)`：汇总多份 run，选择 baseline，计算 delta 和 summary。
- `write_training_scale_run_comparison_outputs(...)`：写出 JSON、CSV、Markdown、HTML。
- `render_training_scale_run_comparison_markdown(...)` / `render_training_scale_run_comparison_html(...)`：渲染审阅报告。

核心字段：

- `runs`：每个 run 的摘要，包含 `status`、`allowed`、`gate_status`、`gate_profile`、`scale_tier`、`variant_count`、`batch_status`、`comparison_status` 和 `readiness_score`。
- `baseline`：用于比较的基线 run，默认第一份，也可按名称或序号指定。
- `baseline_deltas`：相对 baseline 的 `allowed_delta`、`readiness_delta`、`gate_relation`、`batch_relation` 和解释。
- `summary`：allowed/blocked、batch started/skipped、gate pass/warn/fail、readiness improvement/regression 计数。
- `best_by_readiness`：当前 readiness score 最高的 run。
- `recommendations`：针对 blocked、gate fail、gate warn 或 readiness regression 的后续建议。

`readiness_score` 是本版的轻量排序指标：allowed、gate status、batch status、comparison status 和 execute 状态共同影响分数。它不是模型能力分数，只用于比较训练启动链路是否更健康。

### `scripts/compare_training_scale_runs.py`

这是命令行入口。典型用法：

```powershell
python scripts/compare_training_scale_runs.py runs/scale-run-review/training_scale_run.json runs/scale-run-standard/training_scale_run.json --name review --name standard --baseline review --out-dir runs/training-scale-run-comparison
```

CLI 输出 run 数量、baseline、summary、best_by_readiness 和输出路径。

### `tests/test_training_scale_run_comparison.py`

测试覆盖：

- 比较 allowed run 和 blocked run 时，summary 能正确记录 allowed/blocked、batch started、gate fail。
- 支持传入 run 目录，而不只是 JSON 文件。
- blocked 作为 baseline 时，allowed run 的 readiness delta 是正数。
- HTML 能正确转义 `<allowed>`。
- 空输入和重复名称会失败。

这些测试保护 v72 产物进入 v73 comparison 的边界。

### `c/73`

本版截图和解释写入：

```text
c/73/图片
c/73/解释/说明.md
```

截图覆盖单测、默认 baseline comparison、blocked baseline comparison、结构检查、Playwright HTML 和文档检查。

## 输入输出格式

输入是一组 v72 run：

```powershell
python scripts/compare_training_scale_runs.py run-a/training_scale_run.json run-b/training_scale_run.json --name review --name standard --baseline review --out-dir runs/training-scale-run-comparison
```

输出：

- `training_scale_run_comparison.json`：机器可读比较报告。
- `training_scale_run_comparison.csv`：每个 run 一行，包含 readiness delta、gate relation、batch relation。
- `training_scale_run_comparison.md`：人审阅 Markdown。
- `training_scale_run_comparison.html`：浏览器报告。

## 为什么这是合理推进

v70-v72 已经形成“计划 -> gate -> 受控 batch”的单次链路。v73 把它从单次审阅推进到多次审阅，尤其适合比较 review/standard/strict profile 在同一语料上的不同结果。它不是泛化的大 registry，而是针对 scale run 这一条新链路做窄而实用的比较层。

## 测试如何保护链路

测试会先真实生成 v70 plan，再用 v72 生成 allowed 和 blocked 两类 run，最后交给 v73 comparison。这样覆盖的是实际产物链路，而不是手写假 JSON。

重点保护：

- allowed/blocked 计数不能错。
- batch started/skipped 判断不能错。
- readiness delta 的方向不能反。
- 目录输入和 JSON 文件输入都能工作。
- HTML 不会被 run name 注入。

## 一句话总结

v73 把 MiniGPT 从“能受控启动单次训练规模计划”推进到“能比较多次受控启动的 gate 与 batch 差异”。
