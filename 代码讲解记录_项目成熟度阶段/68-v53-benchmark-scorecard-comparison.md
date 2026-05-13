# 第五十三版代码讲解：benchmark scorecard comparison

## 本版目标、来源和边界

v49 已经生成 run 级 benchmark scorecard，v50 增加 task type / difficulty drilldown，v51 增加 per-prompt rubric scoring，v52 又把 rubric 分数带入 registry 做多 run 排名。v53 的目标是把这条线收口：当多个 run 的 scorecard 分数不同，不只告诉你谁高谁低，还解释变化来自哪个 run、哪个 prompt、哪个任务类型和哪个难度分组。

本版不重新设计评分规则，不训练模型，不修改 registry 排名逻辑，也不把 scorecard comparison 接入 release gate。它只读取已有 `benchmark_scorecard.json`，做 baseline 对比和导出。

## 所在链路

```text
benchmark_scorecard.json / run directory
 -> load_benchmark_scorecard
 -> build_benchmark_scorecard_comparison
 -> baseline_deltas / case_deltas / task_type_deltas / difficulty_deltas
 -> JSON / CSV / case delta CSV / Markdown / HTML
```

这一层回答的问题是：如果 registry 看到某个 run 的 rubric 分数退化，退化具体落在哪个 case，新增了哪些 missing terms 或 failed checks，是否集中在某类任务或某个难度。

## 关键文件

- `src/minigpt/benchmark_scorecard_comparison.py`：核心模块，负责读取 scorecard、选择 baseline、计算 run/case/group delta，并渲染多种输出。
- `scripts/compare_benchmark_scorecards.py`：命令行入口，支持 scorecard JSON 路径或 run 目录，支持 `--name`、`--baseline` 和 `--out-dir`。
- `tests/test_benchmark_scorecard_comparison.py`：测试多 scorecard fixture，覆盖读取、delta、输出和 HTML 转义。
- `README.md`：把当前版本、能力清单、tag、截图说明和后续路线更新到 v53。
- `b/53/解释/说明.md`：记录本版截图含义和 tag 含义。

## 输入数据

`load_benchmark_scorecard` 可以读取两种输入：

```text
<run-dir>/benchmark-scorecard/benchmark_scorecard.json
<path>/benchmark_scorecard.json
```

它会把真实读取路径写入 `_source_path`。这个字段不是业务评分的一部分，而是为了后续报告能说明证据来源。

核心输入字段来自 v49-v52 已经形成的 scorecard：

- `summary.overall_score`
- `summary.rubric_avg_score`
- `summary.rubric_pass_count`
- `summary.rubric_warn_count`
- `summary.rubric_fail_count`
- `summary.weakest_rubric_case`
- `rubric_scores.cases`
- `case_scores`
- `drilldowns.task_type`
- `drilldowns.difficulty`

## 核心数据结构

`runs` 是每个 scorecard 的摘要行，字段包括：

- `name`：显示名，来自 `--name`，否则从 run 目录或文件名推断。
- `source_path`：scorecard JSON 真实路径。
- `run_dir`：原 scorecard 记录的 run 目录。
- `overall_score` / `overall_status`：scorecard 总分和状态。
- `rubric_avg_score` / `rubric_status`：per-prompt rubric 平均分和状态。
- `weakest_rubric_case` / `weakest_rubric_score`：该 run 的最弱 prompt。

`baseline_deltas` 是 run 级变化：

- `overall_score_delta`
- `rubric_avg_score_delta`
- `rubric_pass_count_delta`
- `rubric_warn_count_delta`
- `rubric_fail_count_delta`
- `weakest_case_changed`
- `overall_relation`
- `rubric_relation`
- `explanation`

这里的 relation 使用 `improved`、`regressed`、`tied`、`baseline`、`missing`。scorecard 分数越高越好，所以 delta 大于 0 是 improved，小于 0 是 regressed。

`case_deltas` 是 prompt 级变化：

- `case`
- `run_name`
- `baseline_rubric_score`
- `rubric_score`
- `rubric_score_delta`
- `added_missing_terms`
- `removed_missing_terms`
- `added_failed_checks`
- `removed_failed_checks`
- `explanation`

这一层是 v53 最关键的解释能力。它把“rubric 平均分下降”拆成“哪个 case 多缺了哪些词、哪些检查从通过变成失败”。

`task_type_deltas` 和 `difficulty_deltas` 来自 scorecard drilldown：

- `group_by`
- `key`
- `score_delta`
- `rubric_score_delta`
- `case_count`
- `relation`
- `explanation`

这两个分组不是最终模型能力证明，而是定位弱项的索引：它们告诉你退化是否集中在问答、摘要、格式化输出，或者 easy/medium/hard 某个难度。

## 运行流程

`build_benchmark_scorecard_comparison` 的流程比较直接：

1. 读取所有 scorecard。
2. 根据 `--name` 或路径生成显示名。
3. 生成每个 scorecard 的 run 摘要。
4. 选择 baseline，默认第一个，也可以用名称、路径、run_dir 或 1-based index。
5. 计算 run-level delta。
6. 合并 baseline 与候选 run 的 case map，计算 case-level delta。
7. 读取 task type / difficulty drilldown，计算分组 delta。
8. 生成 summary、best_by_overall_score、best_by_rubric_avg_score 和 recommendations。

## 输出产物

`write_benchmark_scorecard_comparison_outputs` 会生成：

```text
benchmark_scorecard_comparison.json
benchmark_scorecard_comparison.csv
benchmark_scorecard_case_deltas.csv
benchmark_scorecard_comparison.md
benchmark_scorecard_comparison.html
```

JSON 是最完整的结构化证据，供后续脚本消费。CSV 是 run 级对比，适合表格过滤。case delta CSV 是 prompt 级证据，适合定位退化。Markdown 是可读审阅文本。HTML 是浏览器展示和截图证据。

这些产物都是最终证据，不是临时文件。临时 fixture、测试输出和截图中间文件不会进入版本目录。

## CLI 用法

示例：

```powershell
python scripts/compare_benchmark_scorecards.py `
  runs/base `
  runs/candidate `
  --name base `
  --name candidate `
  --baseline base `
  --out-dir output/benchmark-scorecard-comparison
```

输入可以是 run 目录，也可以是具体 `benchmark_scorecard.json`。

## 测试和证据

`tests/test_benchmark_scorecard_comparison.py` 覆盖了几类风险：

- run 目录能自动定位 `benchmark-scorecard/benchmark_scorecard.json`。
- baseline 名称能正确选择。
- 更强 run 会被识别为 rubric improvement。
- 退化 run 会产生 `regressed` relation。
- case 级新增 missing terms 和 failed checks 会进入 `case_deltas`。
- task type / difficulty 的分组退化能被识别。
- JSON、CSV、case delta CSV、Markdown、HTML 都会写出。
- HTML 对 `<base>` 这样的文本做转义，避免报告被注入破坏。

运行证据保存在 `b/53/图片`。其中 Playwright 截图证明 HTML 不是只写了文件，而是能被真实浏览器打开。

## 和 v52 的关系

v52 的 registry 告诉你哪个 run 的 rubric 分数最高、哪个 run 相对最佳退化最多。v53 则给出下一跳解释：当你从 registry 发现退化后，可以把对应 scorecard 拿来对比，看到具体的 prompt、missing terms、failed checks 和分组变化。

这就是一次收口，而不是继续拆 `links/trends/dashboard`：它把前四版形成的 scorecard 证据链变成可追因的比较报告。

## 一句话总结

v53 把 MiniGPT 从“多 run 可以排名 correctness”推进到“多 run 可以解释 correctness 为什么变化”的阶段。
