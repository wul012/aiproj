# v783 seed handoff markdown split

## 本版目标和边界

v783 是维护拆分版本，不新增 promoted seed handoff 功能，不改变 report schema，也不改变 Markdown 文本内容。它只把 `promoted_training_scale_seed_handoff_sections.py` 中的 Markdown renderer 移到独立模块。

本版不改变：

- `render_promoted_training_scale_seed_handoff_markdown` 的函数名。
- `write_promoted_training_scale_seed_handoff_markdown` 的函数名。
- 从 `promoted_training_scale_seed_handoff_sections` 导入 Markdown 函数的兼容路径。
- HTML renderer 和 receipt/assurance section 输出。

## 为什么这一刀有必要

`promoted_training_scale_seed_handoff_sections.py` 同时包含两套大型 renderer：

- Markdown renderer：大量 bullet、table、command 和 receipt/assurance 字段。
- HTML renderer：stats card、plan section、execution section、artifact section、receipt/assurance HTML section。

两者都很长，但演进原因不同。Markdown 更像归档文本证据，HTML 更像浏览器截图和人工检查页面。把它们放在同一个文件里，会让任何一边改动都需要穿过另一边的大段内容。

## 关键文件

### `src/minigpt/promoted_training_scale_seed_handoff_markdown.py`

新增模块承接：

- `render_promoted_training_scale_seed_handoff_markdown(report)`
- `write_promoted_training_scale_seed_handoff_markdown(report, path)`

它消费 report dict 和 receipt/assurance helper 输出，生成 Markdown 归档文本。它不生成 HTML，不负责 CSS，也不写 JSON/CSV。

### `src/minigpt/promoted_training_scale_seed_handoff_sections.py`

sections 模块现在导入并 re-export Markdown 函数：

```python
from minigpt.promoted_training_scale_seed_handoff_markdown import (
    render_promoted_training_scale_seed_handoff_markdown,
    write_promoted_training_scale_seed_handoff_markdown,
)
```

这样已有测试和调用方仍然可以从 sections 模块拿到 Markdown 函数。该文件现在主要保留 HTML renderer 和 HTML section helpers。

拆分后 sections 文件从 653 行降到 408 行。

## 数据流

```text
seed handoff report
  -> promoted_training_scale_seed_handoff_markdown.render_*
  -> Markdown evidence

seed handoff report
  -> promoted_training_scale_seed_handoff_sections.render_*_html
  -> HTML evidence / screenshot
```

v783 的边界是输出格式拆分，而不是业务字段拆分。

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\promoted_training_scale_seed_handoff_sections.py src\minigpt\promoted_training_scale_seed_handoff_markdown.py
python -m pytest tests\test_promoted_training_scale_seed_handoff.py tests\test_promoted_training_scale_seed_handoff_suite_design.py -q -o cache_dir=runs\pytest-cache-v783-focused
```

结果 `29 passed`。这些测试覆盖 seed handoff 的 Markdown/HTML artifact 接线、suite design 字段、artifact module 与 sections module 的导入一致性。

## 运行证据

本版运行证据归档在：

- `e/783/解释/说明.md`
- `e/783/解释/refactor-summary.html`
- `e/783/图片/v783-seed-handoff-markdown-split.png`

这些证据用于说明 renderer 拆分边界、行数变化和测试结果。

## 一句话总结

v783 把 promoted seed handoff 的 Markdown renderer 从 HTML sections 文件中拆出，让归档文本和浏览器页面输出可以独立维护。
