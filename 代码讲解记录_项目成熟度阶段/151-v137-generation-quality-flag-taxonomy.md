# v137 generation quality flag taxonomy 代码讲解

## 本版目标

v137 的目标是把 generation quality 从“只给出 pass/warn/fail 和 case 级 flags”推进到“能汇总问题类型、严重级别和最差样本”的诊断层。

本版明确不做三件事：

- 不继续做 artifact split，v135-v136 的拆分轮次已经收口。
- 不宣称模型质量变强；本版只让已有生成样本的弱项证据更具体。
- 不改变 generation quality 的输入文件、输出文件名和 CLI 基本调用方式。

## 前置路线

前置能力来自这条链路：

```text
eval suite / sample lab outputs
 -> generation_quality.py 计算 continuation metrics 和 flags
 -> generation_quality_artifacts.py 写出 JSON/CSV/Markdown/SVG/HTML
 -> registry/model card/project audit 等后续证据链消费质量状态
```

v136 已经把输出写入层拆到 `generation_quality_artifacts.py`。因此 v137 不再拆新模块，而是在已经清楚的边界内补诊断语义：核心计算层新增 `flag_summary`，artifact 层只负责把同一份摘要渲染出来。

## 关键文件

- `src/minigpt/generation_quality.py`: 新增 `_build_flag_summary()`，在 `summary` 里加入 `flag_summary`，并让 recommendations 提醒 dominant flag。
- `src/minigpt/generation_quality_artifacts.py`: 在 Markdown 和 HTML 里新增 `Flag Breakdown`，展示 total flags、severity counts、flag id counts 和 worst cases。
- `scripts/analyze_generation_quality.py`: CLI 输出新增 `flags=` 和 `dominant_flag=`，方便终端 smoke 直接证明 taxonomy 生效。
- `tests/test_generation_quality.py`: 增强重复样本、空 continuation、Markdown/HTML 输出的断言，锁住 taxonomy 行为。
- `README.md`: 更新当前版本、能力矩阵、v137 focus、tag 列表和 `c/137` 截图说明。
- `c/137/解释/说明.md`: 保存本版运行截图的解释和证据边界。

## 核心数据结构

`build_generation_quality_report()` 仍然返回同一个 report dict，新增字段位于：

```text
summary.flag_summary
```

结构如下：

```json
{
  "total_flags": 4,
  "flag_id_counts": {
    "empty_continuation": 1,
    "high_ngram_repetition": 1,
    "long_repeat_run": 1,
    "low_diversity": 1
  },
  "flag_level_counts": {
    "fail": 1,
    "warn": 3
  },
  "worst_cases": [
    {
      "name": "empty",
      "status": "fail",
      "flag_count": 1,
      "flag_ids": ["empty_continuation"]
    }
  ]
}
```

字段语义：

- `total_flags`: 所有 case 上 flag 的总数，不等同于 warn/fail case 数，因为一个 case 可以同时触发多个问题。
- `flag_id_counts`: 按问题类型统计，例如 `low_diversity`、`long_repeat_run`、`high_ngram_repetition`、`empty_continuation`。
- `flag_level_counts`: 按严重级别统计，当前主要是 `warn` 和 `fail`。
- `worst_cases`: 只保留最多 5 个最值得优先看的样本，排序规则是 fail 优先、flag 数多优先、名称稳定排序。

这份摘要是最终质量报告的一部分，可以被后续 registry、scorecard、model card 或 release gate 继续消费；Markdown/HTML 里的 `Flag Breakdown` 只是它的可读展示。

## 核心函数

`_build_flag_summary(cases)` 遍历每个 case 的 `flags`：

```text
case.flags
 -> 累加 flag_id_counts
 -> 累加 flag_level_counts
 -> 收集带 flag 的 case
 -> 按 severity 和 flag_count 排序
 -> 截断为 worst_cases 前 5 个
```

这个函数不重新判断文本质量，也不改变 `_flags()` 的阈值逻辑。它只汇总已经生成的 case-level flags，因此不会改变 pass/warn/fail 的原始判定。

`_recommendations(summary, cases)` 新增 dominant flag 提醒：

```text
flag_summary.flag_id_counts
 -> 选择出现次数最多的问题类型
 -> 输出 Prioritize dominant generation flag: <flag_id>
```

这样报告不再只说“有 warn/fail”，还会提示当前最该先修的是哪类生成问题。

## Artifact 展示

`generation_quality_artifacts.py` 新增两段展示：

- `_flag_summary_markdown()`: 在 Markdown 的 Summary 后插入 `## Flag Breakdown`。
- `_flag_summary_section()`: 在 HTML stats 后插入 `Flag Breakdown` panel。

这两个函数只读取 `summary.flag_summary`，不重新计算任何指标。也就是说，JSON 是机器可读证据，Markdown/HTML 是同一证据的可读视图；CSV 和 SVG 仍保留 case-level 视角，不在本版扩大变更。

## CLI 输出

`scripts/analyze_generation_quality.py` 现在会打印：

```text
flags=4
dominant_flag=low_diversity:1
```

当多个 flag 计数相同，选择规则按数量和 flag id 稳定排序。这个输出主要用于 smoke 截图和快速终端判断，不替代 JSON 里的完整 `flag_summary`。

## 测试覆盖

`tests/test_generation_quality.py` 的关键断言包括：

- 正常样本仍是 `pass`，重复样本仍是 `warn`，空 continuation 仍是 `fail`。
- 重复样本会同时触发 `low_diversity`、`long_repeat_run`、`high_ngram_repetition` 三类 warn flag。
- 空 continuation 会触发 `empty_continuation` fail flag。
- `flag_summary.flag_id_counts` 和 `flag_summary.flag_level_counts` 与 fixture 完全一致。
- `worst_cases[0]` 是 fail case，确保最差样本排序优先级稳定。
- Markdown 和 HTML 都包含 `Flag Breakdown`，证明 artifact 层能展示新增摘要。

这些测试保护的是“诊断证据是否真实来自 case flags”，不是只保护页面是否能写出来。

## 证据边界

`c/137` 的截图证明：

- 代码能编译，generation quality 定向测试和全量 unittest 通过。
- CLI smoke 能生成含 `flag_summary` 的 JSON/Markdown/HTML 等产物。
- Playwright/Chrome 能打开含 `Flag Breakdown` 的 HTML 报告。
- README、代码讲解索引、`c/137` 归档和 source encoding 检查完整。

它不证明 MiniGPT 生成能力提升。真正的模型质量提升还需要更大数据、更强 checkpoint、固定 benchmark 对比和多轮训练结果。

## 一句话总结

v137 把 generation quality 从“粗粒度状态报告”推进到“可追踪问题类型、严重级别和最差样本的弱项诊断”，让后续真实评估和训练改进有更具体的抓手。
