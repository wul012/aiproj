# v502 MiniGPT required-term pair branch-retention sweep 代码讲解

## 本版目标和边界

v502 接在 v501 的 loss-branch sweep 后面。v501 已经证明 `loss` 不是完全学不会：只要把语料偏向 `loss`，模型就会输出 `loss`。但代价是原本能命中的 `fixed` 丢掉了。

本版目标是测试另一个更工程化的问题：在不恢复负对比泄露的前提下，能不能用更平衡的 clean corpus 同时保住两条分支。

本版明确不做：

- 不扩展到三词或更多 required terms。
- 不增加旧的 `not loss` / `not fixed` 对比泄露行。
- 不把 partial/tradeoff 结果当成模型质量提升。

## 前置路线

本版读取 v501 的最终产物：

```text
e/501/解释/model-capability-required-term-pair-loss-branch-sweep/model_capability_required_term_pair_loss_branch_sweep.json
```

v501 的事实是：

- `loss_branch_sweep_decision=loss_branch_sweep_tradeoff_only`
- `focus_term_hit_variant_count=3`
- `pair_full_hit_variant_count=0`
- `branch_tradeoff_variant_count=3`

这意味着 `loss` 能被拉回，但不能和 `fixed` 同时稳定保留。

## 关键文件

### `src/minigpt/model_capability_required_term_pair_branch_retention_sweep.py`

这是 v502 主流程。它负责：

- 定位 v501 loss-branch sweep JSON。
- 选择存在 branch tradeoff 的 pair。
- 生成 balanced branch-retention variants。
- 训练新的 tiny checkpoints。
- 对每个 checkpoint probe `fixed:` 和 `loss:`。
- 输出 full-hit、balanced-retention 和 tradeoff 统计。

主入口是：

```python
build_model_capability_required_term_pair_branch_retention_sweep(...)
```

它把模型结果和结构失败分开：训练结构通过但没有 full-hit 时，`status` 仍然是 `pass`，`decision` 会保守地落到 `required_term_pair_branch_retention_partial`。

### `src/minigpt/model_capability_required_term_pair_branch_retention_sweep_components.py`

这是本版的选择、语料和汇总层，避免主文件继续膨胀。

关键函数：

- `select_branch_retention_targets`
  - 从 v501 `target_summaries` 中选择 `branch_tradeoff_variant_count > 0` 的 pair。
  - 真实 v502 只选择 `01-fixed-loss`。
- `normalize_branch_retention_variants`
  - 规范化 variant 参数，包括 `cycle_strategy`、`term_weight` 和 `symmetric_anchor_repeat`。
- `build_required_term_pair_branch_retention_corpus`
  - 生成 balanced clean corpus。
  - 支持 source-order、reverse-order 和 alternating 轮换。
- `summarize_branch_retention_variant_probe_rows`
  - 对每个 variant 判断命中哪些 term、是否保住 source hit、是否命中 focus missed term。
- `summarize_required_term_pair_branch_retention_sweep`
  - 生成最终 summary 和决策字段。

### corpus 设计

本版有三个默认 variants：

```text
alternating-balanced
symmetric-boost
symmetric-anchor
```

它们都只写清洁映射，例如：

```text
fixed:fixed
fixed: fixed
comparison-baseline|fixed:fixed
loss:loss
loss: loss
factual-val-loss|loss:loss
```

不会写：

```text
fixed:fixed not loss
loss:loss not fixed
```

因此本版不是回退到旧泄露语料，而是验证“平衡 clean 语料”能否解决 pair branch retention。

### `src/minigpt/model_capability_required_term_pair_branch_retention_sweep_artifacts.py`

这是产物渲染层，负责写出：

- JSON
- CSV
- TXT
- Markdown
- HTML

HTML 用于 Playwright 截图，CSV 用于快速比较每个 probe 的 continuation，JSON 是后续版本最重要的机器可读输入。

### `scripts/run_model_capability_required_term_pair_branch_retention_sweep.py`

这是 CLI 入口。真实运行命令：

```powershell
python -B scripts/run_model_capability_required_term_pair_branch_retention_sweep.py e/501/解释/model-capability-required-term-pair-loss-branch-sweep --out-dir e/502/解释/model-capability-required-term-pair-branch-retention-sweep --force --require-pass
```

它支持：

- 输入 v501 JSON 或目录。
- `--variant-preset default|fast`。
- `--require-pass` 作为结构失败门禁。
- `--force` 覆盖已有输出目录。

## 真实运行结果

```text
status=pass
decision=required_term_pair_branch_retention_partial
branch_retention_sweep_decision=branch_retention_sweep_tradeoff_remains
training_run_count=3
training_pass_count=3
probe_count=6
probe_hit_count=2
focus_term_hit_variant_count=0
source_retained_variant_count=2
balanced_retention_variant_count=0
pair_full_hit_variant_count=0
retention_tradeoff_variant_count=2
```

解释如下：

- `alternating-balanced` 命中 `fixed`，漏掉 `loss`。
- `symmetric-boost` 命中 `fixed`，漏掉 `loss`。
- `symmetric-anchor` 两边都没稳定命中。

这说明 v502 没有恢复 full-hit，反而证明继续做 corpus 权重微调已经收益变低。

## 测试覆盖

新增测试：

```text
tests/test_model_capability_required_term_pair_branch_retention_sweep.py
```

覆盖内容：

- fake full-hit case：确认真正同时命中 `fixed/loss` 时会被识别为 recovered。
- fake tradeoff case：确认只命中一边时不会误判。
- input failure：当源报告已经 full-hit 时，本版拒绝重复诊断。
- corpus balance：确认 `fixed:fixed` 和 `loss:loss` 数量对称，且不包含 `not loss` / `not fixed`。
- renderer：确认 JSON/CSV/TXT/Markdown/HTML 均能写出。

这些测试保护的是本版最重要的边界：clean corpus、balanced variants、partial 不冒充 full-hit。

## 运行证据

运行证据位于：

```text
e/502
```

其中：

- `e/502/解释/说明.md` 记录真实命令和实验解释。
- `e/502/解释/model-capability-required-term-pair-branch-retention-sweep/` 保存 JSON/CSV/TXT/Markdown/HTML、corpus 和 checkpoints。
- `e/502/图片/01-model-capability-required-term-pair-branch-retention-sweep.png` 是 HTML 报告截图。

## 一句话总结

v502 证明对称 clean corpus 仍不能解决 `fixed/loss` pair 的条件分支选择问题，下一步应该转向更小粒度的 decoding/evaluation diagnostic，而不是继续堆 corpus 权重。
