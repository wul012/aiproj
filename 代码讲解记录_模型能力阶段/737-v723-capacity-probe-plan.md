# v723 capacity-probe plan

## 本版目标和边界

v723 的目标是从 v722 四路比较生成 capacity-probe plan。

本版不训练模型，不修改 corpus。它只回答：在单边 row patching 被关闭后，下一步是否应该做更大 tiny 模型的 controlled probe。

## 前置链路

```text
v722 four-route comparison
 -> fixed-recovery returns to baseline
 -> single-sided row patching closed
v723 capacity-probe plan
 -> same fixed-recovery corpus
 -> larger tiny model config
```

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_readiness_capacity_probe_plan.py`
  - capacity-probe plan builder。
  - 读取 v722 comparison。
  - 校验 row patching 分支是否已关闭。

- `src/minigpt/model_capability_required_term_pair_readiness_capacity_probe_plan_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。

- `scripts/run_model_capability_required_term_pair_readiness_capacity_probe_plan.py`
  - CLI。

- `tests/test_model_capability_required_term_pair_readiness_capacity_probe_plan.py`
  - 覆盖 plan ready、错误 source 阻断、输出格式。

## 校验逻辑

v723 只有在以下条件成立时才 ready：

```text
route_comparison_passed
route_comparison_decision == pair_readiness_fixed_recovery_returns_to_baseline_without_pair_full
no_pair_full_route
fixed_recovery_returned_to_baseline
route_count >= 4
```

这保证 capacity probe 不是随意加模型规模，而是在 row patching 已经被证据关闭后发生。

## 训练配置

计划配置：

```text
seed=3535
max_iters=1800
eval_iters=2
batch_size=16
block_size=16
n_layer=2
n_head=2
n_embd=96
learning_rate=0.01
max_new_tokens=12
temperature=0.2
top_k=1
device=cpu
```

相比 v707/v716/v721：

- 层数从 1 增加到 2。
- attention head 从 1 增加到 2。
- embedding 从 64 增加到 96。
- learning rate 从 0.02 降到 0.01。
- max iters 从 1400 增到 1800。

## 输出和证据

运行证据：

- `e/723/解释/model-capability-required-term-pair-readiness-capacity-probe-plan/`
- `e/723/图片/v723-capacity-probe-plan.png`

关键输出：

```text
decision=pair_readiness_capacity_probe_plan_ready
proposed_next_artifact=pair_readiness_capacity_probe_training_run
n_layer=2
n_head=2
n_embd=96
max_iters=1800
learning_rate=0.01
model_quality_claim=plan_only
```

## 一句话总结

v723 用 v722 的闭环证据把下一步从“继续补 rows”切换到“测试稍大 tiny 模型容量”，为 v724 真实 capacity training 做准备。
