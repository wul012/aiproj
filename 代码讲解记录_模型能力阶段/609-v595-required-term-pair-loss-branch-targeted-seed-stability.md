# v595 required-term pair loss-branch targeted seed stability

## 本版目标和边界

v595 按 v594 决策，对 `v590-targeted` 做 3 seed 稳定性 replay。这里的目标不是证明 targeted route 可推广，而是确认它的 loss-only tradeoff 是否稳定出现。

本版会真实训练 3 个 tiny checkpoint，因此属于模型能力证据，不是单纯文档或治理报告。

## 输入

Corpus mode：

```text
equals_surface_no_pair_id_loss_branch_targeted_repair
```

Seeds：

```text
3535
4535
5535
```

关键训练设置：

```text
max_iters=1800
n_embd=64
device=cpu
```

## 运行链路

脚本入口：

```text
scripts/run_model_capability_required_term_pair_colon_immediate_stability.py
```

虽然脚本名保留 `colon_immediate_stability`，它已支持任意 `PAIR_COEXISTENCE_CORPUS_MODES`，本版传入的是 v589 新增的 loss-branch targeted mode。

每个 seed 都会生成：

```text
required_term_pair_coexistence_refresh_corpus.txt
pair-coexistence-refresh-run/checkpoint.pt
pair-generation-profile-replay/*.json
```

## 关键结果

```text
seed_count=3
pair_full_seed_count=0
pair_full_seed_rate=0.0
stable_pair_full=False
```

CSV 里三个 seed 都是：

```text
pair_full_observed=False
continuation_hit_count=1
```

这意味着 targeted route 的单分支命中是稳定的，但 pair-full 没出现。

## 证据链角色

`e/595` 是 v590 单 seed 结论的跨 seed 验证。它把 “v590 可能是偶然 tradeoff” 收紧成 “targeted route 稳定 tradeoff”。

## 一句话总结

v595 用 3 个真实 seed 证明 targeted loss-branch 不是推广路线，它稳定恢复单分支，却稳定不能 pair-full。
