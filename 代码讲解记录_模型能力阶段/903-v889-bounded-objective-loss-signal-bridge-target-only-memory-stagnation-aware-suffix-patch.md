# v889 stagnation-aware suffix patch 代码讲解

## 本版目标和边界

v889 承接 v888 repair plan，把计划中的五类动作落成 patch corpus。v887 证明 v885 训练只有 surface formatting 变化，没有 contract gain；v888 把这个结论转成修复计划；v889 则把计划变成可以训练的语料补丁。

本版不训练模型，不做 replay，不声称能力提升。它只是给下一版训练提供更有针对性的 no-anchor corpus。

## 关键文件

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_patch.py`
  - 读取 v888 repair plan 和 source corpus。
  - 生成 exact contract prompt、suffix bridge、surface format、ratio 和 verification gate 样本。
- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_patch_artifacts.py`
  - 写出 JSON、CSV、JSONL、corpus、TXT、Markdown、HTML。
- `scripts/build_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_patch.py`
  - CLI 入口，接收 repair plan 和 source corpus。
- `tests/test_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_patch.py`
  - 覆盖 patch ready、plan not ready、输出和 CLI wiring。

## 核心样本结构

v889 固定三条 unchanged contract surface：

```text
canonical_direct_completion -> Answer with exactly two tokens: fixed loss\nanswer:
minimal_direct_completion -> Answer with exactly two words: fixed loss\nanswer:
completion_label_surface -> Complete with exactly two tokens: fixed loss\ncompletion:
```

每条 surface 生成六类样本：

- 空格 exact completion：`prompt + " fixed loss"`。
- 换行 exact completion：`prompt + "\nfixed loss"`。
- `fixed l` 后接 `loss` 的空格版本。
- `fixed l` 后接 `loss` 的换行版本。
- `fixed lo` 后接 `loss` 的空格版本。
- `fixed lo` 后接 `loss` 的换行版本。

此外还加入全局 surface-format 样本和 suffix-ratio 样本，并保留一条 verification gate 文本，提醒 sample success 不能替代 replay recovery。

## 本版真实结果

真实 v889 输出：

```text
patch_example_count=27
replay_prompt_boundary_example_count=6
suffix_position_example_count=12
surface_format_example_count=4
training_corpus_ratio_example_count=4
decoder_anchor_example_count=0
```

suffix 相关样本一共 16 条，surface-format 样本 4 条，满足 suffix 样本占优的计划要求。

## 测试覆盖

测试保护这些条件：

- 合法 v888 plan 能生成 27 条 patch examples。
- 三条 contract surface 都被覆盖。
- suffix-position、surface-format、training-ratio 和 replay-boundary 计数符合预期。
- plan ready 被置 false 时 patch 失败。
- JSON、CSV、JSONL、corpus、TXT、Markdown、HTML 都能写出。

## 一句话总结

v889 把 no-contract-gain 诊断后的修复计划变成一个更贴近 unchanged contract prompt 的 no-anchor suffix patch corpus。
