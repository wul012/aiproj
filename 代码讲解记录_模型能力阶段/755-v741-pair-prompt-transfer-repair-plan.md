# v741 pair prompt transfer repair plan

## 本版目标和边界

v741 的目标是把 v740 的 pair-probe replay 负结果转成下一步修复计划。

本版不训练、不生成 corpus、不修改 contract。它只做一件事：确认 v738 不能 promotion，并规划一个不泄漏 heldout pair prompt 的 contract patch。

## 前置链路

```text
v738 direct-completion surface training
 -> direct probes pair-full
v739 direct-completion route comparison
 -> selected as direct-probe candidate
v740 pair-probe replay
 -> exact heldout pair prompt not ready
v741 repair plan
 -> propose non-leaking pair prompt transfer contract patch
```

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_readiness_pair_prompt_transfer_repair_plan.py`
  - 读取 v740 pair-probe replay。
  - 检查 not-ready、exact pair failed、pair_full_count 为 0。
  - 输出 repair plan。
- `src/minigpt/model_capability_required_term_pair_readiness_pair_prompt_transfer_repair_plan_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
- `scripts/run_model_capability_required_term_pair_readiness_pair_prompt_transfer_repair_plan.py`
  - CLI 入口。
- `tests/test_model_capability_required_term_pair_readiness_pair_prompt_transfer_repair_plan.py`
  - 覆盖 ready、错误输入失败、五格式输出。

## 核心检查

v741 的检查项：

```text
pair_probe_replay_passed
pair_probe_not_ready
exact_pair_failed
no_pair_prompt_full
heldout_pair_remains_heldout
```

这些检查保证计划只来自真实的 v740 not-ready 证据，而不是在 pair-probe 已经 ready 的情况下继续盲目 patch。

## 计划内容

proposed next artifact：

```text
pair_readiness_pair_prompt_transfer_contract_patch
```

核心 repair requirements：

- 添加 surrogate pair-transfer rows，让 fixed/loss 在同一训练行里绑定。
- 覆盖多个非 heldout separator style，避免只贴合单一模板。
- 保留 `fixed=fixed` 和 `loss=loss` direct-completion rows。
- `fixed=|loss=` 继续作为 heldout pair prompt，不能出现在训练行或 materialized corpus 中。
- patch 后必须再跑 pair-probe replay，不能直接 promotion。

## 证据

运行输出：

```text
e/741/解释/model-capability-required-term-pair-readiness-pair-prompt-transfer-repair-plan/
```

截图：

```text
e/741/图片/v741-pair-prompt-transfer-repair-plan.png
```

截图可见：

- `Decision=pair_readiness_pair_prompt_transfer_repair_plan_ready`
- `Ready=True`
- `Next=pair_readiness_pair_prompt_transfer_contract_patch`
- `Requirements=5`

## 一句话总结

v741 把 direct-probe 正向但 pair-probe 失败的边界转成非泄漏修复计划，避免项目把未迁移的能力提前 promotion。
