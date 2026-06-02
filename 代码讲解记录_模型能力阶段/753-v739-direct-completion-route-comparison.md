# v739 direct-completion route comparison

## 本版目标和边界

v739 的目标是比较三条 pair-readiness 路线：

```text
v729 objective-structure training
v733 direct-prompt bridge training
v738 direct-completion surface training
```

它不训练模型、不生成 corpus，也不直接 promotion。它把 v738 的正向结果放回历史路线矩阵中，确认这是不是一个相对前两条路线有明确提升的 candidate。

## 为什么需要这一版

v738 已经显示：

```text
pair_full_observed=True
default_continuation_hit_count=2
```

但单条训练报告只能说明“这次跑出来了”。v739 要回答更工程化的问题：

- 它是否比 v729/v733 更好？
- 它是否只是改变了失败形态？
- 它是否仍有 fixed/loss prompt 污染？
- 它能不能作为下一步 stricter replay 的候选路线？

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_readiness_direct_completion_route_comparison.py`
  - 读取三份 training report。
  - 抽取 default replay hit/miss、pollution、checkpoint 状态。
  - 计算 previous best、hit delta 和 candidate decision。
- `src/minigpt/model_capability_required_term_pair_readiness_direct_completion_route_comparison_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
  - HTML 用于截图和人工比较。
- `scripts/run_model_capability_required_term_pair_readiness_direct_completion_route_comparison.py`
  - CLI 入口，显式接收 `--objective`、`--bridge`、`--direct-completion`。
- `tests/test_model_capability_required_term_pair_readiness_direct_completion_route_comparison.py`
  - 覆盖 candidate、pollution review、checkpoint 缺失和五格式输出。

## 核心数据结构

comparison row 字段包括：

```text
label
status
decision
training_status
checkpoint_exists
pair_full_observed
default_continuation_hit_count
default_hit_terms
default_missed_terms
loss_prompt_fixed_pollution_count
fixed_prompt_loss_pollution_count
non_term_surface_count
suppression_continuation_hit_count
continuation_previews
```

这些字段让报告不只看最终 decision，还能看失败形态：

- 是否没有生成目标词。
- 是否把 `loss=` 误导到 `fixed`。
- 是否把 `fixed=` 误导到 `loss`。
- 是否输出完全不含 fixed/loss 的非目标 surface。

## 决策逻辑

summary 计算：

```text
previous_best_hit_count
direct_completion_default_hit_count
direct_completion_hit_delta_from_previous_best
direct_completion_pair_full_observed
direct_completion_pollution_count
direct_completion_pollution_free
direct_completion_candidate
selected_route
```

只有满足以下条件才会得到：

```text
pair_readiness_direct_completion_route_candidate_found
```

条件：

```text
direct_completion_pair_full_observed=True
direct_completion_default_hit_count > previous_best_hit_count
direct_completion_pollution_count=0
```

真实 v739 结果：

```text
previous_best_hit_count=0
direct_completion_default_hit_count=2
direct_completion_hit_delta_from_previous_best=2
direct_completion_pair_full_observed=True
direct_completion_pollution_free=True
selected_route=direct-completion-surface
```

## 测试覆盖

测试覆盖四个关键场景：

- direct-completion 命中两个 direct probes 时被选为 candidate。
- direct-completion 有污染时进入 review decision，不直接 candidate。
- checkpoint 缺失时 comparison fail。
- JSON/CSV/TXT/Markdown/HTML 五格式输出完整。

## 证据

运行输出：

```text
e/739/解释/model-capability-required-term-pair-readiness-direct-completion-route-comparison/
```

运行截图：

```text
e/739/图片/v739-direct-completion-route-comparison.png
```

截图可见：

- `Decision=pair_readiness_direct_completion_route_candidate_found`
- `Previous best=0`
- `Direct hits=2`
- `Hit delta=2`
- `Pair-full=True`
- `Pollution free=True`

## 为什么还不是 promotion

v739 的 next action 是：

```text
run pair-probe replay and stricter promotion checks before accepting this route
```

原因是 v739 比较的是 heldout direct probes，而 promotion 还需要：

- pair-probe replay。
- 更严格的污染检查。
- 最好再做 seed 稳定性或 replay policy 检查。

## 一句话总结

v739 证明 direct-completion surface 是当前三条路线中第一条明确优于历史失败路线的 candidate，但仍需要 pair-probe replay 和 promotion guard。
