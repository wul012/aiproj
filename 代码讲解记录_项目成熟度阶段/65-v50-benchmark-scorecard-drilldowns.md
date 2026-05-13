# 第五十版代码讲解：benchmark scorecard drilldowns

## 本版目标、来源和边界

v49 让一个 run 有了统一 benchmark scorecard，但总分仍然有一个问题：如果整体是 pass 或 warn，评审者还要自己翻 case 才知道问题集中在哪类任务。本版目标是给 scorecard 增加 task type 和 difficulty 两层 drilldown，让总分背后的弱项可以直接定位。

本版不训练模型，不修改 eval suite 原始格式，不改变 pair batch 生成流程，也不把 drilldown 纳入 release gate。它只基于 v49 已经合并好的 `case_scores` 做分组评分和导出。

## 所在链路

```text
eval suite / generation quality / pair batch
 -> benchmark scorecard
 -> task type drilldown
 -> difficulty drilldown
 -> weakest benchmark slices
```

这一层回答的问题是：当前 run 的 benchmark 短板到底是在问答、摘要、格式化输出，还是在 easy、medium、hard 这类难度切片上。

## 关键文件

- `src/minigpt/benchmark_scorecard.py`：新增 `drilldowns`、schema v2、分组评分、最弱分组、Markdown/HTML 渲染和 drilldown CSV。
- `scripts/build_benchmark_scorecard.py`：CLI 输出新增 `task_type_group_count`、`weakest_task_type`、`difficulty_group_count`、`weakest_difficulty`。
- `tests/test_benchmark_scorecard.py`：覆盖 drilldown 分组、最弱分组、输出文件、Markdown/HTML 区块和 HTML 转义。
- `README.md`：记录 v50 当前能力、tag、截图、学习地图和下一步。
- `b/50/解释/说明.md`：保存本版运行截图解释和 tag 含义。

## 输入和聚合方式

v50 沿用 v49 的输入：

```text
<run-dir>/eval_suite/eval_suite.json
<run-dir>/generation-quality/generation_quality.json
<run-dir>/pair_batch/pair_generation_batch.json
<run-dir>/pair_batch/pair_generation_batch.html
optional registry.json
```

构建时先生成 `case_scores`，每个 case 合并：

- `task_type`
- `difficulty`
- eval 字符数和 unique 字符数
- generation quality 状态和 flag 数
- pair generated equality
- pair generated char delta

然后分别按 `task_type` 和 `difficulty` 分组，得到两个 drilldown 表。

## 分组评分

每个 drilldown row 会计算：

- `coverage_score`：分组 case 数，两个及以上为满分。
- `generation_quality_score`：pass 计 1 分，warn 计 0.5 分，fail 计 0 分。
- `pair_consistency_score`：pair generated 完全一致的比例。
- `pair_delta_stability_score`：按平均生成字符差距扣分。
- `score`：上述四项的加权分。
- `status`：`pass`、`warn` 或 `fail`。

同时输出 `weakest_task_type` 和 `weakest_difficulty`，让 review 入口可以直接看到优先修哪里。

## 输出文件

`write_benchmark_scorecard_outputs` 现在会写出：

```text
benchmark_scorecard.json
benchmark_scorecard.csv
benchmark_scorecard_drilldowns.csv
benchmark_scorecard.md
benchmark_scorecard.html
```

JSON 保存完整结构；组件 CSV 保持 v49 的总分组件；drilldown CSV 专门给任务/难度分组；Markdown 和 HTML 增加 Task Type Drilldown 与 Difficulty Drilldown 两个区块。

## HTML 读法

`benchmark_scorecard.html` 的新读法是：

- 先看顶部 stats 的 group count。
- 再看 Benchmark Components 判断总分来自哪些大组件。
- 然后看 Task Type Drilldown，确认哪类任务分数最低。
- 再看 Difficulty Drilldown，确认是否 hard 或 medium 集中拖分。
- 最后看 Case Scores 定位具体 case。

这样评审者不用从 case 表里手动归纳弱项，scorecard 自己给出任务切片解释。

## 测试和证据

本版测试覆盖：

- schema version 从 1 升到 2。
- task type 分组数量和 difficulty 分组数量。
- `weakest_task_type` 与 `weakest_difficulty` 的计算。
- drilldown CSV 字段和输出路径。
- Markdown/HTML 中的 drilldown 区块。
- 标题 HTML 转义仍然有效。

运行证据保存在 `b/50/图片`，包括全量测试、drilldown smoke、结构检查、Playwright Chrome 截图和文档检查。

## 一句话总结

v50 把 MiniGPT 从“能给 run 一个 benchmark 总分”推进到“能解释 benchmark 总分背后的任务类型和难度短板”的阶段。
