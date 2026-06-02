# v785 registry release-readiness summary split

## 本版目标和边界

v785 是维护拆分版本，不新增 registry 功能，不改变 registry JSON/CSV/SVG/HTML 输出，也不改变 `build_run_registry`、`summarize_registered_run`、`discover_run_dirs` 的 public API。本版只把 `registry_data.py` 内部的 release-readiness comparison 读取、状态判定和 requirement delta 统计拆到独立模块。

本版不改变：

- `RegisteredRun` 字段。
- registry report schema。
- rankings 侧的 release-readiness delta rows、leaderboard、summary。
- artifact/render/leaderboard 模块对 `registry_data._as_optional_float` 等历史私有 helper 的导入。

## 为什么这一刀有必要

`registry_data.py` 原来同时负责：

- run manifest、dataset、benchmark、generation-quality、pair report 等 artifact 汇总。
- `RegisteredRun` dataclass 和 run summary 构造。
- release-readiness comparison status 判定。
- release-readiness benchmark requirement 的状态变化、exit code delta、failed reason added/removed/mixed 统计。

后两类 release-readiness 逻辑与 registry 主流程耦合过深，而且字段名很长。它们继续堆在 `registry_data.py` 会让 run summary 构造难读，也会让未来调整 release-readiness comparison 字段时误碰 registry 其他输入。

v785 把这些 release-readiness 摘要 helper 移到 `registry_release_readiness_summary.py`，让主模块只保留调用点。

## 关键文件

### `src/minigpt/registry_release_readiness_summary.py`

新增模块，负责：

- `read_release_readiness_comparison(root)`
- `release_readiness_html_exists(root)`
- `release_readiness_comparison_status(summary)`
- `release_readiness_deltas(report)`
- benchmark readiness requirement 的 status change、numeric delta、positive delta、exit code delta、failed reason added/removed/mixed 统计。

这个模块只处理 registry 对 release-readiness comparison 的摘要读取和字段计算，不生成 leaderboard，不生成 artifact 文件。

### `src/minigpt/registry_release_readiness.py`

这个文件在 v785 中保留原职责：供 `registry_rankings.py` 导入 `collect_release_readiness_delta_rows`、`release_readiness_delta_leaderboard`、`release_readiness_delta_summary`。本版最初尝试使用同名模块时触发导入回归，因此最终选择更精确的新名字 `registry_release_readiness_summary.py`。

### `src/minigpt/registry_data.py`

主模块现在从 summary 模块导入 release-readiness helper。拆分后文件从 634 行降到 507 行。

另外，本版保留 `_as_optional_float` 在 `registry_data.py` 中的定义。虽然它已经不是 registry data 自身的核心逻辑，但 `registry_artifacts.py`、`registry_render.py`、`registry_leaderboards.py` 仍有历史私有导入。为了保持本版边界稳定，v785 不顺手改这些调用方。

## 数据流

```text
run directory
  -> summarize_registered_run
  -> read_release_readiness_comparison
  -> release_readiness_comparison_status
  -> benchmark requirement delta helpers
  -> RegisteredRun release_readiness_* fields
  -> build_run_registry
```

这条链路的契约点是 `RegisteredRun` 字段和 registry 输出。v785 只移动 helper 所在文件，不改变这些字段的语义。

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\registry_data.py src\minigpt\registry_release_readiness.py src\minigpt\registry_release_readiness_summary.py
python -m pytest tests\test_registry.py tests\test_registry_split.py tests\test_coverage_governance_chain.py -q -o cache_dir=runs\pytest-cache-v785-focused
python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-v785
git diff --check
```

结果：

- focused tests: `24 passed`
- source encoding: `status=pass`
- diff check: pass

这些测试覆盖 registry facade、data/render/artifact split、release-readiness comparison counts、coverage governance chain 对 registry 输出的消费。它们保护了本版最关键的行为：release-readiness 状态和 delta 继续出现在 registry/maturity 链路中。

## 运行证据

本版运行证据归档在：

- `e/785/解释/说明.md`
- `e/785/解释/refactor-summary.html`
- `e/785/图片/v785-registry-release-readiness-summary-split.png`

HTML 证据页展示了拆分后的职责边界、行数变化和测试结果。截图用于确认归档页面可打开，核心指标可见。

## 一句话总结

v785 把 registry 中 release-readiness 摘要层从 run summary 主模块拆出，让 registry 数据模块更像协调层，也为后续继续收束 registry artifact/render 兼容入口留出空间。
