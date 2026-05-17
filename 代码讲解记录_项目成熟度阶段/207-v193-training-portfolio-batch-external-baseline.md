# v193 training portfolio batch external baseline 代码讲解

## 本版目标

v193 的目标是把 v192 的外部 baseline pair 能力从单个 training portfolio 扩展到 batch variant 矩阵。

v192 已经解决了单次 candidate 训练如何比较外部 baseline checkpoint：

```text
baseline checkpoint
 -> candidate checkpoint
 -> pair_batch
 -> benchmark_scorecard
```

但 `run_training_portfolio_batch.py` 仍然只会构造默认 portfolio plan。也就是说，用户一旦进入多 variant 候选矩阵，很容易退回同 checkpoint 自检，除非手工改每个 variant 的单 run 命令。

v193 解决的问题是：

```text
批量候选训练能否共享同一个外部 baseline？
某个 variant 能否覆盖自己的 baseline checkpoint？
batch 报告能否直接看出每个 variant 当前 pair mode？
默认 same-checkpoint 行为是否仍然保持不变？
```

本版明确不做：

- 不自动训练或选择 baseline。
- 不改变 batch comparison 的评分逻辑。
- 不改变单个 `training_portfolio.py` 的 pair batch 输出契约。
- 不把 dry-run 的 planned evidence 当成真实模型能力提升。

## 前置路线

v193 接在 v192 后面：

```text
v191 same-checkpoint pair baseline
 -> v192 single portfolio external baseline
 -> v193 batch portfolio external baseline
```

这个顺序是合理的：先让单 run 链路跑通，再把同一参数语义推广到 batch，而不是在 batch 里另起一套 pair runner。

## 关键文件

```text
scripts/run_training_portfolio_batch.py
src/minigpt/training_portfolio_batch.py
src/minigpt/training_portfolio_batch_artifacts.py
tests/test_training_portfolio_batch.py
c/193/图片
c/193/解释/说明.md
```

`scripts/run_training_portfolio_batch.py` 是命令行入口。

`src/minigpt/training_portfolio_batch.py` 是 batch plan 构造和执行层，本版把 baseline 参数加入 common config 和 variant override。

`src/minigpt/training_portfolio_batch_artifacts.py` 是 batch 报告输出层，本版让 pair mode 进入 CSV、Markdown 和 HTML。

`tests/test_training_portfolio_batch.py` 保护参数透传、variant 覆盖和报告展示。

## 新增 CLI 参数

v193 给 batch 脚本增加：

```text
--pair-baseline-checkpoint
--pair-baseline-tokenizer
--pair-baseline-id
--pair-candidate-id
```

典型 dry-run：

```text
python scripts/run_training_portfolio_batch.py data/sample_zh.txt \
  --out-root runs/v193-batch-dry \
  --pair-baseline-checkpoint runs/baseline/checkpoint.pt \
  --pair-baseline-tokenizer runs/baseline/tokenizer.json \
  --pair-baseline-id baseline-v1 \
  --pair-candidate-id candidate-batch \
  --no-compare
```

这个命令不会执行训练，但会构造两个默认 variant 的 portfolio plan，并让每个 variant 的 pair step 指向同一个 baseline checkpoint。

## common config 与 variant override

`build_training_portfolio_batch_plan()` 现在把四个 pair 参数放入 common config：

```text
pair_baseline_checkpoint
pair_baseline_tokenizer
pair_baseline_id
pair_candidate_id
```

同时 `VARIANT_OVERRIDE_KEYS` 也允许 variant 覆盖这四个字段。

这带来两种用法：

```text
全局 baseline：所有 variant 都和同一个 baseline 比较。
variant baseline：某个 variant 指向自己的 baseline checkpoint。
```

一个重要边界是 tokenizer 默认值。

如果用户传了全局 baseline checkpoint 和 tokenizer，variant 默认继承两者。

如果某个 variant 覆盖 `pair_baseline_checkpoint` 但没有覆盖 `pair_baseline_tokenizer`，v193 会把 tokenizer 清空，让底层 `training_portfolio.py` 根据该 variant 的 baseline checkpoint 目录推导：

```text
<variant-baseline-dir>/tokenizer.json
```

这样不会出现“variant checkpoint 用自己的路径，但 tokenizer 还沿用全局 baseline”的混搭。

## portfolio plan 如何被构造

每个 variant 仍然调用同一个 `build_training_portfolio_plan()`。

v193 只是把配置透传进去：

```text
pair_baseline_checkpoint=config.get("pair_baseline_checkpoint")
pair_baseline_tokenizer=config.get("pair_baseline_tokenizer")
pair_baseline_id=_optional_str(config.get("pair_baseline_id"))
pair_candidate_id=_optional_str(config.get("pair_candidate_id"))
```

这意味着 batch 层不理解 pair batch 的细节。它只负责把参数交给单 run portfolio，让 v192 的 `pair_config` 继续作为唯一语义来源。

## pair mode 输出

batch summary 新增：

```text
pair_mode_counts
```

例如：

```json
{
  "external_baseline": 2
}
```

每个 variant result 新增：

```text
pair_mode
```

CSV 新增 `pair_mode` 列。

Markdown 顶部新增：

```text
Pair modes: `external_baseline=2`
```

HTML stats 区也显示 Pair modes，并在 variant 表里显示每个 variant 的 Pair Mode。

这类字段是人为复核用的，不改变训练过程，也不改变 scorecard 公式。

## 测试如何覆盖链路

`test_build_batch_plan_passes_pair_baseline_to_variants()` 覆盖：

- 全局 baseline checkpoint/tokenizer/id 会进入第一个 variant。
- variant 覆盖 checkpoint 后，会使用自己的 checkpoint。
- variant 覆盖 checkpoint 但不覆盖 tokenizer 时，tokenizer 会跟随 variant checkpoint 目录。
- pair command 中真的出现了 baseline checkpoint 和 candidate id。
- summary 中 `pair_mode_counts` 是 `{"external_baseline": 2}`。

已有 dry-run 测试补充断言：

- 默认不传 baseline 时仍是 `same_checkpoint_baseline`。
- `variant_results` 中会带 `pair_mode`。

renderer 测试补充断言：

- Markdown 中显示 Pair modes。
- HTML 中显示 `same_checkpoint_baseline`。

## 运行证据

v193 的运行证据放在：

```text
c/193/图片
c/193/解释/说明.md
```

关键 smoke 是 batch dry-run：

```text
status=planned
variant_count=2
comparison_status=skipped
pair_mode_counts={"external_baseline": 2}
```

它证明 v193 是 batch plan 能力扩展，而不是必须跑昂贵训练才能验证的模型能力声明。

## 一句话总结

v193 把外部 baseline pair 控制从单次 training portfolio 扩展到 batch variant 矩阵，让多候选训练计划也能明确保留 baseline-vs-candidate 比较语义。
