# v765 objective-level contrast route comparison 代码讲解

## 本版目标和边界

v765 的目标是把 v750、v756、v764 三份 replay evidence 放进同一张 comparison 表，判断 objective-level contrast 是否真正优于之前的 fixed-preserving 和 near-exact surface repair 路线。

本版不训练模型，不修改 checkpoint，也不直接 promotion。它输出的是 route_comparison_winner，后续仍要 promotion guard 和 seed stability。

## 前置路线

- v750：fixed-preserving transfer pair-probe replay，结果 partial。
- v756：near-exact surface repair pair-probe replay，结果 partial。
- v764：objective-level contrast pair-probe replay，结果 ready。
- v765：三路线比较，确认 objective-level contrast 是当前 winner。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_readiness_objective_level_contrast_route_comparison.py`
  - 比较核心。
  - 输入 baseline、exact repair、objective 三份 replay JSON。
  - 生成 route rows，计算 pair-full count、exact hits、objective vs prior delta。
  - 校验 objective route 必须 `required_all_pair_full=True`，且 pair-full count 必须超过 prior max。

- `src/minigpt/model_capability_required_term_pair_readiness_objective_level_contrast_route_comparison_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown 和 HTML。
  - HTML 展示 route rows、checks 和 next action。

- `scripts/run_model_capability_required_term_pair_readiness_objective_level_contrast_route_comparison.py`
  - CLI 入口。
  - `--baseline`、`--exact-repair`、`--objective` 分别输入三条 replay 路线。

- `tests/test_model_capability_required_term_pair_readiness_objective_level_contrast_route_comparison.py`
  - 覆盖 objective wins、objective input fail、objective 未超过 prior 失败和 artifact 输出。

## 输入输出结构

输入：

```text
v750 baseline replay
v756 exact-surface repair replay
v764 objective-level contrast replay
```

v765 输出：

```text
decision=pair_readiness_objective_level_contrast_replay_wins_needs_promotion_guard
objective_route_best=True
objective_pair_full_count=3
objective_vs_baseline_pair_full_delta=2
objective_vs_exact_repair_pair_full_delta=2
promotion_guard_required=True
```

## 比较逻辑

v765 不只看单个 exact prompt，而是要求 objective route 同时满足：

- replay 输入 status 都是 `pass`。
- 三条路线都进入比较表。
- objective route `required_all_pair_full=True`。
- objective route `pair_full_count` 大于 prior max。
- objective exact default hit count 至少为 2。

这个 guard 防止“只比一个 prompt”或“只是打平 prior route”就误判为路线胜出。

## 运行和验证

Focused tests：

```powershell
python -m pytest tests\test_model_capability_required_term_pair_readiness_objective_level_contrast_route_comparison.py -q -o cache_dir=runs\pytest-cache-v765-focused
```

真实运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_objective_level_contrast_route_comparison.py --baseline e\750\解释\model-capability-required-term-pair-readiness-fixed-preserving-transfer-pair-probe-replay --exact-repair e\756\解释\model-capability-required-term-pair-readiness-exact-surface-repair-pair-probe-replay --objective e\764\解释\model-capability-required-term-pair-readiness-objective-level-contrast-pair-probe-replay --out-dir e\765\解释\model-capability-required-term-pair-readiness-objective-level-contrast-route-comparison --require-pass --force
```

Playwright 快照确认 HTML 中可见：

- `Objective best True`
- `Objective pair-full 3`
- `Claim route_comparison_winner`
- next action 是 `run promotion guard and seed stability before accepting the checkpoint`。

截图位于：

```text
e/765/图片/v765-objective-level-contrast-route-comparison.png
```

## 证据链角色

v765 是 route comparison 层。它把 v764 的强 replay 信号放回历史路线里比较，确认 objective-level contrast 是 winner，但还没有完成接受门。

一句话总结：v765 将 objective-level contrast 提升为当前最优路线，同时明确下一步必须进入 promotion guard。
