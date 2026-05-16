# 第一百五十八版：release gate comparison artifact 拆分

## 本版目标

v158 的目标是把 `release_gate_comparison.py` 里的 JSON、CSV、delta CSV、Markdown 和 HTML artifact 写出/渲染逻辑，拆到 `release_gate_comparison_artifacts.py`。

这一版解决的是 v157 之后新的最大模块压力。v157 把 registry render 降下来后，维护扫描显示 `release_gate_comparison.py` 变成最大模块。这个文件同时负责 profile comparison 的核心计算、delta explanation、推荐语，以及所有输出格式。v158 只拆输出层，保留比较计算和 schema。

本版不做三件事：不改变 `build_release_gate_profile_comparison()` 的 report schema，不改变 `scripts/compare_release_gate_profiles.py` 的调用方式，不改变旧模块中 writer/renderer 的导出名字。

## 前置路线

这版延续 v153、v154 的 artifact split 模式：

- v153：release bundle artifact 渲染写出拆到 `release_bundle_artifacts.py`。
- v154：release readiness artifact 渲染写出拆到 `release_readiness_artifacts.py`。
- v158：release gate profile comparison artifact 渲染写出拆到 `release_gate_comparison_artifacts.py`。

这说明后续遇到“计算 + 输出格式”混在一起的大模块时，优先拆 artifact 层，而不是先改核心算法。

## 关键文件

- `src/minigpt/release_gate_comparison_artifacts.py`  
  新增 332 行模块，保存 `write_release_gate_profile_comparison_json()`、`write_release_gate_profile_comparison_csv()`、`write_release_gate_profile_delta_csv()`、Markdown/HTML renderer、以及 `write_release_gate_profile_comparison_outputs()`。

- `src/minigpt/release_gate_comparison.py`  
  从 581 行降到 284 行。它继续负责 profile 列表校验、baseline 解析、调用 `build_release_gate()`、构建 rows、构建 deltas、summary 和 recommendations。writer/renderer 从 artifact 模块导入并继续对外导出。

- `tests/test_release_gate_comparison.py`  
  增加 facade identity 测试，确认旧模块里的 renderer/writer 与 artifact 模块是同一个对象。这样旧 import path 不会被后续拆分破坏。

- `README.md`、`c/README.md`、`代码讲解记录_项目成熟度阶段/README.md`  
  同步 v158 版本说明、证据路径和讲解索引。

## 核心边界

拆分后，比较计算链路仍然在 `release_gate_comparison.py`：

```text
bundle paths
  -> build_release_gate(... profile ...)
  -> _row_from_gate()
  -> _build_profile_deltas()
  -> _build_comparison_summary()
  -> _comparison_recommendations()
```

artifact 输出链路进入 `release_gate_comparison_artifacts.py`：

```text
comparison report
  -> JSON
  -> CSV
  -> delta CSV
  -> Markdown
  -> HTML
```

这条边界的含义是：profile 决策、delta 状态和 explanation 算法仍然属于 comparison 主模块；文件格式、页面布局和 CSV 字段属于 artifact 模块。

## 兼容性

`release_gate_comparison.py` 仍然导出旧名字：

```python
render_release_gate_profile_comparison_html
render_release_gate_profile_comparison_markdown
write_release_gate_profile_comparison_outputs
write_release_gate_profile_delta_csv
```

测试里使用 `assertIs()` 验证这些对象实际指向 `release_gate_comparison_artifacts.py`。这能保护两类用户：

- 从 `minigpt.release_gate_comparison` 导入旧函数的脚本。
- 直接从 artifact 模块导入新函数的后续维护代码。

## 输出字段

artifact 模块保留原有输出：

- `release_gate_profile_comparison.json`
- `release_gate_profile_comparison.csv`
- `release_gate_profile_deltas.csv`
- `release_gate_profile_comparison.md`
- `release_gate_profile_comparison.html`

CSV 字段没有改变。Markdown 仍然包含 Summary、Profile Matrix、Profile Deltas、Recommendations。HTML 仍然包含 stats、Profile Matrix、Profile Deltas 和 Recommendations。

## 测试覆盖

`tests/test_release_gate_comparison.py` 继续覆盖：

- 一个 bundle 在 standard/review/strict/legacy 多 profile 下的矩阵。
- 显式 baseline profile。
- legacy profile 对缺 generation quality/request history 的兼容。
- 多 bundle 比较。
- 空输入/未知 profile/baseline 不在 profiles 中的错误。
- 输出文件存在且内容包含 profile matrix、delta 和 HTML 关键词。
- HTML 转义与 Markdown 原文边界。
- facade identity。

这些测试覆盖了计算结果、输出产物和旧导入路径三类风险。

## 维护压力结果

本版拆分前：

```text
release_gate_comparison.py = 581 lines
```

拆分后：

```text
release_gate_comparison.py = 284 lines
release_gate_comparison_artifacts.py = 332 lines
module_pressure_status=pass
module_warn_count=0
```

这说明 v158 把当前最大模块里的输出层拆出，同时没有改 release gate comparison 的核心比较逻辑。

## 运行截图和证据

v158 的运行证据归档在 `c/158`：

- `01-release-gate-comparison-tests.png`：证明 release gate comparison 测试覆盖 artifact split 和 facade 兼容。
- `02-release-gate-comparison-smoke.png`：证明直接生成 comparison report 后能写出 JSON/CSV/delta CSV/Markdown/HTML。
- `03-maintenance-smoke.png`：证明维护扫描和模块压力扫描仍为 pass。
- `04-source-encoding-smoke.png`：证明源码编码、语法和 Python 3.11 兼容性门禁通过。
- `05-full-unittest.png`：证明全量测试通过。
- `06-docs-check.png`：证明 README、`c/158`、讲解索引、新 artifact 模块和测试关键词都已对齐。

## 一句话总结

v158 把 release gate profile comparison 的输出格式层从比较计算层拆开，让 profile decision/delta 逻辑更聚焦，也让 artifact 渲染和写出更容易单独维护。
