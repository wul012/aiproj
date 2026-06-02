# v690 required-term pair surface baseline contrast

## 本版目标和边界

v690 的目标是把 contextual variant 成功和 non-leaking baseline 失败放在一张机器可读对照表里。v688 已经证明五个 contextual surface 变体全部稳定，v689 也选出了 `space_context_control`。但如果只看这些结论，很容易误以为 minimal prompt 或 non-leaking baseline 也已经稳定。

本版不训练、不生成、不改 selected variant。它只做 evidence contrast，明确上下文锚点仍然必需。

## 前置链路

- v681：surface policy replay，包含 `single_label_default` 和 `single_label_suppress_newline` 两个 non-leaking baseline。
- v689：surface variant selector，选择 `space_context_control` 作为默认 contextual variant。

v690 把两份证据合并，回答“推荐 variant 的成功是否可以替代 non-leaking baseline”。

## 关键文件

### `src/minigpt/model_capability_required_term_pair_surface_baseline_contrast.py`

核心函数 `build_surface_baseline_contrast()`：

1. 从 v689 selector 中取 `selected_variant`。
2. 从 v681 replay 中取所有 `policy_id` 以 `single_label` 开头的 non-leaking baselines。
3. 生成 `contrast_rows`。
4. 汇总 contextual 是否稳定、non-leaking baseline 数量、稳定 baseline 数量。

核心字段：

- `contrast_rows`：对照行，区分 `selected_contextual_variant` 和 `non_leaking_baseline`。
- `summary.contextual_stable`：推荐 contextual variant 是否稳定。
- `summary.non_leaking_baseline_count`：non-leaking baseline 数量。
- `summary.stable_non_leaking_baseline_count`：稳定 non-leaking baseline 数量。
- `summary.contextual_anchor_required`：当前真实运行是 `True`。
- `interpretation.model_quality_claim`：`contextual_anchor_required_for_surface_stability`。

### `scripts/run_model_capability_required_term_pair_surface_baseline_contrast.py`

CLI 输入：

```text
policy_replay variant_selector
```

输出 JSON/CSV/text/Markdown/HTML 五件套，并支持 `--require-pass`。

### `tests/test_model_capability_required_term_pair_surface_baseline_contrast.py`

测试覆盖：

- contextual 稳定且 non-leaking baseline 不稳定时，判定 `contextual_anchor_required=True`。
- 缺少 non-leaking baseline 时失败，防止对照表只剩单边证据。
- 五种输出格式正常渲染。

## 真实运行证据

命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_surface_baseline_contrast.py e\681\解释\model-capability-required-term-pair-surface-policy-replay e\689\解释\model-capability-required-term-pair-surface-variant-selector --out-dir e\690\解释\model-capability-required-term-pair-surface-baseline-contrast --require-pass --force
```

结果：

- `status=pass`
- `decision=required_term_pair_contextual_variant_needed_over_non_leaking_baselines`
- `contextual_stable=True`
- `non_leaking_baseline_count=2`
- `stable_non_leaking_baseline_count=0`
- `contextual_anchor_required=True`
- `model_quality_claim=contextual_anchor_required_for_surface_stability`

截图：

- `e/690/图片/v690-surface-baseline-contrast.png`

说明：

- `e/690/解释/说明.md`

## 结论边界

v690 是本批次的关键边界版本。它承认 v688 的多 surface 稳定是有效进展，但也明确这条进展依赖 contextual anchor。后续如果要追求真正的 minimal prompt model capability，需要新 objective，而不是把当前 decode aid promotion。

## 验证

```powershell
python -m py_compile src\minigpt\model_capability_required_term_pair_surface_baseline_contrast.py scripts\run_model_capability_required_term_pair_surface_baseline_contrast.py tests\test_model_capability_required_term_pair_surface_baseline_contrast.py
python -m pytest tests\test_model_capability_required_term_pair_surface_baseline_contrast.py -q -o cache_dir=runs\pytest-cache-v690
```

结果：

- `py_compile` 通过。
- `3 passed in 0.14s`。

## 一句话总结

v690 证明当前成功仍是 contextual anchor 成功，而不是 non-leaking baseline 成功，为后续分支收口提供了清晰边界。
