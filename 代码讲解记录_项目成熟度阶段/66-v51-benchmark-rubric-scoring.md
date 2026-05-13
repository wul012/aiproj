# 第五十一版代码讲解：benchmark rubric scoring

## 本版目标、来源和边界

v50 给 benchmark scorecard 增加了 task type / difficulty drilldown，能回答“哪类任务或难度拖分”。但这些分数仍主要来自输出长度、多样性、pair 一致性和字符差距。v51 的目标是补上轻量正确性层：给每个 prompt 增加 rubric-style scoring，让 scorecard 至少能判断 required terms、forbidden terms、长度和任务形态是否满足。

本版不调用外部大模型当裁判，不做人类语义评分，不改变训练流程，也不替代正式 benchmark。它是一个可复现、可解释、可测试的轻量规则层，适合 MiniGPT 学习项目先把“正确性证据结构”搭起来。

## 所在链路

```text
eval suite results
 -> case_scores
 -> rubric_scores
 -> rubric_correctness component
 -> task/difficulty drilldowns
 -> scorecard summary / CSV / HTML
```

这一层回答的问题是：某个 prompt 的输出是否至少满足显式 rubric，比如必须包含哪些关键词、不能出现哪些词、长度是否足够、结构化任务是否像结构化输出。

## 关键文件

- `src/minigpt/benchmark_scorecard.py`：新增 rubric 评分、schema v3、rubric CSV、HTML/Markdown 区块和 summary 字段。
- `scripts/build_benchmark_scorecard.py`：CLI 输出新增 `rubric_status`、`rubric_avg_score`、`weakest_rubric_case`。
- `tests/test_benchmark_scorecard.py`：用临时 run fixture 覆盖 rubric pass/warn、missing terms、forbidden terms、weakest case 和输出文件。
- `README.md`：记录 v51 当前能力、tag、截图、学习地图和下一步。
- `b/51/解释/说明.md`：保存本版运行截图解释和 tag 含义。

## 输入格式

v51 优先读取 eval suite result 里的 `rubric` 字段：

```json
{
  "name": "qa-basic",
  "task_type": "qa",
  "difficulty": "easy",
  "generated": "model training improves learning",
  "continuation": "model training improves learning",
  "rubric": {
    "must_include": ["model", "training"],
    "must_avoid": ["unrelated"],
    "min_chars": 8
  }
}
```

如果没有显式 `rubric.must_include`，代码会从 `expected_behavior` 中提取少量英文关键词作为弱 fallback。显式 rubric 更可靠，后续版本应优先把标准 benchmark prompt 都补上 rubric。

## 评分规则

每个 case 会生成五个检查：

- `has_output`：生成内容是否非空。
- `length_bounds`：字符数是否满足 `min_chars` / `max_chars`。
- `must_include`：required terms 是否出现，支持部分得分。
- `must_avoid`：forbidden terms 是否没有出现。
- `task_shape`：按 task type 做轻量形态检查，例如 structured/format/json 任务应有 JSON/list-like 符号。

每个 case 得到 `score` 和 `status`。全部 case 汇总成：

- `rubric_avg_score`
- `rubric_status`
- `rubric_pass_count`
- `rubric_warn_count`
- `rubric_fail_count`
- `weakest_rubric_case`

同时新增 `rubric_correctness` component，使 overall score 能吸收这个正确性维度。

## 输出文件

`write_benchmark_scorecard_outputs` 现在会写出：

```text
benchmark_scorecard.json
benchmark_scorecard.csv
benchmark_scorecard_drilldowns.csv
benchmark_scorecard_rubric.csv
benchmark_scorecard.md
benchmark_scorecard.html
```

`benchmark_scorecard_rubric.csv` 是 v51 新增的重点文件，包含每个 case 的 score、status、matched terms、missing terms 和 failed checks。

## HTML 读法

`benchmark_scorecard.html` 现在可以按这个顺序读：

- 顶部 stats：看 rubric status、rubric avg 和整体分。
- Benchmark Components：看 `rubric_correctness` 是否拖 overall score。
- Rubric Scores：看每个 prompt 的得分、缺失词和失败检查。
- Task/Difficulty Drilldown：看 rubric 分数如何影响任务类型和难度分组。
- Case Scores：把 eval、generation quality、rubric 和 pair 证据合在一行看。

## 测试和证据

本版测试覆盖：

- schema version 升到 3。
- 新增 `rubric_correctness` component。
- rubric 平均分、weakest case、missing terms 和 forbidden terms。
- rubric CSV 输出字段。
- Markdown/HTML 的 Rubric Scores 区块。
- drilldown row 中的 rubric score 和 rubric pass/warn/fail count。

运行证据保存在 `b/51/图片`，包括全量测试、rubric smoke、结构检查、Playwright Chrome 截图和文档检查。

## 一句话总结

v51 把 MiniGPT 从“benchmark 能解释任务分组弱项”推进到“benchmark 能记录每个 prompt 的轻量正确性证据”的阶段。
