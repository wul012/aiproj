# 第六十四版代码讲解：registry release readiness tracking

## 本版目标、来源和边界

v64 的目标是把 v63 的 release readiness comparison 结果接入 run registry。v63 已经能读取多个 `release_readiness.json` 并生成 `release_readiness_comparison.json`，但这个比较结果仍是一个独立报告；registry 只能看到训练 run 的 loss、dataset quality、generation quality、rubric 和 pair delta，不能把发布质量变化放进同一个实验索引。

所以本版新增 registry-level release readiness comparison tracking：当 run 目录下存在 `release-readiness-comparison/release_readiness_comparison.json` 时，registry 会读取它，抽取趋势状态、summary counts、delta 明细，并在 JSON、CSV、HTML 中展示。

本版不做三件事：

- 不重新计算 release readiness comparison，仍消费 v63 的产物。
- 不改变 release gate、project audit 或 readiness dashboard 的规则。
- 不把趋势写入 maturity summary，这一步留给后续版本。

## 本版来自哪条路线

这一版属于项目成熟度阶段的 registry 汇总路线：

```text
v62 release readiness dashboard
 -> v63 release readiness comparison
 -> v64 registry release readiness tracking
```

v62 解决单版发布就绪总览，v63 解决跨版本比较，v64 解决“比较结果如何进入长期 run 索引”。

## 关键新增和修改文件

- `src/minigpt/registry.py`
  - 新增 release readiness comparison artifact 路径。
  - 扩展 `RegisteredRun`，加入 release readiness comparison 状态、baseline status、ready/blocked/improved/regressed/panel delta 计数和 HTML 是否存在。
  - 新增 `_read_release_readiness_comparison()`、`_collect_release_readiness_delta_rows()`、`_release_readiness_delta_summary()` 和 `_release_readiness_delta_leaderboard()`。
  - HTML 中新增 Release Readiness 列、Release Readiness Deltas 面板、排序字段和 artifact 链接。
- `scripts/register_runs.py`
  - CLI 输出新增 `release_readiness_comparison_counts` 和 `release_readiness_delta_summary`，让 smoke 和自动化脚本能直接看到 registry 是否识别发布质量趋势。
- `tests/test_registry.py`
  - fixture 支持生成 `release-readiness-comparison/release_readiness_comparison.json`。
  - 新增 summary、registry counts、delta leaderboard、CSV 字段、HTML 面板和交互排序断言。
- `README.md`
  - 更新到 v64，加入能力说明、tag、截图索引、讲解索引、学习路线和下一步方向。
- `b/64/解释/说明.md`
  - 说明本版截图如何证明 registry release readiness tracking 的闭环。

## 输入格式和目录约定

registry 默认从 run 目录读取：

```text
release-readiness-comparison/release_readiness_comparison.json
release-readiness-comparison/release_readiness_comparison.html
```

同时保留根目录兼容：

```text
release_readiness_comparison.json
release_readiness_comparison.html
```

主输入仍是 v63 的 comparison JSON，关键字段来自：

```text
summary.readiness_count
summary.baseline_status
summary.ready_count
summary.blocked_count
summary.improved_count
summary.regressed_count
summary.changed_panel_delta_count
deltas[].delta_status
deltas[].status_delta
deltas[].changed_panels
deltas[].audit_score_delta
deltas[].missing_artifact_delta
deltas[].explanation
```

## 核心数据结构

`RegisteredRun` 新增字段：

```text
release_readiness_comparison_status
release_readiness_report_count
release_readiness_baseline_status
release_readiness_ready_count
release_readiness_blocked_count
release_readiness_improved_count
release_readiness_regressed_count
release_readiness_changed_panel_delta_count
release_readiness_html_exists
```

`release_readiness_comparison_status` 是 registry 层的摘要状态，不替代 v63 的 delta：

- 有 `regressed_count` 时标为 `regressed`。
- 有 `improved_count` 时标为 `improved`。
- 总体状态未变但 panel 有变化时标为 `panel-changed`。
- 没有改善或退化但存在 blocked release 时标为 `blocked`。
- 其他有 comparison 但无变化时标为 `stable`。
- 找不到 comparison 时为 `missing`。

registry 顶层新增：

```text
release_readiness_comparison_counts
release_readiness_delta_summary
release_readiness_delta_leaderboard
```

`release_readiness_delta_summary` 记录 delta 总数、涉及 run 数、regressed/improved/panel-changed/same 数量、panel 变化数量和最大 readiness status delta。

`release_readiness_delta_leaderboard` 把 delta 明细按风险排序：regressed 优先，其次 improved、panel-changed、same；同类里按 status delta 绝对值和 panel 变化数量排序。

## 运行流程

registry 构建流程变为：

```text
build_run_registry()
 -> summarize_registered_run()
    -> _read_release_readiness_comparison()
    -> _release_readiness_comparison_status()
 -> _collect_release_readiness_delta_rows()
 -> _release_readiness_delta_summary()
 -> _release_readiness_delta_leaderboard()
 -> render/write JSON, CSV, SVG, HTML
```

CSV 新增 release readiness 字段，便于表格筛选。HTML 新增：

- Release Readiness 运行列表列。
- `readiness cmp` artifact 链接。
- Release Readiness Deltas 面板。
- Release Readiness 排序选项。
- 顶部 Release readiness 和 Readiness deltas 统计卡。

## 输出产物的作用

`registry.json` 是最终结构化索引，后续 maturity summary 可以直接读取 `release_readiness_delta_summary`。

`registry.csv` 是人工表格检查入口，新增字段能快速筛选出 regressed 或 panel-changed 的 run。

`registry.html` 是浏览器审阅入口，Release Readiness Deltas 面板把 release 退化和改善放在 loss leaderboard、rubric leaderboard、pair delta leaders 旁边。

`registry.svg` 本版没有强行扩展。SVG 仍承担轻量总览作用，避免把发布治理信息塞进已经很紧的静态图里。

## 测试覆盖了什么

`tests/test_registry.py` 覆盖：

- 单个 run 能读取 release readiness comparison summary，识别 `improved` 状态和 HTML artifact。
- 多 run registry 能统计 `release_readiness_comparison_counts`。
- delta summary 能统计 improved/regressed 数量。
- delta leaderboard 会把 regressed run 排在前面，优先暴露发布质量风险。
- CSV 包含 `release_readiness_comparison_status`。
- HTML 包含 Release Readiness 列、Release Readiness Deltas 面板、`readiness cmp` 链接、顶部统计卡和排序选项。

这些断言保护的是 registry 层“读得到、算得出、导得出、看得见”四件事。

## README、截图和归档的证明作用

README 证明 v64 已进入项目总能力列表、tag 列表、截图索引、讲解索引和下一步路线。

`b/64/图片` 保存真实运行证据：单测、CLI smoke、结构检查、Playwright 浏览器渲染和文档检查。

`b/64/解释/说明.md` 说明每张截图的证明范围。

本篇讲解负责说明 registry 为什么只消费 v63 产物，而不重复计算 release readiness。

## 和后续版本的关系

v64 已经让 registry 持有 release readiness trend context。下一步可以让 project maturity summary 读取 registry 的 `release_readiness_delta_summary`，把发布质量历史纳入成熟度评审。

## 一句话总结

v64 把 MiniGPT 的发布质量趋势从独立 comparison report 接入 run registry，让 release readiness 的改善、退化和 panel 变化能和实验质量证据一起长期索引。
