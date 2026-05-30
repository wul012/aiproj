# v511 required-term pair continuation-span stability 代码讲解

## 本版目标与边界

v511 的目标是复查 v510 的 prefix gain 是否跨 seed 稳定。v510 已经证明 `fixed` 的最小命中前缀从 `4` 降到 `1`，但那只是一个 seed。v511 把同一 continuation-span objective 在 seed `510` 和 `511` 上复跑，形成稳定性判断。

本版不引入新语料主题，不扩大模型，不宣称自由生成已经恢复。它只验证同一 tiny objective 的 seed-level reproducibility。

## 前置链路

前置版本：

- v509：给出下一步计划 `continuation_span_objective_fixed_loss`。
- v510：训练一个 tiny continuation-span checkpoint，观察到 prefix-boundary gain，但自由生成没有 full-hit。

v511 的问题是：v510 的 prefix gain 是否只是单 seed 偶然。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_continuation_span_stability.py`
  - 主流程：按 seeds 多次调用 v510 builder，汇总 seed rows 和稳定性 summary。
- `src/minigpt/model_capability_required_term_pair_continuation_span_stability_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
- `scripts/run_model_capability_required_term_pair_continuation_span_stability.py`
  - CLI 入口，支持 `--seeds`、训练参数、`--force` 和 `--require-pass`。
- `tests/test_model_capability_required_term_pair_continuation_span_stability.py`
  - 覆盖稳定 prefix gain 和空 seed 失败。
- `src/minigpt/model_capability_required_term_pair_continuation_span_objective.py`
  - 本版同步补 `refresh_training_artifact_status()`，修复训练返回后 artifact flags 偶发滞后的误判。

## 核心数据结构

`seed_rows` 是 v511 的核心：

- `seed`
- `status`
- `decision`
- `continuation_span_decision`
- `checkpoint_exists`
- `generation_hit_count`
- `candidate_pair_full_generation_hit`
- `candidate_one_token_prefix_hit_count`
- `prefix_minimum_improved_count`
- `source_one_token_retained_count`
- `out_dir`

`summary` 汇总 seed 层级稳定性：

- `seed_count`
- `pass_count`
- `checkpoint_exists_count`
- `prefix_gain_seed_count`
- `full_pair_generation_seed_count`
- `both_terms_one_token_seed_count`
- `stable_prefix_gain`
- `stable_full_pair_generation`

## 核心函数流程

`build_model_capability_required_term_pair_continuation_span_stability()` 是主入口：

1. 清洗 seed 列表。
2. 校验 v509 rollup 是否仍推荐 `continuation_span_objective_fixed_loss`。
3. 对每个 seed 调用 v510 的 `build_model_capability_required_term_pair_continuation_span_objective()`。
4. `summarize_continuation_span_seed_rows()` 把每个 seed 的结果压成一行。
5. `summarize_continuation_span_stability()` 判断是否 stable prefix gain 或 stable full generation。

`refresh_training_artifact_status()` 解决本版遇到的真实问题：第一次运行被中断后，seed 510 的日志和 checkpoint 已存在，但报告中的 artifact flags 仍是 false。函数会重新检查 checkpoint/tokenizer/metrics/config 文件，并在 return code 为 `0` 且核心 artifact 存在时修正 status。

## 真实结果解释

真实运行结果：

- `seed_count=2`
- `pass_count=2`
- `checkpoint_exists_count=2`
- `prefix_gain_seed_count=2`
- `full_pair_generation_seed_count=0`
- `stable_prefix_gain=True`
- `stable_full_pair_generation=False`

这说明 v510 的 prefix gain 跨 seed 复现，但自由生成恢复还没有稳定出现。下一步不应该继续重复同一 prompt，而应该加入 held-out prompt variants。

## 输出证据

v511 输出位置：

```text
e/511/解释/model-capability-required-term-pair-continuation-span-stability/
```

截图和说明归档在：

```text
e/511/图片
e/511/解释/说明.md
```

## 测试覆盖

测试覆盖：

- 两个 fake seed 都产生 prefix gain 时，报告为 `required_term_pair_continuation_span_prefix_gain_stable`。
- seed 列表为空时，报告失败并在 `--require-pass` 下返回非零。
- v510 的 artifact status refresh 能把磁盘实际存在的 checkpoint/tokenizer 修正为 pass。

这些测试保护 v511 的工程契约：稳定性报告不能只看单个 seed，也不能被 artifact flags 的短暂误判污染。

## 一句话总结

v511 把 v510 的单 seed prefix gain 推进为双 seed 稳定信号，同时明确下一步要做 held-out prompt 泛化验证。
