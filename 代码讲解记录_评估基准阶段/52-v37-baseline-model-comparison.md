# 52-v37-baseline-model-comparison

## 本版目标、来源和边界

v37 的目标是把早期 `compare_runs` 从“并排看几个 run”升级成“围绕一个 baseline 判断候选模型是否更好”。v36 已经给 prepared corpus 增加 `dataset_version.json`，因此本版可以在模型横向比较时同时回答三件事：

```text
这个候选模型比 baseline 的 best_val_loss 是升还是降？
它是不是换了 tokenizer、模型大小或训练步数？
它是否仍然使用同一个 dataset version？
```

本版不做三件事：

- 不训练更大的模型，也不声称指标代表真实通用能力。
- 不替代 benchmark eval suite 和 generation quality，只补“相对 baseline 的结构化比较”。
- 不把不同 dataset version 的 run 强行判为可比，只记录并提醒数据版本差异。

## 本版处在评估链路的哪一环

当前评估基准链路变成：

```text
dataset version
 -> training run manifest
 -> eval / history / model report
 -> baseline model comparison
 -> registry / model card / release-style evidence
```

v35 固定 prompt suite，v36 固定 dataset 身份，v37 固定“比较参照物”。这样后续看不同 tokenizer、模型大小、训练步数时，不再只看一堆孤立 loss，而是看“相对 baseline 改善了多少、代价是什么”。

## 关键文件

```text
src/minigpt/comparison.py
scripts/compare_runs.py
tests/test_comparison.py
src/minigpt/__init__.py
README.md
b/37/解释/说明.md
```

核心逻辑集中在 `comparison.py`。CLI 只新增 `--baseline`，保留旧的 run_dirs 和 `--name` 用法。

## 输入和输出

输入仍然是一组 run 目录：

```powershell
python scripts/compare_runs.py runs/tiny runs/wide --name tiny --name wide --baseline tiny --out-dir runs/comparison
```

`--baseline` 可以是 run name、run path 或 1-based index；不传时默认第一个 run 是 baseline。

输出现在包含：

```text
comparison.json
comparison.csv
comparison.svg
comparison.md
comparison.html
```

`comparison.html` 用于浏览器查看，`comparison.md` 方便贴到报告或答辩材料，`comparison.csv` 适合后续表格处理。

## JSON 字段语义

`comparison.json` 的关键结构是：

```json
{
  "schema_version": 2,
  "baseline": {},
  "runs": [],
  "baseline_deltas": [],
  "summary": {},
  "recommendations": []
}
```

其中 `runs` 会记录：

- `model_signature`：把 tokenizer、layer/head/embedding、block size、vocab size、参数量、训练步数压成一个可比较签名。
- `dataset_version`：来自 run manifest 或 `dataset_version.json`。
- `dataset_fingerprint`：来自 dataset version 或 dataset quality。
- `token_count` / `train_token_count` / `val_token_count`：来自 run manifest。

`baseline_deltas` 会记录每个 run 相对 baseline 的变化：

- `best_val_loss_delta`
- `best_val_loss_delta_pct`
- `eval_loss_delta`
- `perplexity_delta`
- `total_parameters_delta`
- `total_parameters_ratio`
- `max_iters_delta`
- `tokenizer_changed`
- `model_signature_changed`
- `dataset_version_changed`
- `best_val_loss_relation`

这里的 delta 方向是 `candidate - baseline`。所以 loss delta 小于 0 表示候选更好，参数 ratio 大于 1 表示候选更大。

## 为什么这版有工程价值

旧的比较报告能看出谁的 best_val_loss 更低，但不能直接回答：

```text
这个 run 是不是只因为换了数据才变好？
这个 run 变好付出了多少参数量代价？
这个 run 和 baseline 的 tokenizer 是否一致？
这个 run 能不能直接作为下一轮候选？
```

v37 把这些问题变成机器可读字段，并在 HTML/Markdown 里展示出来。它仍然是学习型项目，但已经开始接近真实实验管理中的 baseline comparison 思维。

## 测试覆盖链路

`tests/test_comparison.py` 覆盖：

- `summarize_run` 能读取 run manifest、dataset version、token count 和 model signature。
- `build_comparison_report` 默认选择第一个 run 作为 baseline。
- 显式 `baseline="small"` 能生成正确 delta。
- loss 下降被标为 `improved`，loss 上升被标为 `regressed`。
- CSV 包含 baseline delta 字段。
- `write_comparison_outputs` 生成 JSON/CSV/SVG/Markdown/HTML。
- HTML 渲染会转义 run name 和 dataset version 中的特殊字符。

这些断言保护的是“比较语义”和“证据出口”，不是某个固定样式。

## 归档和截图证据

本版运行证据放在：

```text
b/37/图片
b/37/解释/说明.md
```

关键截图包括：

```text
01-unit-tests.png
02-baseline-comparison-smoke.png
03-baseline-comparison-structure-check.png
04-playwright-baseline-comparison.png
05-docs-check.png
```

其中 `02` 证明 CLI 能比较 baseline/wide/BPE 三个候选；`03` 证明 JSON/CSV/SVG/Markdown/HTML 和 delta 字段齐全；`04` 证明新增 HTML 报告能被真实 Chrome 打开；`05` 证明 README、b/37 归档和讲解索引已经闭环。

## 一句话总结

v37 把 MiniGPT 的横向比较从“看多个 run 的数值”推进到“围绕 baseline 解释模型候选是否更好、代价多大、数据是否一致”的阶段。
