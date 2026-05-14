# v78 training scale promotion index 代码讲解

## 本版目标

v78 的目标是把 v77 的 promotion acceptance 再向后收口一步：当项目手里有多份 `training_scale_promotion.json` 时，先建立一个统一索引，明确哪些运行结果可以进入后续训练规模对比，哪些只能保留为 review 或 blocked 证据。

v77 已经能判断一次 handoff 执行结果是：

```text
promoted
review
blocked
```

但如果后续要比较多个训练规模运行，不能把 `review` 或 `blocked` 的结果也混进 baseline 对比里。v78 解决的就是这个入口问题：只把满足 promotion 条件、并且 `training_scale_run.json` 仍然存在的结果转成 compare-ready inputs。

本版明确不做：

- 不重新训练模型。
- 不修改 v77 生成的 promotion 报告。
- 不直接比较模型分数。
- 不把 review/blocked 结果伪装成可比较基线。
- 不替代 `compare_training_scale_runs.py`，只为它准备干净输入。

## 前置链路

v78 接在 v75-v77 之后：

```text
v75 consolidated training scale workflow
 -> v76 controlled training scale handoff
 -> v77 training scale promotion acceptance
 -> v78 training scale promotion index
 -> compare_training_scale_runs.py
```

这条链路让项目从“能执行训练规模建议”继续推进到“能筛选哪些执行结果有资格进入横向比较”。这也回应了之前的方向判断：不要继续无限拆 dashboard/link，而是让已经完成的治理链服务于真实模型能力比较。

## 关键新增文件

```text
src/minigpt/training_scale_promotion_index.py
scripts/index_training_scale_promotions.py
tests/test_training_scale_promotion_index.py
c/78/图片
c/78/解释/说明.md
```

README、`c/README.md` 和 `代码讲解记录_项目成熟度阶段/README.md` 同步加入 v78 索引，保证版本表、运行证据和讲解入口一致。

## 核心模块

### `load_training_scale_promotion`

输入可以是 JSON 文件，也可以是 promotion 输出目录：

```text
runs/training-scale-workflow/promotion/training_scale_promotion.json
runs/training-scale-workflow/promotion
runs/training-scale-workflow
```

解析目录时会按顺序查找：

```text
training_scale_promotion.json
promotion/training_scale_promotion.json
training-scale-promotion/training_scale_promotion.json
```

读取成功后，模块会给 payload 加上 `_source_path`。这个字段不来自 v77 原始报告，而是 v78 为后续索引加的来源定位字段。

### `build_training_scale_promotion_index`

这是 v78 主函数。它读取多份 promotion 报告，生成四类核心数据：

```text
promotions
comparison_inputs
summary
recommendations
```

`promotions` 是逐份 promotion 的摘要行，保留所有输入，包括 promoted、review、blocked。这样 blocked/review 不会消失，后续审查仍能看到为什么它没有进入对比。

`comparison_inputs` 只包含真正可比较的运行：

```text
promotion_status == "promoted"
training_scale_run_path 指向的文件存在
```

这个条件由 `promoted_for_comparison` 表达。它比只看状态更严格，因为一份历史 promotion JSON 可能还在，但对应的 `training_scale_run.json` 已被移动或清理。缺少源运行文件时，v78 不会生成 compare 命令。

## 核心字段语义

### `promotions[]`

每一行代表一份 promotion 报告：

```text
name
promotion_source_path
promotion_status
promoted_for_comparison
handoff_path
training_scale_run_path
training_scale_run_exists
batch_path
handoff_status
scale_run_status
batch_status
variant_count
ready_variant_count
required_artifact_count
available_required_artifact_count
primary_variant
primary_checkpoint
primary_registry
primary_maturity_narrative
missing_required
blockers
review_items
```

其中 `primary_variant` 优先选择 ready variant；如果没有 ready variant，就保留第一个 variant，方便 review/blocked 状态也能解释自己的缺口。

### `comparison_inputs`

这是后续脚本最应该消费的区域：

```text
run_count
names
training_scale_run_paths
baseline_name
compare_command_ready
compare_command
```

当 promoted 输入不足两个时，`compare_command_ready` 为 `false`，报告会说明当前只能把单个 promoted run 当作 baseline candidate。只有两个或更多 promoted run 时，v78 才生成：

```powershell
python scripts/compare_training_scale_runs.py <run-a> <run-b> --name <a> --name <b> --baseline <baseline>
```

### `summary`

`summary` 是给人和脚本快速判断用的摘要：

```text
promotion_count
promoted_count
review_count
blocked_count
missing_count
comparison_ready_count
compare_command_ready
non_comparable_count
```

它把“项目有多少 promotion 证据”和“多少可以进入模型能力比较”分开，避免把治理证据的数量误解成模型对比的质量。

## 输出产物

CLI：

```powershell
python scripts/index_training_scale_promotions.py runs/training-scale-workflow/promotion --out-dir runs/training-scale-workflow/promotion-index
```

输出：

```text
training_scale_promotion_index.json
training_scale_promotion_index.csv
training_scale_promotion_index.md
training_scale_promotion_index.html
```

JSON 是后续自动化最稳定的输入；CSV 适合横向扫多份 promotion；Markdown 适合进入讲解和审查记录；HTML 用于浏览器验收和归档截图。

CLI 还支持：

```text
--name
--baseline
--require-compare-ready
```

`--require-compare-ready` 适合把 v78 放进脚本或 CI：如果 promoted 输入不足两个，命令会返回非零退出码，阻止继续比较。

## 测试覆盖

`tests/test_training_scale_promotion_index.py` 覆盖四个关键判断：

- 两个 promoted 报告会进入 compare inputs，并生成 compare 命令。
- promoted/review/blocked 混合输入会保留三类状态，但只有 promoted 进入 compare inputs。
- baseline 不能指向 review 或 blocked 输入。
- JSON/CSV/Markdown/HTML 能落盘，并且 HTML 会转义 `<Index>`、`<alpha>` 这类特殊字符。

这些断言保护的是 v78 的边界：它必须让不可比较的运行可见，但不能让它们进入模型能力比较。

## 运行归档

`c/78` 保存本版截图和解释：

```text
c/78/图片
c/78/解释/说明.md
```

截图覆盖新单测、完整回归、混合 promotion smoke、compare-ready smoke、结构检查、Playwright/Chrome HTML 验收和文档索引检查。临时 fixture 与 smoke 输出放在 `tmp/v78-smoke`、`tmp/v78-evidence`，提交前按 cleanup gate 删除。

## 一句话总结

v78 把 MiniGPT 的训练规模链路从“能验收某次执行结果”推进到“能筛选多次验收结果，只把 promoted 运行交给后续对比”。
