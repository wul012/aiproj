# 第六十八版代码讲解：Training Portfolio Comparison

## 本版目标、来源和边界

v68 的目标是把 v67 的单次 `training_portfolio.json` 推进为多次实验组合对比。v67 已经能从数据源一路跑到 checkpoint、eval suite、generation quality、benchmark scorecard、dataset card、registry、maturity summary 和 maturity narrative；但它回答的是“这一轮训练是否完整”。v68 继续回答“多轮训练之间谁更好，为什么更好，是否有证据缺口”。

本版来自当前路线里的“真实评估、数据版本、模型对比、本地训练组合收口”。它不重新训练模型，不重新计算 benchmark，也不替代 v53 的 benchmark scorecard comparison。v53 只比较 scorecard；v68 比较的是整份 portfolio，并额外读取 scorecard、dataset card、manifest、eval suite、generation quality 和 maturity narrative 的关键字段。

明确不做的事情：

- 不判断一个模型是否能生产使用，只给学习型 MiniGPT 实验的可比证据。
- 不自动选择更大语料，也不下载外部数据。
- 不改 v67 pipeline 的执行顺序，避免把“跑实验”和“比较实验”绑死。
- 不把所有下游 JSON 原文塞进报告，只抽取对横向比较有意义的摘要字段。

## 本版接在什么链路后面

v67 的链路是：

```text
source txt
 -> prepare_dataset
 -> train
 -> eval_suite
 -> generation_quality
 -> benchmark_scorecard
 -> dataset_card
 -> registry
 -> maturity_summary
 -> maturity_narrative
 -> training_portfolio.json
```

v68 的链路是：

```text
training_portfolio.json (baseline)
training_portfolio.json (candidate)
training_portfolio.json (review/regressed...)
 -> compare_training_portfolios.py
 -> training_portfolio_comparison.json/csv/md/html
```

也就是说，v68 把“单次实验组合跑”变成“多次实验组合跑的可比报告”。这为后续真正跑更大中文语料、不同模型尺寸、不同 tokenizer 或 LoRA 对照时提供统一入口。

## 关键新增文件

### `src/minigpt/training_portfolio_comparison.py`

这是本版核心模块，负责读取、汇总、比较和渲染。

关键公开函数：

- `load_training_portfolio(path)`：接受 `training_portfolio.json` 文件或包含该文件的目录，读取 JSON，并补充 `_source_path`，让后续命名、相对路径解析和错误定位有来源。
- `build_training_portfolio_comparison(...)`：构建完整比较报告。它加载多份 portfolio，解析显示名，选择 baseline，生成每个 portfolio 的摘要和 baseline delta。
- `write_training_portfolio_comparison_outputs(...)`：一次性输出 JSON、CSV、Markdown、HTML 四种证据产物。
- `render_training_portfolio_comparison_markdown(...)` / `render_training_portfolio_comparison_html(...)`：把同一个结构化 report 渲染成人读版本。

核心内部结构是 portfolio summary：

```text
name
source_path
run_name
dataset_name / dataset_version / dataset
status / execute / step_count / completed_steps / failed_step
artifact_count / available_artifact_count / artifact_coverage
core_artifacts
overall_score / rubric_avg_score / weakest_rubric_case
best_val_loss / final_val_loss / parameter_count
train_token_count / val_token_count / eval_case_count
generation_quality_status
dataset_readiness_status / dataset_quality_status / dataset_warning_count
maturity_portfolio_status / maturity_release_readiness_trend
```

这些字段分别来自：

- portfolio 自身的 `execution` 和 `artifacts`。
- `benchmark_scorecard.json` 的 `summary`。
- `dataset_card.json` 的 `dataset` 和 `summary`。
- `run_manifest.json` 的 `data`、`model`、`results.history_summary`。
- `eval_suite.json` 的 suite 名称、版本和 case 数。
- `generation_quality.json` 的质量状态、case 数和唯一字符比例。
- `maturity_narrative.json` 的 portfolio status、release trend 和 request history status。

### `scripts/compare_training_portfolios.py`

这是命令行入口。用法示例：

```powershell
python scripts/compare_training_portfolios.py runs/a/training_portfolio.json runs/b/training_portfolio.json --name small --name larger --baseline small --out-dir runs/training-portfolio-comparison
```

CLI 的设计保持和已有 comparison 脚本一致：

- 位置参数接收一个或多个 portfolio 文件或目录。
- `--name` 可以重复，用来给报告里的 run 起短名。
- `--baseline` 支持名称、路径、run_name 或 1-based index。
- `--out-dir` 指定输出目录。
- 标准输出打印 `portfolio_count`、`baseline`、`best_by_overall_score`、`best_by_final_val_loss`、`summary` 和保存路径，便于截图和脚本校验。

### `tests/test_training_portfolio_comparison.py`

单测构造临时 portfolio fixture，不依赖真实训练耗时。它写出与真实 v67 产物同形的 JSON，包括 scorecard、dataset card、manifest、eval suite、generation quality、registry、maturity summary 和 maturity narrative。

覆盖重点：

- portfolio 可以从目录加载。
- baseline delta 能区分 improved、regressed、artifact regression、maturity review。
- 相对 artifact 路径能通过 `project_root` 正确解析。
- JSON/CSV/Markdown/HTML 输出存在，HTML 对 `<base>` 这样的名字做转义。
- `names` 数量和输入数量不一致时直接报错，避免报告错位。

### README、阶段索引和 `b/68`

README 新增 v68 的版本说明、命令用法、项目结构、验证截图索引和学习地图说明。`代码讲解记录_项目成熟度阶段/README.md` 追加第 83 篇。`b/68` 保存本版运行截图和解释，继续遵守 v32 之后运行证据放在 `b/` 的规则。

## 核心数据结构和字段语义

`build_training_portfolio_comparison` 输出的顶层结构是：

```json
{
  "schema_version": 1,
  "title": "...",
  "generated_at": "...",
  "portfolio_count": 3,
  "baseline": {},
  "portfolios": [],
  "baseline_deltas": [],
  "summary": {},
  "best_by_overall_score": {},
  "best_by_rubric_avg_score": {},
  "best_by_artifact_coverage": {},
  "best_by_final_val_loss": {},
  "recommendations": []
}
```

`portfolios` 是每个实验组合的压缩摘要；`baseline_deltas` 是相对 baseline 的变化。二者用 `name` 对齐，所以 CSV 输出可以把摘要和 delta 合并成一行。

重要 delta 字段：

- `overall_score_delta`：候选 portfolio 的 scorecard overall 分数减 baseline 分数，越大越好。
- `rubric_avg_score_delta`：候选 rubric 平均分减 baseline 分数，越大越好。
- `final_val_loss_delta`：候选最终验证损失减 baseline 损失，越小越好；所以 relation 里负数是 `improved`。
- `artifact_coverage_delta`：候选产物覆盖率减 baseline 覆盖率，用来发现“分数更高但证据少了”的情况。
- `dataset_warning_delta`：候选数据警告数量减 baseline 警告数量。
- `maturity_status_changed`：候选 maturity narrative 的 portfolio status 是否变化。
- `explanation`：把主要变化压缩成一句话，供 Markdown/HTML 表格直接阅读。

## 路径解析为什么要宽松

真实 v67 portfolio 里的 artifact path 可能是绝对路径，也可能在后续手工归档或测试里变成相对路径。v68 使用 `_resolve_artifact_path` 依次尝试：

```text
absolute path
project_root / relative path
training_portfolio.json 所在目录 / relative path
当前工作目录 / relative path
```

这样做的目的不是掩盖错误，而是让报告在真实 run、临时 smoke fixture、归档复制后的目录里都能尽量读到证据。如果最终仍然找不到，对应 artifact 的 `exists` 会是 `false`，并进入 artifact coverage delta。

## 输出产物是不是最终证据

`training_portfolio_comparison.json` 是机器可读的最终证据，适合后续脚本继续消费。

`training_portfolio_comparison.csv` 是表格证据，适合人工快速查看每个 run 的分数、验证损失、数据警告和成熟度状态。

`training_portfolio_comparison.md` 是审阅说明，适合放进讲解或版本归档。

`training_portfolio_comparison.html` 是浏览器证据，适合截图、展示和交接。它不需要服务端，Playwright 直接打开本地文件即可。

这些产物都是派生报告，不会反向修改训练 run，也不会覆盖原始 scorecard、dataset card 或 manifest。

## 测试如何真实覆盖链路

本版测试不是只检查函数存在，而是构造三类 portfolio：

- baseline：完整产物、分数中等、验证损失正常。
- candidate：完整产物、score 更高、validation loss 更低。
- review：score 更低、validation loss 更高、dataset warnings 增加、maturity status 变成 review，并故意缺一个 artifact。

关键断言保护了这些行为：

- `best_by_overall_score` 和 `best_by_final_val_loss` 都能选中 candidate。
- `score_improvement_count`、`score_regression_count`、`artifact_regression_count`、`maturity_review_count` 都能正确计数。
- validation loss 的改进方向和 score 相反：loss delta 为负才是 improved。
- HTML 转义防止 portfolio 名称影响页面结构。
- 相对路径解析保证真实项目和临时 fixture 都能被读取。

如果这些测试失败，通常说明 baseline 对齐、artifact path、分数方向或 HTML 输出有一个环节被改坏了。

## 和后续版本的关系

v68 的真正价值会在下一步更明显。后续可以用同一个命令比较：

- 小样本 smoke run vs 较大中文语料 run。
- char tokenizer vs BPE tokenizer。
- 小模型 vs 稍大模型。
- 不同训练步数或学习率。
- from-scratch MiniGPT vs 外部开源模型微调实验的摘要产物。

也就是说，v68 不是模型能力提升本身，而是让“模型能力是否提升”有一个稳定比较面板。

## 一句话总结

v68 把 MiniGPT 从“能端到端跑出一份训练组合证据”推进到“能把多份训练组合证据放在同一基线上解释改进、退化和证据缺口”。
