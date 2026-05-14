# 第七十版代码讲解：Training Scale Planner

## 本版目标、来源和边界

v70 的目标是把 v69 的 training portfolio batch 再向前补一个“训练前规划”入口：在真正执行多组训练之前，先扫描语料来源，判断语料规模，读取数据质量状态，估算每个训练 variant 的 token budget，并输出一份可以直接交给 v69 batch runner 的 `training_scale_variants.json`。

它解决的问题是：后续如果要跑更大的中文语料，不能只靠手写多组 `max_iters`、`block_size`、`n_embd` 参数。项目需要先回答“这份语料大概处于 tiny/small/medium/large 哪一层”“是否有质量警告”“这组训练矩阵大概会消耗多少 token budget”“下一步应该先 smoke 还是直接跑 extended”。

本版不做这些事情：

- 不下载或扩充真实大语料。
- 不执行训练，也不替代 v69 的 batch runner。
- 不判断模型能力已经提升；它只提供训练前规划证据。
- 不把规划结果写进永久 run registry；真正训练后的 registry 仍由 v67/v69 链路负责。

## 本版接在哪条链路后面

v67 已经提供单次训练组合跑：

```text
source -> prepare/train/eval/quality/scorecard/card/registry/maturity -> training_portfolio.json
```

v68 已经提供多份 portfolio 的 baseline comparison：

```text
training_portfolio.json x N -> training_portfolio_comparison.*
```

v69 把多组训练参数组织成 batch matrix：

```text
variant matrix -> portfolio plan/result x N -> comparison -> training_portfolio_batch.*
```

v70 放在 v69 前面：

```text
text sources
 -> dataset scale/quality scan
 -> training_scale_plan.*
 -> training_scale_variants.json
 -> run_training_portfolio_batch.py --variants ...
```

也就是说，v70 不是新的展示末端，而是一个训练矩阵的生成器。它让“更大语料训练”从口头计划变成可复用的前置产物。

## 关键新增文件

### `src/minigpt/training_scale_plan.py`

这是 v70 的核心模块。

关键函数：

- `build_training_scale_plan(...)`：读取 `.txt` source，调用已有的 `build_prepared_dataset`、`build_dataset_report` 和 `build_dataset_quality_report`，生成训练规模规划报告。
- `scale_tier(char_count)`：把语料字符数分成 `tiny`、`small`、`medium`、`large` 四档。
- `write_training_scale_plan_outputs(...)`：一次性写出 JSON、CSV、Markdown、HTML 和 batch-compatible variants JSON。
- `render_training_scale_plan_markdown(...)` / `render_training_scale_plan_html(...)`：把规划结果变成可审阅文档和浏览器报告。

核心数据结构是 `report`：

- `dataset`：记录数据集名称、版本前缀、source 数量、字符数、行数、唯一字符比例、fingerprint、scale tier、quality status、warning count。
- `sources_detail`：来自 `data_prep` 的每个源文件摘要，包含路径、字符数、行数和 sha256。
- `quality_issues`：来自 `data_quality` 的 warning/info 列表，用于提示 tiny source、重复行、低唯一字符比例等问题。
- `variants`：真正交给 v69 batch runner 的训练参数矩阵。
- `variant_matrix`：面向人审阅的矩阵摘要，包含 `token_budget` 和 `corpus_pass_estimate`。
- `batch`：记录 `training_scale_variants.json` 路径、推荐 batch 输出目录、baseline variant 和完整 batch command。
- `recommendations`：根据 scale tier 与质量警告生成下一步建议。

`training_scale_variants.json` 是本版最关键的桥接产物。它不是最终训练证据，而是给 v69 消费的输入文件；真正的训练结果仍应由 v69 写出 `training_portfolio_batch.*` 和 per-variant portfolio。

### `scripts/plan_training_scale.py`

这是命令行入口。典型用法：

```powershell
python scripts/plan_training_scale.py data --out-dir runs/training-scale-plan --dataset-name sample-zh --dataset-version-prefix v70
```

CLI 会输出：

- `scale_tier`
- `source_count`
- `char_count`
- `quality_status`
- `warning_count`
- `variant_count`
- `baseline`
- `batch_command`
- `outputs`

这些字段适合做截图，也适合后续脚本判断是否可以继续执行 batch。

### `tests/test_training_scale_plan.py`

测试覆盖的是 v70 到 v69 的真实接口边界，而不是只测字符串渲染：

- 规划器能读取 source 并生成 scale tier、variant matrix 和 batch command。
- `write_training_scale_plan_outputs` 写出的 `training_scale_variants.json` 能被 v69 的 `load_training_portfolio_batch_variants` 读取。
- 读取后的 variants 能继续进入 `build_training_portfolio_batch_plan`。
- tiny corpus 会产生 warning，并且 `max_variants=1` 能限制输出矩阵。
- `recursive=False` 时不会误读嵌套目录。
- HTML 渲染会转义 `<demo>` 这类输入，避免报告页被注入。

### `c/70`

本版运行截图和解释按照新归档规则写入：

```text
c/70/图片
c/70/解释/说明.md
```

这里的截图不是训练样本图，而是 v70 闭环证据：单测、CLI smoke、tiny corpus smoke、结构检查、Playwright 打开 HTML 报告，以及 README/讲解记录/c 归档一致性检查。

## 输入输出格式

输入是训练 source，可以是 `.txt` 文件，也可以是目录：

```powershell
python scripts/plan_training_scale.py data
```

输出目录默认是：

```text
runs/training-scale-plan
```

关键输出：

- `training_scale_plan.json`：完整机器可读规划报告。
- `training_scale_plan.csv`：variant matrix 表格，适合横向比较参数和 token budget。
- `training_scale_plan.md`：人审阅说明。
- `training_scale_plan.html`：浏览器证据页。
- `training_scale_variants.json`：v69 batch runner 可以直接读取的 variants 文件。

`training_scale_variants.json` 形态是：

```json
{
  "schema_version": 1,
  "source": "training_scale_plan",
  "dataset": {
    "scale_tier": "tiny"
  },
  "variants": [
    {
      "name": "scale-smoke",
      "dataset_version": "v70-smoke",
      "max_iters": 50,
      "batch_size": 8,
      "block_size": 64
    }
  ]
}
```

v69 的 loader 本来就支持 `{ "variants": [...] }` 格式，所以 v70 不需要改动 v69 模块就能完成交接。

## 为什么这是合理推进

前面几版已经把“训练后怎么组织证据”做得比较完整：portfolio、comparison、batch matrix 都存在了。v70 转向“训练前怎么规划”，避免继续只做 HTML 或链接层的小增量。

它把用户之前提到的“不要继续拆 links/trends/dashboard，要做收口或 benchmark suite”落到训练侧：先让项目知道数据规模和训练矩阵是否匹配，再决定是否执行更大的 batch。

## 测试如何保护链路

`tests/test_training_scale_plan.py` 重点保护三类风险：

- 数据入口风险：目录递归、tiny corpus、质量 warning、source 统计是否正确。
- batch 交接风险：v70 写出的 variants JSON 是否能被 v69 loader 和 batch plan 消费。
- 报告安全风险：Markdown/HTML 是否包含关键 batch command，HTML 是否正确转义用户输入。

这些测试失败时，通常说明 v70 规划结果不再可靠，或者无法交给 v69 执行。

## 一句话总结

v70 把 MiniGPT 从“能批量声明训练实验矩阵”推进到“能在训练前根据语料规模和质量生成可执行 batch 矩阵”，让更大中文语料实验有了前置规划层。
