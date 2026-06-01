# v687 required-term pair surface variant plan

## 本版目标和边界

v687 的目标是给 v688 的真实 replay 准备输入计划。v686 已经生成 `pair_context_prefix_budget_8`，但这个 profile 只验证了一个 prompt surface：`{other_term}={other_term} {term}=`。如果只用这个形式，无法判断策略是有一定表面鲁棒性，还是只对一个空格分隔模板有效。

本版不跑模型，不训练，不产出新的模型能力结论。它只生成 surface variant plan，明确下一版要测哪些 prompt 变体。

## 前置链路

- v684：确认 selected policy 有 contextual-anchor risk。
- v685：确认最小稳定 continuation budget 是 8。
- v686：合成执行 profile `pair_context_prefix_budget_8`。

v687 接在 profile 后面，围绕同一个 profile 派生变体。

## 关键文件

### `src/minigpt/model_capability_required_term_pair_surface_variant_plan.py`

核心函数是 `build_surface_variant_plan()`。它读取 execution profile，检查：

- source report 必须 `status=pass`。
- profile 必须存在。
- `promotion_allowed` 必须仍然是 `False`。
- `max_new_tokens` 必须存在。

通过后生成 `variant_rows`。每个 row 包含：

- `variant_id`：变体标识。
- `base_policy_id`：来源 policy，这里是 `pair_context_prefix`。
- `prompt_template`：后续 replay 使用的模板。
- `separator_style`：空格、分号、换行、紧凑、worded。
- `leakage_level`：固定为 `contextual_anchor`。
- `included_in_replay`：是否纳入下一版 replay。
- `rationale`：为什么要测这个变体。

本版计划的五个变体：

- `space_context_control`
- `semicolon_context`
- `newline_context`
- `compact_context`
- `worded_context`

### `scripts/run_model_capability_required_term_pair_surface_variant_plan.py`

CLI 输入一个 profile 目录或 JSON 文件，输出 JSON/CSV/text/Markdown/HTML 五件套。它不接 checkpoint，也不调用 generator。

### `tests/test_model_capability_required_term_pair_surface_variant_plan.py`

测试覆盖：

- 正常 profile 生成 5 个 included variants。
- 如果 profile 取消 promotion boundary，会失败。
- 五种输出格式都能渲染。

## 真实运行证据

命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_surface_variant_plan.py e\686\解释\model-capability-required-term-pair-surface-policy-execution-profile --out-dir e\687\解释\model-capability-required-term-pair-surface-variant-plan --require-pass --force
```

结果：

- `status=pass`
- `decision=required_term_pair_surface_variant_plan_ready`
- `variant_count=5`
- `included_variant_count=5`
- `max_new_tokens=8`
- `model_quality_claim=contextual_surface_variant_plan`

截图：

- `e/687/图片/v687-surface-variant-plan.png`

说明：

- `e/687/解释/说明.md`

## 为什么这版要单独存在

variant replay 会产生 5 个变体、3 个 seed、2 个 term，共 30 个真实 generation case。把变体计划单独成版，可以在 replay 前审计输入是否合理，也让后续失败时知道失败来自哪个 separator surface，而不是来自临时脚本里的隐式模板。

## 验证

```powershell
python -m py_compile src\minigpt\model_capability_required_term_pair_surface_variant_plan.py scripts\run_model_capability_required_term_pair_surface_variant_plan.py tests\test_model_capability_required_term_pair_surface_variant_plan.py
python -m pytest tests\test_model_capability_required_term_pair_surface_variant_plan.py -q -o cache_dir=runs\pytest-cache-v687
```

结果：

- `py_compile` 通过。
- `3 passed in 0.09s`。

## 一句话总结

v687 把 `pair_context_prefix_budget_8` 的 surface 鲁棒性问题转成五个明确变体，为 v688 的真实 replay 提供了可审计输入。
