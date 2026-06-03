# v812 route promotion bounded real replay repair strategy revision 代码讲解

## 本版目标和边界

v812 的目标是把 v811 的真实 regression 结果转成下一轮 repair 的执行策略。v811 已经证明：v810 repair checkpoint 在同一套 bounded replay 上从 baseline 的 `2/5` 退到 `0/5`，所以项目不能继续把“训练过”当作“变强了”，必须先调整 repair 策略。

本版不新增 benchmark，不训练新 checkpoint，也不宣称模型能力提升。它只做一件事：把退步证据、原始 repair plan、repair seed 和 training evidence 汇合成一份 strategy revision，为下一版 seed revision 提供明确输入。

## 前置链路

v812 消费四份历史证据：

- v811 comparison：确认 repair checkpoint regressed，`passed_case_delta=-2`。
- v808 repair plan：保留原始 failed-case repair tasks，避免修复目标漂移。
- v809 repair seed：读取原始 seed 的 example count，判断下一轮 seed 如何扩展。
- v810 training evidence：读取实际训练步数和 artifact ready 状态，作为“训练产物存在但不等于能力提升”的上下文。

这四份输入让 v812 既不拍脑袋改策略，也不只看最后一个 JSON 字段。

## 关键文件

- `src/minigpt/model_capability_route_promotion_bounded_real_replay_repair_strategy_revision.py`
  - 构建 strategy revision 的核心模块。
  - 输出 `case_actions`、`strategy_actions`、`strategy_revision`、`summary` 和 `interpretation`。

- `src/minigpt/model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_artifacts.py`
  - 写出 JSON/CSV/text/Markdown/HTML。
  - HTML 分成 `Case Actions` 与 `Strategy Actions` 两个表，便于后续人工审查。

- `scripts/build_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision.py`
  - CLI 入口。
  - 支持从 comparison、plan、seed、training 四个 JSON 或目录读取输入。
  - `--require-revision-ready` 可用于后续门禁。

- `tests/test_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision.py`
  - 覆盖退步可生成修订、已提升时不应修订、CLI 输出和目录定位。

## 核心数据结构

`case_actions` 是 v812 的 case 级修复清单：

```json
{
  "case_id": "case-1",
  "severity": "regression",
  "baseline_pass": true,
  "repair_pass": false,
  "baseline_hit_terms": ["fixed", "loss"],
  "repair_hit_terms": [],
  "repair_missed_terms": ["fixed", "loss"],
  "recommended_seed_change": "add_baseline_preservation_and_contrastive_repair_examples",
  "required_guardrail": "preserve_baseline_pass_before_accepting_repair_checkpoint"
}
```

这里最重要的是 `severity`：

- `regression`：baseline 原本能过，repair checkpoint 反而没过，下一轮 seed 必须加入 baseline preservation。
- `persistent_gap`：baseline 和 repair 都没过，下一轮 seed 继续做直接 bridge 或 missing-term retention。

这比单纯“失败 case 重训”更精确，因为它区分了“原本会，现在不会”和“一直不会”。

`strategy_actions` 是策略级动作清单：

- `block_current_repair_checkpoint`
- `add_baseline_preservation_examples`
- `balance_direct_and_self_check_examples`
- `short_training_with_replay_first`
- `retain_original_repair_tasks`

这些动作把 v811 的 regression 变成下一轮 seed/training 的具体要求。

## 判定逻辑

v812 的 `_checks()` 要求：

- comparison 必须 `status=pass`。
- comparison summary 必须 ready。
- repair checkpoint 不能已经 improved；如果已经 improved，就不该走 strategy revision。
- promotion 必须被 blocked。
- 原始 repair plan、repair seed、training run 都必须 `status=pass`。
- case rows 和 case actions 必须存在。

这意味着 v812 只服务于“repair 没变好或退步”的场景。若下一次 repair checkpoint 真正提升，应该走 review/promotion 路线，而不是继续创建 strategy revision。

## CLI 流程

脚本执行顺序：

1. 定位 v811 comparison JSON。
2. 定位 v808 repair plan JSON。
3. 定位 v809 repair seed JSON。
4. 定位 v810 training run evidence JSON。
5. 调用核心 builder 生成 strategy revision。
6. 写出 JSON/CSV/text/Markdown/HTML。
7. 根据 `--require-revision-ready` 决定退出码。

真实运行输出：

```text
status=pass
decision=model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_ready
blocked_checkpoint=True
regression_detected=True
passed_case_delta=-2
pass_rate_delta=-0.4
case_action_count=5
strategy_action_count=5
next_step=build_bounded_real_replay_repair_seed_revision
```

## 测试覆盖

测试保护三条边界：

- regression 输入可以生成 ready revision，并设置 `blocked_checkpoint=True`。
- 如果 repair checkpoint 已经提升，revision 应失败，防止路线重复。
- CLI 能从目录读取四类输入，并写出五类输出。

这些测试确保 v812 不会把“已经提升的 checkpoint”误送入修订流程，也不会在缺少关键证据时生成策略。

## 运行证据

v812 证据位于 `e/812`：

- `e/812/解释/model-capability-route-promotion-bounded-real-replay-repair-strategy-revision/`
  - JSON/CSV/text/Markdown/HTML 输出。
- `e/812/图片/v812-bounded-real-replay-repair-strategy-revision-html.png`
  - Playwright MCP 截图。
- `e/812/解释/说明.md`
  - 运行结论、输入输出和验证命令。

## 一句话总结

v812 把 v811 的“repair checkpoint 退步”转成了可执行的下一轮 repair 策略，要求后续 seed revision 先保护 baseline 已通过能力，再继续修 persistent gaps。
