# v735 bridge closeout plan

## 本版目标和边界

v735 的目标是把 v734 bridge comparison 的结论转成下一步路线计划。

本版不训练、不生成 corpus、不修改 contract。它是一个 closeout plan：关闭 direct-prompt bridge patch，规划下一步 direct-completion surface contract。

## 前置链路

```text
v731 direct-prompt bridge patch
v732 bridge corpus
v733 bridge training
v734 bridge comparison
 -> no improvement + fixed pollution
v735 bridge closeout plan
 -> direct-completion surface contract
```

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_readiness_bridge_closeout_plan.py`
  - 读取 bridge comparison。
  - 检查 no hit delta、pollution introduced、bridge not improved。
  - 输出 closeout plan。
- `src/minigpt/model_capability_required_term_pair_readiness_bridge_closeout_plan_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
- `scripts/run_model_capability_required_term_pair_readiness_bridge_closeout_plan.py`
  - CLI 入口。
- `tests/test_model_capability_required_term_pair_readiness_bridge_closeout_plan.py`
  - 覆盖 ready、bridge 改善时失败、五格式输出。

## 核心检查

v735 的检查项：

```text
comparison_passed
comparison_decision
no_hit_delta
pollution_introduced
bridge_not_improved
```

只有当 bridge route 同时满足：

```text
default_hit_delta=0
bridge_pollution_introduced=True
bridge_improved=False
```

才会输出 ready plan。

## 下一步计划

v735 proposed next artifact：

```text
pair_readiness_direct_completion_surface_contract
```

这个 contract 的要求：

- balanced direct completion rows，例如 `fixed=fixed` 和 `loss=loss`。
- prefix ladder 必须 fixed/loss 对称。
- paired rows 与 direct rows 分开。
- surface checks 要区分 exact direct completion 和 heldout pair probe leakage。

## 证据

运行证据：

- `e/735/解释/model-capability-required-term-pair-readiness-bridge-closeout-plan/`
- `e/735/图片/v735-bridge-closeout-plan.png`

## 一句话总结

v735 关闭 direct-prompt bridge patch 路线，改为规划更紧凑的 direct-completion surface。
