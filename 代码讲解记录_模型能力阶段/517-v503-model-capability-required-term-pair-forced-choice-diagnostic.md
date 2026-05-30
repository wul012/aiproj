# v503 required-term pair forced-choice diagnostic 代码讲解

## 本版目标与边界

v503 解决的是 v502 之后的一个判断问题：branch-retention sweep 的自由生成没有恢复 `fixed/loss` full-hit，那么失败是否等于模型完全没有学到第二个分支。

本版新增 teacher-forced forced-choice diagnostic。它读取 v502 的真实 checkpoint，在同一个 prompt 后分别强制评分候选词 `fixed` 和 `loss`，用平均 NLL 判断模型内部更偏向哪个候选。它不做新训练，不改变 v502 证据，也不把 forced-choice 结果直接包装成自由生成能力。

## 前置链路

前置版本是 v502：

- v502 训练了 `alternating-balanced`、`symmetric-boost`、`symmetric-anchor` 三个 balanced clean 变体。
- 自由生成阶段三个变体都没有 full-hit。
- `symmetric-anchor` 在生成上甚至没有命中短 continuation，但它仍保留了真实 checkpoint，可用于更细的内部偏好诊断。

v503 的作用就是在 v502 checkpoint 和下一步 decoding/generation 诊断之间补一层只读证据。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_forced_choice_diagnostic.py`
  - 负责主流程编排：定位 source report、选择 targets/runs、调用 checkpoint scorer、汇总 status/decision/interpretation。
- `src/minigpt/model_capability_required_term_pair_forced_choice_diagnostic_components.py`
  - 负责纯数据逻辑：选择可评分 checkpoint、按 prompt 汇总 best candidate、按 variant 汇总 full-match/collapse。
- `src/minigpt/model_capability_required_term_pair_forced_choice_diagnostic_artifacts.py`
  - 负责 JSON/CSV/text/Markdown/HTML 证据输出，和主诊断逻辑分离，避免报告渲染膨胀到核心模块里。
- `scripts/run_model_capability_required_term_pair_forced_choice_diagnostic.py`
  - 提供 CLI 入口，支持输入 v502 JSON 或目录，支持 `--require-pass`、`--force`、`--pair-limit`、`--run-limit` 和 `--device`。
- `tests/test_model_capability_required_term_pair_forced_choice_diagnostic.py`
  - 覆盖成功、collapse、输入失败、选择器、summary、渲染和 CLI exit 边界。

## 核心数据结构

`targets` 来自 v502 report 的 `targets` 字段，保留：

- `pair_id`
- `term_names`
- `terms`
- `focus_missed_term`
- `source_hit_terms`

`runs` 来自 v502 report 的 `training_rows`，只选择 `checkpoint_exists=True` 且同时有 checkpoint/tokenizer 路径的行：

- `run_id`
- `pair_id`
- `variant_id`
- `variant_label`
- `checkpoint_path`
- `tokenizer_path`

`score_rows` 是 v503 的最小评分事实表。每个 run、prompt、candidate 一行，核心字段包括：

- `prompt_term`
- `candidate_term`
- `is_expected_candidate`
- `avg_nll`
- `total_nll`
- `first_token_rank`
- `first_token_logprob`

`prompt_summaries` 将同一个 run/prompt 下的候选聚合，比较 expected candidate 与 best candidate：

- `expected_term`
- `best_candidate_term`
- `expected_is_best`
- `expected_rank`
- `expected_margin_vs_best`

`variant_summaries` 再按 checkpoint 变体聚合：

- `expected_best_count`
- `expected_best_rate`
- `forced_choice_full_match`
- `best_candidate_by_prompt`
- `collapse_candidate`

## 核心函数流程

`build_model_capability_required_term_pair_forced_choice_diagnostic()` 是主入口。

1. 从 v502 report 选择 forced-choice targets。
2. 从 v502 training rows 选择可评分 checkpoint runs。
3. 对每个 target/run 组合调用 `_score_run_choices()`。
4. `_score_run_choices()` 对每个 prompt term 枚举所有 candidate term。
5. 默认 scorer `_score_candidate_with_checkpoint()` 加载 tokenizer 和 checkpoint，逐 token teacher-force 候选词，计算 NLL 和首 token rank。
6. 汇总 prompt 和 variant 层结果。
7. 输出 `status`、`decision`、`summary`、`interpretation` 和多格式 artifacts。

这里的 teacher-forced 评分和自由生成不同：它不是让模型自己续写，而是问模型“在这个 prompt 后，如果下一个候选是 fixed/loss，哪个整体负对数似然更低”。因此它适合诊断内部偏好，但不能替代生成质量评估。

## 输出证据

v503 输出位置：

```text
e/503/解释/model-capability-required-term-pair-forced-choice-diagnostic/
```

其中：

- JSON 是完整结构化证据，供后续脚本消费。
- CSV 是逐 candidate score rows，便于查看 NLL/rank。
- text 是命令行摘要，便于 CI 或日志读取。
- Markdown/HTML 是人工审阅报告。

本次真实运行结果：

- `status=pass`
- `decision=required_term_pair_forced_choice_internal_match`
- `expected_best_count=4`
- `forced_choice_full_match_variant_count=1`
- `best_variant_id=symmetric-anchor`

## 测试覆盖

单测覆盖了几条关键边界：

- fake scorer 下 expected candidate 全部胜出时，报告进入 `required_term_pair_forced_choice_internal_match`。
- fake scorer 让两个 prompt 都 collapse 到 `fixed` 时，summary 能识别 partial/collapse。
- 源 report 没有可评分 checkpoint 时，`status=fail` 且 `--require-pass` 会返回失败。
- selector 只选择 checkpoint/tokenizer 路径完整的 training row。
- renderer 输出 text/Markdown/HTML/CSV/JSON，保证人工报告和结构化证据同步。

## 运行证据

本版运行证据归档在 `e/503`：

- `e/503/解释/说明.md` 解释真实运行结果和边界。
- `e/503/图片/01-model-capability-required-term-pair-forced-choice-diagnostic.png` 截取 HTML 报告，证明 prompt choices 和 variant summary 可人工复核。

## 一句话总结

v503 证明 v502 的失败不是单一结论：至少一个 checkpoint 已经在 forced-choice 内部打分上学到 `fixed/loss` 分支偏好，但自由生成仍需要继续诊断。
