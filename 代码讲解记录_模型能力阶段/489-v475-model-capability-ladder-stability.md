# v475：model capability ladder stability

## 本版目标和边界

v475 的目标是复核 v474 观察到的 tiny training signal 是否能跨 seed 重复。v474 已经证明 `max_iters=1,2,4` 的 ladder 可以跑通，并且 seed `1337` 下 best validation loss 有轻微下降；但单 seed 不足以判断这个方向是否稳定。

本版不做大模型训练，不引入外部 benchmark，也不把 tiny CPU smoke 的稳定 loss 下降称为真实模型能力跃迁。它只新增一个多 seed replay 层：把每个 seed 的 v474 ladder 报告读进来，比较 loss delta、score delta 和 generation flags delta。

## 前置能力

本版直接复用：

- `scripts/run_model_capability_ladder.py`
  - 负责单 seed 的完整 ladder。
- `src/minigpt/model_capability_ladder.py`
  - 提供 ladder report 和 `trend_summary`。
- `src/minigpt/model_capability_ladder_artifacts.py`
  - 提供单 seed ladder 的 JSON/CSV/text/Markdown/HTML 输出。

v475 只在这些能力之上增加 seed replay，不改训练模型本身。

## 关键新增和修改文件

- `src/minigpt/model_capability_ladder_stability.py`
  - 核心稳定性逻辑：解析 seed、读取每个 seed 的 trend delta、计算跨 seed 摘要。
- `src/minigpt/model_capability_ladder_stability_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
- `scripts/run_model_capability_ladder_stability.py`
  - CLI 入口，按 seed 调用 v474 ladder runner。
- `scripts/run_model_capability_ladder.py`
  - 增加单线程 CPU 环境，避免 PyTorch CPU 训练因 OpenMP/BLAS 线程竞争变慢。
- `tests/test_model_capability_ladder_stability.py`
  - 覆盖稳定性决策、输出文件、失败 seed、seed 参数校验和线程环境。
- `tests/test_model_capability_ladder.py`
  - 给 v474 runner 的单线程环境增加回归保护。

## 核心数据结构

最终报告是 `model_capability_ladder_stability.json`。

关键字段：

- `rows`
  - 每个 seed 一行。
  - 记录 `seed`、`trend_decision`、`best_val_loss_delta`、`score_delta`、`generation_flags_delta`。
- `stability_summary`
  - 汇总跨 seed 方向。
  - `loss_improvement_seed_count` 表示多少个 seed 的 loss delta 小于 0。
  - `eval_improvement_seed_count` 表示多少个 seed 出现 score 上升或 flags 下降。
  - `mean_best_val_loss_delta` 是跨 seed 的平均 loss delta。
- `interpretation`
  - 固定保留 `model_quality_claim=not_claimed`，防止把 tiny smoke 写成强模型质量声明。

## 稳定性判断

本版提供四种决策：

- `repeated_loss_with_some_eval_improvement`
  - 所有成功 seed 都 loss 下降，并且至少一个 seed 有 eval 侧改善。
- `repeated_loss_improvement_without_eval_improvement`
  - 所有成功 seed 都 loss 下降，但没有 score 或 flags 改善。
- `mixed_loss_improvement`
  - 只有部分 seed loss 下降。
- `no_repeated_training_signal`
  - 没有重复训练信号。

v475 的真实结果是 `repeated_loss_improvement_without_eval_improvement`。

## 线程环境修正

开发时发现，如果不限制 CPU 线程，当前桌面环境中单次 tiny train 可能从几秒变成一分半以上。这不是模型能力变化，而是 CPU 线程调度问题。

因此两个 runner 都注入：

```text
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1
OPENBLAS_NUM_THREADS=1
NUMEXPR_NUM_THREADS=1
```

这个改动让 tiny PyTorch smoke 更稳定，也让后续能力复核不会被环境线程竞争污染。

## 真实运行结果

配置：

- Seeds：`1337,2026`
- Max iters：`1,2,4`
- Suite：`standard-zh`
- Case token cap：`4`
- Tiny model：`n_layer=1`、`n_head=1`、`n_embd=8`

结果：

| Seed | Best val loss delta | Score delta | Generation flags delta |
| ---: | ---: | ---: | ---: |
| 1337 | -0.0031 | 0.0 | 0.0 |
| 2026 | -0.0286 | 0.0 | 0.0 |

解释：两个 seed 都出现 loss 下降，但没有 scorecard 或 generation-quality flags 改善。因此本版只能说明训练信号方向有初步重复性，不能说明模型输出能力已经明显变强。

## 测试覆盖

新增测试覆盖：

- 所有 seed loss 下降但无 eval 改善时，决策为 `repeated_loss_improvement_without_eval_improvement`。
- 至少一个 seed 有 score 或 flags 改善时，决策升级为 `repeated_loss_with_some_eval_improvement`。
- seed 数不足或 delta 缺失时，报告失败。
- JSON/CSV/text/Markdown/HTML 输出全部生成。
- seed 列表必须非空且唯一。
- runner 会注入单线程 CPU 环境。

本版还跑了真实双 seed ladder，证据写入 `e/475`，并用 Playwright MCP 检查 HTML 报告。

## 一句话总结

v475 让 MiniGPT 的模型能力观察从“单 seed 训练阶梯”推进到“双 seed 稳定性复核”，证明 loss 改善方向可重复，但仍没有观察到 scorecard 或 generation-quality 层面的能力提升。
