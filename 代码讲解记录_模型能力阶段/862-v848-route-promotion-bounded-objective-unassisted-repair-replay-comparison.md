# v848：bounded objective unassisted repair replay comparison

## 本版目标和边界

v848 的目标是检验 v847 训练出来的 checkpoint 是否真的恢复了 bounded objective contract。

边界：

- 不再训练模型。
- 不使用 decoder anchor。
- 不修改 v836 objective contract。
- 不因 v847 training loss 下降而宣称模型能力提升。

这版的重点是把“训练产物可用”推进到“真实 replay 是否命中”，并保留失败证据。

## 前置链路

输入来自两条链：

- v836 objective contract：提供 3 个 replay cases 和目标 completion `fixed loss`。
- v847 unassisted repair training run：提供 checkpoint、tokenizer 和训练证据。

v848 检查：

```text
bounded_objective_contract_ready=True
bounded_objective_unassisted_repair_training_ready=True
checkpoint.pt exists
tokenizer.json exists
case_count=3
```

## 关键新增文件

- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_replay_comparison.py`
  - v848 的核心 adapter。它复用 v839 的 replay engine，把 v847 的 `bounded_objective_unassisted_repair_training_ready` 映射到通用 replay engine 需要的 ready key。
- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_replay_comparison_artifacts.py`
  - 复用通用 replay renderer，并写入 v848 专属文件名。
- `scripts/run_model_capability_route_promotion_bounded_objective_unassisted_repair_replay_comparison.py`
  - CLI 入口，支持 objective contract、training run、checkpoint/tokenizer override、device 和 require flags。
- `tests/test_model_capability_route_promotion_bounded_objective_unassisted_repair_replay_comparison.py`
  - 覆盖 zero-hit、contract recovered but holdout required、training not ready、writer/CLI wiring。
- `e/848/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-replay-comparison/`
  - 保存真实 replay comparison 产物。
- `e/848/图片/v848-bounded-objective-unassisted-repair-replay-comparison-html.png`
  - Playwright MCP 截图。

## 为什么用 adapter

v839 已经有稳定的 replay engine：

```text
contract cases -> MiniGPTGenerator -> continuation -> required-term scoring -> summary/decision
```

v848 没有必要复制这一段。它只需要说明“输入训练 run 是 unassisted repair route”，所以 adapter 做三件事：

1. 把 `bounded_objective_unassisted_repair_training_ready` 映射成通用的 `bounded_objective_training_ready`。
2. 把 decision 改写成 v848 专属语义，例如 `...unassisted_repair_replay_zero_hit`。
3. 在 summary/comparison/interpretation 中写明 `decoder_anchor_used=False`。

这比复制一份 replay engine 更利于维护。

## 核心字段

v848 summary 包含：

```text
bounded_objective_unassisted_repair_replay_comparison_ready
objective_contract_recovered
canonical_case_pass
case_count
passed_case_count
any_hit_case_count
zero_hit_case_count
pass_rate
promotion_ready
decoder_anchor_used
next_step
```

`promotion_ready` 固定为 `False`。即使 future replay recovered，也还需要 unchanged holdout。

## 真实结果

```text
status=pass
decision=model_capability_route_promotion_bounded_objective_unassisted_repair_replay_zero_hit
objective_contract_recovered=False
case_count=3
passed_case_count=0
any_hit_case_count=0
zero_hit_case_count=3
pass_rate=0.0
model_quality_claim=not_improved
```

三条 continuation：

```text
canonical_direct_completion -> " tos\n\nan"
minimal_direct_completion -> " thed te"
completion_label_surface -> " los\n\nan"
```

`completion_label_surface` 出现了 `los`，但不是完整 `loss`；评分按 required term 完整包含判断，因此仍然是 zero-hit。

## 测试覆盖

focused pytest 覆盖：

- fake runner 输出无目标词时，report ready 但 contract 未恢复。
- fake runner 输出 `fixed loss` 时，contract recovered，但仍然需要 holdout。
- training summary 不是 unassisted ready 时，report fail。
- artifact writer 和 CLI 能正常落盘。

focused pytest：

```text
4 passed
```

全量回归：

```text
1722 passed
```

source encoding hygiene：

```text
status=pass
source_count=1252
syntax_error_count=0
```

## 运行证据

真实命令：

```text
python scripts/run_model_capability_route_promotion_bounded_objective_unassisted_repair_replay_comparison.py --objective-contract e/836/解释/model-capability-route-promotion-bounded-objective-contract --training-run e/847/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-training-run --device cpu --out-dir e/848/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-replay-comparison --require-comparison-ready --force
```

HTML 截图：

```text
e/848/图片/v848-bounded-objective-unassisted-repair-replay-comparison-html.png
```

## 一句话总结

v848 用真实 replay 证明：v847 的无锚点训练没有恢复 `fixed/loss` 目标输出，下一步应诊断 zero-hit，而不是继续把训练版本往前堆。
