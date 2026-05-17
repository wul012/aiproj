# v183 maintenance pressure builder split

## 本版目标

v183 的目标是把 module pressure 扫描从 `maintenance_policy.py` 拆到 `maintenance_pressure.py`。

它解决的问题是：`maintenance_policy.py` 同时负责两类维护治理逻辑：

- maintenance batching/proposal policy：判断低风险 utils migration 是否应该合并成一版。
- module pressure audit：扫描 Python 模块行数、AST 函数/类数量、最大函数长度并给出拆分建议。

这两个能力都属于维护治理，但输入、输出、算法和演进节奏不同。v183 把 module pressure builder 独立出来，让 `maintenance_policy.py` 回到 batching/proposal 决策，降低后续继续维护时的认知压力。

本版明确不做：

- 不改变 `build_module_pressure_report()` 的 report schema。
- 不改变 `scripts/check_maintenance_batching.py` 的导入路径和输出文件。
- 不改变 maintenance batching report、proposal decision 的行为。
- 不改变 artifact writer 和 HTML/Markdown/CSV/JSON 输出格式。
- 不把维护扫描包装成新的治理层，也不把模块压力结果解释成模型质量提升。

## 前置路线

v109 引入 maintenance batching policy，用来约束连续单模块 utils migration 的版本粒度。

v110 引入 module pressure audit，用来扫描大文件和长函数，避免只靠主观感受判断是否需要拆分。

v119 已经把 maintenance policy 的 artifact rendering/writing 拆到 `maintenance_policy_artifacts.py`。

v183 是对 v109/v110/v119 的继续收口：artifact 已经独立，压力扫描 builder 也应该从 batching/proposal policy 中独立出来。

## 关键文件

### `src/minigpt/maintenance_pressure.py`

这是本版新增的 module pressure builder。

公开 API：

- `build_module_pressure_report(paths, ...)`
- `DEFAULT_MODULE_WARNING_LINES`
- `DEFAULT_MODULE_CRITICAL_LINES`
- `DEFAULT_MODULE_TOP_N`

核心私有函数：

- `_module_pressure_row()`：读取单个 Python 文件，统计行数、字节数、AST 结构和 parse error。
- `_python_ast_summary()`：用 `ast.parse()` 统计函数数量、类数量、最大函数长度和最大函数名。
- `_module_pressure_status()`：根据 warning/critical 阈值给出 `pass`、`warn`、`critical`。
- `_module_pressure_summary()`：汇总 warn/critical 数量、最大模块、最大函数等信息。
- `_module_pressure_recommendations()`：根据 summary 给出维护建议。

这个模块只负责生成结构化 module pressure report，不负责写文件，不负责 batching policy，也不负责 release/tag 文档。

### `src/minigpt/maintenance_policy.py`

这个模块保留 maintenance batching/proposal policy：

- `build_maintenance_batching_report()`
- `build_maintenance_proposal_decision()`
- release entry/proposal item normalize helpers
- low-risk category/high-risk flag 判断

同时它从 `maintenance_pressure.py` 重新导入并导出：

```python
from minigpt.maintenance_pressure import (
    DEFAULT_MODULE_CRITICAL_LINES,
    DEFAULT_MODULE_TOP_N,
    DEFAULT_MODULE_WARNING_LINES,
    build_module_pressure_report,
)
```

这保证旧调用方继续从 `minigpt.maintenance_policy` 使用 module pressure 能力，不需要知道内部已经拆分。

### `tests/test_maintenance_policy.py`

本版新增 facade identity 测试：

- `maintenance_policy.build_module_pressure_report is maintenance_pressure.build_module_pressure_report`
- 旧导出的默认阈值与新模块常量一致。

这类测试保护的是兼容契约：拆分后行为不是复制一份新实现，而是旧入口指向新实现。

## 数据结构和输入输出

`build_module_pressure_report()` 的输入仍然是 Python 文件路径列表，输出仍然是原来的 report 字典：

- `schema_version`
- `title`
- `generated_at`
- `policy`
- `summary`
- `modules`
- `top_modules`
- `recommendations`

其中每个 module row 包含：

- `path`
- `status`
- `line_count`
- `byte_count`
- `function_count`
- `class_count`
- `max_function_lines`
- `largest_function`
- `parse_error`
- `recommendation`

这些字段仍然由 `maintenance_policy_artifacts.py` 的 JSON/CSV/Markdown/HTML writers 消费。v183 没有改变任何 downstream artifact contract。

## 运行流程

拆分后的 module pressure 链路是：

```text
scripts/check_maintenance_batching.py
 -> minigpt.maintenance_policy.build_module_pressure_report()
 -> minigpt.maintenance_pressure.build_module_pressure_report()
 -> module pressure report dict
 -> minigpt.maintenance_policy_artifacts.write_module_pressure_outputs()
```

maintenance batching 链路仍然留在 policy module：

```text
history/proposal items
 -> maintenance_policy.build_maintenance_batching_report()
 -> maintenance_policy_artifacts.write_maintenance_batching_outputs()
```

两条链路在脚本里一起运行，但 builder 职责已经分开。

## 测试和证据

本版运行的关键验证包括：

- `python -B -m unittest tests.test_maintenance_policy tests.test_maintenance_policy_artifacts -v`
  - 覆盖 batching policy、proposal decision、module pressure builder、artifact outputs 和 facade identity。
- `python -B scripts/check_maintenance_batching.py --out-dir runs/maintenance-v183`
  - 覆盖真实 CLI smoke，确认 batching warning 仍是历史节奏提醒，module pressure 为 `pass`。
- `python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-v183`
  - 确认新增模块没有 BOM、语法错误或 Python 3.11 兼容问题。
- 全量 unittest discovery
  - 确认 v183 没有破坏其他 MiniGPT 链路。

运行截图和解释归档在 `c/183`。这些截图是版本证据，不是后续脚本消费的结构化输入。

## 边界说明

v183 是维护治理内部边界拆分，不是模型能力提升。它让后续处理 registry、playground、benchmark 等较大模块时，可以继续使用 module pressure audit，同时不会让 maintenance policy 模块无限膨胀。

当前 module pressure 仍然是轻量静态分析：它可以提示行数、长函数和 parse error，但不能替代人工设计判断。

## 一句话总结

v183 把 module pressure builder 从 maintenance batching policy 中拆出，让维护治理工具链在保持旧入口稳定的同时拥有更清晰的职责边界。
