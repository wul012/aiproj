# v722 four-route pair-readiness comparison

## 本版目标和边界

v722 的目标是把 v721 fixed-recovery training run 纳入 route comparison。

本版不训练模型，不生成 corpus。它扩展已有 v717 比较器，让同一个工具支持三路和四路输入。

## 前置链路

```text
v707 baseline split -> fixed-only
v712 loss-retention prefix -> no direct hit
v716 structured-template -> loss-only
v721 fixed-recovery -> fixed-only
v722 four-route comparison -> fixed-recovery returns to baseline
```

## 关键修改

- `src/minigpt/model_capability_required_term_pair_readiness_route_comparison.py`
  - `build_pair_readiness_route_comparison` 增加可选 `fixed_recovery_report`。
  - summary 增加：
    - `fixed_recovery_vs_baseline_default_hit_delta`
    - `fixed_recovery_vs_structured_default_hit_delta`
    - `fixed_recovery_default_hit_terms`
    - `fixed_recovery_default_missed_terms`
    - `fixed_recovery_returns_to_baseline`

- `scripts/run_model_capability_required_term_pair_readiness_route_comparison.py`
  - 增加可选 `--fixed-recovery`。
  - 不传时仍保持 v717 三路比较行为。

- `tests/test_model_capability_required_term_pair_readiness_route_comparison.py`
  - 增加 fixed-recovery 返回 baseline 的测试。

## 判定逻辑

新增判断：

```text
fixed_recovery_returns_to_baseline =
    fixed_recovery.hit_terms == baseline.hit_terms
    and fixed_recovery.default_hit_count == baseline.default_hit_count
```

真实结果：

```text
baseline-split: hit ['fixed'], miss ['loss']
structured-template: hit ['loss'], miss ['fixed']
fixed-recovery: hit ['fixed'], miss ['loss']
```

所以 decision 是：

```text
pair_readiness_fixed_recovery_returns_to_baseline_without_pair_full
```

## 工程意义

v722 的判断很关键：

- v716 不是无效，它证明 structured rows 能保住 loss。
- v721 不是突破，它只是把模型拉回 fixed-only。
- 继续做单边 fixed/loss rows，很可能继续在两个分支之间摆动。

因此 next action 明确写为：

```text
close single-sided fixed/loss row patching and test capacity or objective structure instead
```

## 证据

运行证据：

- `e/722/解释/model-capability-required-term-pair-readiness-four-route-comparison/`
- `e/722/图片/v722-four-route-comparison.png`

## 一句话总结

v722 用四路真实训练对比关闭单边 row patching 方向，把后续路线推向模型容量或训练目标结构。
