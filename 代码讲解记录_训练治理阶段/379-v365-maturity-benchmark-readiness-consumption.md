# 379-v365 maturity benchmark readiness consumption

## 本版目标和边界

v364 已经让 `benchmark_history.py` 生成 `readiness_requirement`，但这个门禁只停留在 benchmark history 自身。v365 的目标是把这份门禁接入成熟度叙事，让 `maturity_narrative` 能看见 readiness requirement 的 pass/fail、exit code 和失败原因，并在失败时把组合 portfolio 降为 `review`。

本版不新增治理链，不扩展新的 release gate，也不声称模型质量提升。它只把已有 benchmark history 维度里的门禁字段向 maturity narrative 传播一层。

## 关键文件

- `src/minigpt/maturity_narrative_summary.py`
  - 在 `_benchmark_history_summary()` 中读取 `readiness_requirement`。
  - 聚合 `benchmark_history_readiness_requirement_failed_count`、`benchmark_history_readiness_requirement_exit_code_max` 和失败原因列表。
  - 在 `_portfolio_status()` 中把 readiness requirement failure 纳入 review 条件。
  - 在 recommendations 中优先提示修复 benchmark history readiness requirement。

- `src/minigpt/maturity_narrative_sections.py`
  - `Benchmark History` section 的状态现在会把 readiness requirement failure 视为 `fail`。
  - claim 增加 readiness requirement failure 数、最大 exit code 和失败原因，方便人工阅读。

- `src/minigpt/maturity_narrative_artifacts.py`
  - Markdown summary 增加 readiness failure、readiness exit、readiness reasons。
  - HTML stats 增加 `History readiness failures` 和 `History readiness exit`。

- `scripts/build_maturity_narrative.py`
  - stdout 增加 readiness requirement 相关字段，便于 CI 或命令行 smoke 直接读取。

- `tests/test_maturity_narrative.py`
  - ready portfolio fixture 增加 pass requirement，确认旧路径保持 ready。
  - 新增 failure 用例：scorecard/decision 本身可推进，但 history requirement 因 `insufficient_ready_entries` 失败时，portfolio 变为 `review`。

## 核心数据结构

输入来自 benchmark history JSON：

```json
{
  "readiness_requirement": {
    "status": "fail",
    "decision": "stop",
    "exit_code": 1,
    "min_ready_entries": 2,
    "ready_count": 1,
    "failed_reasons": ["insufficient_ready_entries"]
  }
}
```

成熟度 summary 输出新增字段：

```json
{
  "benchmark_history_readiness_requirement_failed_count": 1,
  "benchmark_history_readiness_requirement_exit_code_max": 1,
  "benchmark_history_readiness_requirement_failed_reasons": ["insufficient_ready_entries"]
}
```

这些字段的作用是让 maturity narrative 不只知道“历史里有 ready 条目”，还知道“这批历史是否满足本次要求的 ready 条目数量、真实 benchmark 约束和 regression 边界”。

## 运行流程

1. `build_maturity_narrative()` 读取 maturity、registry、request history、scorecard、decision、benchmark history 和 dataset card。
2. `build_maturity_narrative_summary()` 把每个 benchmark history 转成 summary row。
3. `_benchmark_history_summary()` 提取 `readiness_requirement`。
4. 聚合层计算失败数量、最大 exit code 和失败原因。
5. `_portfolio_status()` 如果发现 readiness requirement failure，就把整体状态设为 `review`。
6. section、Markdown、HTML 和 CLI stdout 输出相同字段，保证人读和机器读一致。

## 测试覆盖

- `test_build_maturity_narrative_ready_portfolio` 验证 pass requirement 不影响原本 ready portfolio。
- `test_build_maturity_narrative_marks_review_for_history_readiness_requirement_failure` 验证 requirement fail 会触发 `review`，并把失败原因写入 summary 和 section claim。
- `test_write_maturity_narrative_outputs` 验证 Markdown/HTML 真实渲染新增字段。

## 运行截图和证据

- `d/365/图片/01-maturity-readiness-requirement-review.png`
- `d/365/解释/说明.md`

截图样例里 `benchmark_history_readiness_requirement_failed_count=1`，portfolio status 被拉到 `review`，证明 v364 的 benchmark history gate 已被 maturity narrative 消费。

## 一句话总结

v365 把 benchmark history readiness gate 从单点报告推进到成熟度叙事判定，让模型评估证据链更像一个可被后续 review 消费的闭环。
