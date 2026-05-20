# 311. v297 release readiness CI order evidence

## 本版目标与边界

v297 的目标是把 v296 已经进入 project audit 的 CI workflow order 计数继续传到 release bundle 和 release readiness。这样 promoted seed handoff assurance smoke 是否仍早于 coverage gate，不只在 hygiene/audit 层可见，也会出现在发布总包、发布就绪面板、Markdown/HTML 报告和 CLI stdout 中。

本版不改变 GitHub Actions workflow，不修改 readiness 的 ship/review 判定规则，也不把 order violation 单独升级为新的发布阻断条件。它只让已有 CI hygiene 证据在发布阶段不丢失。

## 前置链路

v294 定义了 smoke-before-coverage 的 required order 检查。v295 增加了行号诊断。v296 把 order 计数从 hygiene JSON 扩展到 CLI stdout 和 project audit context。

v297 继续向下游推进：release bundle 汇总发布证据，release readiness 决定是否可 ship/review。因此这两层需要保留同一组 `required_order_count` 和 `order_violation_count`，否则发布阶段只能看到 CI pass/fail，无法看到顺序漂移的具体计数。

## 关键文件

- `src/minigpt/release_bundle.py`
  - summary 新增 `ci_workflow_required_order_count` 和 `ci_workflow_order_violation_count`。
  - CI workflow context 保留 `required_order_count` 和 `order_violation_count`。
  - 当显式 CI hygiene JSON 不存在时，从 project audit 的 `ci_workflow_context` 兜底读取 order 计数。

- `src/minigpt/release_readiness.py`
  - readiness summary 新增两项 CI order 字段。
  - CI workflow panel detail 显示 `required_order=<n>; order_violations=<n>`。
  - 直接读取 CI hygiene JSON 或只依赖 bundle summary/context 时，都使用同一套字段。

- `src/minigpt/release_bundle_artifacts.py`
  - release bundle Markdown summary 增加 CI required order 和 order violations。
  - HTML stats 增加 CI order violations，方便浏览器报告快速扫描。

- `src/minigpt/release_readiness_artifacts.py`
  - release readiness Markdown summary 和 HTML stats 增加 CI order 计数。

- `scripts/build_release_bundle.py` 与 `scripts/build_release_readiness.py`
  - CLI stdout 打印 `ci_workflow_required_order_count` 和 `ci_workflow_order_violation_count`。
  - CI 日志或本地脚本输出不打开 JSON 也能确认发布层是否看到顺序证据。

- `tests/test_release_bundle.py` 与 `tests/test_release_readiness.py`
  - fixture 加入 pass 和 fail 两种 order 计数。
  - 断言 release bundle summary/context 与 release readiness summary/panel 都能看到这些字段。
  - 额外覆盖“直接 CI hygiene 报告缺失时，从 bundle summary/context 读取”的场景。

## 输入输出

release bundle CLI 现在会输出：

```text
ci_workflow_required_order_count=1
ci_workflow_order_violation_count=0
```

release readiness CLI 同样输出这两项。发布 JSON 里字段分两层：

- `summary.ci_workflow_required_order_count`
- `summary.ci_workflow_order_violation_count`
- `ci_workflow_context.required_order_count`
- `ci_workflow_context.order_violation_count`

readiness panel detail 则使用更适合人工阅读的形式：

```text
required_order=1; order_violations=0
```

## 测试与证据

本版运行了以下验证：

- `python -B -m unittest tests.test_release_bundle tests.test_release_readiness`
  - 16 个聚焦测试通过，覆盖 release bundle/readiness 的新增字段。
- `python -B -m unittest tests.test_release_readiness_comparison tests.test_maturity tests.test_coverage_governance_chain`
  - 15 个下游治理测试通过，确认 readiness/maturity 链没有回归。
- `python -B -m unittest discover -s tests`
  - 558 个全量测试通过。
- `python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-v297`
  - 283 个源文件全部 clean。
- `python -B scripts\run_test_coverage.py --out-dir runs\test-coverage-v297 --fail-under 80`
  - coverage gate 通过，line coverage 为 90.3%。
- release bundle/readiness 两个 CLI 样例输出均显示 order 字段。

运行截图和解释归档在 `c/297`。其中 CLI 截图证明发布层 stdout 已暴露字段，聚焦测试截图证明 JSON/context/panel 链路受测试保护，全量测试和 coverage 截图证明这次传播没有破坏既有治理链。

## 链路角色

v297 让 CI workflow order evidence 从 audit 层继续进入发布阶段。之后如果 smoke-before-coverage 顺序漂移，release readiness 不只会知道 CI hygiene 有问题，还能显示 required order 规则数和具体违规数。

一句话总结：v297 把 CI workflow 顺序证据带到 release bundle 和 release readiness，让发布判断阶段也能看见同一条 smoke-before-coverage 治理证据。
