# v501 MiniGPT required-term pair loss-branch sweep 代码讲解

## 本版目标和边界

v501 接在 v500 的 contrast-free pair training 后面。v500 已经确认 `fixed/loss` 语料中的直接泄露被移除，但训练结果仍然只命中 `fixed`，稳定漏掉 `loss`。

本版目标不是继续扩展模型规模，也不是宣称模型质量提升，而是补一个更窄的真实训练实验：把 v500 中漏掉的 `loss` 分支放到更有利的位置，观察它能否被拉回，以及拉回后是否还能保留 `fixed`。

明确不做的事：

- 不恢复 v499 发现的负对比泄露行。
- 不扩展到三词或更多 required terms。
- 不把 partial/tradeoff 结果解释成 full-hit 能力。

## 前置路线

本版依赖上一版产物：

```text
e/500/解释/model-capability-required-term-pair-contrast-free-training/model_capability_required_term_pair_contrast_free_training.json
```

v500 的核心事实是：

- `contrast_free_training_decision=contrast_free_training_partial_only`
- 3 个 variants 全部命中 `fixed`
- 3 个 variants 全部漏掉 `loss`
- `variant_pair_full_hit_count=0`

v501 因此只处理“已去泄露但仍 partial”的 pair，不对已经 full-hit 的 pair 重复训练。

## 关键文件

### `src/minigpt/model_capability_required_term_pair_loss_branch_sweep.py`

这是本版主流程。它负责：

- 定位 v500 contrast-free training JSON。
- 从 `variant_summaries` 中找出稳定漏掉的分支。
- 生成 loss-branch sweep variants。
- 写出新的 clean corpus。
- 调用 tiny training。
- 对每个 checkpoint 分别 probe `fixed:` 和 `loss:`。
- 汇总 full-hit、focus-hit 和 tradeoff。

核心入口是：

```python
build_model_capability_required_term_pair_loss_branch_sweep(...)
```

输入是 v500 报告字典，输出是 v501 report dict。函数只在结构失败、输入不适合、或训练失败时把 `status` 置为 `fail`；模型仍然 partial 或 tradeoff 不算结构失败。

### `select_loss_branch_targets`

这个函数从 v500 的 `variant_summaries` 反推出诊断目标：

- `hit_terms` 统计源 variants 已命中的 term。
- `missed_terms` 统计源 variants 漏掉的 term。
- `stable_missed_terms` 表示每个源 variant 都漏掉的 term。
- `focus_missed_term` 是本版要救援的主分支。

真实 v501 中，它选出：

```text
pair_id=01-fixed-loss
hit_term_names=fixed
focus_missed_term=loss
stable_missed_terms=loss
```

### `build_required_term_pair_loss_branch_corpus`

这个函数生成新的 clean corpus。它支持三个关键参数：

- `term_order`
  - `source-order`：保留 v500 pair term 顺序。
  - `missed-first`：把漏掉的 `loss` 放在每轮前面。
- `missed_weight`
  - 给漏掉分支更多 clean row copy。
- `missed_anchor_repeat`
  - 在主体循环后追加漏掉分支的 anchor rows。

生成的行仍然是自己的 prompt 对自己的 term，例如：

```text
loss:loss
loss: loss
factual-val-loss|loss:loss
```

不会写：

```text
loss:loss not fixed
fixed:fixed not loss
```

所以 v501 是一个针对分支偏置的 clean 实验，不是把旧泄露放回来。

### `summarize_loss_branch_variant_probe_rows`

这个函数解释每个 variant 的 probe 结果。它区分三种情况：

- `pair_full_hit=True`
  - `fixed` 和 `loss` 都命中。
- `focus_missed_term_hit=True`
  - 原先漏掉的 `loss` 被拉回。
- `branch_tradeoff=True`
  - `loss` 被拉回，但源命中的 `fixed` 丢失。

真实 v501 三个 variants 都是 `branch_tradeoff=True`。

### `src/minigpt/model_capability_required_term_pair_loss_branch_sweep_artifacts.py`

这是产物渲染层，输出：

- JSON：完整结构化证据。
- CSV：每条 probe 的 continuation hit 和 preview。
- TXT：命令行摘要。
- Markdown：适合阅读和归档。
- HTML：适合截图和快速复查。

它不训练模型，也不改变判断逻辑，只把主流程 report 渲染成证据格式。

### `scripts/run_model_capability_required_term_pair_loss_branch_sweep.py`

这是 CLI 入口。典型命令：

```powershell
python -B scripts/run_model_capability_required_term_pair_loss_branch_sweep.py e/500/解释/model-capability-required-term-pair-contrast-free-training --out-dir e/501/解释/model-capability-required-term-pair-loss-branch-sweep --force --require-pass
```

它支持：

- 输入 v500 JSON 或目录。
- `--variant-preset default|fast`。
- `--require-pass` 作为结构失败门禁。
- `--force` 清空已有输出目录。

## 真实运行链路

1. 读取 v500 JSON。
2. 识别 `01-fixed-loss` 的稳定漏分支为 `loss`。
3. 生成三个 variants：
   - `missed-first-order`
   - `missed-boosted`
   - `missed-anchored`
4. 每个 variant 写一个 corpus。
5. 每个 corpus 训练一个 tiny checkpoint。
6. 每个 checkpoint probe 两个 prompt：
   - `fixed:`
   - `loss:`
7. 汇总是否 full-hit、是否拉回 `loss`、是否丢掉 `fixed`。

## 本版真实结果

```text
status=pass
decision=required_term_pair_loss_branch_tradeoff
loss_branch_sweep_decision=loss_branch_sweep_tradeoff_only
training_run_count=3
training_pass_count=3
probe_count=6
probe_hit_count=3
focus_term_hit_variant_count=3
pair_full_hit_variant_count=0
branch_tradeoff_variant_count=3
```

三个 variants 都把 `loss` 拉回来了，但没有任何一个 variant 同时保住 `fixed`。

典型 continuation：

```text
fixed: -> losssssssss
loss:  -> losssssssss
```

这说明 v501 的能力证据是 tradeoff，而不是 full recovery。

## 测试覆盖

新增测试文件：

```text
tests/test_model_capability_required_term_pair_loss_branch_sweep.py
```

覆盖点包括：

- full-hit fake case：确认 report 能识别“真正恢复”。
- tradeoff fake case：确认 `loss` 命中但 `fixed` 丢失时不会被误判成 full-hit。
- input failure：当源报告已经 full-hit 时，本版拒绝重复诊断。
- corpus cleanliness：确认新 corpus 不包含 `not loss` 或 `not fixed`。
- artifacts：确认 JSON/CSV/TXT/Markdown/HTML 都能写出。

这些测试保护的是本版判断边界：结构通过、模型 tradeoff、模型 full-hit 是三件不同的事。

## 运行证据

运行证据位于：

```text
e/501
```

其中：

- `e/501/解释/说明.md` 记录真实命令、结果和解释。
- `e/501/解释/model-capability-required-term-pair-loss-branch-sweep/` 保存 JSON/CSV/TXT/Markdown/HTML、corpus 和 checkpoint。
- `e/501/图片/01-model-capability-required-term-pair-loss-branch-sweep.png` 是 HTML 报告截图。

## 一句话总结

v501 把 `loss` 从 v500 的稳定漏项拉回成稳定命中，但同时丢掉 `fixed`，把问题定位为 tiny pair 条件选择 tradeoff，而不是单个 required term 完全学不会。
