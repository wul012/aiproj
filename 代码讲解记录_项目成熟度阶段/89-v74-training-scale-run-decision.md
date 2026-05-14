# v74 training scale run decision 代码讲解

## 本版目标

v74 的目标是读取 v73 `training_scale_run_comparison.json`，从多次 gated scale run 中选择一个最适合进入真实 `--execute` 阶段的候选，并把被拒绝的 run、拒绝原因、决策状态和下一步执行命令写成证据。

它解决的问题是：v73 已经能比较 review、standard、strict 等 profile 下的运行差异，但人还需要自己判断“下一步到底该跑哪一个”。v74 把这个判断收口成一个可复查的 decision artifact。

本版明确不做：

- 不直接执行训练；只生成建议和命令。
- 不绕过 v71 gate 或 v72 gated runner。
- 不替代 v73 comparison；它消费 comparison，而不是重新比较原始 run。
- 不把 warn 当作生产级通过；默认只给 `review_warnings_then_execute` 状态，提醒先审阅 warning。

## 前置链路

v70-v73 已经形成一条训练规模治理链：

```text
v70 training_scale_plan
 -> v71 training_scale_gate
 -> v72 training_scale_run
 -> v73 training_scale_run_comparison
 -> v74 training_scale_run_decision
```

v74 站在这条链路最后一层。它只在已有 run comparison 足够清楚时，帮用户把“比较结果”转换成“下一步动作”。

## 关键新增文件

```text
src/minigpt/training_scale_run_decision.py
scripts/decide_training_scale_run.py
tests/test_training_scale_run_decision.py
c/74/图片
c/74/解释/说明.md
```

README、`c/README.md` 和本目录 README 也同步更新，用来证明 v74 已经进入项目结构、运行归档和代码讲解索引。

## 核心模块

### `load_training_scale_run_comparison`

这个函数读取 v73 comparison。输入可以是：

```text
runs/training-scale-run-comparison/training_scale_run_comparison.json
runs/training-scale-run-comparison/
```

如果传入目录，会自动寻找 `training_scale_run_comparison.json`。读取后会附加 `_source_path`，后续用它定位 comparison 所在目录，并尝试解析原始 `training_scale_run.json`。

### `build_training_scale_run_decision`

这是 v74 的核心函数。主要输入字段：

- `comparison_path`：v73 comparison JSON 或目录。
- `min_readiness`：最低 readiness 分数，默认 60。
- `require_gate_pass`：是否只接受 gate pass，默认 false。
- `require_batch_started`：是否要求候选进入 batch dry-run 层，默认 true。
- `execute_out_root`：生成执行命令时使用的输出目录。
- `python_executable`：命令里的 Python 可执行路径。

输出核心字段：

- `decision_status`：`ready`、`review` 或 `blocked`。
- `recommended_action`：下一步建议动作。
- `selected_run`：被选中的 comparison run。
- `selected_delta`：该 run 相对 baseline 的 delta。
- `selected_origin`：从原始 run 中读取的 `plan_path`、`project_root`、`out_root`、`allow_warn` 等上下文。
- `execute_command`：列表形式的下一步执行命令。
- `execute_command_text`：适合复制审阅的命令文本。
- `rejected_runs`：被拒绝候选及原因。
- `summary`：候选数量、拒绝数量、最终状态和选中 run 摘要。

## 决策规则

v74 不是简单选最高分，而是先做资格过滤：

```text
1. gate 必须允许该 run。
2. gate 不能是 fail。
3. 默认允许 warn，但如果传入 --require-gate-pass，则 warn 也会被拒绝。
4. 默认要求 batch dry-run 已经启动，避免从未进入 batch 的 run 被误选。
5. readiness_score 必须达到 min_readiness。
```

过滤后，`_select_candidate` 按以下顺序挑选：

```text
readiness_score
gate_status 顺序 fail < warn < pass
batch_status 顺序 skipped < failed < planned < completed
warning_count 更少优先
gate_warn_count 更少优先
```

这样可以避免只看单一分数。一个分数略高但 gate 更差的 run，不会轻易压过更稳的候选。

## 执行命令生成

v74 会尝试从 `selected_run.source_path` 找到原始 `training_scale_run.json`，再读取其中的：

- `plan_path`
- `project_root`
- `gate_profile`
- `compare`
- `allow_warn`
- `allow_fail`

然后生成：

```powershell
python scripts/run_training_scale_plan.py --plan <plan> --project-root <root> --out-root <out>-execute --gate-profile <profile> --execute
```

这个命令只是证据，不会自动执行。它的意义是把“下一步应该跑什么”明确写进报告，避免手工拼命令时选错 plan、profile 或 out_root。

## CLI

`scripts/decide_training_scale_run.py` 是命令行入口：

```powershell
python scripts/decide_training_scale_run.py runs/training-scale-run-comparison/training_scale_run_comparison.json --out-dir runs/training-scale-run-decision
```

常用控制：

- `--min-readiness`：提高或降低 readiness 门槛。
- `--require-gate-pass`：只有 gate pass 才能进入候选。
- `--no-require-batch-started`：允许未进入 batch dry-run 的 run 参与候选。
- `--execute-out-root`：指定下一步 execute 命令输出目录。

如果最终 `decision_status=blocked`，CLI 会返回非零退出码。这让它可以接入后续自动化流程：没有可执行候选时，流程应该停止。

## 输出产物

v74 写出四类文件：

```text
training_scale_run_decision.json
training_scale_run_decision.csv
training_scale_run_decision.md
training_scale_run_decision.html
```

JSON 是后续模块消费的主证据；CSV 适合快速索引；Markdown 适合代码审阅；HTML 适合用浏览器看决策面板和 rejected runs。它们都是最终证据，不是临时日志。

## 测试覆盖

`tests/test_training_scale_run_decision.py` 不只手写一个 comparison fixture，而是实际串起：

```text
build_training_scale_plan
run_training_scale_plan(review)
run_training_scale_plan(standard)
build_training_scale_run_comparison
build_training_scale_run_decision
```

关键断言包括：

- 默认模式会选择 review/warn 且 batch dry-run 已启动的 run。
- `--require-gate-pass` 会阻断 warn-only 候选。
- 提高 `min_readiness` 会阻断低分候选。
- HTML 会转义危险字符，避免 run name 里的 `<allowed>` 被当作标签。
- 空 comparison 会抛出 `ValueError`。

这些测试保护的是 v74 的真实链路：v70-v73 的产物字段如果变化，v74 会及时暴露不兼容。

## 运行归档

`c/74` 保存本版运行截图和解释：

```text
c/74/图片
c/74/解释/说明.md
```

截图中包含 focused tests、全量 tests、compileall、默认 decision smoke、严格 blocked smoke、结构检查、文档检查和 Playwright/Chrome HTML 截图。它们用于证明 v74 不只是代码存在，而是能消费真实 comparison 并生成可浏览报告。

## 一句话总结

v74 把 MiniGPT 从“能比较多次受控训练启动”推进到“能选择下一次是否进入真实训练执行”的训练前决策层。
