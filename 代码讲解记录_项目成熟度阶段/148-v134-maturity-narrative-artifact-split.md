# v134 maturity narrative artifact split 代码讲解

## 本版目标

v134 的目标是把 `maturity_narrative.py` 里的“构建 maturity narrative 证据叙事”和“把叙事写成 JSON/Markdown/HTML 产物”分开。拆分后，`maturity_narrative.py` 继续负责读取上游证据、生成 summary、sections、evidence matrix、recommendations 和 warnings；`maturity_narrative_artifacts.py` 负责 JSON 写入、Markdown 渲染、HTML 渲染和三类输出文件的统一落盘。

本版明确不做：

- 不改变 `maturity_narrative.json` 的 schema。
- 不改变 `maturity_narrative.md` 和 `maturity_narrative.html` 的文件名。
- 不改变 `scripts/build_maturity_narrative.py` 的 CLI 参数和调用方式。
- 不改变旧的 `from minigpt.maturity_narrative import write_maturity_narrative_outputs` 导入方式。
- 不把本次拆分解释成模型能力提升；它只是让 maturity narrative 的证据发布边界更清楚。

## 前置路线

v134 接在 v133 之后，继续沿用 v110 以来的 pressure-guided cleanup 路线：

```text
v110 module pressure audit
 -> v121 maturity artifact split
 -> v132 training portfolio artifact split
 -> v133 registry ranking split
 -> v134 maturity narrative artifact split
```

v134 前的维护预检显示 module pressure 仍为 pass，但最大模块已经落到 `maturity_narrative.py`。这个模块不是危险到需要大重构，而是存在一个清晰的低风险边界：证据叙事构建和输出产物渲染可以分开。

## 关键文件

- `src/minigpt/maturity_narrative.py`: 保留 `build_maturity_narrative()`、`utc_now()`、证据读取、summary/sections/evidence matrix/recommendations/warnings 构建逻辑，并从新 artifact 模块 re-export 写入与渲染函数。
- `src/minigpt/maturity_narrative_artifacts.py`: 新增 artifact 层，负责 `write_maturity_narrative_json()`、`render_maturity_narrative_markdown()`、`write_maturity_narrative_markdown()`、`render_maturity_narrative_html()`、`write_maturity_narrative_html()` 和 `write_maturity_narrative_outputs()`。
- `tests/test_maturity_narrative.py`: 增加 facade identity 回归测试，确认旧模块导出的 artifact 函数与新模块是同一个函数对象。
- `README.md`: 更新当前版本、能力矩阵、v134 focus、tag 列表、项目结构和截图归档说明。
- `c/134/解释/说明.md`: 说明本版运行证据、截图含义和能力边界。

## narrative 的核心数据结构

`build_maturity_narrative()` 输出的是一个面向项目成熟度说明的 dict，核心字段如下：

```text
schema_version
title
generated_at
project_root
inputs
summary
sections
evidence_matrix
recommendations
warnings
```

`inputs` 记录 maturity summary、registry、request history summary、benchmark scorecards 和 dataset cards 的来源路径。`summary` 把上游证据压缩成 portfolio status、current version、release readiness trend、request history status、benchmark average、dataset warning count 等关键信号。`sections` 是面向人阅读的叙事块，每块包含 status、claim、evidence、boundary 和 next_step。`evidence_matrix` 把每类证据的路径、存在性、状态和说明列出来，供后续审计或展示消费。

v134 没有改这些字段，只改变了这些字段如何被写成 JSON、Markdown 和 HTML。

## 拆分前的问题

拆分前，`maturity_narrative.py` 同时承担两类职责：

```text
1. 读取上游治理证据并生成 maturity narrative dict
2. 把 narrative dict 渲染和写入 JSON/Markdown/HTML
```

第二类职责包含：

```text
write_maturity_narrative_json
render_maturity_narrative_markdown
write_maturity_narrative_markdown
render_maturity_narrative_html
write_maturity_narrative_html
write_maturity_narrative_outputs
_markdown_table
_section_cards
_evidence_table
_list_section
_card
_style
_md
_e
```

这些函数不需要知道 maturity summary 如何从 registry 或 request history 中计算出来。把它们留在主模块里，会让后续新增叙事 section、调整 evidence matrix 或修改 HTML 样式时互相挤压。

## 新 artifact 模块的职责

`maturity_narrative_artifacts.py` 只接收已经构建好的 narrative dict，不读取上游 evidence 文件，也不重新计算 portfolio status。它做三件事：

- JSON writer: 以 UTF-8 和 `ensure_ascii=False` 写出 `maturity_narrative.json`。
- Markdown renderer/writer: 输出 Portfolio Summary、Narrative、Evidence Matrix、Recommendations 和 Warnings。
- HTML renderer/writer: 输出可浏览器打开的 maturity narrative 页面，并继续使用 HTML escaping 保护文本展示。

因此新的边界可以概括为：

```text
maturity_narrative.py 负责 evidence -> narrative dict
maturity_narrative_artifacts.py 负责 narrative dict -> JSON/Markdown/HTML files
scripts/build_maturity_narrative.py 继续作为 CLI 编排入口
tests 负责锁住 schema、HTML escaping、输出文件和 facade
c/134 负责保存运行证据
```

## facade 为什么要保留

旧调用仍然有效：

```python
from minigpt.maturity_narrative import (
    build_maturity_narrative,
    render_maturity_narrative_html,
    write_maturity_narrative_outputs,
)
```

`build_maturity_narrative()` 仍来自 `maturity_narrative.py`，而 `render_maturity_narrative_html()` 和 `write_maturity_narrative_outputs()` 由 `maturity_narrative.py` 从 `maturity_narrative_artifacts.py` 重新导出。这样脚本、测试和外部使用者不需要迁移导入路径。

## 测试覆盖

`tests/test_maturity_narrative.py` 覆盖了几类关键行为：

- ready portfolio: 确认上游 evidence 完整时 portfolio status 为 `ready`，并保留 benchmark、dataset、request history 等 summary 信号。
- release regression: 确认 release readiness 回退时降为 `review`，并产生修复建议。
- missing request history: 确认缺少请求历史证据时降为 `incomplete` 并写入 warning。
- output writer: 确认 JSON/Markdown/HTML 三类文件都写出，并包含 Evidence Matrix 与 Benchmark Quality。
- HTML escaping: 确认标题等用户可见文本会被转义。
- facade identity: 确认旧模块导出的 artifact 函数与新模块中的函数对象一致。

再加上 compile check、full unittest discovery、maintenance smoke、source encoding hygiene 和 Playwright HTML 截图，可以证明本次拆分没有破坏导入、CLI、输出文件或浏览器证据页。

## 证据意义

v134 的价值不是新增一个成熟度报告，而是让 maturity narrative 的“叙事构建”和“证据发布”拥有独立维护边界。以后如果要调整 narrative 的证据来源，应优先改 `maturity_narrative.py`；如果要调整 Markdown/HTML 展示或输出写入，应优先改 `maturity_narrative_artifacts.py`。

真正的能力边界是：

```text
maturity_narrative.py 负责汇总和解释已有治理证据
maturity_narrative_artifacts.py 负责发布同一份叙事证据
README/c/134 负责说明本次拆分和运行证据
模型质量仍需要真实训练、固定 benchmark 和 checkpoint 对比证明
```

## 一句话总结

v134 把 maturity narrative 从“叙事构建和证据发布混在一个模块”推进到“evidence narrative + artifact writer”双层结构，维护边界更清楚，但模型质量声明保持克制不变。
