# v161 dataset card artifact split 代码讲解

## 本版目标

v161 的目标是把 `dataset_card.py` 里的 JSON、Markdown 和 HTML 输出层拆出去，让 dataset card 的“证据汇总/数据治理判断”和“人机可读产物发布”分开。

本版解决的问题是：`dataset_card.py` 已经成为 v160 后的最大模块。它一边读取 `dataset_version.json`、`dataset_report.json`、`dataset_quality.json` 并汇总 dataset identity、provenance、quality、artifact 和 recommendation；一边又负责 Markdown/HTML 渲染、输出 artifact 标记和页面样式。这类输出层代码体积大，但不应和 dataset card schema 构建纠缠在一起。

本版明确不做这些事，核心边界是保留 dataset card schema：

- 不改变 `build_dataset_card()` 返回的 card schema。
- 不改变 `scripts/build_dataset_card.py` 的参数和输出文件名。
- 不改变 dataset readiness、quality status、warnings、recommendations 的判定规则。
- 不改变 maturity narrative、training portfolio comparison 等下游读取 `dataset_card.json` 的方式。

## 前置路线

这版延续的是 artifact split 和数据治理路线：

- v54 引入 dataset card，把数据来源、质量、用途和限制显式化。
- v83-v108 做 report utility migration，统一基础报告行为。
- v153-v160 多次把治理模块的 artifact 输出层拆出。
- v161 把 dataset card 的渲染/写出也纳入这条维护节奏。

这不是新增 report 层，而是把已有 report 的输出代码放到更合适的位置。

## 关键文件

- `src/minigpt/dataset_card_artifacts.py`：新增 artifact 模块，负责 dataset card JSON/Markdown/HTML 写出、HTML 渲染、Markdown 表格、artifact 输出标记和页面样式。
- `src/minigpt/dataset_card.py`：保留 dataset card schema 构建、dataset/provenance/quality/artifact/recommendation 汇总，从 artifact 模块导入并继续导出旧 writer/renderer。
- `tests/test_dataset_card.py`：增加 facade identity 测试，确认旧导出指向新 artifact 实现。
- `README.md`、`c/161/解释/说明.md`、`c/README.md`：记录本版能力、运行证据和截图归档位置。

## 核心边界

`dataset_card.py` 继续负责数据治理判断：

- 读取 dataset version、prepared dataset report 和 quality report。
- 生成 `dataset`、`summary`、`provenance`、`quality`、`artifacts`、`recommendations`、`warnings`。
- 判断 readiness：`ready`、`review`、`incomplete`。
- 保持 `DEFAULT_INTENDED_USE` 和 `DEFAULT_LIMITATIONS`。

`dataset_card_artifacts.py` 只负责产物输出：

- `write_dataset_card_json()`
- `render_dataset_card_markdown()`
- `write_dataset_card_markdown()`
- `render_dataset_card_html()`
- `write_dataset_card_html()`
- `write_dataset_card_outputs()`

其中 `write_dataset_card_outputs()` 会继续标记 `dataset_card_json`、`dataset_card_md`、`dataset_card_html` 这些输出 artifact，保证保存后的 JSON 能看到自身产物。

## 关键函数

### `build_dataset_card()`

这是主入口，仍在 `dataset_card.py`。输入是 prepared dataset directory，输出是完整 dataset card。

核心字段保持不变：

- `dataset`
- `summary`
- `intended_use`
- `limitations`
- `provenance`
- `quality`
- `artifacts`
- `recommendations`
- `warnings`

这些字段是 maturity narrative、training portfolio comparison 和项目展示层能继续消费的关键。

### `write_dataset_card_outputs()`

这个函数现在来自 `dataset_card_artifacts.py`，但仍可从 `dataset_card.py` 导入。它写出三个文件：

- `dataset_card.json`
- `dataset_card.md`
- `dataset_card.html`

JSON 是机器可读证据；Markdown 是审阅/归档文本；HTML 是浏览器可读展示。

### Facade 导出

`dataset_card.py` 顶部导入 artifact 函数并保持同名导出。旧代码：

```python
from minigpt.dataset_card import write_dataset_card_outputs
```

仍然可用。

## 行数变化

拆分前：

- `src/minigpt/dataset_card.py`：567 行。

拆分后：

- `src/minigpt/dataset_card.py`：247 行。
- `src/minigpt/dataset_card_artifacts.py`：355 行。

这次把当前最大模块明显压下去，同时没有触碰数据质量和 readiness 判断。

## 测试覆盖

`tests/test_dataset_card.py` 覆盖：

- 完整 prepared dataset 可以生成 ready dataset card。
- 重复数据会进入 review，并保留 issue codes。
- JSON/Markdown/HTML 输出真实写出，HTML 会转义标题和描述。
- 缺失输入会记录 warnings。
- 旧 facade writer/renderer 指向 artifact 模块实现。

同时 v161 局部测试还覆盖：

- maturity narrative 读取 dataset card。
- training portfolio 计划里携带 dataset card artifact。
- training portfolio comparison 读取 dataset card summary。

这些测试保护了 dataset card 作为数据治理证据的下游兼容性。

## 运行截图和证据

本版运行证据放在 `c/161`：

- `01-dataset-card-tests.png`：dataset card 和下游数据卡消费链路测试。
- `02-dataset-card-smoke.png`：直接 dataset card artifact smoke。
- `03-maintenance-smoke.png`：维护扫描和 module pressure。
- `04-source-encoding-smoke.png`：源码编码、语法和 Python 3.11 兼容。
- `05-full-unittest.png`：全量 unittest discovery。
- `06-docs-check.png`：README、说明、源码和测试关键词对齐。

这些截图是运行证据归档，不是程序运行时消费的输入。

## 一句话总结

v161 把 dataset card 的“数据证据汇总”和“报告产物发布”分开，让数据治理核心逻辑更轻、更容易维护，同时保持 schema、CLI 和旧导入路径稳定。
