# v79 promoted training scale comparison 代码讲解

## 本版目标

v79 的目标是把 v78 的 promotion index 真正接到训练规模对比链路上：读取 `training_scale_promotion_index.json`，只取其中 `promoted_for_comparison=true` 的运行，再复用已有的 `training_scale_run_comparison` 逻辑生成对比结果。

v78 已经能回答：

```text
哪些 promotion 是 promoted？
哪些 promotion 只是 review 或 blocked？
后续 compare 命令应该吃哪些 training_scale_run.json？
```

v79 继续推进的问题是：不要让用户手动复制命令，也不要让 review/blocked 运行误入模型能力比较。它把 v78 的索引变成一个受控比较入口。

本版明确不做：

- 不重新训练模型。
- 不重新生成 promotion 报告。
- 不改变 v73 `training_scale_run_comparison` 的评分逻辑。
- 不把 review 或 blocked promotion 纳入对比。
- 不在 promoted 输入不足两个时伪造比较结论。

## 前置链路

v79 接在 v75-v78 之后：

```text
v75 consolidated training scale workflow
 -> v76 controlled training scale handoff
 -> v77 training scale promotion acceptance
 -> v78 training scale promotion index
 -> v79 promoted training scale comparison
```

这条链路让项目从“知道哪些结果被验收为 promoted”继续推进到“只在 promoted 结果之间做训练规模横向比较”。

## 关键新增文件

```text
src/minigpt/promoted_training_scale_comparison.py
scripts/compare_promoted_training_scale_runs.py
tests/test_promoted_training_scale_comparison.py
c/79/图片
c/79/解释/说明.md
```

README、`c/README.md` 和项目成熟度阶段讲解索引同步更新到 v79。

## 核心模块

### `load_training_scale_promotion_index`

输入可以是：

```text
runs/training-scale-workflow/promotion-index/training_scale_promotion_index.json
runs/training-scale-workflow/promotion-index
runs/training-scale-workflow
```

目录输入会查找：

```text
training_scale_promotion_index.json
promotion-index/training_scale_promotion_index.json
```

读取后会附加 `_source_path`，用于输出报告定位 index 来源。

### `build_promoted_training_scale_comparison`

这是 v79 的主函数。它做四步：

```text
1. 读取 v78 promotion index
2. 从 promotions[] 中筛选 promoted_for_comparison=true 的行
3. 检查 promoted run 的 training_scale_run.json 是否存在
4. promoted 输入不少于两个时，调用 build_training_scale_run_comparison
```

如果 promoted 输入不足两个、路径缺失、或者 baseline 不在 promoted 集合里，v79 不会抛出中断给用户，而是生成 `comparison_status=blocked` 的报告，并写出 blocker 和 recommendation。

## 核心字段语义

### `comparison_status`

```text
compared
blocked
```

`compared` 表示已经成功复用 v73 对比逻辑生成结果；`blocked` 表示当前 index 不满足比较条件。

### `promotions[]`

v79 保留 index 中的 promotion 行，但只给 promoted 行补充 comparison 信息：

```text
name
promotion_status
promoted_for_comparison
training_scale_run_path
training_scale_run_exists
comparison_status
allowed
gate_status
batch_status
readiness_score
```

这样 review/blocked 行不会消失，报告仍然能解释它们为什么没有参与比较。

### `comparison_inputs`

这个区域记录真正交给对比器的输入：

```text
run_count
names
training_scale_run_paths
resolved_paths
missing_paths
baseline_name
compare_command_ready
```

其中 `resolved_paths` 是 v79 解析后的真实路径；如果有缺失路径，就进入 blocked。

### `comparison`

当状态为 `compared` 时，`comparison` 内嵌已有 `build_training_scale_run_comparison` 的完整报告，包括：

```text
runs
baseline
baseline_deltas
summary
best_by_readiness
recommendations
```

这意味着 v79 没有复制一套新评分标准，而是把 promoted-only 的输入边界加到已有训练规模对比器前面。

## 输出产物

CLI：

```powershell
python scripts/compare_promoted_training_scale_runs.py runs/training-scale-workflow/promotion-index --out-dir runs/training-scale-workflow/promoted-comparison
```

输出：

```text
promoted_training_scale_comparison.json
promoted_training_scale_comparison.csv
promoted_training_scale_comparison.md
promoted_training_scale_comparison.html
```

JSON 是后续自动化最稳定的输入；CSV 把 promotion 状态和 comparison delta 放在同一张表；Markdown 适合审查记录；HTML 用于浏览器验收和截图归档。

CLI 支持：

```text
--baseline
--require-compared
```

`--require-compared` 适合脚本化流程：如果 promoted 输入不足或 baseline 不合法，命令会返回非零退出码。

## 测试覆盖

`tests/test_promoted_training_scale_comparison.py` 覆盖：

- 两个 promoted 加一个 review 输入时，只比较两个 promoted。
- promoted 输入不足两个时，报告为 blocked。
- baseline 指向非 promoted 名称时，报告为 blocked。
- JSON/CSV/Markdown/HTML 能落盘，HTML 会转义 `<Promoted Compare>` 和 `<alpha>`。

这些断言保护的是 v79 的核心边界：comparison 必须只发生在 promoted 结果之间。

## 运行归档

`c/79` 保存本版截图和解释：

```text
c/79/图片
c/79/解释/说明.md
```

截图覆盖新单测、完整回归、promoted-only smoke、blocked smoke、结构检查、Playwright/Chrome HTML 验收和文档索引检查。临时 fixture 与 smoke 输出放在 `tmp/v79-smoke`、`tmp/v79-evidence`，提交前按 cleanup gate 删除。

## 一句话总结

v79 把 MiniGPT 的训练规模链路从“筛出可比较 promoted 结果”推进到“只在 promoted 结果之间执行训练规模对比”。
