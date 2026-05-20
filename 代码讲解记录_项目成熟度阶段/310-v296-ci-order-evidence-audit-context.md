# 310. v296 CI workflow order evidence audit context

## 本版目标与边界

v296 的目标是把 v294-v295 已经建立的 CI workflow order 证据，从 `ci_workflow_hygiene.json` 内部继续外露到两处更容易被使用的地方：命令行 stdout 和 project audit context。这样当 promoted seed handoff assurance smoke 与 coverage gate 的顺序漂移时，CI 日志、审计检查和后续治理报告都能直接看到 order 计数。

本版不修改 GitHub Actions workflow 的真实步骤，不改变 smoke/coverage 的执行策略，也不新增新的门禁阈值。它只扩展已有证据的可见范围，让下游消费者少读一层 JSON。

## 前置链路

v292 把 promoted seed handoff assurance smoke 放进 GitHub Actions。v293 让 smoke 自己写出 summary artifact。v294 让 CI workflow hygiene 检查 smoke 是否存在、是否在 coverage 之前。v295 把这个顺序检查升级为行号证据。

v296 接着做的是“证据传播”：既然 hygiene summary 里已经有 `required_order_count` 和 `order_violation_count`，就让 CLI 输出和 project audit context 都携带同一组字段。

## 关键文件

- `scripts/check_ci_workflow_hygiene.py`
  - 读取 CI workflow hygiene report 的 summary。
  - 在 stdout 中新增 `required_order_count` 和 `order_violation_count`。
  - 让 CI 日志不打开 JSON artifact 也能判断 order 规则是否存在、是否违规。

- `src/minigpt/project_audit_contexts.py`
  - `build_ci_workflow_hygiene_check()` 的 detail 增加 `order_violations=<n>`。
  - 同一个 check 的 evidence payload 增加 `required_order_count` 与 `order_violation_count`。
  - `build_ci_workflow_context()` 也暴露这两个字段；缺失输入时显式给出 `None`，避免下游误解为 0。

- `tests/test_project_audit.py`
  - 构造带 order 计数的 CI hygiene fixture。
  - 断言 audit check detail、evidence 和 context 三个出口都能读到 `order_violation_count`。
  - 保护下游治理链路不会退回到只能读原始 hygiene JSON 的状态。

## 输入输出

CI hygiene CLI 现在会输出：

```text
required_order_count=1
order_violation_count=0
```

这两个字段的语义分别是：

- `required_order_count`：当前 hygiene policy 要检查的 required order 规则数量。
- `order_violation_count`：实际 workflow 中违反 required order 的数量。

project audit context 中同样保留这两个字段。对于真实 pass 场景，`order_violation_count=0`；对于测试中的模拟漂移场景，fixture 使用 `order_violation_count=1`，证明 audit 层会如实传递失败计数。

## 测试与证据

本版运行了四类验证：

- `python -B scripts\check_ci_workflow_hygiene.py --out-dir runs\ci-workflow-hygiene-v296`
  - 证明 CLI stdout 已输出 order 计数，当前 workflow 为 `status=pass`。
- `python -B -m unittest tests.test_ci_workflow tests.test_project_audit`
  - 证明 CI hygiene 和 project audit 的新增字段都被测试覆盖。
- `python -B -m unittest discover -s tests`
  - 558 个单测通过，确认改动没有破坏更宽的治理链。
- `python -B scripts\run_test_coverage.py --out-dir runs\test-coverage-v296 --fail-under 80`
  - 覆盖率门禁通过，line coverage 为 90.3%。

运行截图和解释归档在 `c/296`。其中 CI hygiene 截图证明 stdout 新字段存在，audit/context 截图证明代码和测试都能消费这些字段，覆盖率与全量测试截图证明本版是收口型增强，不是只改文档。

## 链路角色

v296 把 CI workflow order evidence 从“hygiene 内部摘要”推进为“CI 日志可见 + project audit 可消费”的治理上下文。它让后续 release readiness、maturity summary 或外部审计脚本更容易判断：关键 smoke 是否仍然稳定地位于 coverage gate 之前。

一句话总结：v296 让 CI workflow 顺序证据离开单一 JSON artifact，进入 stdout 和 project audit context，增强了发布治理链的可读性和可复用性。
