# v688 required-term pair surface variant replay

## 本版目标和边界

v688 的目标是执行 v687 的 surface variant plan，用真实 checkpoint generation 检查 `pair_context_prefix_budget_8` 是否对 separator 和轻量措辞变化稳定。

本版不训练，不改 corpus，不改变 v684 的风险边界。它只证明 contextual surface policy 的变体鲁棒性，不证明 minimal prompt baseline。

## 前置链路

- v676：三颗 dual-boundary seed checkpoint。
- v686：执行 profile `pair_context_prefix_budget_8`。
- v687：5 个 surface variant 计划。

v688 将 v687 的计划转成 v681 replay builder 能消费的 policy rows，然后运行真实 generation。

## 关键文件

### `src/minigpt/model_capability_required_term_pair_surface_variant_replay.py`

核心函数 `build_surface_variant_replay()` 做四步：

1. 读取 seed stability 和 variant plan。
2. 把 `variant_rows` 转成 replay policy rows，其中 `policy_id` 使用 `variant_id`。
3. 调用 v681 的 `build_model_capability_required_term_pair_surface_policy_replay()`，复用已有 checkpoint loading、prompt formatting 和 generation logic。
4. 将底层 `policy_summaries` 改写成 `variant_summaries`，并生成本版 summary。

核心字段：

- `settings.max_new_tokens`：来自 v687/v686 的最小稳定 budget，真实运行为 `8`。
- `variant_summaries`：每个变体的 seed 数、hit case 数、pair-full seed 数和稳定状态。
- `case_rows`：30 个真实 generation case。
- `summary.stable_variant_ids`：真实运行中 5 个变体全部稳定。
- `interpretation.model_quality_claim`：`contextual_surface_variant_stable`。

### `scripts/run_model_capability_required_term_pair_surface_variant_replay.py`

CLI 输入：

```text
stability variant_plan
```

它会定位正式 JSON、执行 replay、写出 JSON/CSV/text/Markdown/HTML 五件套。这个脚本调用真实 generator，不是只读汇总。

### `tests/test_model_capability_required_term_pair_surface_variant_replay.py`

测试用 fake checkpoint/tokenizer 和 fake generator 覆盖：

- 部分 variant 稳定时，能正确产生 `partial_stability` 决策。
- source plan 失败时，report 失败。
- 五种输出格式都能渲染。

测试保护的是 replay 汇总和输出契约；真实模型证据来自本版归档运行。

## 真实运行证据

命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_surface_variant_replay.py e\676\解释\model-capability-required-term-pair-dual-boundary-seed-stability e\687\解释\model-capability-required-term-pair-surface-variant-plan --out-dir e\688\解释\model-capability-required-term-pair-surface-variant-replay --device cpu --require-pass --force
```

结果：

- `status=pass`
- `decision=required_term_pair_surface_variant_replay_all_variants_stable`
- `variant_count=5`
- `stable_variant_count=5`
- `stable_variant_ids=['compact_context', 'newline_context', 'semicolon_context', 'space_context_control', 'worded_context']`
- `max_new_tokens=8`
- `model_quality_claim=contextual_surface_variant_stable`

这次 replay 一共运行 30 个真实 generation case：5 个 variant × 3 个 seed × 2 个 term。

截图：

- `e/688/图片/v688-surface-variant-replay.png`

说明：

- `e/688/解释/说明.md`

## 结论边界

v688 证明的是 contextual surface variant 稳定性。由于所有 variant 都包含另一个 term 作为上下文锚点，本版不能推翻 v684 的风险结论，也不能改写成 promoted model baseline。

更准确的说法是：`pair_context_prefix_budget_8` 对几种上下文表面形式有稳定性，后续可以选择一个偏好的展示 variant，但必须保留 `contextual_decode_*` 口径。

## 验证

```powershell
python -m py_compile src\minigpt\model_capability_required_term_pair_surface_variant_replay.py scripts\run_model_capability_required_term_pair_surface_variant_replay.py tests\test_model_capability_required_term_pair_surface_variant_replay.py
python -m pytest tests\test_model_capability_required_term_pair_surface_variant_replay.py -q -o cache_dir=runs\pytest-cache-v688
```

结果：

- `py_compile` 通过。
- `3 passed in 0.13s`。

## 一句话总结

v688 用 30 个真实 generation case 证明 `pair_context_prefix_budget_8` 的五个 contextual surface 变体全部稳定，同时保留“不晋升为无上下文 baseline”的边界。
