# v119 maintenance policy artifact split 代码讲解

## 本版目标

v119 继续执行 v110 的 module pressure audit 路线，目标是把 `maintenance_policy.py` 中已经稳定的输出写入和页面渲染逻辑抽到独立模块：

```text
maintenance_policy.py           -> batching policy、proposal decision、module pressure scan、AST summary、recommendations、旧导出
maintenance_policy_artifacts.py -> maintenance batching 和 module pressure 的 JSON/CSV/Markdown/HTML 输出与展示 helper
```

本版解决的问题是：v109-v110 把“低风险维护要不要合并”和“大模块压力怎么判断”做成了可运行工具，但 `maintenance_policy.py` 后续同时承担策略计算、AST 扫描、CSV/Markdown/HTML 输出和页面 helper。v119 把证据发布层拆出，让维护策略本体从 751 非空行降到 414 非空行。

本版明确不做：

- 不改变 `build_maintenance_batching_report()` 的 report schema。
- 不改变 `build_module_pressure_report()` 的 report schema。
- 不改变 `scripts/check_maintenance_batching.py` 的 CLI 参数和输出文件名。
- 不改变 `minigpt.maintenance_policy` 的旧 public artifact 导出。
- 不改变 module pressure 的 warning/critical 阈值、AST 统计方式或 recommendation 规则。

## 前置路线

v119 接在这条维护收口路线后面：

```text
v109 maintenance batching policy
 -> v110 module pressure audit
 -> v111-v118 多个厚模块 artifact/contract/data split
 -> v119 maintenance policy artifact split
```

这说明项目不只是用 maintenance policy 约束其他模块，也开始反过来治理维护工具本身。策略判断应该留在 policy 模块；JSON/CSV/Markdown/HTML 发布应该进入 artifact 模块。

## 关键文件

```text
src/minigpt/maintenance_policy_artifacts.py
src/minigpt/maintenance_policy.py
tests/test_maintenance_policy_artifacts.py
README.md
代码讲解记录_项目成熟度阶段/README.md
c/119/图片
c/119/解释/说明.md
```

`src/minigpt/maintenance_policy_artifacts.py` 是本版新增的 artifact 层。它负责两组证据输出：

- maintenance batching：`maintenance_batching.json`、`maintenance_batching.csv`、`maintenance_batching.md`、`maintenance_batching.html`
- module pressure：`module_pressure.json`、`module_pressure.csv`、`module_pressure.md`、`module_pressure.html`

`src/minigpt/maintenance_policy.py` 仍然是旧 public API 的入口。它继续负责：

- release history 归一化。
- proposal item 归一化。
- batching / split / batch_by_category / single_ok 决策。
- Python module pressure 扫描。
- AST function/class/largest function 统计。
- summary 和 recommendations。

旧代码继续写：

```python
from minigpt.maintenance_policy import write_module_pressure_outputs
```

不会被破坏。

`tests/test_maintenance_policy_artifacts.py` 是新增测试。它直接导入 artifact 模块，验证 artifact 模块可以独立消费 report，并验证 `minigpt.maintenance_policy` 的旧导出仍然指向新实现。

## 核心数据结构

maintenance batching report 的关键字段包括：

- `policy.single_module_utils_limit`：连续单模块 utils 迁移的警戒阈值。
- `summary.status`：`pass` 或 `warn`。
- `summary.decision`：例如 `batch_next_related_work` 或 `continue_with_policy`。
- `single_module_utils_runs`：连续单模块 utils migration 的起止版本、长度和版本列表。
- `proposal`：当前提议的维护项是否适合 batch、按 category batch、split 或 single_ok。
- `recommendations`：下一步维护节奏建议。

module pressure report 的关键字段包括：

- `policy.warning_lines` / `policy.critical_lines`：行数阈值。
- `modules`：每个 Python 模块的 path、status、line_count、byte_count、function_count、class_count、largest_function 和 recommendation。
- `top_modules`：按行数排序后的前 N 个模块。
- `summary`：warn/critical 数量、最大模块、最大函数和整体 decision。
- `recommendations`：是否需要小步拆分、是否只需观察。

这些字段仍由 `maintenance_policy.py` 计算。v119 只改变它们写入文件和渲染页面的位置。

## 核心函数

`write_maintenance_batching_outputs(report, out_dir)`

统一写出 batching policy 的 JSON、CSV、Markdown 和 HTML。JSON 是完整机器可读证据；CSV 是 summary/proposal 单行摘要；Markdown/HTML 用于人工检查和截图。

`write_module_pressure_outputs(report, out_dir)`

统一写出 module pressure 的 JSON、CSV、Markdown 和 HTML。CSV 展开每个模块的 `line_count`、`function_count`、`max_function_lines` 和 `recommendation`，适合快速排序和审查。

`render_maintenance_batching_markdown()` / `render_maintenance_batching_html()`

渲染 maintenance batching 的 summary、single-module utility runs、proposal 和 recommendations。

`render_module_pressure_markdown()` / `render_module_pressure_html()`

渲染 module pressure 的 summary、top modules 和 recommendations。HTML 仍然做 escaping，因此标题里的 `<...>` 不会变成真实标签。

## 输入输出边界

v119 后的运行流程是：

```text
history/proposal/module paths
 -> maintenance_policy.build_maintenance_batching_report()
 -> maintenance_policy.build_module_pressure_report()
 -> report dicts
 -> maintenance_policy_artifacts.write_*()
 -> JSON/CSV/Markdown/HTML evidence
```

artifact 输出是正式证据，不是临时调试文件。CLI 仍然写到用户指定的 `--out-dir`，文件名保持不变。artifact 模块不读取版本历史、不扫描 Python 文件、不解析 AST，因此它不会影响策略判断。

## 测试覆盖

`tests/test_maintenance_policy_artifacts.py` 新增两类断言：

- 直接调用 artifact 模块写出 maintenance batching 和 module pressure 两组输出，检查 JSON/CSV/Markdown/HTML 都存在，CSV header、Markdown section 和 HTML escaping 都正确。
- 验证 `minigpt.maintenance_policy` 的旧 artifact 函数与 `maintenance_policy_artifacts` 中的新函数是同一对象，锁住 facade parity。

原有 `tests/test_maintenance_policy.py` 继续覆盖：

- 连续单模块 utils migration 的 warn 判断。
- batched utils release 打断 warning run。
- proposal batch/split 决策。
- module pressure 对大文件、语法错误和 HTML escaping 的处理。

## 运行证据

v119 的运行证据放在：

```text
c/119/图片
c/119/解释/说明.md
```

截图覆盖新增 artifact 单测、旧 maintenance policy 回归、compileall、全量 unittest、CLI smoke、输出文件检查、Playwright/Chrome 打开 HTML、README/阶段索引/c README 检查。

README 更新了当前版本、版本标签、结构树和截图索引。阶段 README 追加了 `134-v119-maintenance-policy-artifact-split.md`，说明这次拆分属于项目成熟度阶段的治理工具自我收口。

## 一句话总结

v119 把 maintenance policy 从“策略判断、AST 扫描和证据发布混在一个模块”推进到“policy logic 与 artifact rendering 分离”的维护状态，让治理工具本身也更容易继续演进。
