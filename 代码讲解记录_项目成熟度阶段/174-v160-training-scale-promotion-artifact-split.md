# v160 training scale promotion artifact split 代码讲解

## 本版目标

v160 的目标是把 `training_scale_promotion.py` 里的 JSON、CSV、Markdown 和 HTML 输出层拆出去，让 promotion acceptance 的“判定逻辑”和“证据发布”分开。

本版解决的问题是：`training_scale_promotion.py` 已经成为当前最大模块，既要读取 handoff、scale run、batch 和 portfolio evidence，又要判断 promoted/review/blocked，还要渲染 CSV、Markdown、HTML。输出层和决策层混在一起，会让后续维护 promotion 证据时更容易误碰核心判断。

本版明确不做这些事，核心边界是保留 promotion decision schema：

- 不改变 `build_training_scale_promotion()` 返回的 report schema。
- 不改变 `scripts/build_training_scale_promotion.py` 的参数和输出文件名。
- 不改变 promoted/review/blocked 的判定规则。
- 不改变后续 promotion index、promoted comparison、promoted decision 的输入格式。

## 前置路线

这版延续的是 v153 之后的 artifact split 路线：

- v153 拆 release bundle artifact。
- v154 拆 release readiness artifact。
- v158 拆 release gate comparison artifact。
- v159 拆 server HTTP helper。
- v160 回到训练规模链路，把 promotion acceptance 的 artifact 写出层拆出。

这符合当前项目的维护节奏：优先拆展示/输出层，保留核心业务 contract。

## 关键文件

- `src/minigpt/training_scale_promotion_artifacts.py`：新增 artifact 模块，负责 promotion JSON/CSV/Markdown/HTML 写出和渲染。
- `src/minigpt/training_scale_promotion.py`：保留 handoff 读取、证据解析、variant readiness、blocker/review item、summary 和 recommendation 构建；从 artifact 模块导入并继续导出旧 writer/renderer。
- `tests/test_training_scale_promotion.py`：增加 facade identity 测试，确认旧导出指向新 artifact 实现。
- `README.md`、`c/160/解释/说明.md`、`c/README.md`：记录本版能力、运行证据和截图归档位置。

## 核心边界

`training_scale_promotion.py` 继续负责 promotion decision：

- 读取 `training_scale_handoff.json`。
- 定位 `training_scale_run.json` 和 `training_portfolio_batch.json`。
- 读取每个 variant 的 `training_portfolio.json`。
- 检查 checkpoint、run manifest、eval suite、generation quality、benchmark scorecard、dataset card、registry、maturity summary、maturity narrative 等 required artifacts。
- 生成 `summary`、`blockers`、`review_items` 和 `recommendations`。

`training_scale_promotion_artifacts.py` 只负责 artifact output：

- `write_training_scale_promotion_json()`
- `write_training_scale_promotion_csv()`
- `render_training_scale_promotion_markdown()`
- `write_training_scale_promotion_markdown()`
- `render_training_scale_promotion_html()`
- `write_training_scale_promotion_html()`
- `write_training_scale_promotion_outputs()`

这条边界让 promotion 判断可以继续被后续模块消费，而输出样式和文件写出可以独立维护。

## 关键函数

### `build_training_scale_promotion()`

这是主入口，仍在 `training_scale_promotion.py`。输入是 handoff 文件或目录，输出是完整 promotion report。

report 的核心字段保持不变：

- `summary`
- `training_scale_run`
- `batch`
- `variants`
- `evidence_rows`
- `blockers`
- `review_items`
- `recommendations`

### `write_training_scale_promotion_outputs()`

这个函数现在来自 `training_scale_promotion_artifacts.py`，但仍可从 `training_scale_promotion.py` 导入。它写出四个文件：

- `training_scale_promotion.json`
- `training_scale_promotion.csv`
- `training_scale_promotion.md`
- `training_scale_promotion.html`

JSON 是机器可读证据；CSV 是 variant-level 摘要；Markdown/HTML 是人工审阅证据。

### Facade 导出

`training_scale_promotion.py` 顶部导入 artifact 函数并保持同名导出。这样旧代码：

```python
from minigpt.training_scale_promotion import write_training_scale_promotion_outputs
```

仍然可用。

## 行数变化

拆分前：

- `src/minigpt/training_scale_promotion.py`：575 行。

拆分后：

- `src/minigpt/training_scale_promotion.py`：350 行。
- `src/minigpt/training_scale_promotion_artifacts.py`：255 行。

这次减少了主 promotion 模块的阅读压力，同时没有把决策规则切碎。

## 测试覆盖

`tests/test_training_scale_promotion.py` 覆盖：

- 完整 handoff + 完整 variant evidence 可以 promoted。
- failed handoff 会 blocked。
- 缺 registry/maturity narrative 等证据会进入 review。
- JSON/HTML 输出真实写出，HTML 会转义标题。
- 旧 facade writer/renderer 指向 artifact 模块实现。

同时 v160 局部测试还覆盖：

- promotion index
- promoted training scale comparison
- promoted training scale decision

这些测试保护了 promotion report 被后续链路消费的兼容性。

## 运行截图和证据

本版运行证据放在 `c/160`：

- `01-training-promotion-tests.png`：promotion 和后续 promoted 链路测试。
- `02-training-promotion-smoke.png`：直接 promotion artifact smoke。
- `03-maintenance-smoke.png`：维护扫描和 module pressure。
- `04-source-encoding-smoke.png`：源码编码、语法和 Python 3.11 兼容。
- `05-full-unittest.png`：全量 unittest discovery。
- `06-docs-check.png`：README、说明、源码和测试关键词对齐。

这些截图是运行证据归档，不是程序运行时消费的输入。

## 一句话总结

v160 把 training scale promotion 的“是否可提升”和“如何发布证据”分开，让训练规模治理链路更容易维护，同时保持旧 CLI、schema 和导入路径稳定。
