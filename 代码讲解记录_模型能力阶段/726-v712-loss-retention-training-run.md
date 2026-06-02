# v712 loss-retention training run

## 本版目标和边界

v712 的目标是训练 v711 的 loss-retention patched corpus，并观察它是否改善 v707 的 fixed-only 失败。

本版不宣称模型能力提升。它是一次真实训练回归检查。

## 前置链路

```text
v708 diagnostic -> loss prompt absorbed by fixed
v709 plan -> loss-retention repair
v710 patch -> add 8 loss-retention rows
v711 materialization -> 6400 corpus lines
v712 training -> real checkpoint + heldout replay
```

## 运行结果

核心输出：

```text
decision=pair_readiness_training_no_pair_full
checkpoint_exists=True
pair_full_observed=False
default_continuation_hit_count=0
```

样本：

```text
fixed= -> fixed=los=los=los=
loss=  -> loss=los=los=los=
```

这比 v707 更差：v707 至少 fixed direct hit，v712 两个 direct probes 都没有完整命中。

## 关键产物

```text
e/712/解释/model-capability-required-term-pair-readiness-loss-retention-training-run/
e/712/图片/v712-loss-retention-training-run.png
```

其中 checkpoint 是真实训练产物，但 `model_quality_claim=not_claimed`。

## 解释

v710 patch 的方向是恢复 loss retention，但实际训练显示 tiny 模型学成了 `los` 前缀循环。它没有完成 `loss`，也污染了 `fixed=`。

这说明下一步不应该继续加更多 `loss=lo/los` 前缀行，而应该做 v707/v712 对比 closeout，停止这种单边 prefix 加权。

## 一句话总结

v712 用真实训练证明 loss-retention patch 没有改善 pair-readiness，反而把两个 direct probes 都推向 `los` 前缀循环。
