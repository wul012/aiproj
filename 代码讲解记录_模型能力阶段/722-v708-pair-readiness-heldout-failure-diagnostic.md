# v708 pair-readiness heldout failure diagnostic

## 本版目标和边界

v708 的目标是诊断 v707 的 heldout direct replay 失败。它不训练、不改 corpus，只读取 v707 报告并分析 fixed/loss direct probes 的污染关系。

本版解决的问题是：不能只看到 `pair_full_observed=False`，还要知道到底是哪一支被哪一支吸附。

## 前置链路

v707 输出：

```text
decision=pair_readiness_training_no_pair_full
fixed= -> fixed=fixed=fixed=
loss=  -> loss=fixed=fixed=
```

v708 读取其中的 `replay_report.case_rows`。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_readiness_heldout_failure_diagnostic.py`
  - 诊断 builder。
  - 读取 training run report，提取 replay case rows。
  - 判断 `expected-fixed`、`expected-loss`、`loss-prompt-fixed-pollution` 等污染类型。

- `src/minigpt/model_capability_required_term_pair_readiness_heldout_failure_diagnostic_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 展示每个 probe 的 pollution class。

- `scripts/run_model_capability_required_term_pair_readiness_heldout_failure_diagnostic.py`
  - CLI。
  - 输入 v707 training run JSON 或目录。

- `tests/test_model_capability_required_term_pair_readiness_heldout_failure_diagnostic.py`
  - 覆盖 loss prompt 被 fixed 吸附、失败 replay 阻断、输出格式。

## 核心分类

每一行 replay case 会转成 analysis row：

```text
profile_id
term
prompt
generated
continuation
continuation_hit
fixed_present
loss_present
pollution_class
```

pollution class 包含：

```text
expected-fixed
expected-loss
fixed-prompt-loss-pollution
loss-prompt-fixed-pollution
miss
```

## 真实结果

v708 输出：

```text
decision=pair_readiness_loss_prompt_absorbed_by_fixed
dominant_failure=loss_prompt_absorbed_by_fixed
fixed_hit_count=1
loss_hit_count=0
loss_prompt_fixed_pollution_count=1
```

这说明下一步应该做 loss-retention repair，而不是继续泛泛增加训练步数。

## 一句话总结

v708 将 v707 的 no pair-full 归因为 loss prompt 被 fixed 分支吸附，为下一版制定 loss-retention 修复计划提供了可复核证据。
