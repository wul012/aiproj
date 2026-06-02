# v725 five-route pair-readiness comparison

## 本版目标和边界

v725 的目标是把 v724 capacity-probe training run 纳入 pair-readiness route comparison。

本版不训练新模型，也不宣称模型质量提升。它只做同源训练报告之间的只读比较：把 v707、v712、v716、v721、v724 放在同一张路线表里，判断“轻量加容量”是否真正优于 fixed-recovery。

## 前置链路

```text
v707 baseline split training
 -> fixed-only
v712 loss-retention training
 -> no direct hit
v716 structured-template training
 -> loss-only
v721 fixed-recovery training
 -> fixed-only
v724 capacity-probe training
 -> fixed-only
v725 five-route comparison
 -> close light capacity bump and plan objective-structure change
```

## 关键修改文件

- `src/minigpt/model_capability_required_term_pair_readiness_route_comparison.py`
  - `build_pair_readiness_route_comparison()` 增加可选 `capacity_probe_report` 和 `capacity_probe_path`。
  - `_summary()` 增加 capacity-probe 与 fixed-recovery、baseline 的 hit delta。
  - `_decision()` 增加 `pair_readiness_capacity_probe_no_improvement_fixed_only`。
  - `_interpretation()` 明确下一步从 objective structure 入手。
- `src/minigpt/model_capability_required_term_pair_readiness_route_comparison_artifacts.py`
  - text/HTML 输出增加 `capacity_probe_vs_fixed_recovery_default_hit_delta` 和 `capacity_probe_no_improvement`。
- `scripts/run_model_capability_required_term_pair_readiness_route_comparison.py`
  - CLI 增加 `--capacity-probe`，默认不传时兼容旧四路线比较。
- `tests/test_model_capability_required_term_pair_readiness_route_comparison.py`
  - 新增 capacity-probe no-improvement 用例，覆盖五路线决策。

## 核心数据结构

route row 仍复用原来的训练报告摘要字段：

```text
label
path
status
decision
training_status
checkpoint_exists
pair_full_observed
default_continuation_hit_count
default_hit_terms
default_missed_terms
model_quality_claim
```

v725 新增的 summary 字段是：

```text
capacity_probe_vs_fixed_recovery_default_hit_delta
capacity_probe_vs_baseline_default_hit_delta
capacity_probe_default_hit_terms
capacity_probe_default_missed_terms
capacity_probe_no_improvement
```

这里的关键判断不是看 capacity-probe 是否训练成功，而是看它是否比 v721 fixed-recovery 多命中 `loss`。实际结果显示：

```text
capacity_probe_vs_fixed_recovery_default_hit_delta=0
capacity_probe_default_hit_terms=['fixed']
capacity_probe_default_missed_terms=['loss']
capacity_probe_no_improvement=True
```

## 运行流程

CLI 先把五个输入路径都规范化到 JSON 报告：

```text
baseline -> v707 training report
loss-retention -> v712 training report
structured-template -> v716 training report
fixed-recovery -> v721 training report
capacity-probe -> v724 training report
```

然后 builder 生成 route rows，summary 计算每条路线的 direct probe hit count，decision 层按优先级判断：

1. 输入有缺失或 checkpoint 不存在则失败。
2. 任一路线出现 pair-full，则进入候选复核。
3. capacity-probe 未改善 fixed-recovery，则关闭轻量容量路线。
4. fixed-recovery 回到 baseline，则关闭单边 row patching。
5. structured-template 只改变 failure shape 时不提升。

v725 命中第 3 条，因此输出：

```text
decision=pair_readiness_capacity_probe_no_improvement_fixed_only
next_action=treat this light capacity bump as closed and plan an objective-structure change before larger runs
```

## 证据产物

运行证据：

- `e/725/解释/model-capability-required-term-pair-readiness-five-route-comparison/`
- `e/725/图片/v725-five-route-comparison.png`

这些产物是只读比较证据，不是训练产物。后续版本可以消费这里的 JSON，制定 objective-structure 变更计划。

## 测试覆盖

新增测试构造五条训练路线：

- baseline fixed-only。
- loss-retention 无命中。
- structured-template loss-only。
- fixed-recovery fixed-only。
- capacity-probe fixed-only。

断言保护：

- route_count 必须是 5。
- decision 必须是 `pair_readiness_capacity_probe_no_improvement_fixed_only`。
- capacity probe 相对 fixed-recovery delta 必须是 0。
- `capacity_probe_no_improvement` 必须为 true。

这保证 v725 不是靠文档判断，而是由可复用 builder 直接从训练报告中推导结论。

## 一句话总结

v725 把容量探针放进五路线对比，确认轻量加容量没有改善 fixed/loss 共存，项目下一步应调整训练目标结构而不是继续盲目加模型规模。
