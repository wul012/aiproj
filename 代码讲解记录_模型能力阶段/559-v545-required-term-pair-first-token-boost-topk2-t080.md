# v545 required-term pair first-token boost top-k2 t0.8 代码讲解

## 本版目标和边界

v544 达到 `2/3` pair-full，只剩 seed `1535`。一个直觉修法是强化 first-token 训练样本，也就是复用已有 `colon_immediate_first_token_boost` corpus。v545 在 v544 的最佳解码配置 `top_k=2, temperature=0.8` 下运行这个 corpus，验证它是否真的能修复剩余 seed。

本版没有新增代码。它是一次负向实验，用来排除错误方向。

## 前置能力

复用已有参数：

- `corpus_mode=colon_immediate_first_token_boost`
- `top_k=2`
- `temperature=0.8`
- `repeat=420`
- `bridge_repeat=40`
- `max_iters=2200`

复用已有诊断：

- colon-immediate stability runner
- missed-seed first-token diagnostic
- Playwright MCP HTML 截图

## 实验输入

`colon_immediate_first_token_boost` 会额外加入：

```text
fixed:f
loss:l
fixed:fi
loss:lo
fixed:fix
loss:los
```

这个 corpus 的目标是强化冒号后的第一 token，但它会改变整体短上下文分布。

## 真实结果

stability：

```text
decision=required_term_pair_colon_immediate_not_stable
pair_full_seed_count=0/3
```

diagnostic：

```text
missed_seed_count=3
missed_first_token_gap_count=3
```

seed 明细：

```text
535  -> fixed rank=2, loss rank=1
1535 -> fixed rank=2, loss rank=1
2535 -> fixed rank=2, loss rank=2
```

这说明短前缀增强没有把 fixed/loss 两个分支同时稳定，反而破坏了 v544 已经恢复的 seed `535` 和 `2535`。

## 链路角色

v545 的价值不在提升指标，而在排除无效修法。它告诉后续版本不要继续堆 `fixed:f` / `loss:l` 短样本，而应尝试更结构化的数据，例如明确对比、校准或 hard-seed 定向样本。

## 验证覆盖

验证内容包括：

- 真实三 seed 训练和 replay。
- stability 主报告与 missed-seed diagnostic 报告。
- 每个 seed 的 first-token sidecar。
- Playwright MCP 截图和 snapshot。
- 全量 pytest、source encoding、`git diff --check` 和 GitHub Actions。

一句话总结：v545 用真实负结果证明 first-token boost corpus 会使当前 fixed/loss pair 目标退化。
