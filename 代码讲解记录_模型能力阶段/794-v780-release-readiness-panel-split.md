# v780 release readiness panel split

## 本版目标和边界

v780 是维护优化版本，不新增 dashboard 字段、不新增 gate、不改变 release readiness 的输入输出 contract。它只处理 `release_readiness.py` 中的 panel builder 过多问题。

本版不改变：

- `build_release_readiness_dashboard` 的函数签名。
- release readiness report 的 `summary`、`panels`、`actions`、`evidence` 结构。
- Markdown/HTML/JSON 输出函数。
- 现有 release readiness 测试 fixture。

## 为什么这一刀有必要

`release_readiness.py` 原本同时负责：

- 解析 bundle 路径和可选输入路径。
- 读取 registry、audit、gate、request history、maturity、CI workflow、coverage JSON。
- 组装 dashboard summary。
- 生成 actions 和 evidence。
- 构造九类 panel 的 detail 文本。

其中 panel 构造占了大量篇幅，并且每个 panel 都有自己的 fallback 字段和展示口径。继续放在主文件里，会让 dashboard 主流程难以阅读，也会让以后调整某个 panel detail 时误碰路径解析或 summary 逻辑。

## 关键文件

### `src/minigpt/release_readiness_panels.py`

新增模块承接 panel 构造：

- `registry_panel`
- `bundle_panel`
- `audit_panel`
- `gate_panel`
- `request_history_panel`
- `benchmark_history_panel`
- `maturity_panel`
- `ci_workflow_panel`
- `test_coverage_panel`

它只做 panel 的 `key/title/status/detail/source_path` 构造，不负责读取 JSON，不负责决定 dashboard 总状态，不负责写 artifact。

### `src/minigpt/release_readiness.py`

主文件现在通过别名导入 panel builder：

```python
from minigpt.release_readiness_panels import (
    audit_panel as _audit_panel,
    benchmark_history_panel as _benchmark_history_panel,
    bundle_panel as _bundle_panel,
    ci_workflow_panel as _ci_workflow_panel,
    gate_panel as _gate_panel,
    maturity_panel as _maturity_panel,
    registry_panel as _registry_panel,
    request_history_panel as _request_history_panel,
    test_coverage_panel as _test_coverage_panel,
)
```

主文件保留 dashboard 的编排职责：

- `build_release_readiness_dashboard` 负责路径、读取、组装。
- `_summary` 负责 dashboard summary。
- `_actions` 负责 release action list。
- `_evidence` 负责 bundle artifact evidence 行。

拆分后主文件从 701 行降到 391 行。

## 数据流

```text
bundle path + optional inputs
  -> build_release_readiness_dashboard
  -> read JSON inputs
  -> release_readiness_panels.*
  -> summary / actions / evidence
  -> release readiness report
```

panel 模块只在第三步介入，它消费已经读取好的 dict 和 path，不参与文件系统读取。

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\release_readiness.py src\minigpt\release_readiness_panels.py
python -m pytest tests\test_release_readiness.py -q -o cache_dir=runs\pytest-cache-v780-focused
```

结果 `14 passed`。这组测试覆盖 release readiness dashboard 的主要 panel、summary、action 和 fallback 行为，因此能确认 panel 拆分后输出没有漂移。

## 运行证据

本版运行证据归档在：

- `e/780/解释/说明.md`
- `e/780/解释/refactor-summary.html`
- `e/780/图片/v780-release-readiness-panel-split.png`

这些证据说明拆分边界、行数变化和定向测试，不是新的生产 contract。

## 一句话总结

v780 把 release readiness dashboard 的 panel 细节从主流程中拆出，让主文件回到路径读取、汇总编排和产物输出的清晰职责。
