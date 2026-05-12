# 32. v17 Run Registry

这一版新增 `src/minigpt/registry.py` 和 `scripts/register_runs.py`，把多个 run 目录整理成一个实验注册表。

## 文件角色

`registry.py` 负责读取 run 目录里的：

- `run_manifest.json`
- `train_config.json`
- `history_summary.json`
- `dataset_quality.json`
- `eval_suite/eval_suite.json`
- 常见 artifact 是否存在

然后输出统一的 `registry.json`、`registry.csv` 和 `registry.svg`。

`register_runs.py` 是命令行入口，可以直接传 run 目录，也可以用 `--discover` 从一个父目录下自动发现带 `run_manifest.json` 的 run。

## 核心流程

```text
run directories
 -> summarize_registered_run
 -> build_run_registry
 -> best_by_best_val_loss
 -> dataset_fingerprints / quality_counts
 -> registry.json / registry.csv / registry.svg
```

## 与 comparison 的区别

`compare_runs.py` 更偏训练指标对比，主要看 loss、perplexity、参数量。

`register_runs.py` 更偏实验资产索引，会同时记录：

- Git commit 和 dirty 状态。
- tokenizer、max_iters、参数量。
- 数据来源类型。
- dataset fingerprint。
- dataset quality 状态。
- eval suite case 数和平均不同字符数。
- artifact 数量、checkpoint/dashboard 是否存在。

所以 registry 更适合做“实验目录”和后续检索，comparison 更适合做“指标对比”。

## 输出意义

`registry.json` 适合被程序继续读取。

`registry.csv` 适合用表格软件查看。

`registry.svg` 适合快速放进截图归档，观察每个 run 的 best val loss、artifact 数量、数据质量和 eval suite 覆盖情况。

## 一句话总结

v17 把分散在多个目录里的实验结果收成一张索引表，让 MiniGPT 项目开始具备“管理很多实验”的能力。
