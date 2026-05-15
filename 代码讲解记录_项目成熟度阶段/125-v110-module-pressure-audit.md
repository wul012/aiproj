# 第一百一十版代码讲解：Module Pressure Audit

## 本版目标

v110 的目标是回应“aiproj 代码膨胀持续，应该做轻量定向质量优化”的判断，并把它落成可运行、可测试、可截图归档的模块体量压力扫描。

它解决的问题是：项目已经有了 v109 的版本粒度策略，但“哪些模块真的大、应该优先看哪里、是否需要马上重构”还容易停留在主观印象。v110 不直接拆 `server.py`、`registry.py` 或 `playground.py`，而是先建立一份量化报告，让后续拆分有依据。

本版明确不做：

- 不改变 MiniGPT 模型、训练、推理、评估或发布门禁行为。
- 不重构大模块，不移动 `server.py`、`registry.py`、`benchmark_scorecard.py` 里的业务逻辑。
- 不把行数当成唯一质量指标，也不因为文件大就自动要求重写。
- 不把服务/API、UI 或输出契约变更藏进维护批次。

## 路线来源

本版来自 v109 的维护策略线：

```text
v83 report_utils consolidation
 -> v108 batched low-risk utility migration
 -> v109 maintenance batching policy
 -> v110 module pressure audit
```

v109 回答的是“低风险维护是否拆得太碎”；v110 回答的是“模块体量压力是否已经需要计划性拆分”。这两者共同约束后续质量优化：低风险同类清理要合并，大模块拆分要谨慎、定向、有测试保护。

## 关键文件

- `src/minigpt/maintenance_policy.py`
  - 新增 `build_module_pressure_report` 和 `write_module_pressure_outputs`。
  - 使用标准库 `ast` 读取 Python 模块结构，统计行数、函数数、类数和最长函数跨度。
  - 输出 JSON/CSV/Markdown/HTML，和 v109 的 batching 报告保持同一维护策略入口。
- `scripts/check_maintenance_batching.py`
  - 扩展 CLI。
  - 默认仍生成 `maintenance_batching.*`，同时扫描 `src/minigpt` 并生成 `module_pressure.*`。
  - 新增 `--module-scope`、`--module-warning-lines`、`--module-critical-lines`、`--module-top-n` 和 `--skip-module-pressure`。
- `tests/test_maintenance_policy.py`
  - 新增 module pressure 单测。
  - 覆盖大模块阈值、AST 函数跨度、语法错误容错、输出文件生成和 HTML 转义。
- `src/minigpt/__init__.py`
  - 导出 `build_module_pressure_report` 和 `write_module_pressure_outputs`。
- `README.md`
  - 当前版本、命令说明、tag 列表和截图归档更新到 v110。
- `c/110`
  - 保存本版运行截图和解释。

## 核心数据结构

`build_module_pressure_report(paths, ...)` 的输入是 Python 文件路径列表。CLI 默认从 `src/minigpt` 递归收集 `*.py`。

每个模块会归一成一条 module row：

```json
{
  "path": "src\\minigpt\\server.py",
  "status": "critical",
  "line_count": 1676,
  "byte_count": 68508,
  "function_count": 83,
  "class_count": 8,
  "max_function_lines": 526,
  "largest_function": "create_handler",
  "parse_error": "",
  "recommendation": "Plan a targeted split around stable contracts before adding more features."
}
```

关键字段语义：

- `path`：相对项目根目录的模块路径。
- `status`：按行数阈值分为 `pass`、`warn`、`critical`。
- `line_count`：文本行数，用于发现体量压力。
- `function_count` / `class_count`：由 AST 统计，用于辅助判断模块复杂度。
- `max_function_lines` / `largest_function`：最长函数跨度，帮助优先找更小的抽取点。
- `parse_error`：语法错误或读取异常，不吞掉异常信息。
- `recommendation`：针对该模块的轻量建议。

报告的 `summary` 记录：

- `module_count`：扫描模块数量。
- `warn_count` / `critical_count`：超过阈值的模块数量。
- `largest_module` / `largest_line_count`：最大文件。
- `largest_function` / `largest_function_lines`：最长函数。
- `decision`：
  - `plan_targeted_split`：存在 critical 模块，应该计划性拆分。
  - `monitor_large_modules`：存在 warn 模块，先观察并随相关改动抽取。
  - `continue`：没有体量压力。

## 核心函数

`build_module_pressure_report(paths, project_root=...)`

这是总入口。它逐个读取 Python 文件，生成 module row，按行数降序排序，再生成 summary、top modules 和 recommendations。

`_python_ast_summary(text)`

它用 `ast.parse` 构建语法树，再统计：

- `ast.FunctionDef`
- `ast.AsyncFunctionDef`
- `ast.ClassDef`

函数跨度使用 `lineno` 和 `end_lineno` 计算。这样比字符串搜索更稳，也能避免把注释里的 `def` 当成函数。

`_module_pressure_status(line_count, warning_lines, critical_lines)`

默认阈值：

```text
warning_lines = 700
critical_lines = 1200
```

这些阈值不是生产级复杂度标准，而是本项目当前阶段的维护提示线。它们的作用是提醒“接下来再碰这个模块时要先想边界”，不是强制马上拆。

`write_module_pressure_outputs(report, out_dir)`

写出：

- `module_pressure.json`
- `module_pressure.csv`
- `module_pressure.md`
- `module_pressure.html`

JSON 是机器可读主证据；CSV 适合快速排序；Markdown 适合代码审查；HTML 用于浏览器查看和 Playwright 截图。

## CLI 运行流程

默认命令：

```powershell
python scripts/check_maintenance_batching.py --out-dir runs/maintenance-batching
```

流程是：

```text
读取 history/proposal 或默认 smoke 数据
 -> build_maintenance_batching_report()
 -> 写出 maintenance_batching.*
 -> 收集 module scope 下的 Python 文件
 -> build_module_pressure_report()
 -> 写出 module_pressure.*
 -> 打印 batching summary 和 module pressure summary
```

可以只看某个目录或文件：

```powershell
python scripts/check_maintenance_batching.py --module-scope src/minigpt/server.py --out-dir runs/server-pressure
```

也可以跳过模块体量扫描：

```powershell
python scripts/check_maintenance_batching.py --skip-module-pressure
```

## 本版扫描结论

本版 smoke 扫描 `src/minigpt`，得到：

- `module_count=53`
- `module_pressure_status=warn`
- `module_pressure_decision=plan_targeted_split`
- `module_critical_count=3`
- `module_warn_count=7`
- `largest_module=src\minigpt\server.py`

当前 critical 模块是：

- `src\minigpt\server.py`
- `src\minigpt\registry.py`
- `src\minigpt\benchmark_scorecard.py`

这说明之前“代码膨胀持续”的判断合理，但落实方式不应该是大重构。更合理的顺序是：先围绕稳定契约拆小块，例如 server 的 handler/HTML artifact 边界、registry 的 HTML script/helper 边界、scorecard 的渲染/评分边界。

## 测试覆盖

`tests/test_maintenance_policy.py` 新增三类测试：

- 大模块阈值测试：构造临时 Python 文件，确认超过阈值后 summary 进入 `plan_targeted_split`，最大模块和最长函数能被识别。
- 语法错误容错测试：构造 broken Python 文件，确认 `parse_error` 记录 `syntax-error:<line>`，而不是让整个报告失败。
- 输出与转义测试：确认 JSON/CSV/Markdown/HTML 都生成，HTML 标题会转义 `<Pressure>`，Markdown 保留原始可读文本。

这些测试保护的是“扫描依据”和“报告契约”，避免后续改动把大模块识别、AST 容错或输出格式破坏掉。

## 证据闭环

v110 证据放在 `c/110`：

- `01-unit-tests.png`：证明 focused tests、compileall 和全量 unittest 通过。
- `02-maintenance-pressure-smoke.png`：证明 CLI 同时生成 batching 和 module pressure 报告。
- `03-module-pressure-structure-check.png`：证明源码、CLI、测试、导出、README、讲解和 c 归档对齐。
- `04-module-pressure-output-check.png`：证明 module pressure JSON/CSV/Markdown/HTML 字段存在，且 critical 模块被识别。
- `05-playwright-module-pressure-html.png`：证明 HTML 报告能在真实 Chrome 中渲染。
- `06-docs-check.png`：证明 README、c/README 和项目成熟度阶段索引引用 v110。

## 一句话总结

v110 把“代码膨胀持续”的合理批评转化为可运行的 module pressure audit，让后续 MiniGPT 质量优化从主观感受推进到有阈值、有 AST 证据、有截图闭环的定向拆分计划。
