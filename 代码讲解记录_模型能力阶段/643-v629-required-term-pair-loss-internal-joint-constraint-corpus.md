# v629 required-term pair loss-internal joint-constraint corpus

## 本版目标和边界

v629 解决 v628 暴露的单边 bridge 问题：fixed bridge 可以让 `fixed=` 生成 fixed，但会把 `loss=` 也拉向 fixed。

本版新增两个 corpus mode，用于把 generation anchor 和 internal preference anchor 合并成同一训练约束。它不运行真实 tiny 训练，不判断模型能力提升，只证明下一版训练输入已经准备好。

## 前置路线

前置证据链是：

```text
v621 internal first-token route: forced-choice 可同时偏好 fixed/loss，但生成只保 loss
v626 decode bridge check: fixed 是 generation gap
v628 fixed bridge route: fixed 修复，但 loss 丢失
v629 joint constraint corpus: 同时约束 fixed/loss 的生成与内部偏好
```

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_loss_internal_preference_objective_corpus.py
tests/test_model_capability_required_term_pair_loss_internal_preference_objective_corpus.py
e/629/解释/loss-internal-joint-constraint-corpus-contract/
e/629/解释/说明.md
```

`model_capability_required_term_pair_loss_internal_preference_objective_corpus.py` 新增两个 mode：

```text
equals_surface_no_pair_id_loss_internal_joint_cycle_repair
equals_surface_no_pair_id_loss_internal_balanced_anchor_repair
```

`joint_cycle` 把 `fixed=fixed`、`loss=loss`、generation row、internal rank row 和 tradeoff 禁止语句放在同一循环里。它的意图是减少“修复 fixed 时覆盖 loss”的单边梯度。

`balanced_anchor` 用成对 anchor 维持 fixed/loss 的提示权重一致，避免某一侧因为重复密度更高而成为默认输出。

## 合约产物

```text
model_capability_required_term_pair_loss_internal_joint_constraint_corpus_contract.json
model_capability_required_term_pair_loss_internal_joint_constraint_corpus_contract.csv
model_capability_required_term_pair_loss_internal_joint_constraint_corpus_contract.txt
model_capability_required_term_pair_loss_internal_joint_constraint_corpus_contract.md
model_capability_required_term_pair_loss_internal_joint_constraint_corpus_contract.html
```

这些产物是只读证据，证明：

- 注册 mode 数量从 4 扩展到 6。
- 新增两个 joint constraint mode。
- 样本继续移除 `pair=01` 这类容易泄漏的显式 pair id。
- 下一步应该运行真实 seed 3535 训练，而不是直接 promotion。

## 测试覆盖

新增测试覆盖两类风险：

- `joint_cycle` 必须同时包含 generation row 和 internal rank row。
- `balanced_anchor` 必须保留 fixed/loss 的相同提示权重。
- 两个 mode 都不能重新引入 `pair=01`。

本版 targeted 测试结果：

```text
python -m pytest tests/test_model_capability_required_term_pair_loss_internal_preference_objective_corpus.py -q -o cache_dir=runs/pytest-cache-v629-targeted
7 passed in 0.32s
```

## 一句话总结

v629 没有宣称模型能力变强，而是把下一轮真实训练从单边 bridge 推进到 generation/internal 联合约束。
