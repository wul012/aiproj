# v642 required-term pair alignment comparison with internal-repair

## 本版目标和边界

v642 把 v640/v641 internal-repair 证据纳入 generation/internal alignment comparison。它还修复了比较器的一个边界：没有 generation hit 的真实负结果应该被比较，而不是被当成输入坏了。

## 关键修改

```text
src/minigpt/model_capability_required_term_pair_generation_internal_alignment_comparison.py
tests/test_model_capability_required_term_pair_generation_internal_alignment_comparison.py
```

新增分类：

```text
internal_pair_full_generation_none
internal_partial_generation_none
generation_none
```

其中 v640/v641 命中 `internal_pair_full_generation_none`。

## 运行结果

```text
decision=keep_generation_pair_full_and_repair_internal_preference
generation_pair_full_count=1
internal_pair_full_count=2
aligned_pair_full_count=0
```

路线矩阵：

```text
loss-internal-joint-cycle   -> generation_pair_full_internal_partial
joint-cycle-internal-repair -> internal_pair_full_generation_none
```

## 证据意义

v642 证明 internal-repair 不是失败输入，而是一个“内部成功、生成失败”的真实负结果。下一步要合并 v630 和 v641 的优点，而不是继续单边加强 internal。

## 测试覆盖

新增测试覆盖 zero-generation-hit 场景，确保这类真实负结果仍然 `status=pass` 并进入 route decision。

## 一句话总结

v642 把 v640/v641 的分裂状态纳入统一矩阵：generation 和 internal 都有半边成功，但还没有同一 checkpoint 同时成功。
