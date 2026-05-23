# v409 maturity narrative benchmark history suite design

## 本版目标和边界

v409 的目标是把 v408 已经进入 benchmark history ledger 的 suite-design readiness 继续接入 maturity narrative。这样成熟度叙事层不只看到“benchmark history readiness failed”，还能直接说明失败是否来自 prompt suite design 不适合比较。

本版不新建治理链，不新增评测题集，不训练 checkpoint，也不改变 release readiness 的判断规则。它只让 maturity narrative 消费已有 history 字段，把历史账本中的 suite-design 边界展示到 summary、section、Markdown/HTML 和 CLI。

## 前置能力

本版承接：

- v406：scorecard comparison 记录 suite-design comparison readiness。
- v407：scorecard decision 把 suite-design not-ready 转成 review/remediation。
- v408：benchmark history 记录 `suite_design_non_comparison_ready_entry_count`、`design_comparison_changed_entry_count` 和 `suite_design_non_comparison_ready_entries`。

v409 位于成熟度叙事层，负责让人类审阅者在 portfolio summary 中直接看见这条边界。

## 关键文件

### `src/minigpt/maturity_narrative_summary.py`

summary 新增聚合字段：

```text
benchmark_history_suite_design_non_comparison_ready_entry_count
benchmark_history_design_comparison_changed_entry_count
```

`_benchmark_history_summary()` 从 history summary 中读取：

```text
suite_design_non_comparison_ready_entry_count
design_comparison_changed_entry_count
```

`_portfolio_status()` 现在会把 history 中的 suite-design not-ready entry 当作 review 信号。也就是说，即使 scorecard decision artifact 不在当前输入里，只要 benchmark history ledger 保存了这条边界，maturity narrative 仍会进入 review。

recommendations 增加专门提示：

```text
Fix benchmark history suite-design comparison readiness before treating repeated scorecard evidence as clean benchmark evidence.
```

这条提示比普通 readiness failure 更具体，便于定位问题来自题集设计，而不是模型分数、case regression 或 generation quality。

### `src/minigpt/maturity_narrative_sections.py`

Benchmark History section 的 status 现在会因为 `benchmark_history_suite_design_non_comparison_ready_entry_count > 0` 进入 warning/review 路径。

claim 增加：

```text
suite-design not-ready entries=<n>
design comparison changes=<n>
```

这样 HTML/Markdown 的叙事正文就能说明：历史证据不是单纯“失败”，而是“题集设计层还不适合比较”。

### `src/minigpt/maturity_narrative_artifacts.py`

Portfolio Summary 的 Markdown 表格新增：

```text
Benchmark history suite-design not-ready
Benchmark history design changes
```

HTML stats 新增：

```text
History design review
History design changes
```

这些字段让浏览器截图和 Markdown 审阅都能看到 v408 的 history 信号已经进入 maturity narrative。

### `scripts/build_maturity_narrative.py`

CLI stdout 新增：

```text
benchmark_history_suite_design_non_comparison_ready_entries
benchmark_history_design_comparison_changed_entries
```

这样自动化日志不用打开 JSON，也能确认 maturity narrative 是否发现 suite-design history 边界。

### `tests/test_maturity_narrative.py`

新增和更新的测试覆盖：

- ready history 默认 `suite_design_non_comparison_ready_entry_count=0`。
- suite-design not-ready history 会让 portfolio status 进入 `review`。
- Benchmark History section claim 包含 suite-design not-ready entries 和 design comparison changes。
- Markdown/HTML 输出包含新增字段。
- CLI stdout 打印新增字段。

## 输入输出

输入仍是：

```text
maturity_summary.json
registry.json
request_history_summary.json
benchmark_scorecard.json
benchmark_scorecard_decision.json
benchmark_history.json
dataset_card.json
```

输出新增：

```text
maturity_narrative.json
  summary.benchmark_history_suite_design_non_comparison_ready_entry_count
  summary.benchmark_history_design_comparison_changed_entry_count

maturity_narrative.md/html
  Benchmark history suite-design not-ready
  History design review

CLI stdout
  benchmark_history_suite_design_non_comparison_ready_entries
```

这些字段是 maturity review 证据，不是模型质量证明。

## 测试覆盖

定向验证命令：

```text
python -m pytest tests\test_maturity_narrative.py -q
python -m py_compile src\minigpt\maturity_narrative_summary.py src\minigpt\maturity_narrative_sections.py src\minigpt\maturity_narrative_artifacts.py scripts\build_maturity_narrative.py tests\test_maturity_narrative.py
```

本版还会回归 benchmark history 测试，确认 v408 的 ledger 字段仍然能被上游正确生成。

完整验证还包括全量 pytest、source encoding 和 `git diff --check`。

## 运行证据

运行截图与说明归档在：

```text
d/409/图片/01-maturity-narrative-history-suite-design-evidence.png
d/409/解释/说明.md
d/409/解释/v409-maturity-narrative-history-suite-design-evidence.html
```

## 一句话总结

v409 把 prompt suite design 不就绪从 benchmark history 继续推进到 maturity narrative，让成熟度总览能直接说明“历史 benchmark 证据为什么还不能当成干净模型提升证据”。
