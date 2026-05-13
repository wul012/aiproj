# 第五十二版代码讲解：registry benchmark rubric tracking

## 本版目标、来源和边界

v51 已经给 benchmark scorecard 增加了 per-prompt rubric scoring，但它仍停留在单个 run 的报告里。v52 的目标是把这些 rubric correctness 分数带入 run registry，让多次实验可以按正确性得分排序，并标出相对最佳 run 的 regression。

本版不改变 rubric scoring 算法，不重新生成 scorecard，不训练模型，也不把 rubric 分数变成 release gate。它只读取每个 run 已有的 `benchmark-scorecard/benchmark_scorecard.json`，把关键信息汇总进 registry。

## 所在链路

```text
benchmark_scorecard.json
 -> summarize_registered_run
 -> build_run_registry
 -> benchmark_rubric_leaderboard
 -> registry CSV / SVG / HTML
```

这一层回答的问题是：多个 run 中，哪个 run 的 benchmark correctness 最好，哪个 run 相对最佳分数退化最多，弱项 prompt 是什么。

## 关键文件

- `src/minigpt/registry.py`：新增 benchmark scorecard artifact 路径、rubric 字段、leaderboard、summary、CSV 字段、HTML Rubric 列和 Rubric Leaderboard。
- `scripts/register_runs.py`：CLI 输出新增 rubric counts 和 rubric summary。
- `tests/test_registry.py`：用多 run fixture 覆盖 rubric 读取、排名、退化、CSV/HTML 输出和 scorecard 链接。
- `README.md`：记录 v52 当前能力、tag、截图、学习地图和下一步。
- `b/52/解释/说明.md`：保存本版运行截图解释和 tag 含义。

## 输入数据

registry 会优先读取：

```text
<run-dir>/benchmark-scorecard/benchmark_scorecard.json
```

也兼容：

```text
<run-dir>/benchmark_scorecard.json
```

读取的重点字段来自 scorecard summary：

- `overall_status`
- `overall_score`
- `rubric_status`
- `rubric_avg_score`
- `rubric_pass_count`
- `rubric_warn_count`
- `rubric_fail_count`
- `weakest_rubric_case`
- `weakest_rubric_score`

## Registry 新字段

每个 run 新增：

- `benchmark_scorecard_status`
- `benchmark_scorecard_score`
- `benchmark_rubric_status`
- `benchmark_rubric_avg_score`
- `benchmark_rubric_rank`
- `benchmark_rubric_delta_from_best`
- `is_best_benchmark_rubric`
- `benchmark_weakest_rubric_case`
- `benchmark_weakest_rubric_score`
- `benchmark_scorecard_html_exists`

registry 顶层新增：

- `benchmark_rubric_counts`
- `benchmark_rubric_leaderboard`
- `benchmark_rubric_summary`

## 排名和退化

`_annotate_rubric_leaderboard` 按 `benchmark_rubric_avg_score` 从高到低排序。第一名是 correctness 当前最佳 run，其余 run 的：

```text
benchmark_rubric_delta_from_best = current_score - best_score
```

如果这个 delta 为负，就表示相对最佳 run 存在 correctness regression。`benchmark_rubric_summary` 会统计 regression 数量、最佳 run、最弱 run 和最大退化 run。

## HTML 读法

`registry.html` 现在多了三处 rubric 入口：

- 顶部 stats 的 `Rubric` 卡片：看 best、weakest 和 regression count。
- Runs 表的 `Rubric` 列：看每个 run 的 status、score、rank、delta 和 weakest case。
- `Rubric Leaderboard`：按 correctness 分数查看排名。

同时 Links 里会出现 `scorecard`，可以从 registry 直接打开单个 run 的 scorecard HTML。

## 测试和证据

本版测试覆盖：

- `summarize_registered_run` 能读取 scorecard rubric summary。
- `build_run_registry` 能生成 rubric counts、leaderboard、rank、delta 和 regression summary。
- registry CSV 包含 rubric 字段。
- registry HTML 包含 Rubric 列、Rubric Leaderboard、scorecard 链接和 sort option。
- 旧的 pair delta、generation quality、loss leaderboard 功能仍然通过回归测试。

运行证据保存在 `b/52/图片`，包括全量测试、registry rubric smoke、结构检查、Playwright Chrome 截图和文档检查。

## 一句话总结

v52 把 MiniGPT 从“单 run 能解释 prompt correctness”推进到“多 run 能比较 correctness 排名和退化”的阶段。
