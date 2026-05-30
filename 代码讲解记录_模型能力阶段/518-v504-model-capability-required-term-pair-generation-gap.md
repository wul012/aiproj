# v504 required-term pair generation gap 代码讲解

## 本版目标与边界

v504 的目标是解释 v503 的 forced-choice 结果和 v502 的自由生成结果为什么不一致。

v503 显示 `symmetric-anchor` checkpoint 在 teacher-forced 打分下已经能让 `fixed:` 选择 `fixed`、`loss:` 选择 `loss`。但 v502 的自由生成仍然没有 full-hit。v504 不重新训练、不重新生成，只把这两份已经归档的证据逐 prompt 对齐，判断 gap 是不是存在。

## 前置链路

本版依赖两份前置证据：

- v503 forced-choice diagnostic：提供每个 prompt 的 `best_candidate_term`、`expected_is_best`、NLL 和 variant summary。
- v502 branch-retention sweep：提供每个 prompt 的 archived free-generation continuation、hit count 和 pair-level generation summary。

这让 v504 成为一个只读对照层：它不是新训练链，也不是新能力宣称，而是把“内部偏好”和“自由生成表达”拆开看。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_generation_gap.py`
  - 主流程入口，负责读取 source link、检查输入、构建 report、给出 decision 和 interpretation。
- `src/minigpt/model_capability_required_term_pair_generation_gap_components.py`
  - 负责 gap rows、variant summaries 和 summary 的纯数据汇总。
- `src/minigpt/model_capability_required_term_pair_generation_gap_artifacts.py`
  - 负责 JSON/CSV/text/Markdown/HTML 输出，避免渲染逻辑塞进核心诊断模块。
- `scripts/run_model_capability_required_term_pair_generation_gap.py`
  - CLI 入口，支持输入 v503 JSON 或目录，默认根据 v503 的 `source_required_term_pair_branch_retention_sweep` 追溯 v502。
- `tests/test_model_capability_required_term_pair_generation_gap.py`
  - 覆盖 gap observed、generation aligned、输入失败、gap class 分类和渲染输出。

## 核心数据结构

`gap_rows` 是本版最重要的事实表，一行对应一个 variant/prompt：

- `variant_id`
- `run_id`
- `prompt_term`
- `expected_term`
- `forced_best_candidate_term`
- `forced_expected_is_best`
- `generation_continuation_hit`
- `generation_continuation_preview`
- `gap_class`

`gap_class` 有四种：

- `aligned_hit`：内部偏好和自由生成都命中 expected。
- `internal_only`：内部偏好命中 expected，但自由生成没有命中。
- `generation_only`：自由生成命中，但内部 forced-choice 没偏向 expected。
- `aligned_miss`：内部和自由生成都没命中。

`variant_summaries` 再按 variant 汇总：

- `forced_expected_best_count`
- `forced_choice_full_match`
- `generation_hit_count`
- `generation_pair_full_hit`
- `gap_counts`
- `forced_generation_gap`

## 核心函数流程

`build_model_capability_required_term_pair_generation_gap()` 是主入口。

1. 定位 v503 forced-choice report。
2. 从 v503 的 `source_required_term_pair_branch_retention_sweep` 读取 v502 branch-retention report。
3. `_input_issues()` 检查两份 source report 是否可读、是否 pass、是否具备 prompt summaries 和 probe rows。
4. `build_generation_gap_rows()` 用 `run_id + prompt_term` 把 v503 prompt summary 和 v502 generation probe 对齐。
5. `classify_generation_gap()` 给每行标记 gap class。
6. `summarize_generation_gap_variants()` 聚合到 variant 层。
7. `summarize_required_term_pair_generation_gap()` 生成整体 summary 和 decision。

## 真实结果解释

v504 的真实结果是：

- `forced_choice_full_match_variant_count=1`
- `generation_full_match_variant_count=0`
- `forced_generation_gap_variant_count=1`
- `internal_only_prompt_count=2`
- `best_gap_variant_id=symmetric-anchor`

这说明当前不是“完全没学到 pair preference”，而是至少一个 checkpoint 的内部打分已经支持 pair preference，但自由生成没有把这个 preference 稳定表达出来。

因此，下一步不应该继续盲目做 corpus weighting；更合理的是围绕 `symmetric-anchor` 做生成侧诊断，例如 deterministic decoding、长度预算、首 token rank 到实际采样路径的差异。

## 输出证据

v504 输出位置：

```text
e/504/解释/model-capability-required-term-pair-generation-gap/
```

输出包括：

- JSON：完整结构化 gap report。
- CSV：逐 prompt gap rows，便于查 continuation 和 classification。
- text：命令行摘要。
- Markdown/HTML：人工审阅报告。

截图和解释归档在：

```text
e/504/图片
e/504/解释/说明.md
```

## 测试覆盖

测试保护了几类关键行为：

- forced-choice full-match 但 generation 不 full-match 时，decision 为 `required_term_pair_generation_gap_observed`。
- generation 也 full-match 时，decision 转为 `required_term_pair_generation_aligned`。
- 缺少 source branch-retention link 时，报告失败且 `--require-pass` 返回非零。
- 四种 gap class 都有明确断言。
- JSON/CSV/text/Markdown/HTML 输出都能生成。

## 一句话总结

v504 把 `fixed/loss` 问题从“训练是否学到”进一步拆成“内部偏好是否能被自由生成表达”，为下一步生成侧诊断确定了最小目标。
