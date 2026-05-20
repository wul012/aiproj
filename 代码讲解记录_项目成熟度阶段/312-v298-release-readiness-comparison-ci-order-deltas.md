# 312. v298 release readiness comparison CI order deltas

## 本版目标与边界

v298 的目标是让 release readiness comparison 能比较 CI workflow order violation 的跨版本变化。v297 已经把 `ci_workflow_required_order_count` 和 `ci_workflow_order_violation_count` 带到单个 release readiness 报告；v298 则解决“两个 readiness 报告之间是否出现 smoke-before-coverage 漂移”的对比问题。

本版不改变 release readiness 的生成逻辑，不新增发布阻断规则，也不扩展到 maturity/registry 汇总。它只在 comparison 层增加 row、delta、summary、artifact 和 CLI 输出。

## 前置链路

v294 定义 CI workflow required order 检查。v295 增加行号证据。v296 把 order 计数传入 project audit。v297 把 order 计数传入 release bundle 和 release readiness。

v298 承接 v297 的单报告字段，把它们变成跨版本比较信号：如果两个 release readiness 都是 `ready`，CI status 也都是 `pass`，但新版本的 `order_violation_count` 从 0 变成 1，comparison 仍会把它记为 CI workflow regression。

## 关键文件

- `src/minigpt/release_readiness_comparison.py`
  - readiness row 新增 `ci_workflow_required_order_count` 与 `ci_workflow_order_violation_count`。
  - delta 新增 `ci_workflow_required_order_delta` 与 `ci_workflow_order_violation_delta`。
  - summary 新增 `ci_workflow_order_regression_count` 与 `max_abs_ci_workflow_order_violation_delta`。
  - `_is_ci_workflow_regression()` 现在会把 order violation 增加视为 CI workflow hygiene regression。
  - delta explanation 会写出 `CI workflow order violation delta is <n>`。

- `src/minigpt/release_readiness_comparison_artifacts.py`
  - comparison CSV 增加 order count 字段。
  - delta CSV 增加 order delta 字段。
  - Markdown readiness matrix 展示 CI order violations。
  - Markdown/HTML delta 表展示 CI order violation delta。
  - HTML stats 展示 CI order regressions。

- `scripts/compare_release_readiness.py`
  - CLI stdout 新增 `ci_workflow_order_regressions` 与 `max_abs_ci_workflow_order_violation_delta`。

- `tests/test_release_readiness_comparison.py`
  - fixture 增加 `ci_workflow_order_violations` 参数。
  - 新增同状态测试：baseline/current 都是 ready、CI 都是 pass，但 current 的 order violations 为 1。
  - 断言 summary、rows、delta、explanation、recommendations 都能识别这类细粒度 CI 顺序回归。

## 输入输出

comparison CLI 现在会输出：

```text
ci_workflow_regressions=1
ci_workflow_order_regressions=1
max_abs_ci_workflow_order_violation_delta=1
```

JSON delta 中新增：

```json
{
  "ci_workflow_required_order_delta": 0,
  "ci_workflow_order_violation_delta": 1
}
```

Markdown 和 HTML 会在 readiness matrix 中展示 `CI order violations`，在 delta 表中展示 `CI order violation delta`。

## 测试与证据

本版运行了以下验证：

- `python -B -m unittest tests.test_release_readiness_comparison`
  - 8 个聚焦测试通过，覆盖 order violation delta。
- `python -B -m unittest tests.test_release_readiness tests.test_maturity tests.test_coverage_governance_chain`
  - 17 个治理链测试通过。
- `python -B -m unittest discover -s tests`
  - 559 个全量测试通过。
- `python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-v298`
  - 283 个源文件全部 clean。
- `python -B scripts\run_test_coverage.py --out-dir runs\test-coverage-v298 --fail-under 80`
  - coverage gate 通过，line coverage 为 90.34%。
- `scripts\compare_release_readiness.py` 样例对比输出显示 `ci_workflow_order_regressions=1`。

运行截图和解释归档在 `c/298`。其中 CLI/artifact 截图证明 order delta 不只存在于 JSON，也进入 CSV、Markdown、HTML 和 stdout；测试截图证明同状态 CI pass 但 order violation 增加的情况被覆盖。

## 链路角色

v298 让 release readiness comparison 不再只看 CI 状态和 failed checks。它能发现一种更隐蔽的 drift：CI 看起来仍然 pass，但 smoke-before-coverage 的 required order 已经出现 violation。

一句话总结：v298 把 CI workflow order violation 从单报告证据升级为跨版本 delta，让 readiness comparison 能识别 CI 顺序治理的细粒度回归。
