# v683 required-term pair surface policy minimality check

## 本版目标和边界

v683 的目标是检查 v682 选出的 `pair_context_prefix` 是否足够“最小”，或者它只是一个需要额外说明的 contextual decoding aid。

本版不跑模型、不训练、不改 selector。它只将 selector 与 replay 的证据做规则化检查，避免稳定 policy 被过度解释。

## 前置链路

v681 replay 显示：

- `pair_context_prefix` 三 seed pair-full。
- `dual_boundary_sentence` 三 seed pair-full。
- `single_label_*` 非泄漏 baseline 不稳定。

v682 selector 选择：

- `selected_policy_id=pair_context_prefix`
- `selected_leakage_level=contextual_anchor`
- `promotion_ready=False`

v683 检查这三个事实是否一致。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_surface_policy_minimality_check.py`
  - 读取 selector 与 replay。
  - 检查 selected policy 是否存在、是否稳定、非泄漏 baseline 是否不稳定、是否仍阻止 promotion。

- `src/minigpt/model_capability_required_term_pair_surface_policy_minimality_check_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML。

- `scripts/run_model_capability_required_term_pair_surface_policy_minimality_check.py`
  - CLI 入口。

- `tests/test_model_capability_required_term_pair_surface_policy_minimality_check.py`
  - 覆盖 contextual anchor required、selected policy 不稳定时失败、输出格式。

## 检查项语义

- `selected_policy_present`: selector 必须真的选出 policy。
- `selected_policy_stable`: 被选 policy 必须在 replay 中稳定。
- `non_leaking_baseline_not_stable`: 非泄漏 baseline 不稳定，因此上下文锚点仍必要。
- `selected_policy_contextual_anchor`: selected policy 必须被标记为 contextual anchor。
- `promotion_blocked`: selector 必须阻止直接推广。

## 本版结果

所有检查通过：

- `contextual_anchor_required=True`
- `promotion_ready=False`
- `decision=required_term_pair_surface_policy_contextual_anchor_required`

这说明 `pair_context_prefix` 是可用的解码辅助，但它不是模型在最小 prompt 下的稳定能力。

## 测试与证据

验证命令：

```powershell
python -m py_compile src\minigpt\model_capability_required_term_pair_surface_policy_minimality_check.py src\minigpt\model_capability_required_term_pair_surface_policy_minimality_check_artifacts.py scripts\run_model_capability_required_term_pair_surface_policy_minimality_check.py tests\test_model_capability_required_term_pair_surface_policy_minimality_check.py
python -m pytest tests\test_model_capability_required_term_pair_surface_policy_minimality_check.py -q -o cache_dir=runs\pytest-cache-v683
```

运行证据：

- JSON/CSV/text/Markdown/HTML: `e/683/解释/model-capability-required-term-pair-surface-policy-minimality-check/`
- 截图: `e/683/图片/v683-surface-policy-minimality-check.png`
- 解释: `e/683/解释/说明.md`

一句话总结：v683 把 `pair_context_prefix` 的能力边界定义为“上下文解码辅助”，而不是“最小提示稳定能力”。
