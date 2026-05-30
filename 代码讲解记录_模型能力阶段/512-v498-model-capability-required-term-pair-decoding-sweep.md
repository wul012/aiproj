# v498 model capability required-term pair decoding sweep

## 本版目标和边界

v498 的目标是复核 v497 的下一步判断。v497 对 `fixed/loss` 做了 capacity sweep，4 个 checkpoint 都训练成功，但没有任何 variant 恢复 full-hit。v498 不继续训练、不扩模型、不加新语料，而是复用 v497 已有 checkpoint，改变生成长度、temperature 和 top-k，确认问题是不是出在解码策略上。

本版仍不声明生产级模型质量，也不把 partial hit 包装成能力提升。它只回答一个问题：v497 的 partial checkpoint 是否已经具备双词能力，只是默认短解码没有把它显示出来。

## 前置路线

- v493：one-term 条件下 `fixed/loss/four/chain` 跨 seed 稳定。
- v494：两两组合后全部 partial-only。
- v495：`fixed/loss` 在一个 seed 下出现 full-hit。
- v496：`fixed/loss` 跨 3 seed 复测，full-hit 不复现。
- v497：对 `fixed/loss` 扫训练步数、embedding 宽度和语料密度，仍不恢复 full-hit。
- v498：固定 v497 的 partial checkpoints，只扫 decoding profile。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_decoding_sweep.py`
  - 读取 v497 capacity sweep report。
  - 选择 `pair_partial_hit=True` 且 `pair_full_hit=False` 的 capacity variants。
  - 复用对应 checkpoint/tokenizer，不重新训练。
  - 运行多组 decoding profile，统计每个 target/profile 是否 full-hit。
- `src/minigpt/model_capability_required_term_pair_decoding_sweep_artifacts.py`
  - 输出 JSON、CSV、text、Markdown 和 HTML。
  - HTML 分为 profile results 和 target summary，方便区分“某个 profile 对某个 checkpoint 的表现”。
- `scripts/run_model_capability_required_term_pair_decoding_sweep.py`
  - CLI 入口，支持 `--profile-preset default|fast`、`--target-limit`、`--force` 和 `--require-pass`。
- `tests/test_model_capability_required_term_pair_decoding_sweep.py`
  - 覆盖 recovered、partial、坏 source、空 profile、选择逻辑、summary helpers 和 artifact 输出。
- `e/498/`
  - 保存真实解码扫描产物、CLI 输出、Playwright snapshot 和截图。

## 核心数据结构

输入是 v497 的 `model_capability_required_term_pair_capacity_sweep.json`，主要读取：

```text
summary.pair_capacity_sweep_decision = pair_capacity_sweep_partial_only
summary.capacity_full_hit_observed = False
capacity_rows[]
variant_pair_summaries[]
pairs[]
```

`select_pair_decoding_sweep_targets()` 只选择 partial variants。真实选中两个 target：

```text
01-fixed-loss-baseline-repeat
01-fixed-loss-longer-iters
```

每个 target 记录：

- `checkpoint_path` 和 `tokenizer_path`：复用 v497 训练产物。
- `hit_terms` 和 `missed_terms`：v497 下已经命中/缺失的词。
- `terms`：两个 probe 的 prompt 和 term。

每个 decoding profile 记录：

- `max_new_tokens`
- `temperature`
- `top_k`
- `seed_offset`

这样报告可以明确区分：本版只改解码，不改训练。

## 运行流程

1. CLI 定位 v497 capacity sweep report。
2. builder 校验 source 为 `pass`，且 source 仍是 partial-only。
3. 选择 `baseline-repeat` 和 `longer-iters` 两个 partial checkpoint。
4. 对每个 checkpoint 运行 4 个 decoding profiles。
5. 每个 profile 分别 probe `fixed:` 和 `loss:`。
6. `summarize_decoding_profile_probe_rows()` 汇总 target/profile 的 hit/missed terms。
7. `summarize_pair_decoding_targets()` 判断某个 target 是否在任一 profile 下恢复 full-hit。
8. 写出 JSON/CSV/text/Markdown/HTML，并用 Playwright MCP 截图。

## 真实结果

```text
status=pass
decision=required_term_pair_decoding_sweep_partial
pair_decoding_sweep_decision=pair_decoding_sweep_partial_only
target_count=2
profile_count=4
profile_target_count=8
probe_count=16
probe_hit_count=8
profile_target_full_hit_count=0
profile_target_partial_hit_count=8
decoding_full_hit_observed=False
model_quality_claim=not_claimed
```

明细上有一个很关键的现象：

```text
baseline-repeat: 所有 profile 都只命中 loss，miss fixed
longer-iters deterministic: 只命中 loss，miss fixed
longer-iters sampling: fixed prompt 能命中 fixed，但 loss prompt 反而丢失 loss
```

这说明采样能改变输出偏向，但不能让同一 checkpoint 在两个 prompt 下同时稳定保留两个目标词。问题更像 prompt target separation 或 pair corpus row design，而不是单纯解码长度不足。

## 测试覆盖

测试保护了几个关键边界：

- 当某个 decoding profile 让两个 term 都命中时，必须得到 `required_term_pair_decoding_sweep_recovered`。
- 当 profile 只命中一个 term 时，只能是 partial，不能误判为 recovered。
- source status fail、source 不是 partial-only、source 已经 full-hit、无 targets、无 profiles 都会产生 issue。
- artifact 输出覆盖 JSON/CSV/text/Markdown/HTML，保证报告可机器消费、可人工审阅、可截图归档。
- helper summary 测试保证 best profile 选择依据是 full-hit 优先，其次 hit count。

## 运行证据

- `e/498/解释/model-capability-required-term-pair-decoding-sweep/model_capability_required_term_pair_decoding_sweep.json`
- `e/498/解释/model-capability-required-term-pair-decoding-sweep/model_capability_required_term_pair_decoding_sweep.csv`
- `e/498/解释/model-capability-required-term-pair-decoding-sweep/model_capability_required_term_pair_decoding_sweep.html`
- `e/498/解释/model-capability-required-term-pair-decoding-sweep-cli.txt`
- `e/498/解释/model-capability-required-term-pair-decoding-sweep-snapshot.md`
- `e/498/图片/01-model-capability-required-term-pair-decoding-sweep.png`

## 一句话总结

v498 证明 v497 的 pair full-hit 缺口不是简单解码策略能补出来的；后续应回到 prompt/corpus 的目标分离设计，而不是继续盲目增加训练预算。
