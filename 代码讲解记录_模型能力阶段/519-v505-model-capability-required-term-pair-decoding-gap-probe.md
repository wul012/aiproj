# v505 required-term pair decoding gap probe 代码讲解

## 本版目标与边界

v505 的目标是继续追 v504 的 gap：既然 `symmetric-anchor` 在 forced-choice 下能同时选对 `fixed/loss`，但 archived free generation 没有表达，那么调整生成 profile 是否能让这个内部信号出现。

本版只做生成侧 probe，不训练新 checkpoint，不改 v502-v504 历史证据，也不宣称模型能力已经恢复。它复用 v503 记录的 checkpoint/tokenizer 路径，针对 v504 标出的 best gap variant 跑少量 decoding profile。

## 前置链路

前置证据链是：

- v503：teacher-forced forced-choice 发现 `symmetric-anchor` 是内部 full-match。
- v504：对齐 v503 和 v502，发现 `symmetric-anchor` 的内部 full-match 没被自由生成表达。
- v505：只在 `symmetric-anchor` 上试生成侧 profile，观察内部偏好是否能局部表达。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_decoding_gap_probe.py`
  - 主流程：读取 v504、追溯 v503、选择 gap target、调用生成器、输出 interpretation。
- `src/minigpt/model_capability_required_term_pair_decoding_gap_probe_components.py`
  - 纯数据逻辑：默认 profile、target selection、profile summary 和整体 summary。
- `src/minigpt/model_capability_required_term_pair_decoding_gap_probe_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML，保持渲染和核心逻辑分离。
- `scripts/run_model_capability_required_term_pair_decoding_gap_probe.py`
  - CLI 入口，支持输入 v504 JSON 或目录，支持 `--variant-limit`、`--device`、`--require-pass` 和 `--force`。
- `tests/test_model_capability_required_term_pair_decoding_gap_probe.py`
  - 覆盖 full expression、partial-only、输入失败、target selection 和 profile summary。

## 核心数据结构

`targets` 从 v504 `variant_summaries` 中选择 `forced_generation_gap=True` 的 variant，再通过 v503 `runs` 找到 checkpoint/tokenizer：

- `variant_id`
- `run_id`
- `pair_id`
- `checkpoint_path`
- `tokenizer_path`
- `prompts`

默认 profiles 是三个小 profile：

- `greedy-12`
- `greedy-24`
- `top2-24`

`probe_rows` 一行代表一个 profile/prompt 的生成结果：

- `profile_id`
- `prompt_term`
- `expected_term`
- `continuation`
- `continuation_hit`
- `generated_hit`
- `max_new_tokens`
- `temperature`
- `top_k`
- `seed`

`profile_summaries` 聚合每个 profile 是否 full-hit：

- `continuation_hit_count`
- `profile_full_hit`
- `hit_terms`
- `missed_terms`

## 核心函数流程

`build_model_capability_required_term_pair_decoding_gap_probe()` 是主入口。

1. 读取 v504 generation gap report。
2. 根据 v504 的 `source_required_term_pair_forced_choice_diagnostic` 读取 v503 forced-choice report。
3. `select_decoding_gap_targets()` 选择 `forced_generation_gap=True` 的 variant，并拿到 checkpoint/tokenizer。
4. `_run_decoding_probes()` 按 target/profile/prompt 组合调用生成器。
5. 默认 `_generate_with_checkpoint()` 使用 `MiniGPTGenerator` 和 `GenerationRequest`，复用现有推理路径。
6. `summarize_decoding_gap_profiles()` 汇总每个 profile 的命中情况。
7. 输出 summary、decision 和多格式 artifacts。

## 真实结果解释

真实运行结果：

- `probe_count=6`
- `continuation_hit_count=2`
- `profile_full_hit_count=0`
- `best_profile_id=top2-24`

具体表现：

- `greedy-12` 没有命中。
- `greedy-24` 在 `fixed:` 下生成了 `fixed`，但 `loss:` 仍失败。
- `top2-24` 在 `loss:` 下生成了 `loss`，但 `fixed:` 失败。

这说明生成侧确实能局部表达内部偏好，但表达不稳定。下一步应检查 first-token rank 和实际 sampled path，而不是继续扩大训练语料。

## 输出证据

v505 输出位置：

```text
e/505/解释/model-capability-required-term-pair-decoding-gap-probe/
```

输出包括：

- JSON：完整 probe report。
- CSV：逐 profile/prompt 生成事实表。
- text：命令行摘要。
- Markdown/HTML：人工审阅报告。

截图和解释归档在：

```text
e/505/图片
e/505/解释/说明.md
```

## 测试覆盖

测试覆盖：

- fake generator 同时命中 `fixed/loss` 时，decision 为 `required_term_pair_decoding_gap_expression_found`。
- fake generator 只命中一个 prompt 时，decision 为 `required_term_pair_decoding_gap_partial_only`。
- v504 缺少 v503 source link 时，报告失败。
- target selection 只选择 forced-generation gap variant。
- profile summary 正确识别 missed terms 和 full-hit 状态。

## 一句话总结

v505 把 v504 的 gap 进一步定位为生成 profile 不稳定：内部信号能被局部表达，但还没有稳定到 pair-level full generation。
