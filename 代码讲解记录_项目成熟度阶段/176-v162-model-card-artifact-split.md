# v162 model card artifact split 代码讲解

## 本版目标

v162 的目标是把 `model_card.py` 里的 JSON、Markdown 和 HTML 输出层拆出去，让 model card 的“项目级模型总结/覆盖率判断”和“人机可读产物发布”分开。

本版解决的问题是：`model_card.py` 在 v161 后成为当前最大模块。它既要读取 registry 和 experiment cards，构建 project-level summary、coverage、top runs、recommendations 和 warnings；又要渲染 Markdown/HTML、生成 run table、处理链接和页面样式。这些输出层代码体积大，但不应该和 model card schema 构建混在一起。

本版明确不做这些事，核心边界是保留 model card schema：

- 不改变 `build_model_card()` 返回的 card schema。
- 不改变 `scripts/build_model_card.py` 的参数和输出文件名。
- 不改变 ready/review/incomplete、coverage、recommendations 的判断规则。
- 不改变 project audit、release bundle 等下游读取 `model_card.json` 的方式。

## 前置路线

这版延续的是治理报告 artifact split 路线：

- v161 刚把 dataset card 的 artifact 输出拆到 `dataset_card_artifacts.py`。
- model card 与 dataset card 同属数据/实验治理证据：前者描述模型/运行族，后者描述数据版本。
- v162 对 model card 做同样收口，保持构建逻辑轻量，输出层独立。

这不是新增模型能力，而是降低治理证据链的维护压力。

## 关键文件

- `src/minigpt/model_card_artifacts.py`：新增 artifact 模块，负责 model card JSON/Markdown/HTML 写出、Markdown run table、HTML run table、链接、tag chip 和页面样式。
- `src/minigpt/model_card.py`：保留 registry/experiment card 读取、run summary、coverage、top runs、recommendation 构建，从 artifact 模块导入并继续导出旧 writer/renderer。
- `tests/test_model_card.py`：增加 facade identity 测试，确认旧导出指向新 artifact 实现。
- `README.md`、`c/162/解释/说明.md`、`c/README.md`：记录本版能力、运行证据和截图归档位置。

## 核心边界

`model_card.py` 继续负责项目级模型治理判断：

- 读取 registry。
- 自动发现或加载 experiment cards。
- 汇总 run status、best validation loss、dataset quality、eval suite、generation quality、artifact coverage。
- 构建 `summary`、`coverage`、`top_runs`、`runs`、`recommendations`、`warnings`。

`model_card_artifacts.py` 只负责产物输出：

- `write_model_card_json()`
- `render_model_card_markdown()`
- `write_model_card_markdown()`
- `render_model_card_html()`
- `write_model_card_html()`
- `write_model_card_outputs()`

这让 project audit 和 release bundle 继续依赖稳定 JSON schema，而 Markdown/HTML 展示可以独立演进。

## 关键函数

### `build_model_card()`

这是主入口，仍在 `model_card.py`。输入是 registry 路径和可选 experiment card paths，输出是完整 model card。

核心字段保持不变：

- `summary`
- `intended_use`
- `limitations`
- `coverage`
- `quality_counts`
- `generation_quality_counts`
- `tag_counts`
- `dataset_fingerprints`
- `top_runs`
- `runs`
- `recommendations`
- `warnings`

### `write_model_card_outputs()`

这个函数现在来自 `model_card_artifacts.py`，但仍可从 `model_card.py` 导入。它写出三个文件：

- `model_card.json`
- `model_card.md`
- `model_card.html`

JSON 是 project audit 和 release bundle 消费的机器可读证据；Markdown/HTML 是人工审阅和作品展示入口。

### Facade 导出

`model_card.py` 顶部导入 artifact 函数并保持同名导出。旧代码：

```python
from minigpt.model_card import write_model_card_outputs
```

仍然可用。

## 行数变化

拆分前：

- `src/minigpt/model_card.py`：556 行。

拆分后：

- `src/minigpt/model_card.py`：257 行。
- `src/minigpt/model_card_artifacts.py`：327 行。

这次把当前最大模块明显压下去，同时没有触碰 project-level model card 的判断规则。

## 测试覆盖

`tests/test_model_card.py` 覆盖：

- registry + experiment cards 可以汇总 project-level model card。
- 缺 experiment card 会给出生成建议。
- JSON/Markdown/HTML 输出真实写出。
- HTML 会转义标题和 run name。
- 旧 facade writer/renderer 指向 artifact 模块实现。

同时 v162 局部测试还覆盖：

- project audit 读取 model card。
- release bundle 读取 model card。

这些测试保护了 model card 作为项目级治理证据的下游兼容性。

## 运行截图和证据

本版运行证据放在 `c/162`：

- `01-model-card-tests.png`：model card、project audit、release bundle 测试。
- `02-model-card-smoke.png`：直接 model card artifact smoke。
- `03-maintenance-smoke.png`：维护扫描和 module pressure。
- `04-source-encoding-smoke.png`：源码编码、语法和 Python 3.11 兼容。
- `05-full-unittest.png`：全量 unittest discovery。
- `06-docs-check.png`：README、说明、源码和测试关键词对齐。

这些截图是运行证据归档，不是程序运行时消费的输入。

## 一句话总结

v162 把 model card 的“项目级模型证据汇总”和“报告产物发布”分开，让模型治理核心逻辑更轻、更容易维护，同时保持 schema、CLI 和旧导入路径稳定。
