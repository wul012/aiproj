# v177 dashboard section helper split 代码讲解

## 本版目标

v177 的目标是把 `dashboard_render.py` 中的局部 section/helper 渲染拆到 `dashboard_sections.py`，让 dashboard HTML 入口继续向“页面编排”和“区块渲染”分离。原模块同时负责 dashboard title、summary stats、HTML 外壳、CSS、artifact cards、manifest/dataset/model/training/eval/pair/prediction/attention/chat/text/warning sections、图片链接、artifact 链接、格式化和 HTML escape。入口编排和具体区块混在一起时，后续调整某个 dashboard 区块会挤占主入口可读性。

本版明确不做这些事：不改变 dashboard payload schema，不改变 `collect_artifacts()` 的 artifact key 和 href 规则，不改变 `write_dashboard()` 行为，不改变 `scripts/build_dashboard.py` 用法，不改变旧的 `minigpt.dashboard.render_dashboard_html` 导出，也不改变公开的 `minigpt.dashboard_render.render_dashboard_html` 入口。

## 前置路线

v177 接在 dashboard 和 UI 边界拆分路线后面。v8 建立 dashboard，v123 曾经把 dashboard 渲染从 `dashboard.py` 拆到 `dashboard_render.py`，使 payload 构建和 HTML 生成分离。后续 v155-v171 连续拆出 server logging、checkpoint payload、HTTP helper、request-history endpoint 和 GET route dispatch。v177 继续同一个节奏：不改功能，只把过长渲染入口里的局部 section/helper 移到专门模块。

从维护角度看，v176 之后最大模块是 `dashboard_render.py`。它仍是纯渲染层，不属于业务规则复杂模块，但 492 行里包含大量 CSS 和 section helper。拆出 `dashboard_sections.py` 能让主入口回到 82 行，只展示 dashboard 的整体结构。

## 关键文件

- `src/minigpt/dashboard_render.py`：保留唯一公开入口 `render_dashboard_html()`。它继续负责 title、summary stats、section 顺序、HTML head/body/footer 和对外 `__all__`。
- `src/minigpt/dashboard_sections.py`：新增 section/helper 模块。它负责 CSS、stats grid、artifact grid、manifest/dataset/model/training/eval suite/pair batch/prediction/attention/chat/text/warning sections，以及图片、artifact 链接、格式化和 HTML escape。
- `tests/test_dashboard_render.py`：原有测试继续覆盖 dashboard rendering、legacy render export 和 `write_dashboard()`，新增 section helper 断言。
- `README.md`、`c/177/解释/说明.md`、`代码讲解记录_项目成熟度阶段/README.md`：记录本版能力、证据目录和讲解索引。

## Render 主入口

`render_dashboard_html()` 仍然是外部调用方使用的入口。它从 payload 中读取 `title`、`summary` 和 `artifacts`，构造顶部 stats 列表，然后按固定顺序拼出 style、header、stats grid、artifact grid、run manifest、dataset、model、training、eval suite、pair batch、prediction、attention、chat、sample/generated text 和 warnings。

v177 后，这个函数不再关心每个 section 内部怎么生成 table、link、image 或 CSS。它只决定“有哪些区块”和“区块顺序是什么”。因此 dashboard 页面结构更容易阅读，也更容易判断某个区块是否被遗漏。

## Section 模块

`dashboard_sections.py` 接管了这些能力：

- `style()`：返回 dashboard 页面 CSS。
- `stats_grid()` 和 `artifact_grid()`：渲染顶部指标卡和 artifact card。
- `manifest_section()`、`dataset_section()`、`model_section()`、`training_section()`、`eval_suite_section()`、`pair_batch_section()`、`prediction_section()`、`attention_section()`、`chat_section()`、`text_section()`、`warning_section()`：渲染各个 dashboard 内容区块。
- `image()` 和 `artifact_anchor()`：根据 artifact key 生成图片和链接。
- `fmt()`、`fmt_int()`、`fmt_missing()`、`clip()`、`join_counts()`、`escape()`：负责格式化、截断、计数字符串和 HTML escape。

这个模块不读取磁盘，不构建 payload，不决定 artifact 是否存在。它只消费已经准备好的 payload 字典，输出 HTML 片段。

## 兼容性

旧调用方式仍然有效：

```python
from minigpt.dashboard import render_dashboard_html
from minigpt.dashboard_render import render_dashboard_html
```

原因是 `dashboard.py` 继续从 `dashboard_render.py` 导入 `render_dashboard_html()`，而 `dashboard_render.py` 继续导出同名入口。新模块 `dashboard_sections.py` 只是内部 section/helper 边界，不要求用户或脚本改导入路径。

`tests/test_dashboard_render.py` 新增的 identity 断言保护这个边界：

```python
self.assertIs(dashboard.render_dashboard_html, dashboard_render.render_dashboard_html)
self.assertIs(
    dashboard_render.render_dashboard_html.__globals__["_stats_grid"],
    dashboard_sections.stats_grid,
)
```

它保护的是两层兼容：旧 dashboard facade 没断，render 入口确实消费新 section helper。

## 测试覆盖

v177 的测试覆盖四层：

- `tests.test_dashboard_render` 和 `tests.test_dashboard`：覆盖 dashboard payload rendering、legacy render export、write_dashboard、pair batch links、HTML escaping、invalid JSON warning 和 section helper split。
- 全量 unittest discovery：确认 dashboard 拆分没有破坏训练产物、评估产物、报告产物和发布治理链路。
- source encoding hygiene：确认新模块没有 BOM、语法错误或 Python 3.11 兼容问题。
- maintenance batching：确认 module pressure 继续为 `pass`，没有新 warn/critical 模块。

## 运行证据

v177 的运行截图归档在 `c/177`：

- `01-dashboard-tests.png`：dashboard render 和 dashboard 回归测试通过。
- `02-dashboard-sections-smoke.png`：`render_dashboard_html()` 使用新 section helper，且主模块从 492 行降到 82 行。
- `03-maintenance-smoke.png`：module pressure 为 `pass`。
- `04-source-encoding-smoke.png`：编码、语法和目标 Python 兼容检查通过。
- `05-full-unittest.png`：全量 399 个测试通过。
- `06-docs-check.png`：README、`c/177`、讲解索引、source/test 关键词对齐。

临时 `tmp_v177_*` 日志和 `runs/*v177*` 输出会在提交前按 AGENTS 清理门禁删除，`c/177` 是保留的正式证据。

## 边界说明

`dashboard_sections.py` 不是新的 dashboard payload builder。它不扫描 run 目录，不读取 JSON，不判断 artifact 是否存在，也不写出 `dashboard.html`。这些仍然由 `dashboard.py` 负责。后续修改时，数据收集和 artifact manifest 找 `dashboard.py`，页面外壳顺序找 `dashboard_render.py`，单个区块和 HTML helper 找 `dashboard_sections.py`。

## 一句话总结

v177 把 dashboard 的 style、stats grid、artifact card、内容 section、图片链接、格式化和 HTML escape helper 独立成 `dashboard_sections.py`，让 `dashboard_render.py` 从 492 行降到 82 行，同时保持 payload 构建、write_dashboard、脚本用法、legacy facade 和公开 render 入口不变。
