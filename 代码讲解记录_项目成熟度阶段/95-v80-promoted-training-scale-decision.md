# v80 promoted training scale baseline decision 代码讲解

## 本版目标

v80 的目标是把 v79 的 promoted-only comparison 再向后收口一步：从已经完成比较的 promoted runs 中选出下一阶段稳定 baseline。

v79 已经能保证：

```text
只比较 promoted 运行
review/blocked 运行保留证据但不进入比较
比较不足两个 promoted 输入时明确 blocked
```

v80 继续回答：

```text
比较完成之后，哪一个 promoted run 可以作为下一轮训练规模规划的 baseline？
如果上游 comparison 没完成，是否应该停止？
如果候选 readiness、gate、batch 条件不满足，是否应该进入 review 或 blocked？
```

本版明确不做：

- 不重新训练模型。
- 不重新跑 promotion。
- 不重新定义训练规模对比评分。
- 不从 review/blocked promotion 中选 baseline。
- 不在上游 comparison blocked 时伪造 baseline。

## 前置链路

v80 接在 v75-v79 之后：

```text
v75 consolidated training scale workflow
 -> v76 controlled training scale handoff
 -> v77 training scale promotion acceptance
 -> v78 training scale promotion index
 -> v79 promoted training scale comparison
 -> v80 promoted training scale baseline decision
```

这条链路让项目从“只比较 promoted 结果”推进到“从 promoted 比较结果中选出可解释 baseline”。

## 关键新增文件

```text
src/minigpt/promoted_training_scale_decision.py
scripts/decide_promoted_training_scale_baseline.py
tests/test_promoted_training_scale_decision.py
c/80/图片
c/80/解释/说明.md
```

README、`c/README.md` 和项目成熟度阶段讲解索引同步更新到 v80。

## 核心模块

### `load_promoted_training_scale_comparison`

输入可以是：

```text
runs/training-scale-workflow/promoted-comparison/promoted_training_scale_comparison.json
runs/training-scale-workflow/promoted-comparison
runs/training-scale-workflow
```

目录输入会查找：

```text
promoted_training_scale_comparison.json
comparison/promoted_training_scale_comparison.json
```

读取后附加 `_source_path`，用于输出报告定位上游 comparison 来源。

### `build_promoted_training_scale_decision`

这是 v80 的主函数。它读取 v79 comparison 后执行四步：

```text
1. 读取 promoted_training_scale_comparison.json
2. 将 promotions[] 标准化为候选行
3. 按 readiness、gate、batch 和上游 comparison 状态筛选候选
4. 在候选里选择 readiness/gate/batch 最优 baseline
```

如果上游 `comparison_status` 不是 `compared`，所有候选都会被拒绝，决策进入 `blocked`。这避免了“比较没有完成却选出 baseline”的假证据。

## 决策状态

v80 输出三类状态：

```text
accepted
review
blocked
```

含义：

- `accepted`：上游 comparison 完成，存在合格候选，且无需额外 review。
- `review`：存在可用候选，但 gate warning 或拒绝项需要人工解释。
- `blocked`：上游 comparison 未完成，或没有任何候选通过条件。

## 核心字段语义

### `promotions[]`

每一行代表 v79 comparison 中保留下来的 promoted 输入：

```text
name
promotion_status
promoted_for_comparison
comparison_status
gate_status
batch_status
readiness_score
training_scale_run_path
source_path
```

这里 `training_scale_run_path` 会解析成可检查的真实路径。路径不存在时，该行会被拒绝。

### `selected_baseline`

当有候选通过时，`selected_baseline` 保存被选中的 baseline：

```text
name
gate_status
batch_status
readiness_score
training_scale_run_path
promotion_status
```

选择规则优先级是：

```text
readiness_score 高
gate_status 更好
batch_status 更好
```

这让 baseline 选择不是“拿第一个”，而是沿用训练规模治理链里的可解释排序。

### `rejected_runs`

被拒绝的行会写出原因：

```text
run was not promoted for comparison
comparison report is not compared
gate failed
gate is not pass
batch did not complete
readiness_score below N
training_scale_run.json is missing
```

这些 rejected rows 是最终证据的一部分，不是临时调试信息。它们解释了为什么某些 promoted 或保留行不能成为 baseline。

## 输出产物

CLI：

```powershell
python scripts/decide_promoted_training_scale_baseline.py runs/training-scale-workflow/promoted-comparison --out-dir runs/training-scale-workflow/promoted-decision
```

输出：

```text
promoted_training_scale_decision.json
promoted_training_scale_decision.csv
promoted_training_scale_decision.md
promoted_training_scale_decision.html
```

JSON 是后续自动化最稳定的输入；CSV 方便扫描 selected/rejected 计数；Markdown 适合审查记录；HTML 用于浏览器验收和截图归档。

CLI 支持：

```text
--min-readiness
--require-gate-pass
--allow-incomplete-batch
--require-accepted
```

`--require-accepted` 适合脚本化流程：如果最终状态不是 `accepted`，命令返回非零退出码。

## 测试覆盖

`tests/test_promoted_training_scale_decision.py` 覆盖：

- 完成的 promoted comparison 会选出 readiness/gate/batch 更好的 baseline。
- 上游只有一个 promoted 输入导致 comparison blocked 时，decision 也 blocked。
- 上游 comparison 本身不是 compared 时，decision blocked。
- JSON/CSV/Markdown/HTML 能落盘，HTML 会转义 `<Decision>`。

这些断言保护的是 v80 的边界：只有完整 promoted comparison 之后才能选择 baseline。

## 运行归档

`c/80` 保存本版截图和解释：

```text
c/80/图片
c/80/解释/说明.md
```

截图覆盖新单测、完整回归、accepted smoke、blocked smoke、结构检查、Playwright/Chrome HTML 验收和文档索引检查。临时 fixture 与 smoke 输出放在 `tmp/v80-smoke`、`tmp/v80-evidence`，提交前按 cleanup gate 删除。

## 一句话总结

v80 把 MiniGPT 的训练规模链路从“只比较 promoted 运行”推进到“从 promoted 比较结果中选出下一阶段稳定 baseline”。
