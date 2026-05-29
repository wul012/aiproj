# v496 model capability required-term pair rebalance seed stability

## 本版目标和边界

v496 的目标是复核 v495 的局部能力信号。v495 让 `fixed/loss` 从 v494 的 partial pair 变成了 full-hit pair，但它只是在一个 seed 下出现的结果。v496 不继续扩展三词，而是先对这个 improved pair 做跨 seed 重训，判断 full-hit 是否稳定。

本版不做模型扩容，不做新的语料大改，也不声明生产级模型质量。它只验证一个前置条件：v495 的 pair-level full-hit 能不能跨多个 seed 复现。如果不能，后续就不应该把它当成稳态能力继续往三词推进。

## 前置路线

- v493：`fixed/loss/four/chain` 在 one-term 条件下跨 seed 稳定。
- v494：这些稳定词两两组合后，6 个 pair 全部 partial-only。
- v495：通过 pair rebalance，`fixed/loss` 首次从 partial 变成 full-hit。
- v496：只选择 v495 中 `rebalance_pair_full_hit=True` 且 `hit_count_delta>0` 的 pair，跨 seed 复测。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_rebalance_seed_stability.py`
  - 读取 v495 pair rebalance report。
  - 选择真正改善为 full-hit 的 pair。
  - 对每个 pair 和 seed 重新生成 rebalance corpus、训练 checkpoint、运行两个 term probe。
  - 汇总 seed-level full-hit、pair-level 稳定性和下一步建议。
- `src/minigpt/model_capability_required_term_pair_rebalance_seed_stability_artifacts.py`
  - 写出 JSON、CSV、text、Markdown 和 HTML。
  - HTML 分为 pair stability 和 seed pair rows，方便看每个 seed 的 hit/missed terms。
- `scripts/run_model_capability_required_term_pair_rebalance_seed_stability.py`
  - CLI 入口，支持 `--seeds`、训练参数、`--force` 和 `--require-pass`。
- `tests/test_model_capability_required_term_pair_rebalance_seed_stability.py`
  - 覆盖稳定、部分稳定、训练失败、坏 source、空 seed、选择逻辑和 artifact 输出。
- `e/496/`
  - 保存真实 3 seed 复测产物、CLI 输出、Playwright snapshot 和截图。

## 核心数据结构

输入是 v495 的 `model_capability_required_term_pair_rebalance.json`，主要读取：

- `summary.pair_rebalance_decision`：必须是 `pair_rebalance_full_hit_gain`。
- `summary.pair_full_hit_count`：v495 的 full-hit pair 数，真实值为 `1`。
- `pairs`：提供 pair 的 term、prompt 和 case。
- `compare_rows`：用于判断哪些 pair 真正改善。

`select_rebalance_seed_stability_pairs()` 只选择：

```text
rebalance_pair_full_hit == True
hit_count_delta > 0
```

真实选中的 pair 只有一个：

```text
01-fixed-loss
```

每个 seed 产生一个 `pair_seed_row`，证明训练是否成功、checkpoint 是否存在、使用了哪份 seed corpus。每个 term probe 产生一个 `probe_row`，记录 `continuation_hit_count` 和生成片段。

## 运行流程

1. CLI 定位 v495 pair rebalance report。
2. builder 校验 source 为 `pass` 且存在 full-hit gain。
3. 选择 `fixed/loss` 这个 improved pair。
4. 对 seeds `496,1496,2496` 逐个训练 checkpoint。
5. 每个 seed 分别 probe `fixed:` 和 `loss:`。
6. `summarize_seed_pair_probe_rows()` 统计每个 seed 是否 full-hit。
7. `summarize_pair_seed_stability()` 判断该 pair 是否跨所有 seed 稳定 full-hit。
8. 写出 JSON/CSV/text/Markdown/HTML，并用 Playwright MCP 截图。

## 真实结果

```text
status=pass
decision=required_term_pair_rebalance_seed_stability_not_reproduced
pair_rebalance_seed_stability_decision=rebalance_full_pairs_not_reproduced_across_seeds
selected_pair_count=1
seed_count=3
pair_seed_run_count=3
probe_count=6
training_pass_count=3
checkpoint_exists_count=3
probe_hit_count=3
pair_seed_full_hit_count=0
stable_pair_count=0
pair_rebalance_seed_stable=False
model_quality_claim=not_claimed
```

明细是：

```text
seed 496  -> hit loss, miss fixed
seed 1496 -> hit loss, miss fixed
seed 2496 -> hit loss, miss fixed
```

这说明 v495 的 `fixed/loss` full-hit 不是稳定能力。它在 v496 的三个 seed 下都退回 partial，只能命中 `loss`。

## 测试覆盖

测试保护了几个关键判断：

- 当同一 pair 在所有 seed 下 full-hit 时，必须得到 `required_term_pair_rebalance_seed_stability_observed`。
- 当只在部分 seed full-hit 时，必须是 partial，而不能误判为 stable。
- 训练失败时状态为 `fail`，`--require-pass` 对应非零退出。
- source 不是 full-hit gain、source status fail、无 seed、无 selected pair 都会产生 issue。
- artifact 输出覆盖 JSON/CSV/text/Markdown/HTML，确保报告链路完整。

这些测试继承 `unittest.TestCase`，可以被仓库 coverage gate 的 `unittest discover` 直接计入。

## 运行证据

- `e/496/解释/model-capability-required-term-pair-rebalance-seed-stability/model_capability_required_term_pair_rebalance_seed_stability.json`
- `e/496/解释/model-capability-required-term-pair-rebalance-seed-stability/model_capability_required_term_pair_rebalance_seed_stability.csv`
- `e/496/解释/model-capability-required-term-pair-rebalance-seed-stability/model_capability_required_term_pair_rebalance_seed_stability.html`
- `e/496/解释/model-capability-required-term-pair-rebalance-seed-stability-cli.txt`
- `e/496/解释/model-capability-required-term-pair-rebalance-seed-stability-snapshot.md`
- `e/496/图片/01-model-capability-required-term-pair-rebalance-seed-stability.png`

## 一句话总结

v496 没有制造新的乐观结论，而是把 v495 的单 seed full-hit 放到跨 seed 复核下，证明它仍是脆弱信号；后续应先提升 pair 稳定性，再考虑三词 curriculum。
