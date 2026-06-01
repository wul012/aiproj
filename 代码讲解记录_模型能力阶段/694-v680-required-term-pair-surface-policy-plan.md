# v680 required-term pair surface policy plan

## 本版目标和边界

v680 的目标是把 v679 发现的 `loss` surface failure 转成一组明确、可审计的 generation-surface policy 候选。

本版不运行模型，不做训练，不给模型能力提升结论。它只是防止下一版 replay 随意挑 prompt，尤其防止把 prompt 中直接写出答案的策略误当成模型能力。

## 前置链路

v679 结论：

- seed `2535` 是唯一 surface failure seed。
- failure term 是 `loss`。
- forced-choice internal pair match 已经通过。

因此 v680 要回答的是：下一版应该 replay 哪些 policy，哪些 policy 只应记录为上界或排除项。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_surface_policy_plan.py`
  - 读取 surface failure diagnostic。
  - 生成 policy rows。
  - 计算 replay policy、non-leaking policy、contextual anchor policy 和 excluded upper-bound。

- `src/minigpt/model_capability_required_term_pair_surface_policy_plan_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML。
  - HTML 表展示 prompt template、generation profile、leakage level 和是否进入 replay。

- `scripts/run_model_capability_required_term_pair_surface_policy_plan.py`
  - CLI 入口，支持目录或 JSON 输入。

- `tests/test_model_capability_required_term_pair_surface_policy_plan.py`
  - 覆盖正常 plan、无 failure 的失败输入、所有输出格式。

## policy 字段语义

- `policy_id`: policy 稳定标识。
- `prompt_template`: replay 时用于生成 prompt 的模板。
- `generation_profile`: 使用的 server generation profile。
- `leakage_level`: 是否泄漏答案。
- `replay_scope`: 该 policy 属于 baseline、decode hygiene、contextual anchor 还是 upper-bound。
- `included_in_replay`: 是否进入下一版真实 replay。
- `purpose`: 为什么要保留这个 policy。

## 本版结果

v680 生成 5 个 policy，其中 4 个进入 replay：

- `single_label_default`
- `single_label_suppress_newline`
- `pair_context_prefix`
- `dual_boundary_sentence`

`target_echo_upper_bound` 被排除，因为它已经把 `{term}` 作为答案写进 prompt。

## 测试与证据

验证命令：

```powershell
python -m py_compile src\minigpt\model_capability_required_term_pair_surface_policy_plan.py src\minigpt\model_capability_required_term_pair_surface_policy_plan_artifacts.py scripts\run_model_capability_required_term_pair_surface_policy_plan.py tests\test_model_capability_required_term_pair_surface_policy_plan.py
python -m pytest tests\test_model_capability_required_term_pair_surface_policy_plan.py -q -o cache_dir=runs\pytest-cache-v680
```

运行证据：

- JSON/CSV/text/Markdown/HTML: `e/680/解释/model-capability-required-term-pair-surface-policy-plan/`
- 截图: `e/680/图片/v680-surface-policy-plan.png`
- 解释: `e/680/解释/说明.md`

一句话总结：v680 为 generation-surface replay 建立了可审计 policy 边界，避免后续把 target echo 当作能力提升。
