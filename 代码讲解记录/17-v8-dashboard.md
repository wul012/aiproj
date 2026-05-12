# 17 v8 dashboard 讲解

这一篇讲的是 v8 新增的 `src/minigpt/dashboard.py` 和 `scripts/build_dashboard.py`。

v8 的目标是把前面版本分散生成的实验产物汇总成一个本地静态 HTML：

```text
训练历史
 -> loss 曲线
 -> evaluation report
 -> model report
 -> next-token prediction
 -> attention map
 -> chat transcript
 -> sample text
 -> dashboard.html
```

`dashboard.py` 做三件事：

```text
收集 run 目录里的产物路径
读取 JSON/TXT/SVG 里的关键信息
渲染成 dashboard.html
```

核心入口是：

```python
build_dashboard_payload(run_dir, output_path)
write_dashboard(run_dir, output_path)
```

`collect_artifacts` 会检查这些常见文件是否存在：

```text
checkpoint.pt
tokenizer.json
train_config.json
metrics.jsonl
history_summary.json
loss_curve.svg
sample.txt
eval_report.json
model_report/model_report.json
model_report/model_architecture.svg
predictions/predictions.json
predictions/predictions.svg
attention/attention.json
attention/attention.svg
transcript.json
generated.txt
```

存在的文件会变成可点击链接，缺失的文件会以 missing 状态展示。这样 dashboard 可以服务于不同阶段的 run：只训练过也能打开，做过预测/attention/chat 后会自动展示更多区块。

`render_dashboard_html` 负责把 payload 变成 HTML。它会展示：

```text
overview 统计卡片
artifact 文件网格
model 参数分布和架构 SVG
training summary 和 loss curve
prediction top-k 表格和 SVG
attention top links 和 heatmap
chat transcript
sample/generated 文本
```

其中所有文本都会用 `html.escape` 转义，避免样例文本里出现 `<script>` 这类内容时破坏 HTML。

`scripts/build_dashboard.py` 是命令行入口：

```powershell
python scripts/build_dashboard.py --run-dir runs/minigpt
```

默认输出：

```text
runs/minigpt/dashboard.html
```

一句话总结：v8 把 MiniGPT 从“很多独立命令行观察工具”推进到“一个可复盘的实验报告页面”。
