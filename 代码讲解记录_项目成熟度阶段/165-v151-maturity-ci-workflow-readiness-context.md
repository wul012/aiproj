# 第一百五十一版代码讲解：maturity CI workflow readiness context

## 本版目标

v151 的目标是把 v150 已经进入 registry 的 CI workflow readiness regression 继续接入 `maturity summary`。
这样项目成熟度页不只知道 release readiness 是否整体退化，也能看到 CI workflow hygiene 是否在跨 run 比较中退化。

本版解决的问题是：当 registry 已经能识别 `ci-regressed` 时，maturity summary 仍然只展示普通 readiness regression、improvement 和 panel change，导致最终成熟度总结漏掉 CI 策略漂移。

本版不做三件事：

- 不修改 GitHub Actions workflow。
- 不改变 release gate 的 hard block 规则。
- 不声称 CI workflow hygiene 证明模型能力提升。

## 前置路线

本版承接 v145-v150 的治理链：

```text
v145 -> ci_workflow_hygiene report
v146 -> project_audit CI context
v147 -> release_bundle CI evidence
v148 -> release_readiness CI panel
v149 -> release_readiness_comparison CI deltas
v150 -> registry CI readiness regression tracking
v151 -> maturity CI workflow readiness context
```

v151 让这条链进入项目成熟度层。成熟度 summary 可以消费 registry 中的 `release_readiness_delta_summary`，并把 CI workflow regression 作为 review 信号展示出来。

## 关键文件

```text
src/minigpt/maturity.py
src/minigpt/maturity_artifacts.py
scripts/build_maturity_summary.py
tests/test_maturity.py
tests/test_maturity_artifacts.py
README.md
c/151/解释/说明.md
```

`maturity.py` 负责计算成熟度事实，包括版本计数、能力矩阵、release readiness trend context、request history context 和推荐动作。

`maturity_artifacts.py` 负责把成熟度 summary 渲染成 JSON、CSV、Markdown 和 HTML。

`build_maturity_summary.py` 是命令行入口，负责把 summary 写入输出目录并打印关键 overview 字段。

测试文件负责锁定边界：CI workflow regression 会让 maturity summary 进入 `warn`，但不会改 release gate 硬规则。

## 核心数据结构

成熟度 summary 的 `summary` 区域新增三个字段：

```text
release_readiness_ci_workflow_regression_count
release_readiness_ci_workflow_status_changed_count
release_readiness_max_ci_workflow_failed_check_delta
```

这些字段来自 registry 的：

```text
release_readiness_delta_summary.ci_workflow_regression_count
release_readiness_delta_summary.ci_workflow_status_changed_count
release_readiness_delta_summary.max_abs_ci_workflow_failed_check_delta
```

`release_readiness_context` 也携带同样的字段，供 Markdown/HTML 的 Release Readiness Trend Context 区域展示。

## 趋势状态逻辑

`_release_readiness_trend_status()` 的优先级现在是：

```text
regressed
ci-regressed
improved
panel-changed
stable
comparison_counts fallback
```

这里刻意让 `regressed` 高于 `ci-regressed`。
原因是普通 readiness regression 表示整体 release readiness 退化；`ci-regressed` 表示 CI workflow hygiene 退化，是 maturity review 信号，但语义上仍然比整体 release readiness regression 更窄。

当 `trend_status == "ci-regressed"` 且其它 capability 都是 `pass` 时，`overall_status` 会从 `pass` 降为 `warn`。
这表达的是“需要 review”，不是“发布硬阻断”。

## 归档和讲解计数修正

v151 还修正了 maturity summary 的事实计数口径。

旧逻辑只扫描：

```text
a/
b/
```

但项目从 v69 起已经把运行截图和解释写入：

```text
c/
```

因此 `_discover_archive_versions()` 现在同时扫描 `a/`、`b/`、`c/`。

旧讲解扫描依赖 `代码讲解记录*/*.md` glob。v151 改为先遍历项目根目录，再只接受目录名以 `代码讲解记录` 开头的目录，避免终端编码显示影响 glob，同时不把其它 Markdown 误算进去。

## 输出展示

Markdown overview 新增：

```text
Release readiness CI workflow regressions
```

Release Readiness Trend Context 新增：

```text
CI workflow regressions
CI workflow status changes
Max CI workflow failed-check delta
```

HTML 顶部 stats 新增：

```text
CI regressions
```

HTML Release Readiness Trend Context 也展示同样三个 CI workflow 字段。

CLI 入口新增打印：

```text
release_readiness_ci_workflow_regression_count=<n>
release_readiness_ci_workflow_status_changed_count=<n>
```

这让命令行截图和 CI 日志能直接看到 maturity summary 是否识别到 CI workflow regression。

## 测试覆盖

`tests/test_maturity.py` 新增和更新断言：

- 正常 improved registry 中 CI workflow regression count 为 0。
- `archive_version_count` 能覆盖 `c/` 归档阶段。
- 当 `ci_workflow_regression_count == 1` 且普通 `regressed_count == 0` 时，趋势状态是 `ci-regressed`。
- `ci-regressed` 会让 maturity overall status 变成 `warn`。
- recommendation 中会提示 review CI workflow hygiene regressions。

`tests/test_maturity_artifacts.py` 覆盖：

- Markdown 包含 `CI workflow regressions`。
- HTML 包含 `CI workflow regressions`。
- 旧的 `minigpt.maturity` facade 仍然导出 artifact 函数。

## 证据边界

本版证据属于成熟度和治理链路证据。
它证明的是：registry 中的 CI workflow readiness regression 能被成熟度 summary 消费、展示并转化为 review 建议。

它不证明模型质量提升，不证明训练规模扩大，也不代表发布门禁规则改变。

## 运行与归档

v151 的运行截图和解释放在：

```text
c/151/图片
c/151/解释/说明.md
```

这些证据覆盖 maturity 单测、CLI smoke、CI workflow hygiene、source encoding hygiene、maintenance smoke、全量 unittest 和文档对齐检查。

## 一句话总结

v151 把 CI workflow hygiene 退化信号从 registry 推进到 maturity summary，让项目成熟度总结能够识别 CI 策略漂移，同时保持它只是 review 级治理证据。
