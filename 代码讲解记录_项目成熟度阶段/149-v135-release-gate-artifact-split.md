# v135 release gate artifact split 代码讲解

## 本版目标

v135 的目标是把 `release_gate.py` 里的“计算 release gate 结果”和“把 gate report 写成 JSON/Markdown/HTML 产物”分开。拆分后，`release_gate.py` 继续负责 policy profiles、bundle checks、summary、recommendations 和 `exit_code_for_gate()`；`release_gate_artifacts.py` 负责 JSON 写入、Markdown 渲染、HTML 渲染和三类输出文件的统一落盘。

本版明确不做：

- 不改变 `gate_report.json` 的 schema。
- 不改变 `gate_report.md` 和 `gate_report.html` 的文件名。
- 不改变 `scripts/check_release_gate.py` 的 CLI 参数和调用方式。
- 不改变旧的 `from minigpt.release_gate import write_release_gate_outputs` 导入方式。
- 不把本次拆分解释成模型质量提升或生产发布能力提升；它只让 release gate 的证据发布边界更清楚。

## 前置路线

v135 接在 v134 之后，也是用户确认“后续只做两次左右拆分”的第一刀：

```text
v110 module pressure audit
 -> v119 maintenance policy artifact split
 -> v121 maturity artifact split
 -> v134 maturity narrative artifact split
 -> v135 release gate artifact split
```

v134 后维护预检显示 module pressure 仍为 pass，但最大模块是 `release_gate.py`。它内部存在明确低风险边界：policy/check/summary 是 gate 决策层，JSON/Markdown/HTML 是 artifact 发布层。因此 v135 只拆这个边界，不继续扩大到 release bundle、comparison 或 server。

## 关键文件

- `src/minigpt/release_gate.py`: 保留 `release_gate_policy_profiles()`、`resolve_release_gate_policy()`、`build_release_gate()`、`exit_code_for_gate()` 和所有 gate check/summary/recommendation helper，并从 artifact 模块 re-export 写入与渲染函数。
- `src/minigpt/release_gate_artifacts.py`: 新增 artifact 层，负责 `write_release_gate_json()`、`render_release_gate_markdown()`、`write_release_gate_markdown()`、`render_release_gate_html()`、`write_release_gate_html()` 和 `write_release_gate_outputs()`。
- `tests/test_release_gate.py`: 增加 facade identity 回归测试，确认旧模块导出的 artifact 函数与新模块是同一个函数对象。
- `README.md`: 更新当前版本、能力矩阵、v135 focus、tag 列表、项目结构和截图归档说明。
- `c/135/解释/说明.md`: 说明本版运行证据、截图含义和能力边界。

## gate report 的核心数据结构

`build_release_gate()` 输出的是一个面向本地发布治理的 gate dict，核心字段如下：

```text
schema_version
title
generated_at
bundle_path
release_name
policy
summary
checks
recommendations
bundle_recommendations
warnings
```

`policy` 记录 profile、audit score 阈值、ready run 阈值、是否要求 generation quality 和 request history summary 审计检查。`summary` 汇总 gate_status、decision、pass/warn/fail count、release status、audit score、ready runs 和 missing artifacts。`checks` 是最终 gate 依据，每一项包含 id、title、status、detail。`recommendations` 则根据 pass/warn/fail 给出后续动作。

v135 没有改这些字段，只改变了这些字段如何被写成 JSON、Markdown 和 HTML。

## 拆分前的问题

拆分前，`release_gate.py` 同时承担两类职责：

```text
1. 根据 release bundle 和 policy profile 计算 gate 结果
2. 把 gate dict 渲染和写入 JSON/Markdown/HTML
```

第二类职责包含：

```text
write_release_gate_json
render_release_gate_markdown
write_release_gate_markdown
render_release_gate_html
write_release_gate_html
write_release_gate_outputs
_key_value_section
_check_section
_list_section
_stat
_style
_markdown_table
_fmt_any
_md
```

这些函数不需要知道 audit score 阈值如何解析，也不需要知道 request history summary 缺失时为什么 gate 会 fail。把它们留在主模块里，会让 release policy 和 report rendering 互相挤压。

## 新 artifact 模块的职责

`release_gate_artifacts.py` 只接收已经构建好的 gate dict，不读取 release bundle，不解析 policy profile，也不重新计算 gate status。它做三件事：

- JSON writer: 写出 `gate_report.json`。
- Markdown renderer/writer: 输出 Summary、Policy、Checks、Recommendations、Bundle Recommendations 和 Bundle Warnings。
- HTML renderer/writer: 输出可浏览器打开的 release gate 页面，并继续使用 HTML escaping 保护文本展示。

因此新的边界可以概括为：

```text
release_gate.py 负责 bundle + policy -> gate dict
release_gate_artifacts.py 负责 gate dict -> JSON/Markdown/HTML files
scripts/check_release_gate.py 继续作为 CLI 编排入口
tests 负责锁住 schema、HTML escaping、输出文件和 facade
c/135 负责保存运行证据
```

## facade 为什么要保留

旧调用仍然有效：

```python
from minigpt.release_gate import (
    build_release_gate,
    render_release_gate_html,
    write_release_gate_outputs,
)
```

`build_release_gate()` 仍来自 `release_gate.py`，而 `render_release_gate_html()` 和 `write_release_gate_outputs()` 由 `release_gate.py` 从 `release_gate_artifacts.py` 重新导出。这样 `scripts/check_release_gate.py`、已有测试和外部使用者不需要迁移导入路径。

## 测试覆盖

`tests/test_release_gate.py` 覆盖了几类关键行为：

- policy profiles: 确认 standard/review/strict/legacy profile 可用，且返回副本。
- gate pass/warn/fail: 覆盖 ready bundle、bundle warning、incomplete release、generation quality 缺失、request history summary 缺失。
- policy override: 确认显式参数能覆盖 profile 阈值和 required checks。
- output writer: 确认 JSON/Markdown/HTML 三类文件都写出，并包含 Checks 和 release gate 标题。
- HTML escaping: 确认 release name/title 会被转义。
- facade identity: 确认旧模块导出的 artifact 函数与新模块中的函数对象一致。

再加上 compile check、full unittest discovery、maintenance smoke、source encoding hygiene 和 Playwright HTML 截图，可以证明本次拆分没有破坏导入、CLI、输出文件或浏览器证据页。

## 证据意义

v135 的价值不是新增一个 release gate，而是让 release gate 的“决策计算”和“证据发布”拥有独立维护边界。以后如果要调整 policy profile、audit score 或 checks，应优先改 `release_gate.py`；如果要调整 Markdown/HTML 展示或输出写入，应优先改 `release_gate_artifacts.py`。

真正的能力边界是：

```text
release_gate.py 负责本地发布门禁判断
release_gate_artifacts.py 负责发布同一份门禁证据
README/c/135 负责说明本次拆分和运行证据
模型质量和真实生产发布仍需要真实训练、固定 benchmark、checkpoint 对比和外部流程验证
```

## 一句话总结

v135 把 release gate 从“门禁判断和证据发布混在一个模块”推进到“gate decision + artifact writer”双层结构，是有限拆分计划中的第一刀，维护边界更清楚但能力声明保持克制。
