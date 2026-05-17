# v192 external pair baseline portfolio 代码讲解

## 本版目标

v192 的目标是把 v191 的 same-checkpoint pair baseline 往前推进一步：让 training portfolio 可以直接使用一个外部 baseline checkpoint，与本次新训练出的 candidate checkpoint 做固定 prompt pair batch。

v191 已经把 pair batch 接入了真实训练组合链路：

```text
generation_quality
 -> pair_batch
 -> benchmark_scorecard
```

但当时只有一个新训练出的 checkpoint，所以 pair batch 默认左右两侧都是同一个 checkpoint。这能证明可复现性，却不能证明 candidate 相对 baseline 的生成差异。

v192 解决的问题是：

```text
如果用户已经有一个 baseline checkpoint，training portfolio 能否直接比较 baseline 和本次 candidate？
这个比较能否进入 scorecard，而不是停留在手工 pair_batch.py 命令？
报告打开时能否看出当前 pair mode？
same-checkpoint 判断能否避免只比较展示 id 的误判？
```

本版答案是：可以。v192 给 training portfolio 增加可选 baseline checkpoint/tokenizer/id 参数，并在报告里记录 `pair_config`。默认行为仍保持 v191 的同 checkpoint 自检，只有显式传入 baseline checkpoint 时才切换为 `external_baseline`。

本版明确不做：

- 不自动选择最佳 baseline。
- 不改变训练超参数或训练规模。
- 不改变 benchmark scorecard 的主评分公式。
- 不改变 pair batch 输出文件名和下游读取路径。
- 不把一次极小 smoke 的结果解读成模型能力提升。

## 前置路线

v192 接在真实训练证据链和 v191 pair baseline 之后：

```text
v186 real training run evidence
 -> v187 eval summary
 -> v188 generation quality summary
 -> v189 benchmark scorecard summary
 -> v190 scorecard quality path compatibility
 -> v191 same-checkpoint pair baseline
 -> v192 external baseline pair portfolio
```

这说明当前路线已经从“治理报告完整”重新回到“真实模型运行链路”：每一步都尽量让后续 scorecard、registry 和 maturity 能消费真实产物。

## 关键文件

```text
scripts/run_training_portfolio.py
src/minigpt/training_portfolio.py
src/minigpt/training_portfolio_artifacts.py
src/minigpt/pair_batch.py
tests/test_training_portfolio.py
tests/test_pair_batch.py
c/192/图片
c/192/解释/说明.md
```

`scripts/run_training_portfolio.py` 是用户入口。本版新增四个 CLI 参数。

`src/minigpt/training_portfolio.py` 是 pipeline plan 的核心，它根据是否传入 baseline checkpoint 决定 pair mode。

`src/minigpt/training_portfolio_artifacts.py` 是人可读输出层，本版让 Markdown 和 HTML 都显示 Pair mode。

`src/minigpt/pair_batch.py` 是 pair case 结果构造层，本版修正 `same_checkpoint` 判断逻辑。

## 新增 CLI 参数

v192 给 portfolio 脚本增加：

```text
--pair-baseline-checkpoint
--pair-baseline-tokenizer
--pair-baseline-id
--pair-candidate-id
```

典型用法是：

```text
python scripts/run_training_portfolio.py data/sample_zh.txt \
  --out-root runs/v192-portfolio-exec \
  --run-name v192-candidate \
  --pair-baseline-checkpoint runs/v192-baseline/checkpoint.pt \
  --pair-baseline-tokenizer runs/v192-baseline/tokenizer.json \
  --pair-baseline-id baseline-v1 \
  --pair-candidate-id candidate-v2 \
  --execute
```

这个命令训练 candidate，然后自动运行 pair batch：

```text
baseline checkpoint -> candidate checkpoint
```

如果不传 `--pair-baseline-checkpoint`，命令仍保持 v191 行为：

```text
candidate checkpoint -> candidate checkpoint
```

## pair_config 的结构

`build_training_portfolio_plan()` 现在会返回：

```text
pair_config
```

默认同 checkpoint 自检时：

```json
{
  "mode": "same_checkpoint_baseline",
  "left_checkpoint": "<run_dir>/checkpoint.pt",
  "right_checkpoint": "<run_dir>/checkpoint.pt",
  "left_tokenizer": "<run_dir>/tokenizer.json",
  "right_tokenizer": "<run_dir>/tokenizer.json",
  "left_id": "<run_name>",
  "right_id": "<run_name>"
}
```

外部 baseline 模式时：

```json
{
  "mode": "external_baseline",
  "left_checkpoint": "<baseline>/checkpoint.pt",
  "right_checkpoint": "<candidate_run>/checkpoint.pt",
  "left_tokenizer": "<baseline>/tokenizer.json",
  "right_tokenizer": "<candidate_run>/tokenizer.json",
  "left_id": "baseline-v1",
  "right_id": "candidate-v2"
}
```

这不是临时字段。它会写入 `training_portfolio.json`，并在 Markdown/HTML 中显示 `Pair mode`，用于人工复核。

## pair_batch step 如何变化

v191 的 pair step 固定是：

```text
--left-checkpoint <run_dir>/checkpoint.pt
--right-checkpoint <run_dir>/checkpoint.pt
```

v192 改为由 `pair_config` 生成：

```text
--left-checkpoint <pair_config.left_checkpoint>
--right-checkpoint <pair_config.right_checkpoint>
--left-tokenizer <pair_config.left_tokenizer>
--right-tokenizer <pair_config.right_tokenizer>
--left-id <pair_config.left_id>
--right-id <pair_config.right_id>
```

这样 training portfolio 不需要新增一套 pair runner，也不改变已有 `scripts/pair_batch.py` 的输出契约。

## same_checkpoint 判断为什么要改

v191 的 scorecard 已经优先比较 checkpoint 路径，避免两个不同 checkpoint 使用同一个展示 id 时被误判为 same-checkpoint。

但 `pair_batch.py` 自己构造 case result 时，原来仍然只看：

```text
left_checkpoint_id == right_checkpoint_id
```

这在两种情况下不够稳：

- 同一个 checkpoint 被传入不同展示 id，应当仍是 same checkpoint。
- 两个不同 checkpoint 被传入同一个展示 id，不应当是 same checkpoint。

v192 把判断改为：

```text
如果 response 中有 checkpoint 路径，优先比较路径；
只有路径缺失时，才退回比较展示 id。
```

这让 pair batch 和 scorecard 的边界语义保持一致。

## 输出产物如何被消费

外部 baseline 模式下，portfolio 仍然写出同样的 pair batch 四件套：

```text
pair_generation_batch.json
pair_generation_batch.csv
pair_generation_batch.md
pair_generation_batch.html
```

scorecard 仍从固定路径读取：

```text
<run_dir>/pair_batch/pair_generation_batch.json
<run_dir>/pair_batch/pair_generation_batch.html
```

区别是 JSON 里左侧 checkpoint 来自 baseline，右侧 checkpoint 来自 candidate。scorecard summary 会显示：

```text
pair_comparison_mode = cross_checkpoint_or_unknown
pair_same_checkpoint_baseline = false
```

这说明 v192 真正进入了跨 checkpoint 证据，而不是同 checkpoint 自检。

## 测试如何覆盖链路

`tests/test_training_portfolio.py` 新增外部 baseline 测试，保护：

- `pair_config.mode == external_baseline`
- 左侧 checkpoint 是 baseline。
- 右侧 checkpoint 是 candidate run。
- pair command 包含 baseline tokenizer。
- left/right id 被写入命令。
- Markdown 和 HTML 都显示 Pair mode。

`tests/test_pair_batch.py` 新增 same checkpoint 边界测试，保护：

- 路径相同、id 不同，仍判定 same checkpoint。
- 路径不同、id 相同，不判定 same checkpoint。

真实 smoke 还额外跑了：

```text
python scripts/train.py ... --out-dir runs/v192-baseline
python scripts/run_training_portfolio.py ... --pair-baseline-checkpoint runs/v192-baseline/checkpoint.pt --execute
```

结果是：

```text
portfolio_status=completed
completed_steps=11/11
available_artifacts=18/18
pair_config_mode=external_baseline
pair_same_flags=[False]
scorecard_pair_mode=cross_checkpoint_or_unknown
```

## README 和运行证据

README 的 Current version 更新到 v192，强调：

- v192 不再只依赖 same-checkpoint 自检。
- 外部 baseline checkpoint 可以作为 pair 左侧。
- 默认行为不变，仍能无 baseline 参数运行。
- Pair mode 会出现在 portfolio JSON、Markdown 和 HTML 中。

运行截图和解释放在：

```text
c/192/图片
c/192/解释/说明.md
```

这些截图证明测试、真实 baseline + candidate smoke、scorecard summary、Playwright HTML、source encoding、全量 unittest 和文档同步都完成。

## 一句话总结

v192 把 training portfolio 的 pair 证据从“同 checkpoint 可复现自检”升级为“可选外部 baseline 与本次 candidate 的真实跨 checkpoint 比较入口”。
