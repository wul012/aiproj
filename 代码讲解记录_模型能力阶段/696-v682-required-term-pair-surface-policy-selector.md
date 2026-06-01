# v682 required-term pair surface policy selector

## 本版目标和边界

v682 的目标是在 v681 找到的多个稳定 policy 中选择一个更小、更可维护、更少绑定训练措辞的候选，作为下一步 minimality/leakage 检查对象。

本版不跑模型、不训练、不改变 replay 结果。它是一个选择器和约束层，防止“谁稳定就直接推广”的过度结论。

## 前置链路

v681 显示：

- `dual_boundary_sentence`: 三 seed pair-full。
- `pair_context_prefix`: 三 seed pair-full。

两个 policy 都稳定，但它们并不等价：

- `dual_boundary_sentence` 更长，并直接复用训练 corpus 的边界措辞。
- `pair_context_prefix` 更短，只提供另一个 term 的上下文锚点。

v682 选择更小的候选进入下一步。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_surface_policy_selector.py`
  - 读取 plan 与 replay。
  - 组合 replay summary 与 policy metadata。
  - 计算 leakage rank、prompt length、是否使用 boundary sentence。
  - 选择稳定且更小的 policy。

- `src/minigpt/model_capability_required_term_pair_surface_policy_selector_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML。

- `scripts/run_model_capability_required_term_pair_surface_policy_selector.py`
  - CLI 入口。

- `tests/test_model_capability_required_term_pair_surface_policy_selector.py`
  - 覆盖稳定候选选择、无稳定候选失败、输出格式。

## 选择规则

选择顺序：

1. 必须 `stable_pair_full=True`。
2. 按 `leakage_rank` 从低到高排序。
3. 避免 `uses_boundary_sentence=True`。
4. prompt template 更短优先。

这使得 `pair_context_prefix` 胜过 `dual_boundary_sentence`。

## 本版结果

- `selected_policy_id=pair_context_prefix`
- `selected_leakage_level=contextual_anchor`
- `selected_uses_boundary_sentence=False`
- `promotion_ready=False`

选择器明确保留边界：这是 decoding-surface policy 候选，不是模型能力推广。

## 测试与证据

验证命令：

```powershell
python -m py_compile src\minigpt\model_capability_required_term_pair_surface_policy_selector.py src\minigpt\model_capability_required_term_pair_surface_policy_selector_artifacts.py scripts\run_model_capability_required_term_pair_surface_policy_selector.py tests\test_model_capability_required_term_pair_surface_policy_selector.py
python -m pytest tests\test_model_capability_required_term_pair_surface_policy_selector.py -q -o cache_dir=runs\pytest-cache-v682
```

运行证据：

- JSON/CSV/text/Markdown/HTML: `e/682/解释/model-capability-required-term-pair-surface-policy-selector/`
- 截图: `e/682/图片/v682-surface-policy-selector.png`
- 解释: `e/682/解释/说明.md`

一句话总结：v682 把 surface policy 从“多个稳定候选”收敛到更小的 `pair_context_prefix`，并阻止过早推广。
