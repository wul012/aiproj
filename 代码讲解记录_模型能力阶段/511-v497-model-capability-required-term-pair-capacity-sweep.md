# v497 model capability required-term pair capacity sweep

## 本版目标和边界

v497 的目标是承接 v496 的负结果：v495 中 `fixed/loss` 曾经出现 full-hit，但 v496 用 seeds `496,1496,2496` 复测后全部退回 partial，只命中 `loss`。因此本版不扩展三词，不继续堆新治理链，而是做一个更直接的能力实验：固定 `fixed/loss` 这个脆弱 pair，扫训练步数、embedding 宽度和语料密度，看 full-hit 是否能被容量变化恢复。

本版不声明生产级模型质量，也不把 partial hit 解释为模型能力提升。它只回答一个问题：v495 的双命中是不是“稍微加容量就能稳定回来”的信号。

## 前置路线

- v493：`fixed/loss/four/chain` 在 one-term 条件下跨 seed 稳定。
- v494：这些稳定词两两组合后，6 个 pair 全部 partial-only。
- v495：pair rebalance 让 `fixed/loss` 首次出现 full-hit。
- v496：同一 pair 跨 3 个 seed 复测，`0/3` seed full-hit。
- v497：对这个 fragile pair 做 capacity sweep，避免在不稳定基础上扩展三词。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_capacity_sweep.py`
  - 读取 v496 seed-stability report。
  - 选择 `stable_full_hit_across_seeds=False` 的 fragile full-hit-gain pair。
  - 定义默认 capacity variants：baseline repeat、longer iters、wider embedding、denser corpus。
  - 为每个 variant 生成 pair corpus、训练 checkpoint、运行两个 term probe。
  - 汇总 variant-level full hit、pair-level recovered signal 和下一步建议。
- `src/minigpt/model_capability_required_term_pair_capacity_sweep_artifacts.py`
  - 输出 JSON、CSV、text、Markdown 和 HTML。
  - HTML 把卡片指标、variant results、pair summary 分开，方便直接截图验收。
- `scripts/run_model_capability_required_term_pair_capacity_sweep.py`
  - CLI 入口，支持 `--variant-preset default|fast`、训练基础参数、`--force` 和 `--require-pass`。
- `tests/test_model_capability_required_term_pair_capacity_sweep.py`
  - 用 `unittest.TestCase` 覆盖 recovered、partial、training failure、坏 source、空 variants、选择逻辑和 artifact 输出。
- `e/497/`
  - 保存真实容量扫描产物、CLI 输出、Playwright snapshot 和截图。

## 核心数据结构

输入是 v496 的 `model_capability_required_term_pair_rebalance_seed_stability.json`，核心字段是：

```text
summary.source_pair_rebalance_decision = pair_rebalance_full_hit_gain
summary.pair_rebalance_seed_stability_decision = rebalance_full_pairs_not_reproduced_across_seeds
pairs[]
pair_seed_summaries[]
```

`select_pair_capacity_sweep_pairs()` 只选择跨 seed 不稳定的 pair。真实数据里只选中：

```text
01-fixed-loss
```

每个 capacity variant 会产生一个 `capacity_row`：

- `capacity_run_id`：如 `01-fixed-loss-longer-iters-seed-496`。
- `capacity_corpus_path`：该 variant 的训练语料。
- `max_iters / n_embd / repeat`：本次容量变化参数。
- `checkpoint_exists / tokenizer_exists / metrics_exists / train_config_exists`：训练证据。

每个 term probe 会产生一个 `probe_row`：

- `variant_id`
- `term`
- `generated_preview`
- `continuation_preview`
- `continuation_hit_count`

这使报告可以区分“训练失败”“checkpoint 缺失”和“模型确实没有在 continuation 中生成目标词”。

## 运行流程

1. CLI 定位 v496 seed-stability report。
2. builder 校验 source status 为 `pass`，且来源确实是 v495 full-hit gain。
3. 选择 fragile pair：`fixed/loss`。
4. 生成 4 个 capacity variants：
   - `baseline-repeat`
   - `longer-iters`
   - `wider-embd`
   - `denser-corpus`
5. 每个 variant 重新构造 pair rebalance corpus。
6. 每个 variant 训练一个 tiny checkpoint。
7. 对 `fixed:` 和 `loss:` 分别运行短 continuation probe。
8. `summarize_capacity_variant_probe_rows()` 统计每个 variant 是否 full-hit。
9. `summarize_pair_capacity_sweep()` 汇总某个 pair 是否在任一 variant 中恢复 full-hit。
10. 写出 JSON/CSV/text/Markdown/HTML，并用 Playwright MCP 截图。

## 真实结果

```text
status=pass
decision=required_term_pair_capacity_sweep_partial
pair_capacity_sweep_decision=pair_capacity_sweep_partial_only
selected_pair_count=1
variant_count=4
variant_run_count=4
probe_count=8
training_pass_count=4
checkpoint_exists_count=4
probe_hit_count=2
variant_pair_full_hit_count=0
variant_pair_partial_hit_count=2
capacity_full_hit_observed=False
best_variant_id=longer-iters
best_variant_hit_count=1
model_quality_claim=not_claimed
```

variant 明细：

```text
baseline-repeat -> hit loss, miss fixed
longer-iters   -> hit loss, miss fixed
wider-embd     -> miss fixed, miss loss
denser-corpus  -> miss fixed, miss loss
```

这说明当前问题不是“单纯把 1600 步改成 2400 步就能解决”，也不是“embedding 从 64 到 96 就能恢复”。`denser-corpus` 也没有带来恢复，下一步更应该检查 prompt 形状、生成长度、解码策略和 pair corpus 的正负样本设计。

## 测试覆盖

测试保护了几类关键行为：

- 当某个 variant 对 `fixed/loss` 双命中时，决策必须是 `required_term_pair_capacity_sweep_recovered`。
- 当只命中一个词时，决策必须保持 `required_term_pair_capacity_sweep_partial`，不能误报 full-hit。
- 训练失败时 report status 必须为 `fail`，`--require-pass` 应返回非零退出。
- source 不是 v495 full-hit gain、source status fail、无 fragile pair、无 variants 时都要产生 issue。
- artifact 输出覆盖 JSON/CSV/text/Markdown/HTML，保证报告可机器消费、可人工审阅、可截图归档。

## 运行证据

- `e/497/解释/model-capability-required-term-pair-capacity-sweep/model_capability_required_term_pair_capacity_sweep.json`
- `e/497/解释/model-capability-required-term-pair-capacity-sweep/model_capability_required_term_pair_capacity_sweep.csv`
- `e/497/解释/model-capability-required-term-pair-capacity-sweep/model_capability_required_term_pair_capacity_sweep.html`
- `e/497/解释/model-capability-required-term-pair-capacity-sweep-cli.txt`
- `e/497/解释/model-capability-required-term-pair-capacity-sweep-snapshot.md`
- `e/497/图片/01-model-capability-required-term-pair-capacity-sweep.png`

## 一句话总结

v497 把 v496 的脆弱 pair 放进容量扫描里复核，结果证明简单加预算、加宽度或加语料密度仍不能恢复 full-hit；项目下一步应先诊断 prompt/解码/语料形状，而不是继续扩展目标词数量。
