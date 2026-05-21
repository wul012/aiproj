# 385-v371 maturity benchmark requirement carryover

## 本版目标和边界

v371 承接 v370 registry 的 requirement 聚合结果，把 benchmark-history readiness requirement 的变化继续传递到 maturity summary、maturity narrative、CLI stdout 和 HTML/Markdown 报告。这样成熟度总览不再只看 `benchmark_history_regression_count`，也会把 requirement status change 和 exit-code delta 当作 release review 信号。

本版不改训练流程，不扩大模型规模，不改变 benchmark history、release readiness comparison 或 registry 的原始 schema。它只做下游消费和展示，让已有证据在 maturity 层可见。

## 前置链路

前置能力来自：

- v364：benchmark history readiness gate 定义了 readiness requirement。
- v365-v368：maturity narrative、project audit、release bundle 和 release gate 开始消费 readiness requirement。
- v369：release readiness comparison 把 requirement status、exit code、failed reasons 和 delta 写入比较结果。
- v370：registry 汇总 run row、summary、leaderboard、CSV、HTML 和 CLI 输出中的 requirement change。

v371 是同一条链路进入项目成熟度总览和组合叙事的版本。

## 关键文件

- `src/minigpt/maturity.py`
  - `_release_readiness_context()` 从 registry 的 `release_readiness_delta_summary` 读取 `benchmark_history_readiness_requirement_status_changed_count` 和 `max_abs_benchmark_history_readiness_requirement_exit_code_delta`。
  - `_release_readiness_trend_status()` 在 requirement change 大于 0 时返回 `benchmark-regressed`。
  - `_summary()` 把两个字段提升为 `release_readiness_benchmark_requirement_status_changed_count` 和 `release_readiness_max_benchmark_requirement_exit_code_delta`。
  - `_recommendations()` 在 requirement change 出现时给出复核建议。
- `src/minigpt/maturity_artifacts.py`
  - Markdown overview、HTML stat card 和 Release Readiness 表格都显示 requirement changes 与 exit delta。
- `src/minigpt/maturity_narrative_summary.py`
  - `_release_summary()` 合并 release context 与 maturity summary 中的 requirement 字段。
  - 即使只有 maturity summary 可用，只要 requirement change 大于 0，也会把 release trend 兜底设为 `benchmark-regressed`。
  - 顶层 summary 输出 `release_readiness_benchmark_requirement_status_changed_count` 和 `release_readiness_benchmark_requirement_exit_code_delta_max`。
- `src/minigpt/maturity_narrative_sections.py`
  - Release Quality Trend claim 增加 `benchmark requirement changes` 和 `benchmark requirement exit delta`。
- `src/minigpt/maturity_narrative_artifacts.py`
  - Markdown portfolio summary 和 HTML stat cards 显示 requirement change。
- `scripts/build_maturity_summary.py`
  - CLI stdout 打印 maturity summary 中的 requirement change 和 exit delta。
- `scripts/build_maturity_narrative.py`
  - CLI stdout 打印 narrative summary 中的 requirement change 和 exit delta。
- `tests/test_maturity.py`
  - 覆盖 maturity summary 从 registry 读取 requirement change，并把 maturity 标记为需要复核。
- `tests/test_maturity_artifacts.py`
  - 覆盖 Markdown 与 HTML 输出包含 requirement change 字段。
- `tests/test_maturity_narrative.py`
  - 覆盖 narrative summary、release section、recommendations、Markdown 和 HTML 都能看到 requirement change。
- `AGENTS.md`
  - 增加仓库级规则：写代码时不要制造难于维护的巨型代码文件，职责变宽或接近约 500-800 行时要做必要拆分。

## 核心数据结构

registry 的 release-readiness delta summary 输入字段：

```json
{
  "benchmark_history_readiness_requirement_status_changed_count": 1,
  "max_abs_benchmark_history_readiness_requirement_exit_code_delta": 1
}
```

maturity summary 输出字段：

```json
{
  "release_readiness_benchmark_requirement_status_changed_count": 1,
  "release_readiness_max_benchmark_requirement_exit_code_delta": 1,
  "release_readiness_trend_status": "benchmark-regressed"
}
```

maturity narrative summary 输出字段：

```json
{
  "portfolio_status": "review",
  "release_readiness_trend_status": "benchmark-regressed",
  "release_readiness_benchmark_requirement_status_changed_count": 1,
  "release_readiness_benchmark_requirement_exit_code_delta_max": 1
}
```

这三组字段代表不同层次：registry 是多运行目录聚合，maturity summary 是项目成熟度总览，maturity narrative 是面向审阅者的解释入口。

## 运行流程

1. `scripts/build_maturity_summary.py` 读取 registry。
2. `maturity._release_readiness_context()` 取出 registry 的 release-readiness delta summary。
3. `_release_readiness_trend_status()` 根据 requirement change 把趋势判为 `benchmark-regressed`。
4. `write_maturity_outputs()` 写出 JSON、CSV、Markdown、HTML。
5. `scripts/build_maturity_narrative.py` 再读取 maturity summary、registry、benchmark、dataset 和 request history。
6. `build_maturity_narrative_summary()` 将 requirement change 提升到 portfolio summary。
7. narrative report 在顶部 stat cards、Release Quality Trend claim、Evidence Matrix 和 recommendations 中显示 review 原因。

## 测试覆盖

- `test_benchmark_requirement_change_marks_maturity_for_review`
  - 构造 registry 中 requirement change 为 1 的场景。
  - 断言 maturity summary 的 release trend 变成 `benchmark-regressed`。
  - 断言新增字段进入 summary。
- `test_write_maturity_outputs`
  - 断言 Markdown 包含 `Release readiness benchmark requirement changes`。
  - 断言 HTML 包含 `Benchmark req changes`。
- `test_build_maturity_narrative_marks_review_for_benchmark_requirement_change`
  - 构造 benchmark-history regression count 为 0、但 requirement change 为 1 的场景。
  - 断言 portfolio status 是 `review`。
  - 断言 release section claim 写出 requirement change 与 exit delta。
  - 断言 recommendations 提醒审阅 readiness requirement 变化。
- `test_write_maturity_narrative_outputs`
  - 断言 narrative Markdown 和 HTML 都有 requirement change 字段。

## 运行截图和证据

- `d/371/图片/01-maturity-benchmark-requirement.png`
- `d/371/解释/说明.md`
- `d/371/解释/maturity-summary-command.txt`
- `d/371/解释/maturity-narrative-command.txt`
- `d/371/解释/playwright-snapshot.txt`
- `d/371/解释/playwright-text-check.txt`

本版临时 fixture 放在 `runs/__tmp_v371_maturity`，只用于生成证据和截图，提交前会删除。最终归档只保留 `d/371` 和代码讲解。

一句话总结：v371 让 benchmark readiness requirement 的变化从 registry 进入 maturity 总览和 narrative 审阅入口，避免成熟度报告只看到 benchmark case 数量而漏掉 readiness requirement 失败。
