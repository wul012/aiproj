# v811 route promotion bounded real replay repair checkpoint comparison 代码讲解

## 本版目标和边界

v811 的目标是补上 v810 repair checkpoint 的真实复跑对比：同一套 v803 bounded benchmark suite，先有 v806 baseline checkpoint 的真实 replay 结果，再用 v810 repair checkpoint 重新 replay，然后由 comparison 报告判断 repair checkpoint 是否真的比 baseline 更好。

本版明确不做三件事：

- 不把 v810 的训练 loss 下降当作模型能力提升。
- 不因为 comparison `status=pass` 就推进 route promotion。
- 不继续扩大 benchmark suite，而是先把同一套 bounded replay 的前后对比闭环。

因此 v811 是一版“能力提升反证”版本：它发现 repair checkpoint 从 `2/5` 退到 `0/5`，并把这个退步固化为可复核的 JSON/Markdown/HTML 证据。

## 前置链路

本版承接 v806-v810：

- v806：用 v770 objective-level contrast checkpoint 跑真实 bounded replay，得到 `passed_case_count=2/5`。
- v807：审查 v806 replay，确认存在模型缺口。
- v808：把失败 case 转成 repair plan。
- v809：把 repair plan 转成 seed JSONL 和 corpus。
- v810：用 repair corpus 做了一次真实 CPU tiny training，产出 repair checkpoint。
- v811：不再停在“训练产物存在”，而是把 repair checkpoint 放回同一套 bounded replay 里复跑，并与 v806 对比。

这条链路的关键是：训练产物只是候选物，只有 replay comparison 能决定它是否值得进入后续 promotion review。

## 关键文件

- `src/minigpt/model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison.py`
  - 核心比较器。
  - 读取 baseline replay、repair replay 和可选 training evidence。
  - 输出 `comparison`、`summary`、`case_rows`、`check_rows`、`interpretation`。

- `src/minigpt/model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML 五类证据。
  - HTML 用卡片展示 `baseline_passed_case_count`、`repair_passed_case_count`、`pass_rate_delta`、`promotion_ready`。
  - CSV/Markdown 保留逐 case 对比，方便后续脚本或人工检查。

- `scripts/compare_model_capability_route_promotion_bounded_real_replay_repair_checkpoint.py`
  - CLI 入口。
  - 支持输入 replay JSON 或 replay 输出目录。
  - `--require-comparison-pass` 只要求比较合同成立。
  - `--require-improvement` 会在 repair checkpoint 没有提升时返回 1，适合后续强门禁。

- `tests/test_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison.py`
  - 覆盖退步、提升、源输入失败、CLI 输出与 `--require-improvement` 失败路径。

## 核心数据结构

`case_rows` 是本版最重要的逐 case 证据：

```json
{
  "case_id": "case-name",
  "baseline_pass": true,
  "repair_pass": false,
  "delta": -1,
  "baseline_hit_terms": ["fixed", "loss"],
  "baseline_missed_terms": [],
  "baseline_continuation": "...",
  "repair_hit_terms": ["fixed"],
  "repair_missed_terms": ["loss"],
  "repair_continuation": "..."
}
```

它不是只比较总分，而是保留每个 case 的 baseline 命中、repair 命中和 repair missed terms。这样后续修复可以定位“哪个 case 退步”，而不是只看到总分下降。

`comparison` 汇总前后差异：

- `baseline_passed_case_count`
- `repair_passed_case_count`
- `passed_case_delta`
- `baseline_pass_rate`
- `repair_pass_rate`
- `pass_rate_delta`
- `repair_checkpoint_improved`
- `repair_checkpoint_regressed`
- `promotion_ready`
- `next_step`

本版真实输出中，`passed_case_delta=-2`、`pass_rate_delta=-0.4`、`promotion_ready=False`。这说明 comparison 本身可用，但模型候选不可推进。

## 判定逻辑

`status` 和 `promotion_ready` 被刻意分开：

- `status=pass`：baseline replay、repair replay、training evidence 等输入结构有效，case 数一致，comparison 可以被信任。
- `promotion_ready=True`：repair checkpoint 必须比 baseline 通过更多 case，并且 repair replay 自身达到 route quality ready。

所以 v811 的真实结果是：

```text
status=pass
decision=model_capability_route_promotion_bounded_real_replay_repair_checkpoint_regressed
promotion_ready=False
```

这不是矛盾。它表示“证据链通过，模型候选失败”。

## CLI 流程

脚本入口先定位输入：

1. `locate_route_promotion_bounded_real_replay()` 支持直接传 JSON 或输出目录。
2. `locate_repair_training_run()` 支持可选 training evidence。
3. `build_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison()` 生成 comparison。
4. `write_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison_outputs()` 写出五类证据。
5. `resolve_exit_code()` 根据参数决定是否失败退出。

本版真实运行没有使用 `--require-improvement`，因为当前目标是归档真实退步证据，而不是让命令硬失败。后续 CI 或 promotion gate 可以在需要时启用这个门禁。

## 测试覆盖

测试不是只检查文件存在，而是覆盖核心语义：

- 退步场景：baseline `2/3`，repair `0/3`，comparison `status=pass`，但 `repair_checkpoint_regressed=True`，`--require-improvement` 返回 1。
- 提升场景：baseline `1/3`，repair `3/3`，`promotion_ready=True`，improvement gate 返回 0。
- 源失败场景：baseline replay `status=fail`，comparison 直接失败，防止坏输入被误当作有效比较。
- CLI 场景：目录输入、输出五件套、`--require-comparison-pass` 与 `--require-improvement` 都被走通。

这些断言保护的是 v811 的核心边界：比较报告可以成功生成，但模型能力提升必须由真实 replay 差异证明。

## 运行证据

本版证据放在 `e/811`：

- `e/811/解释/model-capability-route-promotion-bounded-real-replay-repair-checkpoint-replay/repair-replay/`
  - v810 repair checkpoint 的真实 bounded replay 输出。
- `e/811/解释/model-capability-route-promotion-bounded-real-replay-repair-checkpoint-replay/comparison/`
  - v806 baseline 与 v810 repair replay 的 comparison 输出。
- `e/811/图片/v811-bounded-real-replay-repair-checkpoint-comparison-html.png`
  - Playwright MCP 截取的 HTML 可视化证据。
- `e/811/解释/说明.md`
  - 运行结论与验证命令说明。

## 一句话总结

v811 把“repair checkpoint 是否真的更好”从口头判断变成了可复跑、可截图、可门禁的 comparison contract，并用真实结果证明本次 repair checkpoint 不应被 promoted。
