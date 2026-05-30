# v536 required-term pair colon-immediate stability 代码讲解

## 本版目标和边界

v535 通过 `colon_immediate` corpus 得到单 seed fixed/loss pair-full。v536 不急着宣称模型能力稳定，而是做三 seed 复验：`535, 1535, 2535`。

本版不改 corpus，不改模型结构，不增加训练预算。它只回答一个问题：v535 的 pair-full 是否能跨 seed 复现。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_colon_immediate_stability.py`
  - 多 seed wrapper，循环调用 v535 的 `build_model_capability_required_term_pair_coexistence_refresh()`。
- `src/minigpt/model_capability_required_term_pair_colon_immediate_stability_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML，并为每个 seed 写出 refresh sidecar。
- `scripts/run_model_capability_required_term_pair_colon_immediate_stability.py`
  - CLI 入口，暴露 seeds 和训练参数。
- `tests/test_model_capability_required_term_pair_colon_immediate_stability.py`
  - 用 fake train/generate 覆盖 stable、partial、sidecar 输出。
- `e/536/解释/model-capability-required-term-pair-colon-immediate-stability/`
  - 保存真实三 seed 稳定性报告。

## 核心流程

`build_model_capability_required_term_pair_colon_immediate_stability()` 对每个 seed 创建独立目录：

```text
seed-runs/seed-535
seed-runs/seed-1535
seed-runs/seed-2535
```

每个目录内部都运行 v535 的 refresh：

```text
corpus_mode=colon_immediate
repeat=260
bridge_repeat=20
max_iters=1400
n_embd=64
```

然后抽取每个 seed 的摘要为 `seed_rows`：

- `pair_full_observed`
- `default_pair_full_variant_count`
- `suppression_pair_full_variant_count`
- `continuation_hit_count`
- `checkpoint_exists`

顶层 summary 再计算：

```text
seed_count
pair_full_seed_count
pair_full_seed_rate
stable_pair_full
partial_pair_full
```

## 真实结果

真实运行结果：

```text
decision=required_term_pair_colon_immediate_partial_stability
seed_count=3
pair_full_seed_count=1
pair_full_seed_rate=0.3333
stable_pair_full=False
```

seed 明细：

```text
535  -> pair_full=True
1535 -> pair_full=False
2535 -> pair_full=False
```

这说明 v535 的修复方向是真实信号，但还不稳定。

## 测试覆盖

单测覆盖三条路径：

- 所有 fake seed 都 pair-full，decision 应为 stable。
- 只有一个 fake seed pair-full，decision 应为 partial。
- 输出 writer 生成 JSON、CSV、text、Markdown、HTML，并写出每个 seed 的 refresh sidecar。

真实 PyTorch 三 seed 训练由 `e/536` 证据覆盖。

## 链路角色

v536 是 v535 之后必要的刹车：它防止把单 seed 成功误判成稳定能力。后续最合理的路线是检查 missed seeds，而不是直接加大模型或宣称突破。

一句话总结：v536 把 colon-immediate pair-full 从单 seed 成功校准为三 seed partial stability。
