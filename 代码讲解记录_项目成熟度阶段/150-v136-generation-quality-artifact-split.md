# v136 generation quality artifact split 代码讲解

## 本版目标

v136 的目标是把 `generation_quality.py` 里的“计算生成质量证据”和“把质量报告写成 JSON/CSV/Markdown/SVG/HTML 产物”分开。拆分后，`generation_quality.py` 继续负责读取 source report、识别 source type、计算 continuation metrics、生成 flags、summary、recommendations 和 warnings；`generation_quality_artifacts.py` 负责五类输出文件的渲染和落盘。

本版明确不做：

- 不改变 `generation_quality.json` 的 schema。
- 不改变 `generation_quality.csv`、`generation_quality.md`、`generation_quality.svg`、`generation_quality.html` 的文件名。
- 不改变 `scripts/analyze_generation_quality.py` 的 CLI 参数和调用方式。
- 不改变旧的 `from minigpt.generation_quality import write_generation_quality_outputs` 导入方式。
- 不把本次拆分解释成模型质量提升；它只让生成质量证据的计算层和发布层更清楚。

## 前置路线

v136 接在 v135 后，是用户确认“后续只做两次左右拆分”的第二刀，也是本轮拆分收口刀：

```text
v110 module pressure audit
 -> v114 benchmark scorecard artifact split
 -> v120 benchmark scorecard scoring split
 -> v135 release gate artifact split
 -> v136 generation quality artifact split
```

v135 后维护预检显示 module pressure 仍为 pass，最大模块是 `server.py`。但 `server.py` 是服务入口，继续拆它风险更高；因此 v136 选择 generation quality，这一层既有清晰 artifact 边界，又更贴近模型输出质量证据，比继续拆 release-governance 报告更有方向感。

## 关键文件

- `src/minigpt/generation_quality.py`: 保留 `build_generation_quality_report()`、source type 推断、continuation 提取、metrics、flags、summary、recommendations 和 warnings，并从 artifact 模块 re-export 写入与渲染函数。
- `src/minigpt/generation_quality_artifacts.py`: 新增 artifact 层，负责 `write_generation_quality_json()`、`write_generation_quality_csv()`、`render_generation_quality_markdown()`、`write_generation_quality_markdown()`、`write_generation_quality_svg()`、`render_generation_quality_html()`、`write_generation_quality_html()` 和 `write_generation_quality_outputs()`。
- `tests/test_generation_quality.py`: 增加 facade identity 回归测试，确认旧模块导出的 artifact 函数与新模块是同一个函数对象。
- `README.md`: 更新当前版本、能力矩阵、v136 focus、tag 列表、项目结构和截图归档说明。
- `c/136/解释/说明.md`: 说明本版运行证据、截图含义和能力边界。

## quality report 的核心数据结构

`build_generation_quality_report()` 输出的是一个面向生成质量检查的 report dict，核心字段如下：

```text
schema_version
title
generated_at
source_path
source_type
policy
summary
cases
recommendations
warnings
```

`policy` 记录最小 continuation 字符数、最小 unique ratio、最大重复字符 run、最大 repeated n-gram ratio 和 ngram size。`cases` 是每条生成样本的质量行，包含 name、status、prompt、采样参数、char_count、unique_ratio、repeated_ngram_ratio、longest_repeat_run、flags 和 continuation_preview。`summary` 汇总 overall_status、pass/warn/fail 计数、平均长度、平均 unique ratio、平均重复 ngram ratio 和最大重复 run。

v136 没有改这些字段，只改变了这些字段如何被写成 JSON、CSV、Markdown、SVG 和 HTML。

## 拆分前的问题

拆分前，`generation_quality.py` 同时承担两类职责：

```text
1. 根据 eval suite 或 sample lab 输出计算生成质量证据
2. 把 quality report 渲染和写入 JSON/CSV/Markdown/SVG/HTML
```

第二类职责包含：

```text
write_generation_quality_json
write_generation_quality_csv
render_generation_quality_markdown
write_generation_quality_markdown
write_generation_quality_svg
render_generation_quality_html
write_generation_quality_html
write_generation_quality_outputs
_case_section
_key_value_section
_list_section
_stat
_style
_markdown_table
_flag_ids
_status_color
_fmt_any
_md
```

这些函数不需要知道 continuation 如何从 generated 文本中切出来，也不需要知道低多样性或 prompt echo 如何打 flag。把它们留在主模块里，会让质量计算和报告发布互相挤压。

## 新 artifact 模块的职责

`generation_quality_artifacts.py` 只接收已经构建好的 quality report dict，不读取 source report，不重新计算 metrics，也不重新判定 pass/warn/fail。它做五件事：

- JSON writer: 写出机器可读 `generation_quality.json`。
- CSV writer: 写出 case-level 表格，包含 flags 和 continuation preview。
- Markdown renderer/writer: 输出 Summary、Policy、Cases、Recommendations 和 Warnings。
- SVG writer: 输出 unique ratio 与 repeated n-gram ratio 的可视化条形图。
- HTML renderer/writer: 输出可浏览器打开的 generation quality 页面，并继续使用 HTML escaping 保护文本展示。

因此新的边界可以概括为：

```text
generation_quality.py 负责 raw generation evidence -> quality report dict
generation_quality_artifacts.py 负责 quality report dict -> JSON/CSV/Markdown/SVG/HTML files
scripts/analyze_generation_quality.py 继续作为 CLI 编排入口
tests 负责锁住 schema、HTML escaping、输出文件和 facade
c/136 负责保存运行证据
```

## facade 为什么要保留

旧调用仍然有效：

```python
from minigpt.generation_quality import (
    build_generation_quality_report,
    render_generation_quality_html,
    write_generation_quality_outputs,
)
```

`build_generation_quality_report()` 仍来自 `generation_quality.py`，而 `render_generation_quality_html()` 和 `write_generation_quality_outputs()` 由 `generation_quality.py` 从 `generation_quality_artifacts.py` 重新导出。这样 `scripts/analyze_generation_quality.py`、已有测试和外部使用者不需要迁移导入路径。

## 测试覆盖

`tests/test_generation_quality.py` 覆盖了几类关键行为：

- pass/warn/fail: 确认正常 continuation、低多样性样本和空 continuation 会分别落到 pass、warn、fail。
- sample lab 输入: 确认能从 generated 文本中剥离 prompt，形成 continuation preview。
- output writer: 确认 JSON、CSV、Markdown、SVG、HTML 五类文件都写出，并保留 `## Cases` 与文件命名约定。
- HTML escaping: 确认 title 和 case name 会被转义。
- threshold validation: 确认非法阈值会失败。
- facade identity: 确认旧模块导出的 artifact 函数与新模块中的函数对象一致。

再加上 compile check、full unittest discovery、maintenance smoke、source encoding hygiene 和 Playwright HTML 截图，可以证明本次拆分没有破坏导入、CLI、输出文件或浏览器证据页。

## 证据意义

v136 的价值不是新增一种质量指标，而是让 generation quality 的“质量计算”和“证据发布”拥有独立维护边界。以后如果要调整低多样性、重复 n-gram、prompt echo 等判断，应优先改 `generation_quality.py`；如果要调整 CSV/SVG/Markdown/HTML 展示，应优先改 `generation_quality_artifacts.py`。

真正的能力边界是：

```text
generation_quality.py 负责计算已有生成样本的质量证据
generation_quality_artifacts.py 负责发布同一份质量证据
README/c/136 负责说明本次拆分和运行证据
模型质量提升仍需要真实训练、固定 benchmark、checkpoint 对比和人工/自动评估共同证明
```

## 一句话总结

v136 把 generation quality 从“质量计算和证据发布混在一个模块”推进到“quality metrics + artifact writer”双层结构，并作为当前两步拆分计划的收口，后续应回到真实评估、数据和训练证据。
