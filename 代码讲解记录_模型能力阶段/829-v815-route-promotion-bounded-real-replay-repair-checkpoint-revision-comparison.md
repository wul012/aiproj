# v815 route promotion bounded real replay repair checkpoint revision comparison 代码讲解

## 本版目标和边界

v815 的目标是验证 v814 revised repair checkpoint 是否比 v806 baseline 更好。v814 已经用 v813 revised corpus 做了真实训练，但训练产物不等于能力提升，所以 v815 必须把新 checkpoint 放回同一套 bounded benchmark 里 replay。

本版没有新增代码模块，而是复用已有的 bounded real replay 和 checkpoint comparison 工具，重点产出真实运行证据。它不包装失败结果；真实结论是 revised checkpoint 仍然 `0/5`，比 v806 baseline 的 `2/5` 低。

## 输入链路

v815 复用：

- v803 benchmark suite
- v804 suite review
- v805 dry-run scorer
- v814 revised checkpoint/tokenizer
- v806 baseline replay

这里的关键是 benchmark suite 不变，这样 v815 和 v806/v811 可直接比较。

## 运行流程

第一步，调用：

```powershell
python -B scripts\run_model_capability_route_promotion_bounded_real_replay.py `
  --benchmark-suite <v803-suite> `
  --suite-review <v804-review> `
  --dry-run <v805-dry-run> `
  --checkpoint <v814-checkpoint> `
  --tokenizer <v814-tokenizer> `
  --device cpu `
  --out-dir e\815\解释\...\revision-replay `
  --require-execution-pass `
  --force
```

得到 replay 结果：

```text
status=pass
passed_case_count=0
failed_case_count=5
pass_rate=0.0
model_route_quality_ready=False
```

第二步，调用 checkpoint comparison：

```powershell
python -B scripts\compare_model_capability_route_promotion_bounded_real_replay_repair_checkpoint.py `
  --baseline-replay <v806-replay> `
  --repair-replay <v815-replay> `
  --out-dir e\815\解释\...\comparison `
  --require-comparison-pass `
  --force
```

得到 comparison 结果：

```text
decision=model_capability_route_promotion_bounded_real_replay_repair_checkpoint_regressed
baseline_passed_case_count=2
repair_passed_case_count=0
passed_case_delta=-2
pass_rate_delta=-0.4
promotion_ready=False
```

## 为什么这版有价值

这版的价值不是“成功提升模型”，而是把第二次 repair 的失败证据化。v813 增加 baseline preservation，v814 重新训练，但 v815 证明这些措施仍没有转成 replay 能力。

这意味着下一步不应继续做同构 seed 扩写，而应该检查更底层的问题：

- benchmark prompt 是否和训练 text 的分布错位；
- char tokenizer + tiny model 是否难以稳定复现固定短答；
- 训练目标是否只是降低 loss，却没有强化 exact-term generation；
- replay 采样参数是否需要配合 deterministic decoding 或更直接的 answer template。

## 证据产物

- `e/815/解释/model-capability-route-promotion-bounded-real-replay-repair-checkpoint-revision-replay/revision-replay/`
  - v814 checkpoint 的真实 replay 输出。

- `e/815/解释/model-capability-route-promotion-bounded-real-replay-repair-checkpoint-revision-replay/comparison/`
  - v806 baseline 与 v815 replay 的 comparison 输出。

- `e/815/图片/v815-bounded-real-replay-repair-checkpoint-revision-comparison-html.png`
  - Playwright MCP 截图。

- `e/815/解释/说明.md`
  - 本版运行解释和结论。

## 边界说明

`status=pass` 只说明 replay/comparison 执行成功，不说明模型通过。真正的模型能力字段是：

- `model_route_quality_ready=False`
- `promotion_ready=False`
- `repair_checkpoint_regressed=True`

这三个字段共同阻断 promotion。

## 一句话总结

v815 证明 revised repair checkpoint 仍没有恢复 bounded replay 能力，下一步应该从训练目标和 prompt/decoding 对齐上找原因，而不是继续机械扩 seed。
