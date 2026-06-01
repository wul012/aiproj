# v648 required-term pair internal-repair batch closeout

## 本版目标和边界

v648 关闭 v639-v648 十版。它总结两条新尝试：

- heavy internal-repair。
- light-merge。

本版不新增训练结果；它把本轮证据收束为下一步路线。

## 关键修改

```text
src/minigpt/model_capability_required_term_pair_generation_internal_batch_closeout.py
scripts/run_model_capability_required_term_pair_generation_internal_batch_closeout.py
tests/test_model_capability_required_term_pair_generation_internal_batch_closeout.py
```

closeout 工具支持自定义批次范围和 next route，因此 v648 可以正确写入 v639-v648，而不是沿用 v638 的 v629-v638 默认范围。

## 核心结果

```text
decision=close_batch_and_design_two_stage_surface_internal_schedule
batch_version_count=10
aligned_pair_full_count=0
selected_generation_route=loss-internal-joint-cycle
internal_anchor_route=joint-cycle-internal-repair
next_route=two_stage_surface_internal_schedule
```

## 本轮判断

v639/v640/v641 证明：heavy internal repair 可以修 internal，但会破坏 generation。

v644/v645/v646 证明：light merge 更温和，但仍造成 generation/internal 错位。

v647 证明：加入 light-merge 后完整矩阵仍没有 aligned route。

所以 v648 的建议是：停止继续堆相似 corpus，改做两阶段 schedule。

## 测试覆盖

新增测试确认 closeout 可以接受：

```text
batch_start=639
batch_end=648
next_route=two_stage_surface_internal_schedule
```

并输出正确 included versions 和 decision。

## 一句话总结

v648 把本轮结论从“继续修 internal”升级为“单一 corpus 微调已到瓶颈，下一步做两阶段训练调度”。
