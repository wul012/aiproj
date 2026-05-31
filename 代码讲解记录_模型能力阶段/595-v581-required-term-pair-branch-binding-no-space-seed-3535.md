# v581 required-term pair branch-binding no-space seed 3535

## 本版目标和边界

v581 根据 v580 的 whitespace diagnostic 设计一个 no-space branch-binding corpus。目标是让 `fixed=`、`loss=` 后面直接出现目标 term，避免 v579 里自然语言 binding 样本诱导空格。

本版不做多 seed sweep，也不扩大模型。它只验证 seed `3535` 这一条 fresh-seed 问题是否被 no-space objective 修复。

## 关键修改

文件：

```text
src/minigpt/model_capability_required_term_pair_branch_binding_corpus.py
tests/test_model_capability_required_term_pair_coexistence_refresh.py
```

新增 mode：

```text
equals_surface_no_pair_id_branch_binding_no_space_repair
```

它继续放在 branch-binding 专属组件里，旧 corpus 文件只消费 mode tuple 和路由函数，避免文件继续膨胀。

## 语料结构

no-space 样本包括：

```text
fixed=fixed
loss=loss
fixed=fixed|loss=loss
loss=loss|fixed=fixed
fixed=fixed;loss=loss
loss=loss;fixed=fixed
branch_fixed=fixed
branch_loss=loss
```

桥接说明保留，但明确写：

```text
after fixed= write fixed immediately.
after loss= write loss immediately.
```

它不包含 v579 的：

```text
branch fixed prompt fixed= answer fixed
```

因为这类句子会让 equals 后的空格成为强信号。

## 真实运行

输出目录：

```text
e/581/解释/model-capability-required-term-pair-branch-binding-no-space-seed-3535/
```

结果：

```text
pair_full_seed_count=0
continuation_hit_count=0
stable_pair_full=False
```

no-space branch-binding 仍然没有修复 seed `3535`。

## 测试覆盖

新增测试验证：

- 语料包含 direct equals target rows。
- 语料包含双向 paired rows。
- 语料不包含 v579 的自然语言 binding 句。
- 不引入 numeric pair id。

## 链路角色

v581 是 branch-binding route 的第二条实证。它把 v580 的诊断建议落地，但结果仍负，因此下一步要做横向 comparison，而不是继续用直觉加语料。

## 一句话总结

v581 证明 no-space branch-binding 仍未解决 seed `3535`，下一步应比较 v571/v579/v581，决定 branch-binding v1/v2 是否值得继续。
