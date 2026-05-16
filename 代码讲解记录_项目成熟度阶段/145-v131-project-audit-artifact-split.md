# v131 project audit artifact split 代码讲解

## 本版目标

v131 的目标是把 `project_audit.py` 里“审计判断”和“证据文件发布”两种职责分开。拆分后，`project_audit.py` 继续负责读取 registry、model card、request history summary，并计算 checks、summary、recommendations；`project_audit_artifacts.py` 负责把 audit dict 写成 JSON、Markdown、HTML。

本版明确不做：

- 不改变 project audit 的 schema。
- 不改变 pass/warn/fail 评分规则。
- 不改变 `scripts/audit_project.py` 的调用方式。
- 不改变输出文件名：`project_audit.json`、`project_audit.md`、`project_audit.html`。
- 不把治理证据解释成模型质量提升。

## 前置路线

v131 接在 v130 后面，延续同一条压力引导路线：

```text
v110 module pressure audit
 -> v129 training portfolio batch artifact split
 -> v130 experiment card artifact split
 -> v131 project audit artifact split
```

v130 证明 experiment card 可以拆成“run metadata assembly + artifact writer”。v131 把同一方法用在 project audit 上，但对象不同：project audit 是项目级治理检查，不是单 run 实验卡片。它的价值在于把 registry/model-card/request-history 三条证据链汇总为一个审计状态。

## 关键文件

- `src/minigpt/project_audit.py`: 保留核心审计计算，包括 registry 读取、model card 匹配、request history summary 检查、coverage checks、summary 和 recommendations。
- `src/minigpt/project_audit_artifacts.py`: 新增 artifact 层，负责 JSON/Markdown/HTML 写出、HTML section 渲染、Markdown table 渲染和格式化 helper。
- `tests/test_project_audit.py`: 增加 facade identity 断言，保护旧导入路径继续指向新 artifact 实现。
- `README.md`: 更新当前版本、能力矩阵、v131 focus、tag 列表和截图索引。
- `c/131/解释/说明.md`: 说明本版运行证据、截图含义和边界。

## project audit 的核心数据结构

`build_project_audit()` 输出的是一个 audit dict，主要字段包括：

```text
schema_version
title
generated_at
registry_path
model_card_path
request_history_summary_path
summary
checks
request_history_context
runs
recommendations
warnings
```

其中 `summary` 是项目级摘要，例如 overall status、score、run count、ready runs、request history status。`checks` 是逐项审计结果，每条包含：

```text
id
title
status
detail
evidence
```

`runs` 是 registry 与 model card 合并后的 run 表，用于审计每个 run 是否有 checkpoint、dataset quality、eval suite、generation quality、dashboard 和 experiment card。

## 拆分前的问题

拆分前，`project_audit.py` 同时处理两类任务：

```text
1. 审计计算
2. 证据发布
```

审计计算包括 `_build_checks()`、`_summarize_checks()`、`_build_recommendations()`、`_derive_status()` 等。证据发布包括：

```text
write_project_audit_json
render_project_audit_markdown
write_project_audit_markdown
render_project_audit_html
write_project_audit_html
write_project_audit_outputs
```

这些职责混在一个文件里，会让后续修改审计规则时同时面对 HTML、Markdown 和文件写出细节。v131 把输出层拆走后，审计规则更集中，artifact 发布也更容易单独维护。

## 新 artifact 模块的职责

`project_audit_artifacts.py` 承担三类只读证据输出：

- JSON：机器可消费的审计证据。
- Markdown：适合 README、讲解记录和人工审阅的文本证据。
- HTML：适合浏览器打开的可视化审计页面。

这些产物都不参与训练，不修改 registry，不反向改变 model card。它们只是把 audit dict 以不同格式发布出来。

## facade 为什么保留

旧调用仍然有效：

```python
from minigpt.project_audit import build_project_audit, write_project_audit_outputs
```

拆分后 `build_project_audit()` 仍来自 `project_audit.py`，而 `write_project_audit_outputs()` 的真实实现来自 `project_audit_artifacts.py`。测试中新增的 identity 断言保护这一点：

```text
project_audit.write_project_audit_outputs
is project_audit_artifacts.write_project_audit_outputs
```

这能避免旧脚本和旧 import 路径在重构后悄悄分叉。

## 测试覆盖

`tests/test_project_audit.py` 覆盖了几条关键链路：

- 完整项目证据时 audit 应为 `pass`。
- request history summary 非 pass 时 audit 应为 `warn`。
- 缺少 experiment card/model card 时 audit 应给出失败或建议。
- `write_project_audit_outputs()` 仍生成 JSON/Markdown/HTML。
- HTML 对 title/run name 做 escaping，避免报告页面注入未转义文本。
- 旧 facade 导出和新 artifact 模块保持同一函数身份。

再加上 compile check、full unittest、maintenance smoke、source encoding hygiene 和 Playwright HTML 截图，可以证明拆分后代码可导入、输出可生成、页面可打开、编码边界干净。

## 证据意义

v131 的证据不是在证明模型变聪明，而是在证明项目治理链更可维护。project audit 仍然是本地学习型 AI 工程的审计工具，它能检查证据链完整性，但不能替代真实生产审计。

真正的能力边界是：

```text
project_audit.py 负责判断
project_audit_artifacts.py 负责发布
tests 负责锁住旧契约
c/131 负责保留运行证据
```

## 一句话总结

v131 把项目审计从“一个厚模块同时判断和发布”推进到“审计计算 + artifact 发布层”的结构，维护边界更清楚，但审计规则和项目能力声明保持克制不变。
