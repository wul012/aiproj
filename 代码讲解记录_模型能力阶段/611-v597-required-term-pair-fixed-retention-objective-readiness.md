# v597 required-term pair fixed-retention objective readiness

## 本版目标和边界

v597 把 v594 route decision 和 v596 missed-seed diagnostic 合成 fixed-retention objective readiness gate。它不训练模型，而是定义下一轮训练必须满足的输入要求。

本版的边界很重要：它不是新治理链，也不是模型能力提升声明；它是为了防止继续在错误方向上加 loss 权重。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_fixed_retention_objective_readiness.py
src/minigpt/model_capability_required_term_pair_fixed_retention_objective_readiness_artifacts.py
scripts/run_model_capability_required_term_pair_fixed_retention_objective_readiness.py
tests/test_model_capability_required_term_pair_fixed_retention_objective_readiness.py
e/597/解释/model-capability-required-term-pair-fixed-retention-objective-readiness/
```

## 输入

Route decision：

```text
e/594/解释/model-capability-required-term-pair-loss-branch-route-decision/
```

Missed-seed diagnostic：

```text
e/596/解释/model-capability-required-term-pair-loss-branch-targeted-missed-seed-diagnostic/
```

## 核心判断

v594 提供：

```text
fixed_retention_objective_required=True
selected_stability_route=v590-targeted
```

v596 提供：

```text
missed_first_token_gap_count=3
first_token_gap_confirmed=True
```

v597 合并后得到：

```text
decision=design_fixed_retention_objective_before_more_loss_branch_training
```

## Requirement Rows

`fixed_first_token_retention`：

```text
fixed_expected_rank must improve before adding more loss weighting
```

`loss_branch_no_extra_weight`：

```text
new corpus must not increase loss-only row density without fixed retention rows
```

`pair_full_seed_gate`：

```text
run at least one real seed before calling the objective useful
```

## 测试覆盖

测试覆盖：

- route decision 与 diagnostic 对齐时 readiness pass。
- 没有 first-token gap 时 readiness fail。
- CLI 在坏输入和 `--require-pass` 下返回非零。
- JSON/CSV/TXT/Markdown/HTML 都可生成。

## 一句话总结

v597 把“loss 已经够强，fixed retention 不够”固化为下一轮训练契约。
