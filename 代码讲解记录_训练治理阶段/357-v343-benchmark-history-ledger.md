# 第一百三十七篇代码讲解：第343版 benchmark history ledger

本版目标，是把已有的 benchmark scorecard comparison 和 benchmark scorecard decision 两条证据链收束成一份可复用的历史账本。

它不做新的模型训练，不新增评测任务，也不把 tiny smoke 提升成模型质量证明。它解决的是“同一条 benchmark 改进链路被分散在 comparison、decision、CLI 日志和 Markdown 报告里，复盘时需要到处找”的问题。

本版来自前置能力链：

```text
v317 tiny scorecard comparison smoke
v318 tiny scorecard decision smoke
v322-v342 tiny threshold / remediation / CI hygiene / plan digest gate chain
```

所以 v343 只做一件事：把 comparison + decision 结果装进 benchmark history ledger，供后续版本按历史序列查看，而不是只看单次结果。

## 本版新增文件

### 1. `src/minigpt/benchmark_history.py`

这是核心组装层。

它负责读取两类输入：

```text
benchmark_scorecard_comparison.json
benchmark_scorecard_decision.json
```

然后输出一份统一的 history report：

```json
{
  "schema_version": 1,
  "title": "MiniGPT benchmark history",
  "generated_at": "...",
  "evidence_kind": "real-benchmark",
  "summary": {...},
  "entries": [...],
  "recommendations": [...]
}
```

### 2. `src/minigpt/benchmark_history_artifacts.py`

这是输出层。

它把同一份 history report 写成四种产物：

```text
benchmark_history.json
benchmark_history.csv
benchmark_history.md
benchmark_history.html
```

这四个产物都是最终证据，不是中间缓存。JSON 是机器读，CSV 是表格批量读，Markdown 方便讲解和归档，HTML 方便 Playwright/Chrome 预览。

### 3. `scripts/build_benchmark_history.py`

这是命令行入口。

它接收一个或多个 comparison 路径，以及可选的 decision 路径，生成对应 history 输出。

## 核心数据结构

### history report

每条 entry 都是一个比较单元，主要字段是：

```text
baseline_name
candidate_name
decision_status
promotion_readiness
overall_score_delta
rubric_avg_score_delta
case_regression_count
case_improvement_count
generation_quality_total_flags_delta
generation_quality_flag_relation
eval_suite_comparison_status
boundary
```

这些字段的语义很直接：

- `baseline_name` / `candidate_name` 说明这一条历史对比的是谁。
- `decision_status` 说明 decision 侧最终给出的结果。
- `promotion_readiness` 说明这条链路是否已经可以作为可推进候选。
- `*_delta` 说明 scorecard 比较里的实际变化。
- `case_regression_count` / `case_improvement_count` 说明案例层面的反向证据。
- `generation_quality_*` 说明质量旗标变化是否向好。
- `boundary` 说明这条证据是 tiny-smoke plumbing、real-benchmark candidate，还是 eval-suite 未达比较准备状态。

## 输入输出链路

输入不是原始训练日志，而是已有的比较和决策 JSON。

这很重要，因为本版的角色不是重算模型，而是消费现成证据：

```text
comparison -> decision -> history ledger
```

这样做的好处是：

- comparison 负责“差异是什么”
- decision 负责“该怎么处理”
- history 负责“这类结果如何连续回看”

## 测试覆盖

`tests/test_benchmark_history.py` 覆盖了四条关键链路：

1. promote 场景能正确生成 history entry
2. review / tiny-smoke 场景会保留边界和推荐语
3. JSON / CSV / Markdown / HTML 输出能正确落盘
4. CLI 入口可以直接从 comparison + decision 路径生成最终证据

测试里检查的不是“有文件就算过”，而是：

- `promotion_readiness` 是否正确
- `boundary` 是否正确
- `model_quality_claim` 是否区分 real-benchmark 和 tiny-smoke
- 输出文件是否真的包含历史账本字段

## 本版边界

本版明确不做：

- 不新增训练逻辑
- 不改模型结构
- 不替换 tiny smoke 的定位
- 不把 history ledger 当成生产级 benchmark 套件

它只是在 governance 层补一条“历史串联”能力。

## 运行证据

本版会在 `d/343/图片/` 保存：

- benchmark history CLI 输出截图
- unit test 输出截图
- 结构检查截图

解释文件放在：

```text
d/343/解释/说明.md
```

那里会说明每张截图证明什么，以及 `v343.0.0` tag 的含义。

## 一句话总结

v343 把 benchmark comparison 和 decision 从“单次结果”提升成“可连续回看的历史账本”，让评测改进开始具备版本化证据链。
