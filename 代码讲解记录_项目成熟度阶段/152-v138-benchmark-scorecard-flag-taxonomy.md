# v138 benchmark scorecard flag taxonomy 代码讲解

## 本版目标

v138 的目标是把 v137 新增的 generation-quality `flag_summary` 接入 run 级 benchmark scorecard。这样每次看 benchmark 总分时，不只知道 generation quality 是 pass/warn/fail，还能看到本轮生成最常见的问题类型、总 flag 数、最差生成样本，以及这些问题对 generation-quality component 的扣分影响。

本版明确不做：

- 不新增独立报告类型。
- 不继续做 artifact split。
- 不改变 generation quality 自己的 schema 生成方式。
- 不宣称模型能力提升，只让已有质量诊断能进入总评分入口。

## 前置路线

v137 已经完成：

```text
generation_quality.summary.flag_summary
 -> total_flags
 -> flag_id_counts
 -> flag_level_counts
 -> worst_cases
```

但如果这些字段只停留在 `generation_quality.json`，benchmark scorecard 仍然只能看到粗粒度 pass/warn/fail。因此 v138 把这份诊断向上接入：

```text
generation_quality.json
 -> benchmark_scorecard.py
 -> scorecard.summary
 -> scorecard.components[generation_quality].metrics
 -> Markdown / HTML / CLI / c/138 evidence
```

## 关键文件

- `src/minigpt/benchmark_scorecard.py`: 读取 `summary.flag_summary`，计算 `total_flags`、`dominant_flag`、`worst_generation_case` 和 `flag_penalty`。
- `src/minigpt/benchmark_scorecard_artifacts.py`: 在 Markdown summary 和 HTML stats 中展示 generation flag 字段。
- `scripts/build_benchmark_scorecard.py`: CLI 输出新增 `generation_quality_total_flags`、`generation_quality_dominant_flag` 和 `generation_quality_worst_case`。
- `tests/test_benchmark_scorecard.py`: 用带 `flag_summary` 的 fixture 锁住 component 分数、扣分、summary 字段和 recommendations。
- `tests/test_benchmark_scorecard_artifacts.py`: 确认 Markdown/HTML 能展示 dominant flag。
- `README.md`: 更新当前版本、能力矩阵、v138 focus、tag 和截图说明。
- `c/138/解释/说明.md`: 记录本版运行证据和边界。

## 核心数据流

`_generation_quality_component(report)` 是本版核心入口。它读取：

```text
report.summary.case_count
report.summary.pass_count
report.summary.warn_count
report.summary.fail_count
report.summary.flag_summary.total_flags
report.summary.flag_summary.flag_id_counts
report.summary.flag_summary.worst_cases
```

然后构造 component：

```json
{
  "key": "generation_quality",
  "score": 87.0,
  "metrics": {
    "raw_score": 90.0,
    "flag_penalty": 3.0,
    "total_flags": 3,
    "dominant_flag": "low_diversity",
    "worst_generation_case": "fact-check"
  }
}
```

`raw_score` 仍沿用旧逻辑：

```text
(pass_count + warn_count * 0.5) / case_count * 100
```

`flag_penalty` 是新增的轻量惩罚：

```text
min(20, total_flags / case_count * 5)
```

最终 score：

```text
max(0, raw_score - flag_penalty)
```

这个惩罚的意义是区分两种情况：

```text
1 个 warn case 只触发 1 个 flag
1 个 warn case 同时触发 3 个 flag
```

二者过去都会被看成同一个 warn，现在后者会在 run 级 scorecard 上留下更明显的弱项信号。

## dominant flag

`_dominant_flag(flag_id_counts)` 会从 `flag_id_counts` 中选出现次数最多的问题类型。若次数相同，用 flag id 做稳定排序，保证结果可复现。

这个字段进入两个位置：

- `summary.generation_quality_dominant_flag`
- `components[].metrics.dominant_flag`

recommendations 也会提示：

```text
Prioritize generation-quality flag `low_diversity` before comparing this run as improved.
```

这能让 benchmark scorecard 从“总分入口”变成“下一步修哪里”的入口。

## worst generation case

v137 的 `worst_cases` 已经按 fail 优先、flag 数多优先排序。v138 不重新排序，只读取第一个：

```text
summary.generation_quality_worst_case
summary.generation_quality_worst_case_status
```

这样 benchmark scorecard 能直接指向最该打开看的生成样本，而不需要用户再去 raw generation quality JSON 里翻。

## Artifact 展示

`benchmark_scorecard_artifacts.py` 做两处展示增强：

- Markdown Summary 增加 `Generation flags`、`Dominant generation flag`、`Worst generation case`。
- HTML stats 增加 `Gen flags` 和 `Dominant flag`。

这些展示只消费 scorecard dict，不读取原始 generation quality 文件；因此 artifact 层仍保持只渲染、不计算。

## CLI 输出

`scripts/build_benchmark_scorecard.py` 新增三行：

```text
generation_quality_total_flags=3
generation_quality_dominant_flag=low_diversity
generation_quality_worst_case=fact-check
```

这让终端 smoke 和截图能直接证明 taxonomy 已经进入 scorecard，而不必只靠 JSON 结构检查。

## 测试覆盖

`tests/test_benchmark_scorecard.py` 构造了带 `flag_summary` 的 generation quality fixture，并断言：

- `summary.generation_quality_total_flags == 3`
- `summary.generation_quality_dominant_flag == "low_diversity"`
- `summary.generation_quality_worst_case == "fact-check"`
- generation-quality component 的 `raw_score == 90.0`
- `flag_penalty == 3.0`
- 最终 score 是 `87.0`
- recommendations 包含 dominant flag 提醒

`tests/test_benchmark_scorecard_artifacts.py` 继续保护 facade 和 artifact 输出，同时确认 Markdown/HTML 出现 dominant flag。

## 证据边界

`c/138` 证明的是：generation quality 的弱项诊断已经能进入 run 级 benchmark scorecard，并影响 scorecard 的 generation-quality component。

它不证明模型输出已经改善。真正的能力提升仍然要靠真实 checkpoint、固定 prompt suite、多 run scorecard comparison、训练记录和人工/自动评估共同支撑。

## 一句话总结

v138 把 v137 的生成质量问题分类从单独报告推进到 benchmark 总评分入口，让 MiniGPT 的 run 级评估能同时看见分数、问题类型、最差样本和下一步修复方向。
