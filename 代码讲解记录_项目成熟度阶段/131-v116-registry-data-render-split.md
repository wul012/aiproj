# v116 registry data/render split 代码讲解

## 本版目标

v116 继续执行 v110 的 module pressure audit 路线，目标是把 `registry.py` 从一个同时负责 run 发现、artifact 读取、registry 数据汇总、CSV/SVG/HTML 输出和交互页面辅助函数的大文件，拆成三个更清楚的边界：

```text
registry_data.py   -> 数据发现、读取、汇总、排行榜结构
registry_render.py -> JSON/CSV/SVG/HTML 输出和展示辅助函数
registry.py        -> 兼容旧 public API 的 facade
```

本版解决的问题是：v111 只先拆了 registry 的 CSS/JavaScript 资产，降低了展示资产体量，但 registry 主体仍然偏厚。v116 回到主体逻辑，把“生成 registry 数据”和“把 registry 数据发布成文件/页面”分开。

本版明确不做：

- 不改 registry JSON schema。
- 不改 `scripts/register_runs.py` 的调用方式。
- 不改 `minigpt.registry` 的公开导入入口。
- 不改 registry HTML 的交互行为、字段、链接和 leaderboard 含义。
- 不新增模型训练能力，也不把治理工具描述成模型质量提升。

## 前置路线

v116 接在这条维护收口路线后面：

```text
v109 maintenance batching policy
 -> v110 module pressure audit
 -> v111 registry asset split
 -> v112 pair artifact split
 -> v113 request history core split
 -> v114 benchmark scorecard artifact split
 -> v115 playground asset split
 -> v116 registry data/render split
```

v111 证明 registry 的静态页面资产可以先独立维护。v116 进一步证明 registry 的核心也可以按职责拆开：数据层只关心 run 目录里有什么证据，渲染层只关心如何把已经汇总好的 registry 发布成可读产物。

## 关键文件

```text
src/minigpt/registry_data.py
src/minigpt/registry_render.py
src/minigpt/registry.py
tests/test_registry_split.py
tests/test_registry.py
tests/test_registry_assets.py
README.md
c/116/图片
c/116/解释/说明.md
```

`src/minigpt/registry_data.py` 是本版新增的数据层。它保留 `REGISTRY_ARTIFACT_PATHS`、`RegisteredRun`、`discover_run_dirs()`、`summarize_registered_run()` 和 `build_run_registry()`。这个模块负责读 run 目录里的 manifest、history、dataset quality、eval suite、generation quality、benchmark scorecard、pair batch/trend、release readiness comparison 和 run notes，然后汇总成 registry 字典。

`src/minigpt/registry_render.py` 是本版新增的输出层。它负责 `write_registry_json()`、`write_registry_csv()`、`write_registry_svg()`、`render_registry_html()`、`write_registry_html()` 和 `write_registry_outputs()`。HTML 表格、stat card、leaderboard、链接、搜索排序数据属性、CSV 值格式化和 SVG 文本转义都留在这里。

`src/minigpt/registry.py` 现在是 facade。它显式从 `registry_data.py` 和 `registry_render.py` 导入旧 API，并通过 `__all__` 固定公开符号。这样旧代码继续写：

```python
from minigpt.registry import build_run_registry, write_registry_outputs
```

不会因为拆分而中断。

`tests/test_registry_split.py` 是新增测试。它直接导入 `registry_data` 和 `registry_render`，同时验证 facade 的函数身份没有漂移。

## 核心数据结构

`RegisteredRun` 仍然是 registry 的单 run 数据结构，字段包括：

- Git 与训练配置：`git_commit`、`git_dirty`、`tokenizer`、`max_iters`
- 损失与模型规模：`best_val_loss`、`last_val_loss`、`total_parameters`
- 数据治理：`data_source_kind`、`dataset_fingerprint`、`dataset_quality`
- 评估与生成质量：`eval_suite_cases`、`generation_quality_status`、`benchmark_rubric_avg_score`
- pair 和 readiness：`pair_batch_cases`、`pair_trend_reports`、`release_readiness_comparison_status`
- 证据可用性：`artifact_count`、`checkpoint_exists`、`dashboard_exists`
- 人工说明：`note`、`tags`

`build_run_registry()` 输出的 registry 字典仍然包含：

- `runs`
- `best_by_best_val_loss`
- `loss_leaderboard`
- `benchmark_rubric_leaderboard`
- `pair_delta_summary`
- `pair_delta_leaderboard`
- `release_readiness_delta_summary`
- `release_readiness_delta_leaderboard`
- `quality_counts`
- `generation_quality_counts`
- `tag_counts`

这些字段是后续 experiment card、model card、project audit、release bundle、maturity summary 和 HTML registry 继续消费的证据入口。

## 运行流程

一次 registry 构建现在可以分成两段理解：

```text
run directories
 -> registry_data.discover_run_dirs()
 -> registry_data.summarize_registered_run()
 -> registry_data.build_run_registry()
 -> registry dict
 -> registry_render.write_registry_outputs()
 -> registry.json / registry.csv / registry.svg / registry.html
```

数据层的私有 reader，例如 `_read_generation_quality()`、`_read_benchmark_scorecard()`、`_read_release_readiness_comparison()`，只负责把可能存在于不同路径的证据读成字典。它们不拼 HTML，也不关心页面布局。

渲染层的 helper，例如 `_registry_links()`、`_loss_leaderboard_html()`、`_benchmark_rubric_cell()`、`_pair_delta_leaderboard_html()` 和 `_release_readiness_delta_leaderboard_html()`，只消费 registry 字典。它们不再负责到 run 目录里重新汇总业务数据。

## 输出产物含义

`registry.json` 是最终机器可读证据，保留 run 列表、排行榜、统计计数和跨 run delta summary。

`registry.csv` 是表格证据，适合快速检查每个 run 的关键字段是否完整。

`registry.svg` 是静态视觉摘要，展示 best validation loss、artifact count、quality、eval 和 note。

`registry.html` 是交互证据，提供搜索、质量筛选、排序、保存视图、导出可见 CSV、run 链接、loss/rubric/pair/readiness leaderboard。

这些输出不是临时产物；它们是 release bundle、文档截图和后续治理模块可以引用的 registry 证据。

## 测试覆盖

`tests/test_registry.py` 继续保护旧 public API 的完整行为：run discovery、summary 字段读取、pair reports、release readiness、leaderboards、CSV/SVG/HTML 输出和 HTML escaping。

`tests/test_registry_assets.py` 继续保护 v111 抽出的 CSS/JavaScript 资产以及 `render_registry_html()` 对这些资产的集成。

`tests/test_registry_split.py` 新增三类断言：

- 直接用 `registry_data.build_run_registry()` 可以生成完整 registry 数据。
- 直接用 `registry_render.write_registry_outputs()` 可以消费数据层 registry 并写出四类输出。
- `minigpt.registry.build_run_registry` 和 `minigpt.registry_render.render_registry_html` 等 facade 导出仍然指向新实现，旧入口没有被破坏。

失败时，这些测试能拦住三类风险：拆分后数据字段丢失、输出层无法独立消费 registry 字典、旧导入入口变成悬空包装或缺失符号。

## 证据闭环

v116 的运行证据放在：

```text
c/116/图片
c/116/解释/说明.md
```

截图覆盖 registry 定向单测、compileall、全量 `unittest discover` 的最终通过、模块行数、maintenance pressure smoke、registry 输出检查、Playwright/Chrome HTML 渲染和文档索引检查。

README 更新了当前版本、版本标签、结构说明和截图索引。阶段 README 追加了 `131-v116-registry-data-render-split.md`，说明这次拆分属于项目成熟度阶段的维护收口，而不是新功能堆叠。

## 一句话总结

v116 把 registry 从“一个大文件同时做数据汇总和展示发布”推进到“数据层、渲染层、兼容入口三边界清楚”的维护状态，让 MiniGPT 的治理代码更像可以长期继续演进的工程作品。
