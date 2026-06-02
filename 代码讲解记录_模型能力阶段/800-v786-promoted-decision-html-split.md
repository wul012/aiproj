# v786 promoted decision HTML split

## 本版目标和边界

v786 是维护拆分版本，不新增 promoted training scale decision 功能，不改变 decision report schema，不改变 JSON/CSV/Markdown 内容，也不改变 `write_promoted_training_scale_decision_outputs` 的输出文件名。本版只把 HTML renderer、HTML writer、CSS 和 HTML 专用 helper 从 artifact 主模块拆出。

本版不改变：

- `render_promoted_training_scale_decision_html(report)` 的函数名。
- `write_promoted_training_scale_decision_html(report, path)` 的函数名。
- 从 `promoted_training_scale_decision_artifacts` 导入 HTML 函数的兼容路径。
- JSON、CSV、Markdown 和 outputs 汇总函数。

## 为什么这一刀有必要

`promoted_training_scale_decision_artifacts.py` 原来同时承担四种输出格式：

- JSON 写入。
- CSV 字段展平。
- Markdown 归档。
- HTML 页面、CSS、cards、table 和 list section。

HTML renderer 的变更理由和 CSV/Markdown 不同。HTML 面向浏览器截图与人工检查，包含大量展示布局；CSV 面向机器消费；Markdown 面向文本归档。把 HTML 留在 artifact 主模块里，会让主模块持续膨胀，也让任何样式调整都穿过 CSV 字段长表。

v786 先把 HTML 输出面拆出，保留 CSV 巨表以后再单独处理。

## 关键文件

### `src/minigpt/promoted_training_scale_decision_html.py`

新增模块承接：

- `render_promoted_training_scale_decision_html(report)`
- `write_promoted_training_scale_decision_html(report, path)`
- `_rejected_table`
- `_list_section`
- `_style`
- `_card`

它只负责 HTML 展示，不写 JSON/CSV/Markdown，不负责 outputs 汇总。

### `src/minigpt/promoted_training_scale_decision_artifacts.py`

主 artifact 模块现在导入并 re-export HTML 函数：

```python
from minigpt.promoted_training_scale_decision_html import (
    render_promoted_training_scale_decision_html,
    write_promoted_training_scale_decision_html,
)
```

拆分后该文件从 628 行降到 415 行，主要保留 JSON/CSV/Markdown 和 outputs 协调。

## 数据流

```text
promoted decision report
  -> promoted_training_scale_decision_artifacts.write_*_outputs
  -> JSON / CSV / Markdown writers in artifacts module
  -> HTML writer delegated to promoted_training_scale_decision_html
```

这个边界保持了原调用方视角：调用 `write_promoted_training_scale_decision_outputs` 时仍然一次性得到四类 artifact。

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\promoted_training_scale_decision_artifacts.py src\minigpt\promoted_training_scale_decision_html.py
python -m pytest tests\test_promoted_training_scale_decision.py tests\test_promoted_training_scale_decision_review.py -q -o cache_dir=runs\pytest-cache-v786-focused
python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-v786
git diff --check
```

结果：

- focused tests: `13 passed`
- source encoding: `status=pass`
- diff check: pass

这些测试覆盖 promoted training scale decision 的 baseline 选择、review 输出和 artifact writer 接线。HTML 函数仍从 artifacts 模块暴露，因此兼容路径也被间接保护。

## 运行证据

本版运行证据归档在：

- `e/786/解释/说明.md`
- `e/786/解释/refactor-summary.html`
- `e/786/图片/v786-promoted-decision-html-split.png`

HTML 证据页展示了拆分后的职责边界、行数变化和测试结果。截图用于确认归档页可打开，核心指标可见。

## 一句话总结

v786 把 promoted decision 的 HTML 输出面从 artifact 主模块中剥离，让 artifacts 模块回到多格式输出协调层，也为后续单独处理 CSV 字段巨表留下清晰边界。
