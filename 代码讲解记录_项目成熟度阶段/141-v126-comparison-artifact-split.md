# v126 comparison artifact split 代码讲解

## 本版目标

v126 继续按 v110 module pressure audit 做定向收口，目标是把 baseline run comparison 里的证据输出层拆成独立模块：

```text
comparison.py           -> run summarization, baseline selection, deltas, summary, recommendations
comparison_artifacts.py -> JSON/CSV/SVG/Markdown/HTML writers and render helpers
```

本版解决的问题是：`comparison.py` 是项目较早版本的 baseline model comparison 模块，后来同时承担 run 读取、baseline delta 计算、recommendation 生成、CSV/SVG/Markdown/HTML 输出和 HTML 转义。v125 之后 module pressure 报告把它识别为下一处压力点，所以 v126 将稳定的 artifact 发布边界抽出来。

本版明确不做：

- 不改变 `build_comparison_report()` 返回的 schema。
- 不改变 `scripts/compare_runs.py` 的参数和输出文件名。
- 不改变 `comparison.json`、`comparison.csv`、`comparison.svg`、`comparison.md`、`comparison.html` 的含义。
- 不改变 `from minigpt.comparison import write_comparison_outputs` 等旧导入入口。
- 不扩大训练规模，也不声明模型质量提升。

## 前置路线

v126 接在这条收口路线后面：

```text
v118 benchmark scorecard comparison artifact split
 -> v122 training portfolio comparison artifact split
 -> v126 baseline run comparison artifact split
```

这说明项目不是继续做新的 report 变体，而是回到已有比较模块，把“比较计算”和“证据发布”分清楚。run comparison 是早期模块，补上这个边界后，比较类模块的结构更加一致。

## 关键文件

```text
src/minigpt/comparison.py
src/minigpt/comparison_artifacts.py
tests/test_comparison.py
tests/test_comparison_artifacts.py
README.md
c/126/图片
c/126/解释/说明.md
```

`src/minigpt/comparison.py` 继续负责比较本身：

- `RunComparison` 记录单个 run 的 tokenizer、dataset、loss、perplexity、参数量和模型结构签名。
- `summarize_run()` 读取 run 目录下的 `train_config.json`、`history_summary.json`、`eval_report.json`、`model_report.json`、`run_manifest.json`、`dataset_quality.json`、`dataset_version.json`。
- `build_comparison_report()` 汇总多个 run，选 baseline，计算 baseline deltas，生成 summary、best run 和 recommendations。
- `_baseline_delta()`、`_comparison_summary()`、`_comparison_recommendations()` 保留比较语义。
- 旧 artifact 函数名从 `comparison_artifacts.py` re-export，保护旧入口。

`src/minigpt/comparison_artifacts.py` 是本版新增模块，只负责发布证据：

- `write_comparison_json()` 写主 JSON 证据。
- `write_comparison_csv()` 写表格对比证据。
- `write_comparison_svg()` 生成轻量可视化。
- `render_comparison_markdown()` / `write_comparison_markdown()` 生成 Markdown 摘要。
- `render_comparison_html()` / `write_comparison_html()` 生成浏览器报告。
- `write_comparison_outputs()` 一次性写出五类 artifact。
- `_e()`、`_md()`、`_fmt*()`、`_stat_card()`、`_comparison_style()` 只服务输出层。

## 核心数据结构

`RunComparison` 是比较计算层的核心 dataclass。它不是训练配置本身，而是一个 run 的可比较摘要：

```text
name/path
tokenizer
dataset_version/dataset_fingerprint
max_iters/metrics_records
best_val_loss/last_val_loss/eval_loss/perplexity
total_parameters
n_layer/n_head/n_embd/block_size/vocab_size
token_count/train_token_count/val_token_count
model_signature
dashboard_exists
```

`build_comparison_report()` 输出的 report 是后续 artifact 的唯一输入。artifact 模块不再重新读取 run 目录，它只消费这个已经计算好的 report。这样边界更清楚：

```text
run directories
 -> comparison.py builds report dict
 -> comparison_artifacts.py writes evidence files
```

## 输出证据

`comparison.json` 是主证据，保留完整 schema、runs、baseline、baseline_deltas、summary、best_by_* 和 recommendations。

`comparison.csv` 是表格视图，适合快速比较 loss delta、参数量 ratio、tokenizer/model/dataset 是否变化。

`comparison.svg` 是轻量图像证据，展示 best validation loss 和参数量的可视化对比。

`comparison.md` 是可放进 release note 或讲解文档的人工阅读摘要。

`comparison.html` 是浏览器报告，适合截图和演示。v126 用 Playwright/Chrome 打开该 HTML，证明拆分后的 renderer 仍能真实渲染。

这些产物都是只读证据，不反向修改 run，也不参与训练。

## 测试覆盖

`tests/test_comparison.py` 继续覆盖旧行为：

- `summarize_run()` 能从 run 目录读取关键字段。
- `build_comparison_report()` 能选 best run、baseline、baseline deltas。
- CSV、SVG、Markdown、HTML 输出仍存在。
- HTML escaping 仍保护 `<baseline>` 和 `<data>` 这类文本。

`tests/test_comparison_artifacts.py` 新增三类断言：

- `comparison.py` re-export 的 artifact 函数与 `comparison_artifacts.py` 中的真实函数是同一个对象，保护旧入口。
- `write_comparison_outputs()` 能生成 JSON/CSV/SVG/Markdown/HTML 五类文件。
- renderer 能输出 summary 字段，并且 HTML 仍正确转义 baseline 名称。

本版还跑了：

```text
python -m compileall -q src/minigpt/comparison.py src/minigpt/comparison_artifacts.py tests/test_comparison.py tests/test_comparison_artifacts.py
python -m unittest tests.test_comparison tests.test_comparison_artifacts
python -m unittest discover -s tests
python scripts/compare_runs.py ... --out-dir tmp/v126-comparison-smoke/out
python scripts/check_maintenance_batching.py --out-dir tmp/v126-maintenance-smoke ...
```

## 体量变化

拆分后：

```text
comparison.py           -> 342 nonblank lines
comparison_artifacts.py -> 293 nonblank lines
```

v126 的 module pressure smoke 显示：

```text
module_pressure_status=pass
module_warn_count=0
module_critical_count=0
largest_module=src\minigpt\registry_render.py
```

这说明本版不是大重构，而是用一个低风险边界把当前最大压力点降回可控区间。

## 运行证据

v126 的运行证据放在：

```text
c/126/图片
c/126/解释/说明.md
```

截图证明以下闭环：

- 新旧 comparison 测试和全量测试通过。
- CLI 能生成五类 comparison 输出。
- module pressure 从 warn 回到 pass。
- Playwright/Chrome 能打开拆分后的 comparison HTML。
- README、代码讲解和 c/126 归档都已更新。

## 一句话总结

v126 的价值是让 baseline run comparison 也具备清晰的“比较计算层 / artifact 发布层”边界，在不改变旧 CLI、schema 和导出的前提下降低模块压力。
