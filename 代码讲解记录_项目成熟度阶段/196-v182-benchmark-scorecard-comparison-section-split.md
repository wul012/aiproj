# v182 benchmark scorecard comparison section split

## 本版目标

v182 的目标是把 benchmark scorecard comparison 的 Markdown/HTML section 渲染从 artifact writer 中拆出来，形成 `benchmark_scorecard_comparison_sections.py`。

它解决的问题是：`benchmark_scorecard_comparison_artifacts.py` 同时承担 JSON/CSV 写入、Markdown/HTML 页面结构、HTML section、表格格式化和 CSS 样式，职责偏宽。v182 让 artifact 模块回到“写文件和统一输出编排”，让 section 模块专门负责人类可读报告的 section 渲染。

本版明确不做：

- 不改变 benchmark scorecard comparison 的 report schema。
- 不改变 JSON、CSV、case delta CSV 的字段。
- 不改变脚本入口和输出文件名。
- 不改变旧导入路径，已有 `benchmark_scorecard_comparison.py` 和 `benchmark_scorecard_comparison_artifacts.py` 的调用方式继续可用。
- 不新增新的治理报告层，也不扩大模型评估能力宣称。

## 前置路线

v163 已经把 cross-scorecard comparison 的 delta 与 summary 逻辑拆到 `benchmark_scorecard_comparison_deltas.py`，让 comparison entrypoint 不再同时处理全部比较细节。

v181 刚完成 CI workflow hygiene artifact split，证明“保留旧 facade 导入、把渲染/写入边界拆出去”的节奏已经稳定。

v182 延续这条收口路线，但对象换成 benchmark scorecard comparison 的人类可读报告：保留 artifact module 的外部 API，把 Markdown/HTML 结构搬到 section renderer。

## 关键文件

### `src/minigpt/benchmark_scorecard_comparison_sections.py`

这是本版新增的 section renderer。

它提供两个公开函数：

- `render_benchmark_scorecard_comparison_markdown(report)`
- `render_benchmark_scorecard_comparison_html(report)`

它内部继续保留渲染所需的私有 helper：

- `_run_section()` 负责 HTML Runs 表格。
- `_case_delta_section()` 负责 HTML Case Deltas 表格。
- `_group_delta_section()` 负责 Task Type / Difficulty 的 HTML 分组表格。
- `_markdown_group_section()` 负责 Markdown 分组表格。
- `_terms_delta()` 将 added/removed missing terms 和 failed checks 合并成人类可读文本。
- `_fmt()`、`_fmt_signed()`、`_md()`、`_e()` 负责数字、Markdown 和 HTML 安全格式化。
- `_style()` 保留该报告自己的 HTML 样式。

这些 helper 不作为外部 API。它们只服务 comparison report 的 Markdown/HTML 证据，不参与 JSON/CSV 结构消费。

### `src/minigpt/benchmark_scorecard_comparison_artifacts.py`

这个模块现在只保留 artifact writer 的职责：

- `write_benchmark_scorecard_comparison_json()`
- `write_benchmark_scorecard_comparison_csv()`
- `write_benchmark_scorecard_case_delta_csv()`
- `write_benchmark_scorecard_comparison_markdown()`
- `write_benchmark_scorecard_comparison_html()`
- `write_benchmark_scorecard_comparison_outputs()`

其中 Markdown/HTML writer 仍然存在，但 render 函数来自新模块：

```python
from minigpt.benchmark_scorecard_comparison_sections import (
    render_benchmark_scorecard_comparison_html,
    render_benchmark_scorecard_comparison_markdown,
)
```

这保证旧代码如果从 artifact module import render 函数，仍然拿到同一个实现。

### `tests/test_benchmark_scorecard_comparison_artifacts.py`

测试新增了 facade identity 断言：

- artifact module 的 render 函数与 section module 的 render 函数是同一个对象。
- comparison module 的旧 render 导出仍然指向 artifact module 的导出。
- `write_benchmark_scorecard_comparison_outputs()` 和 `write_benchmark_scorecard_case_delta_csv()` 的旧导出保持不变。

这类断言保护的不是“内容刚好相同”，而是导入契约没有断裂：旧调用方不需要知道 v182 新增了 section module。

## 数据结构和输入输出

输入仍然是 benchmark scorecard comparison report 字典，关键字段包括：

- `summary`
- `baseline`
- `runs`
- `baseline_deltas`
- `case_deltas`
- `task_type_deltas`
- `difficulty_deltas`
- `recommendations`

section renderer 是只读消费这些字段：

- Markdown 输出用于人工审阅和版本证据。
- HTML 输出用于可视化报告。
- JSON/CSV 输出仍由 artifact module 生成，适合后续脚本或表格消费。

也就是说，v182 只是把“怎么展示”拆出来，不改变“比较结果是什么”。

## 运行流程

现在完整链路是：

```text
benchmark scorecards
 -> build_benchmark_scorecard_comparison()
 -> comparison report dict
 -> benchmark_scorecard_comparison_artifacts.write_*()
 -> JSON/CSV writers stay local
 -> Markdown/HTML renderers delegate to benchmark_scorecard_comparison_sections.py
```

旧 facade 链路仍然成立：

```text
minigpt.benchmark_scorecard_comparison
 -> minigpt.benchmark_scorecard_comparison_artifacts
 -> minigpt.benchmark_scorecard_comparison_sections
```

这让外部调用方看到的是稳定 API，内部维护看到的是更清楚的边界。

## 测试和证据

本版运行的关键验证包括：

- `python -B -m unittest tests.test_benchmark_scorecard_comparison tests.test_benchmark_scorecard_comparison_artifacts -v`
  - 保护 comparison report 构造、输出文件写入、Markdown/HTML 内容和 facade 导出。
- `python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-v182`
  - 保护新增 Python 文件没有 BOM、语法错误或 Python 3.11 兼容问题。
- `python -B scripts/check_maintenance_batching.py --out-dir runs/maintenance-v182`
  - 保护模块压力仍然为 `pass`。
- 全量 unittest discovery
  - 保护 v182 的拆分没有影响 MiniGPT 其他治理、服务、评估和训练规模链路。

运行截图与解释归档在 `c/182`。这些截图是本版的运行证据，不是后续模块消费的结构化输入。

## 边界说明

v182 不是新能力扩张，而是维护性收口。它提升的是 benchmark comparison 报告链路的可维护性和可审计性，而不是模型质量本身。

当前项目仍应被描述为 MiniGPT 学习项目加 AI 工程治理项目。benchmark scorecard comparison 能帮助比较本地评估结果，但不能替代更大语料训练、真实 baseline 和长期重复实验。

## 一句话总结

v182 把 cross-scorecard comparison 的人类可读 section 渲染从 artifact writer 中拆出来，让 benchmark 比较链路在保持旧 API 稳定的同时更容易继续维护。
