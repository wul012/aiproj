# v686 required-term pair surface policy execution profile

## 本版目标和边界

v686 的目标是把 v684 的 leakage-risk 结论和 v685 的 budget sweep 结论合并成一个可执行 profile。前面已经知道 `pair_context_prefix` 有 contextual-anchor 风险，也知道最小稳定 budget 是 8；v686 把这两个条件写成机器可读配置，供后续 surface variant replay 直接消费。

本版不重新跑 generation，不训练 checkpoint，不改变 promotion 边界。它的产物是 profile，不是模型质量晋升。

## 前置链路

- v684：`risk_level=medium`，`promotion_allowed=False`，`model_quality_claim=contextual_decode_policy_only`。
- v685：`stable_budgets=[8, 12, 16]`，`minimal_stable_budget=8`。

这两份证据分别回答“能不能宣传成 baseline”和“最少给多少 token 才稳定”。v686 把它们合并，避免后续脚本散落复制这些判断。

## 关键文件

### `src/minigpt/model_capability_required_term_pair_surface_policy_execution_profile.py`

核心函数是 `build_surface_policy_execution_profile()`。它读取 leakage report 和 budget report，检查：

- 两个 source report 都是 `status=pass`。
- leakage report 仍然阻止 promotion。
- budget report 有 selected policy。
- budget report 有 `minimal_stable_budget`。

通过后生成 `profile` 字段：

- `profile_id`：真实运行是 `pair_context_prefix_budget_8`。
- `policy_id`：`pair_context_prefix`。
- `prompt_template`：`{other_term}={other_term} {term}=`
- `max_new_tokens`：`8`。
- `temperature`：`0.2`。
- `top_k`：`1`。
- `leakage_level`：`contextual_anchor`。
- `risk_level`：`medium`。
- `allowed_use`：`contextual_decode_surface_variant_replay`。
- `promotion_allowed`：`False`。

这个结构让后续 variant replay 不需要重新猜 budget，也不会丢掉风险边界。

### `scripts/run_model_capability_required_term_pair_surface_policy_execution_profile.py`

CLI 接收两个输入：

```text
leakage budget
```

两者都支持目录或 JSON 文件。脚本会定位正式 JSON、调用 builder、写出 JSON/CSV/text/Markdown/HTML 五件套，并按 `--require-pass` 返回退出码。

### `tests/test_model_capability_required_term_pair_surface_policy_execution_profile.py`

测试覆盖：

- 正常输入会生成 `pair_context_prefix_budget_8`。
- 缺少 minimal stable budget 会失败，防止后续生成一个没有稳定依据的 profile。
- 五种输出格式都能渲染。

## 真实运行证据

命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_surface_policy_execution_profile.py e\684\解释\model-capability-required-term-pair-surface-policy-leakage-risk e\685\解释\model-capability-required-term-pair-surface-policy-budget-sweep --out-dir e\686\解释\model-capability-required-term-pair-surface-policy-execution-profile --require-pass --force
```

输出：

- `status=pass`
- `decision=required_term_pair_surface_policy_execution_profile_selected`
- `profile_id=pair_context_prefix_budget_8`
- `max_new_tokens=8`
- `promotion_allowed=False`
- `model_quality_claim=contextual_decode_execution_profile`

截图：

- `e/686/图片/v686-surface-policy-execution-profile.png`

说明：

- `e/686/解释/说明.md`

## 这版为什么必要

如果直接从 v685 跳到 variant replay，后续脚本需要自己知道“应该用 budget 8、不能 promotion、allowed use 是 surface variant replay”。这些信息散在 v684 和 v685 中，容易被复制错或省略。v686 把它们合成一个明确 profile，后面只读这一个入口。

## 验证

```powershell
python -m py_compile src\minigpt\model_capability_required_term_pair_surface_policy_execution_profile.py scripts\run_model_capability_required_term_pair_surface_policy_execution_profile.py tests\test_model_capability_required_term_pair_surface_policy_execution_profile.py
python -m pytest tests\test_model_capability_required_term_pair_surface_policy_execution_profile.py -q -o cache_dir=runs\pytest-cache-v686
```

结果：

- `py_compile` 通过。
- `3 passed in 0.08s`。

## 一句话总结

v686 把 `pair_context_prefix + budget 8 + no promotion` 固化成执行 profile，让后续 surface variant replay 有了可复用且不越界的入口。
