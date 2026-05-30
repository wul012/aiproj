# v508 required-term pair prefix completion sweep 代码讲解

## 本版目标与边界

v508 接着 v507 的结果：强制第一个 token 只能局部改善，不能恢复 full-hit。于是本版不再只强制第一 token，而是逐步强制 expected term 的更长前缀，看模型从多长前缀开始能补完整 required term。

本版不训练、不改变 checkpoint、不做生产推理策略。它只是一个诊断：判断问题是否已经进入完整词 span completion。

## 前置链路

前置版本：

- v506 发现 expected first token 排名不低，但第一步采样没有稳定选中。
- v507 发现强制 first token 后，`loss` 改善明显，但 `fixed` 仍不稳。

v508 的问题是：如果强制更多 expected term 前缀，`fixed/loss` 各自需要多长前缀才能稳定出现。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_prefix_completion_sweep.py`
  - 主流程：读取 v506、执行 prefix-length sweep、生成 report。
- `src/minigpt/model_capability_required_term_pair_prefix_completion_sweep_components.py`
  - 纯数据逻辑：选择 probe rows、按 prompt/profile 汇总最小命中前缀。
- `src/minigpt/model_capability_required_term_pair_prefix_completion_sweep_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
- `scripts/run_model_capability_required_term_pair_prefix_completion_sweep.py`
  - CLI 入口，支持输入 v506 JSON 或目录。
- `tests/test_model_capability_required_term_pair_prefix_completion_sweep.py`
  - 覆盖 long-prefix、one-token、输入失败、summary 和 artifact 输出。

## 核心数据结构

`prefix_rows` 一行代表一个 profile/prompt/prefix length 的 forced-prefix generation：

- `profile_id`
- `prompt_term`
- `expected_term`
- `expected_token_count`
- `forced_prefix_token_count`
- `forced_prefix_text`
- `completion`
- `completion_preview`
- `prefix_completion_hit`

`probe_summaries` 汇总每个 profile/prompt 的最小命中前缀：

- `expected_token_count`
- `tested_prefix_count`
- `hit_prefix_count`
- `minimum_hit_prefix_token_count`
- `one_token_prefix_hit`
- `full_prefix_hit`

## 核心函数流程

`build_model_capability_required_term_pair_prefix_completion_sweep()` 是主入口。

1. 读取 v506 path trace report。
2. `select_prefix_completion_targets()` 选择有 checkpoint/tokenizer/expected term 的 probe rows。
3. `_sweep_with_checkpoint()` 加载 checkpoint 和 tokenizer。
4. 对 expected term 的 token ids 从 prefix length 1 到完整长度逐个强制。
5. 继续生成剩余 token budget。
6. 判断 continuation 是否包含 expected term。
7. 汇总最小命中前缀和整体 decision。

## 真实结果解释

真实结果：

- `prefix_row_count=27`
- `probe_summary_count=6`
- `one_token_prefix_hit_probe_count=3`
- `full_prefix_hit_probe_count=6`
- `span_completion_gap_probe_count=3`

按词看：

- `loss`：三个 profile 都是一 token 前缀即可补全。
- `fixed`：三个 profile 都需要 4/5 token 前缀才命中。

这说明当前 tiny checkpoint 对 `loss` 的 span completion 比 `fixed` 更容易，`fixed` 不是只缺第一 token，而是缺稳定的完整词 span 续写。

## 输出证据

v508 输出位置：

```text
e/508/解释/model-capability-required-term-pair-prefix-completion-sweep/
```

截图和说明归档在：

```text
e/508/图片
e/508/解释/说明.md
```

## 测试覆盖

测试覆盖：

- 需要长前缀才能命中时，decision 为 `required_term_pair_prefix_completion_long_prefix`。
- 一 token 前缀即可命中时，decision 为 `required_term_pair_prefix_completion_one_token`。
- 无 prefix target 时报告失败。
- summary 正确计算 minimum hit prefix。
- 多格式 artifact 输出完整。

## 一句话总结

v508 证明当前问题已经从第一 token 采样推进到完整词 span completion：`fixed` 需要接近完整前缀，`loss` 则容易补全。
