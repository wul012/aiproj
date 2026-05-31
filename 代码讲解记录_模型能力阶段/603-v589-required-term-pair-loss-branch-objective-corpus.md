# v589 required-term pair loss-branch objective corpus

## 本版目标和边界

v589 接 v588 的结论：下一步必须设计 `loss-branch objective`。本版只做训练输入层，不训练模型、不宣称能力提升，也不新增治理链。

它解决的问题是：过去 branch-binding 和 target-anchor 都没有恢复 `loss`，继续往主 corpus 文件里堆模式会让文件失控。因此本版把 loss-branch objective 独立到新模块，再让主入口只做路由。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_loss_branch_objective_corpus.py
src/minigpt/model_capability_required_term_pair_coexistence_corpus.py
tests/test_model_capability_required_term_pair_coexistence_refresh.py
e/589/解释/loss-branch-objective-corpus-contract/
```

## 核心结构

`PAIR_LOSS_BRANCH_OBJECTIVE_CORPUS_MODES` 定义了 3 个新 mode：

```text
equals_surface_no_pair_id_loss_branch_targeted_repair
equals_surface_no_pair_id_loss_branch_dual_anchor_repair
equals_surface_no_pair_id_loss_branch_micro_span_repair
```

`extend_pair_loss_branch_objective_corpus()` 是新模块的唯一扩展入口。主 `coexistence_corpus.py` 只导入这个入口，不承载具体行生成逻辑。

## 三个 objective 的含义

`targeted_repair`：

```text
loss=loss
loss=loss
prompt loss= target loss
loss= should not drift into fixed
```

它直接提高 `loss` 目标密度，但保留 `fixed=fixed`，避免把问题变成单分支记忆。

`dual_anchor_repair`：

```text
loss=loss|fixed=fixed
fixed=fixed|loss=loss
```

它把两个分支放到同一条 clean record，观察模型是否能同时保留两个 continuation。

`micro_span_repair`：

```text
loss=l
loss=lo
loss=los
loss=loss
```

它针对 v580/v572 这类 first-token gap，让 `loss=` 后的第一 token 更显式。

## 测试覆盖

新增测试断言：

- targeted mode 中 `loss=loss` 密度高于 `fixed=fixed`。
- dual-anchor mode 同时出现 `loss=loss|fixed=fixed` 和反向锚点。
- micro-span mode 包含 `loss=l/lo/los/loss`。
- 三个 mode 都不引入 `pair=01`，避免回到 pair-id 竞争。

## 证据链角色

`e/589` 是 corpus contract 证据，不是模型质量证据。它证明 v590-v592 的训练输入来自可测试 contract，而不是临时手写 corpus。

## 一句话总结

v589 把 “下一步做 loss branch” 从一句路线建议落成了独立、可测试、不会制造巨型文件的训练输入层。
