# v622 required-term pair loss-internal ranked-choice seed 3535

## 本版目标和边界

v622 是 loss-internal-preference objective 的第三条真实训练。它把 teacher-forced scoring 的 candidate rank 形式转成训练文本，例如 `choice loss= candidate loss rank 1`。

本版不做 promotion，也不声明模型质量提升；它只补齐 v619 三种 objective 的第三个真实 checkpoint。

## 输入和输出

输入模式：

```text
equals_surface_no_pair_id_loss_internal_ranked_choice_repair
```

输出：

```text
e/622/解释/model-capability-required-term-pair-loss-internal-ranked-choice-seed-3535/
e/622/图片/v622-loss-internal-ranked-choice-seed-3535.png
```

## 运行结果

```text
training_status=pass
checkpoint_exists=True
pair_full_observed=False
```

replay 结果：

```text
fixed= -> fixed= fixe
loss=  -> fixed= fixe
```

它保住了 fixed，但没有恢复 loss；ranked-choice 行在 tiny corpus 里没有形成 loss 分支生成偏好。

## 证据角色

v622 和 v620、v621 构成三点对照：

- v620：fixed-only。
- v621：loss-only。
- v622：fixed-only。

这给 v623 的比较和 v624 的 forced-choice 诊断提供真实 checkpoint 输入。

## 一句话总结

v622 证明 ranked-choice 文本仍偏向 fixed，三种 loss-internal objective 尚未出现 pair-full。
