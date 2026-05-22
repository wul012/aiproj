# v395 promoted training scale seed section split 代码讲解

## 本版目标和边界

v395 的目标是拆分 `promoted_training_scale_seed_artifacts.py` 中持续膨胀的 HTML section/render helper，把 seed HTML 页面结构迁移到独立模块 `promoted_training_scale_seed_sections.py`。

这是一个维护性版本，不新增治理字段，不改变 seed readiness，不改变 next plan command，不改变 JSON/CSV/Markdown/HTML 输出 schema，也不改变 public import。它解决的是 v394 后 artifact 文件接近 500 行、继续往 seed handoff 推 reason context 前需要收口的问题。

## 前置能力

v394 已经把 promoted-decision maturity CI reason counts 带到 next-cycle seed。该能力让 seed artifact 的 Markdown/HTML 输出继续变厚。按照项目规则，持续接近 500-800 行且职责变宽的文件需要必要拆分，因此 v395 先做边界整理。

```text
promoted_training_scale_seed_artifacts.py
        |
        | v395 extracts HTML section rendering
        v
promoted_training_scale_seed_sections.py
```

## 关键文件

### `src/minigpt/promoted_training_scale_seed_sections.py`

新模块负责：

```text
render_promoted_training_scale_seed_html()
_baseline_section()
_command_section()
_source_table()
_list_section()
_style()
_card()
```

这些函数都是 HTML 视图层职责。它们读取 report、baseline seed、next plan 和 summary，渲染 stat cards、baseline seed table、next plan command、source table、blockers、recommendations 和页面样式。

该模块不写文件、不生成 JSON/CSV/Markdown、不改变数据结构。

### `src/minigpt/promoted_training_scale_seed_artifacts.py`

artifact writer 继续负责：

```text
write_promoted_training_scale_seed_json()
write_promoted_training_scale_seed_csv()
render_promoted_training_scale_seed_markdown()
write_promoted_training_scale_seed_markdown()
write_promoted_training_scale_seed_html()
write_promoted_training_scale_seed_outputs()
```

它现在从 section 模块导入：

```python
from minigpt.promoted_training_scale_seed_sections import render_promoted_training_scale_seed_html
```

因此外部调用 `render_promoted_training_scale_seed_html()` 的路径不变，仍可从 artifact module 或 seed module 使用。

### `tests/test_promoted_training_scale_seed.py`

既有测试继续覆盖：

- seed module re-export；
- artifact module render function；
- HTML escaping；
- full seed output writing；
- CLI-facing evidence；
- reason-count fields不丢失。

本版没有新增大量测试，因为行为不变，关键是确认原有目标测试不破。

## 输入输出说明

输入仍是 `build_promoted_training_scale_seed()` 产生的 report：

```text
baseline_seed
next_plan
summary
blockers
recommendations
```

输出仍是：

```text
promoted_training_scale_seed.json
promoted_training_scale_seed.csv
promoted_training_scale_seed.md
promoted_training_scale_seed.html
```

本版只移动 HTML 生成代码的位置，不改变输出文件名、字段名、字段含义或 CLI 行为。

## 运行流程

```text
write_promoted_training_scale_seed_outputs()
        |
        +--> write JSON
        +--> write CSV
        +--> write Markdown
        +--> write HTML
                 |
                 v
        render_promoted_training_scale_seed_html()
        from promoted_training_scale_seed_sections.py
```

这样 artifact writer 留在产物编排层，HTML section module 留在视图层。

## 测试覆盖

本版定向测试：

```text
python -m pytest tests/test_promoted_training_scale_seed.py -q
```

覆盖点：

- `promoted_training_scale_seed.py` 仍 re-export artifact render/write functions；
- `promoted_training_scale_seed_artifacts.py` 仍暴露同名 HTML renderer；
- HTML escaping 仍生效；
- JSON/CSV/Markdown/HTML output 写入路径不变；
- v394 reason-count 输出仍可渲染。

## 维护收益

拆分后：

```text
promoted_training_scale_seed_artifacts.py: 553 -> 311 lines
promoted_training_scale_seed_sections.py: 256 lines
```

这让后续如果继续把 reason-count context 推到 seed handoff 或 receipt 层，可以先在更清晰的边界上扩展，而不是继续把 artifact writer 做成大文件。

## 证据归档

本版运行截图和说明放在：

```text
d/395/图片
d/395/解释/说明.md
```

`d/395/解释/v395-promoted-training-scale-seed-section-split-evidence.html` 是静态证据页，用于 Playwright MCP 截图；它不是最终机器消费源。

## 一句话总结

v395 没有增加新治理能力，而是把 promoted seed artifact 的 HTML 视图层拆出来，为后续继续推进 seed handoff 链路留出可维护空间。
