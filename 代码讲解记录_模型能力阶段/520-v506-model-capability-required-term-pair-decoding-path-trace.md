# v506 required-term pair decoding path trace 代码讲解

## 本版目标与边界

v506 继续追 v505 的问题：为什么 `symmetric-anchor` 在不同 decoding profile 下能局部生成 `fixed` 或 `loss`，但没有任何 profile 同时 full-hit。

本版不训练、不扩 profile，而是重放 v505 的采样路径。它要回答的是：expected term 是否在第一步就被模型采到，还是只在后续步骤里偶然出现。

## 前置链路

前置版本：

- v503：forced-choice 发现 `symmetric-anchor` 有内部 full-match。
- v504：证明该内部信号没有被 archived free generation 表达。
- v505：少量 decoding profile 能局部表达 `fixed` 或 `loss`，但没有 full-hit profile。

v506 就是在 v505 基础上做 step-level trace。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_decoding_path_trace.py`
  - 主流程：读取 v505、选择 trace target、调用 checkpoint trace、汇总 decision。
- `src/minigpt/model_capability_required_term_pair_decoding_path_trace_components.py`
  - 纯数据逻辑：选择 best variant、汇总 probe summaries、计算 late hit 和 first-token miss。
- `src/minigpt/model_capability_required_term_pair_decoding_path_trace_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
- `scripts/run_model_capability_required_term_pair_decoding_path_trace.py`
  - CLI 入口，支持输入 v505 JSON 或目录，支持 `--variant-limit`、`--device`、`--require-pass` 和 `--force`。
- `tests/test_model_capability_required_term_pair_decoding_path_trace.py`
  - 覆盖 late expression、first-token expression、输入失败、target selection 和 summary 渲染。

## 核心数据结构

`probe_rows` 是逐 probe 的 trace 结果，保留 v505 的 profile/prompt 信息，并新增：

- `first_expected_token_id`
- `first_expected_token_text`
- `first_expected_token_rank`
- `first_expected_token_logprob`
- `first_sample_token_id`
- `first_sample_text`
- `first_sample_matches_expected_first_token`
- `expected_first_token_seen_step`
- `steps`

`steps` 是逐 token 采样轨迹，每步记录：

- `step`
- `sampled_token_id`
- `sampled_text`
- `continuation_preview`

`probe_summaries` 是人工审阅层，重点字段是：

- `continuation_hit`
- `first_expected_token_rank`
- `first_sample_text`
- `late_hit_after_first_miss`
- `expected_first_token_seen_step`

## 核心函数流程

`build_model_capability_required_term_pair_decoding_path_trace()` 是主入口。

1. 从 v505 summary 中读取 best variant。
2. `select_decoding_path_trace_targets()` 选择该 variant 的 probe rows。
3. `_trace_with_checkpoint()` 按 v505 记录的 checkpoint、tokenizer、profile、seed 重放采样。
4. 每一步在采样前计算 expected first token 的 rank/logprob。
5. 每一步采样后记录 token id、token text 和 continuation preview。
6. `summarize_decoding_path_probe_rows()` 判断是否 first-token match 或 late hit。
7. `summarize_required_term_pair_decoding_path_trace()` 生成整体 decision。

## 真实结果解释

真实运行结果：

- `probe_count=6`
- `trace_step_count=120`
- `first_sample_match_count=0`
- `late_hit_after_first_miss_count=2`
- `first_expected_rank_le_5_count=6`

这说明 expected first token 并不是完全排在很后面，反而所有 probe 都在前 5 内；问题在于实际采样第一步没有选它。v505 中 `fixed/loss` 的两个命中都是后续绕回来才出现，不是稳定的 prompt-conditioned 第一 token 表达。

## 输出证据

v506 输出位置：

```text
e/506/解释/model-capability-required-term-pair-decoding-path-trace/
```

输出包括 JSON、CSV、text、Markdown、HTML。截图和说明归档在：

```text
e/506/图片
e/506/解释/说明.md
```

## 测试覆盖

测试覆盖：

- fake trace 出现 late hit 时，decision 为 `required_term_pair_decoding_path_late_expression`。
- fake trace 第一 token 直接命中时，decision 为 `required_term_pair_decoding_path_first_token_expression`。
- 无可 trace rows 时，报告失败。
- target selection 使用 v505 best variant。
- renderer 输出多格式证据。

## 一句话总结

v506 把生成问题定位到第一步采样表达：模型把 expected first token 排得不低，但采样路径没有稳定从它开始。
