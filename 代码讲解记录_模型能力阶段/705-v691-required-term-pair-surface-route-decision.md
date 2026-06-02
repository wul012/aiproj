# v691 required-term pair surface route decision

## 本版目标和边界

v691 的目标是对 v679-v690 的 surface policy 分支做路线决策。前面已经证明 `pair_context_prefix_budget_8` 及其五个变体都稳定，但 v690 也证明 non-leaking baseline 仍不稳定。因此当前分支应该作为 contextual decode aid 收口，而不是继续扩展 surface 变体或 promotion。

本版不训练、不生成、不新增模型证据。它把已有证据转成下一步路线。

## 前置链路

- v689：选择 `space_context_control` 作为默认 contextual variant。
- v690：证明 contextual anchor 仍然必需，non-leaking baseline 稳定数为 0。

v691 只在这两个事实上做决策。

## 关键文件

### `src/minigpt/model_capability_required_term_pair_surface_route_decision.py`

核心函数 `build_surface_route_decision()`：

1. 读取 baseline contrast 和 variant selector。
2. 检查 baseline contrast 是否证明 `contextual_anchor_required=True`。
3. 检查 selector 是否有 selected variant。
4. 输出 route。

核心 route 字段：

- `selected_variant_id`：`space_context_control`
- `current_route`：`contextual_decode_aid_closeout`
- `recommended_next_route`：`minimal_prompt_surface_objective`
- `allowed_use`：`demo_and_diagnostic_contextual_decode`
- `blocked_use`：`baseline_promotion_or_minimal_prompt_claim`
- `promotion_allowed`：`False`

这里的 `recommended_next_route` 不是立即执行的新训练，而是明确如果用户/项目还要追模型能力，应从 minimal-prompt objective 重新设计，而不是继续在 contextual variants 上堆报告。

### `scripts/run_model_capability_required_term_pair_surface_route_decision.py`

CLI 输入：

```text
baseline_contrast variant_selector
```

输出 JSON/CSV/text/Markdown/HTML 五件套，并支持 `--require-pass`。

### `tests/test_model_capability_required_term_pair_surface_route_decision.py`

测试覆盖：

- anchor-required 证据存在时，决策为关闭 contextual 分支并设计 minimal-prompt objective。
- 如果 contrast 没有证明 anchor-required，报告失败，避免无边界收口。
- 五种输出格式正常渲染。

## 真实运行证据

命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_surface_route_decision.py e\690\解释\model-capability-required-term-pair-surface-baseline-contrast e\689\解释\model-capability-required-term-pair-surface-variant-selector --out-dir e\691\解释\model-capability-required-term-pair-surface-route-decision --require-pass --force
```

结果：

- `status=pass`
- `decision=close_contextual_decode_branch_and_design_minimal_prompt_objective`
- `selected_variant_id=space_context_control`
- `current_route=contextual_decode_aid_closeout`
- `recommended_next_route=minimal_prompt_surface_objective`
- `promotion_allowed=False`
- `model_quality_claim=contextual_decode_aid_not_baseline`

截图：

- `e/691/图片/v691-surface-route-decision.png`

说明：

- `e/691/解释/说明.md`

## 路线含义

v691 的结论很克制：当前成果有用，可以服务 demo 和诊断；但它不是 tiny GPT 自然掌握 fixed/loss 的证据。如果继续追能力，下一步要设计新 objective，让 minimal prompt 或 non-leaking surface 自己稳定。

## 验证

```powershell
python -m py_compile src\minigpt\model_capability_required_term_pair_surface_route_decision.py scripts\run_model_capability_required_term_pair_surface_route_decision.py tests\test_model_capability_required_term_pair_surface_route_decision.py
python -m pytest tests\test_model_capability_required_term_pair_surface_route_decision.py -q -o cache_dir=runs\pytest-cache-v691
```

结果：

- `py_compile` 通过。
- `3 passed in 0.12s`。

## 一句话总结

v691 把当前 surface policy 分支收口为 contextual decode aid，并把真正的模型能力后续路线指向 minimal-prompt objective。
