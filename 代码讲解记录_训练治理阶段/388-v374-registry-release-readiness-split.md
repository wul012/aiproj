# v374 registry release readiness split 代码讲解

## 本版目标和边界

v374 解决两个问题：

- `registry_rankings.py` 已经因为 release-readiness delta 聚合变宽，继续放在排名模块里会影响维护。
- v373 已经能识别 failed reason added，但 failed reason removed 还没有完整进入 registry、maturity summary 和 maturity narrative。

本版不新增治理链，不改训练流程，不扩大模型能力声明。它只把现有 release-readiness 证据链拆出更清楚的模块边界，并补齐恢复信号的可见性。

## 前置能力

本版接在 v373 之后。v373 已经让 release readiness comparison 计算 benchmark-history readiness failed reason additions，并让新增原因触发 maturity/narrative review。

v374 延续这条链路：

```text
release_readiness_comparison
 -> registry_release_readiness
 -> registry_data / registry_render
 -> maturity
 -> maturity_narrative
```

## 关键文件

### `src/minigpt/registry_release_readiness.py`

这是本版新增的边界模块，负责三件事：

- `collect_release_readiness_delta_rows(...)` 从每个 run 的 `release_readiness_comparison.json` 读取 delta 行。
- `release_readiness_delta_summary(...)` 汇总 CI、coverage、benchmark-history、requirement 和 failed-reason drift。
- `release_readiness_delta_leaderboard(...)` 按风险优先级排序 release-readiness delta。

核心数据结构仍然是 `dict[str, Any]` 行结构，字段包括：

- `benchmark_history_readiness_requirement_failed_reason_added_count`
- `benchmark_history_readiness_requirement_failed_reason_removed_count`
- `benchmark_history_readiness_requirement_failed_reason_added`
- `benchmark_history_readiness_requirement_failed_reason_removed`

如果旧报告没有直接写 added/removed 字段，模块会从 baseline 和 compared 的 failed reason 列表派生差异，保证旧 evidence 仍可被 registry 消费。

### `src/minigpt/registry_rankings.py`

这个文件现在重新回到“排名和通用 delta 排序”职责。release-readiness 相关函数改为从 `registry_release_readiness.py` 导入，避免单文件继续增长。

拆分后，`registry_rankings.py` 约 243 行，新模块约 383 行。两者都低于项目当前大文件压力阈值，职责也更单一。

### `src/minigpt/registry_data.py`

`RegisteredRun` 新增 run-level 字段：

- `release_readiness_benchmark_requirement_failed_reason_added_count`
- `release_readiness_benchmark_requirement_failed_reason_removed_count`

这些字段来自 release-readiness comparison 的 delta。added 表示新失败原因，removed 表示失败原因消失。两者都可被 CSV、HTML 和 CLI 读取。

### `src/minigpt/release_readiness_comparison.py`

comparison summary 现在同时输出 removed reason 列表：

- `benchmark_history_readiness_requirement_failed_reason_removed`

同时修正了一个判断边界：如果 baseline 已经是 requirement `fail`，candidate 仍然是 `fail` 但失败原因减少，不再被误判为 regression。只有真实状态变差、exit-code 变坏、case/flag 回退或 added reason 出现时，才进入 benchmark-history regression。

### `src/minigpt/maturity.py`

maturity summary 继续把 added reason 当作 review 信号，但 removed reason 只做可见恢复证据：

- summary 输出 removed count/list。
- release readiness context 输出 removed count/list。
- trend status 不因 removed reason 单独降级。

### `src/minigpt/maturity_narrative_summary.py`

narrative summary 接收 removed count/list，并继续保持 portfolio ready 的可能性。它的含义是：现有失败原因减少了，这是恢复证据，不是新风险。

### `src/minigpt/maturity_narrative_sections.py`

release quality claim 现在同时说清：

```text
benchmark failed reasons added=N (...), removed=N (...)
```

这样展示时不会只看到“新增失败原因”，也能看到某些失败原因已经消失。

## 输入输出

输入仍然是各 run 目录里的：

```text
release-readiness-comparison/release_readiness_comparison.json
```

输出继续进入：

- registry JSON/CSV/HTML
- maturity summary JSON/Markdown/HTML
- maturity narrative JSON/Markdown/HTML
- CLI stdout

本版新增或强化的输出字段是 failed reason removed count/list。它们是最终证据字段，可以被后续报告消费。

## 测试覆盖

本版新增和更新了这些测试：

- `tests/test_release_readiness_comparison.py`
  - 覆盖 failed reason removed 的 comparison delta。
  - 验证 removed 不会被当成 benchmark regression。
- `tests/test_registry.py`
  - 覆盖 run-level added/removed counts。
  - 覆盖 registry delta summary 的 removed list。
  - 覆盖 CSV 和 HTML 输出字段。
- `tests/test_maturity.py`
  - 覆盖 removed reason 在 maturity summary 中可见。
  - 验证 removed-only 情况仍可保持 `overall_status=pass`。
- `tests/test_maturity_narrative.py`
  - 覆盖 removed reason 进入 narrative summary 和 release section claim。
  - 验证 removed-only 情况仍可保持 portfolio ready。

验证结果：

```text
59 passed
```

## 运行证据

运行证据归档在：

```text
d/374/图片/01-registry-release-readiness-split-evidence.png
d/374/解释/说明.md
```

截图页面展示本版拆分目标、关键模块、测试结果和文件压力变化。

## 一句话总结

v374 把 registry release-readiness 聚合从排名模块中拆成清晰边界，并让 benchmark-history readiness 的失败原因消失也能成为成熟度证据链里的可见恢复信号。
