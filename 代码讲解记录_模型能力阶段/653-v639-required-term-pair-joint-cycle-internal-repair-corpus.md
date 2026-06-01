# v639 required-term pair joint-cycle internal-repair corpus

## 本版目标和边界

v639 落实 v638 closeout 的下一步：设计 `joint-cycle internal-repair` corpus。它不训练模型，不宣称能力提升，只证明新的训练输入已经准备好。

## 前置路线

```text
v630 joint-cycle: generation pair-full
v631 forced-choice: internal 只保 fixed
v638 closeout: 选择 joint_cycle_internal_repair
v639: 新增对应 corpus mode
```

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_loss_internal_preference_objective_corpus.py
tests/test_model_capability_required_term_pair_loss_internal_preference_objective_corpus.py
e/639/解释/joint-cycle-internal-repair-corpus-contract/
```

## 核心结构

新增模式：

```text
equals_surface_no_pair_id_loss_internal_joint_cycle_internal_repair
```

它同时包含三类行：

```text
generation fixed/loss rows
teacher-forced fixed/loss rows
internal rank fixed/loss rows
```

其中 `teacher forced loss= loss` 和 `internal loss= candidate loss rank 1` 专门对应 v631 的 loss-side internal gap；`generation fixed= fixed` 和 `generation loss= loss` 用来保护 v630 的生成 pair-full。

## 测试覆盖

新增测试确认：

- 新 mode 能生成 generation fixed/loss 行。
- 新 mode 能生成 teacher-forced loss 行。
- 新 mode 能生成 internal loss rank 行。
- 不重新引入 `pair=01` 这类 shortcut。

## 一句话总结

v639 把 v638 的路线判断转成具体语料约束：保 generation，修 internal。
