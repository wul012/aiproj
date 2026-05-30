# v507 required-term pair first-token repair 代码讲解

## 本版目标与边界

v507 接着 v506 的结论走：expected first token 排名不低，但实际第一步没有采到。于是本版强制把 expected first token 接到 prompt 后，再继续原 profile 生成，检查这是否足够恢复 `fixed/loss`。

本版不训练、不改变 checkpoint，也不把 constrained generation 当成正常模型能力。它只是一个诊断实验，用来判断问题是否主要集中在第一 token 采样。

## 前置链路

前置版本：

- v505：不同 decoding profile 只能局部表达 `fixed/loss`。
- v506：所有 probe 第一 token 都没有采到 expected first token，但 expected first token rank 都在前 5。

v507 的问题就是：如果第一 token 被人为修正，后续能否自然补完整个 required term。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_first_token_repair.py`
  - 主流程，读取 v506、选择 repair target、执行 constrained generation、生成 interpretation。
- `src/minigpt/model_capability_required_term_pair_first_token_repair_components.py`
  - 负责选择 first-token miss rows、按 profile 汇总 repaired hit、生成 summary。
- `src/minigpt/model_capability_required_term_pair_first_token_repair_artifacts.py`
  - 负责 JSON/CSV/text/Markdown/HTML 输出。
- `scripts/run_model_capability_required_term_pair_first_token_repair.py`
  - CLI 入口，支持输入 v506 JSON 或目录。
- `tests/test_model_capability_required_term_pair_first_token_repair.py`
  - 覆盖 full expression、partial improvement、输入失败、target selection 和 profile summary。

## 核心数据结构

`repair_rows` 一行代表一个 v506 probe 的 constrained generation 结果：

- `profile_id`
- `prompt_term`
- `expected_term`
- `source_continuation_hit`
- `forced_first_token_id`
- `forced_first_token_text`
- `repaired_continuation`
- `repaired_continuation_hit`
- `repaired_continuation_preview`

`profile_summaries` 聚合 profile 层表现：

- `repaired_hit_count`
- `repaired_profile_full_hit`
- `hit_terms`
- `missed_terms`

## 核心函数流程

`build_model_capability_required_term_pair_first_token_repair()` 是主入口。

1. 读取 v506 path trace report。
2. `select_first_token_repair_targets()` 选择 `first_sample_matches_expected_first_token=False` 且有 `first_expected_token_id` 的 rows。
3. `_repair_with_checkpoint()` 加载原 checkpoint/tokenizer。
4. 把 prompt token ids 后面直接接上 `first_expected_token_id`。
5. 用原 profile 的剩余 token budget 继续生成。
6. 判断 repaired continuation 是否包含 expected term。
7. 汇总 prompt/profile/overall 结果。

## 真实结果解释

真实运行结果：

- `source_continuation_hit_count=2`
- `repaired_continuation_hit_count=3`
- `improved_prompt_count=2`
- `repaired_profile_full_hit_count=0`

这说明 first-token repair 是有效信号，但不是完整解决方案。`loss` 被强制 `l` 后更容易走向 `loss`，但 `fixed` 仍可能变成 `fidddfix...` 这类不稳定 continuation。问题已经从“第一 token 是否能开始”推进到“完整 required term span 是否能稳定完成”。

## 输出证据

v507 输出位置：

```text
e/507/解释/model-capability-required-term-pair-first-token-repair/
```

截图和解释归档在：

```text
e/507/图片
e/507/解释/说明.md
```

## 测试覆盖

测试覆盖：

- fake repair 同时命中 `fixed/loss` 时，decision 为 full expression。
- fake repair 只改善一个 prompt 时，decision 为 improved partial。
- 无 repair target 时，报告失败。
- profile summary 正确识别 missed terms 和 full-hit 状态。
- 多格式 artifact 输出完整。

## 一句话总结

v507 证明第一 token 修复只能带来局部改善，当前 tiny checkpoint 还缺少稳定生成完整 required term span 的能力。
