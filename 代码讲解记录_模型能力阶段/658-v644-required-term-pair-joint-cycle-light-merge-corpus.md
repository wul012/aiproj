# v644 required-term pair joint-cycle light-merge corpus

## 本版目标和边界

v644 新增 joint-cycle light-merge corpus。它吸收 v643 的路线：以 v630 generation route 为 base，用 v641 internal anchor 做轻量修复。

本版不训练模型，只证明新 corpus 输入已准备。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_loss_internal_preference_objective_corpus.py
tests/test_model_capability_required_term_pair_loss_internal_preference_objective_corpus.py
e/644/解释/joint-cycle-light-merge-corpus-contract/
```

## 设计差异

v639 heavy internal-repair 包含 teacher-forced rows，v640 证明它会破坏 generation。

v644 light-merge 保留：

```text
generation fixed= fixed
generation loss= loss
internal fixed= candidate fixed rank 1
internal loss= candidate loss rank 1
```

但不加入：

```text
teacher forced loss= loss
```

这样让 generation 仍是语料主线，internal 修复只是软约束。

## 测试覆盖

测试确认：

- generation fixed/loss rows 存在。
- light merge 标记行存在。
- internal loss rank row 存在。
- heavy teacher-forced loss row 不存在。
- 不引入 pair-id shortcut。

## 一句话总结

v644 将 internal repair 从 heavy 版本降为 light merge，准备验证是否能保住 v630 的生成优势。
