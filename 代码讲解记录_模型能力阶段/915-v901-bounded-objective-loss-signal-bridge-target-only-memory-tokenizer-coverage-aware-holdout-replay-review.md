# v901 tokenizer-covered holdout replay review 代码讲解

## 本版目标与边界

v901 的目标是 review v900 的真实 replay 结果。v900 证明 v890 checkpoint 在 tokenizer-covered holdout suite 上 5/5 通过，但 v898 suite 的 prompt 都显式包含 `fixed/loss`。本版要把“模型确实生成了目标词”和“是否能批准 promotion”分开。

本版不重新 replay，不训练，不修改 suite。它只做 target leakage review。

## 关键文件

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_replay_review.py`
  - 核心 review 逻辑。
  - 读取 v900 real replay 和 v898 suite。
  - 对每条 prompt 检查是否包含 expected terms。

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_replay_review_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。

- `scripts/review_bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_replay.py`
  - CLI 入口。

- `tests/test_bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_replay_review.py`
  - 覆盖 leakage block、target-hidden approval、source fail、CLI/output。

## 核心流程

1. `build_tokenizer_coverage_aware_holdout_replay_review()` 读取 replay summary 和 suite cases。
2. `_review_rows()` 遍历每条 prompt，检查 `fixed/loss` 是否出现在 prompt 中。
3. `_summary()` 统计 `target_leakage_case_count` 和 `target_hidden_case_count`。
4. 只有 source replay ready、model quality ready、且 leakage 为 0 时，`approved_for_promotion=True`。
5. v901 真实结果 leakage 为 5，因此 review ready 但 promotion 不批准。

## 真实结果

- `source_holdout_model_quality_ready=True`
- `target_leakage_case_count=5`
- `target_hidden_case_count=0`
- `approved_for_promotion=False`
- `model_quality_claim=target_leaked_holdout_pass_review_only`
- `next_step=build_target_hidden_tokenizer_covered_holdout_suite`

## 测试意义

测试确保 v900 的正向结果不会被误升格：target-hidden prompt 可以 approval，target-leaked prompt 只能作为 review-only 证据。

## 一句话总结

v901 把 v900 的 5/5 pass 降级为 target-leaked holdout pass，并把下一步指向 target-hidden tokenizer-covered suite。
