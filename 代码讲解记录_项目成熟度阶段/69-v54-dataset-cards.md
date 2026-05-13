# 第五十四版代码讲解：dataset cards

## 本版目标、来源和边界

v13 让项目可以准备数据集，v15 增加 dataset quality report，v36 增加 dataset version manifest。它们已经能记录数据从哪来、指纹是什么、质量状态如何，但这些信息分散在多个 JSON/SVG/HTML 文件里。v54 的目标是生成一张面向人的 dataset card，把数据身份、来源、预期用途、限制、质量问题、证据产物和建议放到同一个入口。

本版不改变数据清洗规则，不重新设计质量检测算法，不训练模型，也不自动判断数据授权是否合法。它只读取已有数据证据，生成可审阅的数据说明卡。

## 所在链路

```text
dataset_version.json
dataset_report.json
dataset_quality.json
 -> build_dataset_card
 -> dataset_card.json / dataset_card.md / dataset_card.html
```

这一层回答的问题是：一个 prepared dataset 是否有清楚身份、来源、质量状态、用途边界和可追溯产物，是否适合作为后续训练或对比实验的数据输入。

## 关键文件

- `src/minigpt/dataset_card.py`：核心模块，读取 dataset evidence，生成 summary、provenance、quality、artifacts、recommendations。
- `scripts/build_dataset_card.py`：命令行入口，支持 `--dataset-dir`、`--out-dir`、`--title`、`--intended-use` 和 `--limitation`。
- `tests/test_dataset_card.py`：构造正常数据、重复数据和空目录，覆盖 ready/review/incomplete 三种状态。
- `README.md`：把 v54 当前能力、tag、截图说明和后续路线同步到项目首页。
- `b/54/解释/说明.md`：保存本版截图解释和 tag 含义。

## 输入数据

dataset card 默认读取：

```text
<dataset-dir>/dataset_version.json
<dataset-dir>/dataset_report.json
<dataset-dir>/dataset_quality.json
```

`dataset_version.json` 提供数据身份：

- `dataset.name`
- `dataset.version`
- `dataset.id`
- `dataset.description`
- `preparation.source_roots`
- `preparation.recursive`
- `outputs`
- `sources`

`dataset_report.json` 提供准备结果：

- `source_count`
- `char_count`
- `line_count`
- `unique_char_count`
- `fingerprint`
- `output_text`
- `sources`

`dataset_quality.json` 提供质量检查：

- `status`
- `warning_count`
- `issue_count`
- `duplicate_line_count`
- `unique_char_ratio`
- `issues`

如果这些文件缺失，card 不会直接失败，而是在 `warnings` 和 `recommendations` 中提示缺失证据。这让空目录或未完整准备的数据也能生成一个 incomplete 状态的说明卡。

## 核心数据结构

`dataset` 是数据身份：

- `name`
- `version`
- `id`
- `description`

`summary` 是用于快速扫描的状态：

- `readiness_status`：`ready`、`review` 或 `incomplete`。
- `quality_status`：来自 quality report 的 `pass`、`warn` 或 `missing`。
- `source_count`
- `char_count`
- `line_count`
- `unique_char_count`
- `short_fingerprint`
- `warning_count`
- `issue_count`
- `output_text_exists`
- `version_manifest_exists`
- `report_exists`
- `quality_report_exists`

`readiness_status` 的规则很保守：quality pass 才是 ready；有 warning 或 issue 就是 review；关键证据缺失则是 incomplete。

`intended_use` 和 `limitations` 是给人读的边界说明。默认 intended use 强调这是 MiniGPT 学习实验和复现审查的数据；默认 limitations 明确轻量质量检查不能证明事实正确、授权合规或安全。

`provenance` 说明来源和准备方式：

- `source_roots`
- `recursive`
- `output_name`
- `output_text`
- `sources`

`quality` 汇总质量信息：

- `status`
- `warning_count`
- `issue_count`
- `duplicate_line_count`
- `issue_codes`
- `severity_counts`
- `issues`

`artifacts` 标记证据产物是否存在：

- `dataset_version.json`
- `dataset_version.html`
- `dataset_report.json`
- `dataset_report.svg`
- `dataset_quality.json`
- `dataset_quality.svg`
- `corpus.txt`
- `dataset_card.json`
- `dataset_card.md`
- `dataset_card.html`

写出 card 时，`write_dataset_card_outputs` 会把自身 JSON/Markdown/HTML artifact 标记为存在，保证输出后的 `dataset_card.json` 能自描述。

## 输出产物

```text
dataset_card.json
dataset_card.md
dataset_card.html
```

JSON 是给后续脚本消费的结构化证据。Markdown 是适合代码审阅和归档的文本版本。HTML 是浏览器查看和截图证据。三者都是最终产物，不是临时文件。

## CLI 用法

示例：

```powershell
python scripts/build_dataset_card.py `
  --dataset-dir datasets/demo-zh/v1 `
  --title "MiniGPT demo dataset card"
```

也可以覆盖说明：

```powershell
python scripts/build_dataset_card.py `
  --dataset-dir datasets/demo-zh/v1 `
  --intended-use "Train tiny local MiniGPT experiments." `
  --limitation "Not reviewed for external distribution."
```

## 测试和证据

`tests/test_dataset_card.py` 覆盖：

- 正常 prepared dataset 会得到 `ready`。
- 重复来源和重复行会得到 `review`，并汇总 issue codes。
- 空目录会得到 `incomplete`，并写入 warnings 和 recommendations。
- 输出 JSON/Markdown/HTML 文件都存在。
- 输出后的 card artifacts 会标记自身 HTML 存在。
- HTML 对 `<Dataset Card>` 和 `<demo>` 这类文本做转义，避免报告被注入破坏。

运行证据保存在 `b/54/图片`。其中 Playwright 截图证明 HTML 可以在真实 Chrome 中打开。

## 和前面版本的关系

v36 的 dataset version 是机器可读的数据身份，v15 的 dataset quality 是轻量质量检查，v54 的 dataset card 是人可读的审阅入口。它不会替代前两个文件，而是把它们合成一个解释层。

## 一句话总结

v54 把 MiniGPT 从“数据证据分散在多个报告里”推进到“数据可以被一张卡片审阅、解释和追溯”的阶段。
