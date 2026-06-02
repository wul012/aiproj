# v689 required-term pair surface variant selector

## 本版目标和边界

v689 的目标是在 v688 全稳定的五个 contextual surface 变体中选出一个推荐默认项。它解决的是工程使用问题：如果所有变体都稳定，后续 demo、对比和 closeout 应该引用哪一个，而不是一直携带 5 个并列选项。

本版不训练、不生成、不改变 v684 的 leakage-risk 边界。选择结果仍然是 contextual demo variant，不是 promoted model baseline。

## 前置链路

- v687 定义 5 个 surface 变体。
- v688 用 30 个真实 generation case 证明 5 个变体全部稳定。

v689 从这两份证据中做排序选择。

## 关键文件

### `src/minigpt/model_capability_required_term_pair_surface_variant_selector.py`

核心函数 `build_surface_variant_selector()`：

1. 读取 variant plan 和 variant replay。
2. 将 plan 中的模板、separator style 与 replay 中的稳定性合并。
3. 计算 selection score。
4. 选择稳定、可读、与原 profile 一致的默认 variant。

候选行字段：

- `variant_id`
- `prompt_template`
- `separator_style`
- `stable_pair_full`
- `pair_full_seed_count`
- `hit_case_count`
- `style_rank`
- `selection_score`
- `selection_reason`

排序思路：

- 不稳定候选直接排除。
- `space` style 优先，因为它和 v686 原 profile 一致。
- `semicolon`、`newline` 可作为备选。
- `worded` 虽然稳定，但引入额外指令措辞。
- `compact` 虽然稳定，但标签融合，不利于可读性。

真实选择是 `space_context_control`。

### `scripts/run_model_capability_required_term_pair_surface_variant_selector.py`

CLI 输入：

```text
variant_plan variant_replay
```

输出 JSON/CSV/text/Markdown/HTML 五件套，并支持 `--require-pass`。

### `tests/test_model_capability_required_term_pair_surface_variant_selector.py`

测试覆盖：

- 当 compact 和 space 都稳定时，优先选择 `space_context_control`。
- 没有稳定 variant 时，报告失败。
- 五种输出格式正常渲染。

## 真实运行证据

命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_surface_variant_selector.py e\687\解释\model-capability-required-term-pair-surface-variant-plan e\688\解释\model-capability-required-term-pair-surface-variant-replay --out-dir e\689\解释\model-capability-required-term-pair-surface-variant-selector --require-pass --force
```

输出：

- `status=pass`
- `decision=required_term_pair_surface_variant_selected_for_contextual_demo`
- `selected_variant_id=space_context_control`
- `stable_variant_count=5`
- `promotion_allowed=False`
- `model_quality_claim=contextual_surface_variant_selected`

截图：

- `e/689/图片/v689-surface-variant-selector.png`

说明：

- `e/689/解释/说明.md`

## 为什么选 space control

全稳定时，选择默认项要考虑可维护性和后续表达。`space_context_control` 与 v686 profile 完全一致，模板短、可读、没有额外自然语言提示，也不把标签挤在一起。它是最适合作为后续对比入口的 conservative default。

## 验证

```powershell
python -m py_compile src\minigpt\model_capability_required_term_pair_surface_variant_selector.py scripts\run_model_capability_required_term_pair_surface_variant_selector.py tests\test_model_capability_required_term_pair_surface_variant_selector.py
python -m pytest tests\test_model_capability_required_term_pair_surface_variant_selector.py -q -o cache_dir=runs\pytest-cache-v689
```

结果：

- `py_compile` 通过。
- `3 passed in 0.14s`。

## 一句话总结

v689 把五个全稳定 contextual variants 收敛为 `space_context_control` 默认项，让后续对比和展示有一个稳定、简洁、不过度声明的入口。
