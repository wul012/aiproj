# v133 registry ranking split 代码讲解

## 本版目标

v133 的目标是把 `registry_data.py` 里“读取 run 证据”和“根据多 run 证据做排名/趋势聚合”分开。拆分后，`registry_data.py` 继续负责发现 run、读取 manifest/history/dataset/eval/pair/release-readiness 文件、构造 `RegisteredRun`，并组装最终 registry dict；`registry_rankings.py` 负责 loss leaderboard、benchmark rubric leaderboard、pair delta、release readiness delta 和 count helper。

本版明确不做：

- 不改变 registry JSON schema。
- 不改变 `build_run_registry()` 的输出字段。
- 不改变 `scripts/register_runs.py` 的 CLI 行为。
- 不改变 registry HTML/CSS/JS 的展示逻辑。
- 不把 registry 排名能力解释成模型质量提升；它只是让已有证据更清楚地聚合。

## 前置路线

v133 接在 v132 后，继续沿用 v110 以来的 pressure-guided cleanup 路线：

```text
v110 module pressure audit
 -> v116 registry data/render split
 -> v128 registry artifact split
 -> v132 training portfolio artifact split
 -> v133 registry ranking split
```

v132 后维护 smoke 显示最大模块转到 `registry_data.py`，但 module pressure 仍为 pass。因此 v133 不是大重构，而是抓住清晰边界：registry data 负责“从 run 读出事实”，registry rankings 负责“跨 run 排名和 delta 聚合”。

## 关键文件

- `src/minigpt/registry_data.py`: 保留 `REGISTRY_ARTIFACT_PATHS`、`RegisteredRun`、`discover_run_dirs()`、`summarize_registered_run()` 和 `build_run_registry()`。
- `src/minigpt/registry_rankings.py`: 新增 ranking/delta 层，负责 loss/rubric leaderboards、benchmark rubric summary、pair delta rows/summary/leaderboard、release readiness delta rows/summary/leaderboard 和 counts。
- `tests/test_registry_rankings.py`: 新增直接测试，覆盖 in-place rank annotation、rubric regression summary、pair delta 聚合、release readiness delta 聚合和 counts。
- `README.md`: 更新当前版本、能力矩阵、v133 focus、tag 列表、项目结构和截图归档说明。
- `c/133/解释/说明.md`: 说明本版运行证据、截图含义和能力边界。

## registry 的核心数据结构

`summarize_registered_run()` 输出 `RegisteredRun`，字段来自多个 run artifact：

```text
run_manifest.json
history_summary.json
dataset_quality.json
eval_suite/eval_suite.json
generation_quality.json
benchmark_scorecard.json
pair_generation_batch.json
pair_batch_trend.json
release_readiness_comparison.json
run_notes.json
```

`build_run_registry()` 会把多个 `RegisteredRun` 转为 `run_rows`，再组合出 registry dict：

```text
schema_version
run_count
runs
best_by_best_val_loss
loss_leaderboard
benchmark_rubric_leaderboard
benchmark_rubric_summary
pair_delta_summary
pair_delta_leaderboard
release_readiness_delta_summary
release_readiness_delta_leaderboard
quality_counts
generation_quality_counts
benchmark_rubric_counts
release_readiness_comparison_counts
pair_report_counts
tag_counts
```

v133 没有改这些字段，只改变了这些字段背后的计算所在模块。

## 拆分前的问题

拆分前，`registry_data.py` 同时承担两类职责：

```text
1. 从单个 run 目录读取事实
2. 对多个 run 做排名、delta 聚合和 summary
```

第二类职责包括：

```text
_annotate_loss_leaderboard
_annotate_rubric_leaderboard
_benchmark_rubric_summary
_collect_pair_delta_rows
_pair_delta_summary
_pair_delta_leaderboard
_collect_release_readiness_delta_rows
_release_readiness_delta_summary
_release_readiness_delta_leaderboard
_counts
```

这些函数不需要知道 `RegisteredRun` 是如何从磁盘读取出来的。把它们留在 `registry_data.py` 会让读取逻辑和聚合逻辑互相挤压，后续新增排行榜或 delta panel 时更容易把文件继续拉长。

## 新 ranking 模块的职责

`registry_rankings.py` 负责四类跨 run 聚合：

- Loss leaderboard: 按 `best_val_loss` 升序排名，并给 run rows 写入 rank/delta/is_best。
- Benchmark rubric leaderboard: 按 rubric avg score 降序排名，并给 run rows 写入 rank/delta/is_best。
- Pair delta aggregation: 从 pair batch reports 中提取 case 级 generated/continuation delta，生成 summary 和 leader list。
- Release readiness delta aggregation: 从 readiness comparison reports 中提取 status/panel/audit deltas，生成 summary 和 prioritized leader list。

这些聚合结果是 registry 的只读证据，不参与训练，不修改 run artifacts，也不代表自动判断模型生产可用。

## facade 为什么不用改

旧调用仍然有效：

```python
from minigpt.registry import build_run_registry, write_registry_outputs, render_registry_html
```

`build_run_registry()` 仍来自 `registry_data.py`，`write_registry_outputs()` 仍来自 `registry_artifacts.py`，`render_registry_html()` 仍来自 `registry_render.py`。v133 只是在 `build_run_registry()` 内部委托 `registry_rankings.py` 做排名和 delta 聚合，所以外部调用方不需要迁移。

## 测试覆盖

`tests/test_registry_rankings.py` 直接覆盖了新模块职责：

- loss leaderboard 会给 run rows 写入 rank、delta 和 is_best。
- rubric leaderboard 会给 run rows 写入 rank 和 delta，并生成 regression summary。
- pair delta rows 能跨 run 聚合，leaderboard 会把最大绝对 delta 排到前面。
- release readiness delta rows 能区分 improved/regressed，并优先展示 regressed。
- counts helper 保持原 registry count 行为。

既有 `tests/test_registry.py` 和 `tests/test_registry_split.py` 继续保护完整 registry schema、HTML 输出、facade identity、pair/readiness panel 和脚本入口。再加 compile check、maintenance smoke、source encoding hygiene、full unittest discovery 和 Playwright HTML 截图，可以证明拆分没有破坏导入、输出或浏览器证据页。

## 证据意义

v133 的价值不是新增一个排行榜，而是让排行榜和 delta 聚合有了自己的维护边界。以后如果要新增新的 registry 排名维度，应该优先考虑放在 `registry_rankings.py`，而不是继续把 `registry_data.py` 拉长。

真正的能力边界是：

```text
registry_data.py 负责读取和组装事实
registry_rankings.py 负责跨 run 排名和 delta 聚合
registry_render.py 负责浏览器展示
registry_artifacts.py 负责文件写出
tests 负责锁住 schema 和 facade
c/133 负责保存运行证据
```

## 一句话总结

v133 把 registry 从“数据读取和跨 run 聚合混在一个厚模块”推进到“事实读取 + ranking/delta 聚合层”的结构，维护边界更清楚，但模型质量声明保持克制不变。
