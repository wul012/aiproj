# 19 v9 run comparison 讲解

这一篇讲的是 v9 新增的 `src/minigpt/comparison.py` 和 `scripts/compare_runs.py`。

v9 的目标是把多个 MiniGPT 实验横向放在一起比较：

```text
run A
run B
run C
 -> 读取各自 train_config/history/eval/model_report
 -> 汇总 tokenizer、训练步数、loss、perplexity、参数量、模型配置
 -> 找出 best validation loss / eval loss / perplexity 最好的 run
 -> 写 comparison.json
 -> 写 comparison.csv
 -> 写 comparison.svg
```

`comparison.py` 里的核心数据结构是：

```python
RunComparison
```

它记录一个 run 的关键字段：

```text
name
path
tokenizer
max_iters
metrics_records
best_val_loss
last_val_loss
eval_loss
perplexity
total_parameters
n_layer / n_head / n_embd
block_size / vocab_size
dashboard_exists
```

`summarize_run` 只读取 run 目录里的产物，不重新训练模型：

```text
train_config.json
history_summary.json
eval_report.json
model_report/model_report.json
metrics.jsonl
dashboard.html
```

这让比较工具很轻量。只要一个目录里有这些文件，它就可以被比较；如果某些文件缺失，对应字段就是 `None`。

`build_comparison_report` 会生成总报告，并自动找出：

```text
best_by_best_val_loss
best_by_eval_loss
best_by_perplexity
```

注意这些“best”只是基于当前 run 的本地小语料和当前评估命令，不能代表真实大模型能力。它适合学习时观察趋势：

```text
模型变宽后参数量如何变化
训练步数变化后 loss 是否变化
tokenizer 改变后 perplexity 是否变化
```

`scripts/compare_runs.py` 是命令行入口：

```powershell
python scripts/compare_runs.py runs/a runs/b --name tiny --name wide --out-dir runs/comparison
```

一句话总结：v9 让 MiniGPT 不只会分析单个 checkpoint，还能比较多个实验，开始具备实验管理的雏形。
