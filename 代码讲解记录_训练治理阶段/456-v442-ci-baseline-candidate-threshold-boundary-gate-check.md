# v442 CI baseline-candidate threshold boundary gate check

## 本版目标和边界

v441 已经把 strict diagnosis gate 的预期退出码做成了可复核报告：内部 gate 返回 `2`，外层 wrapper 校验这个 `2` 是否符合 `execution.expected_exit_code`。v442 往前推进一步，把这个 wrapper 接入 GitHub Actions，并让 CI workflow hygiene 静态检查它是否存在、是否在正确位置执行。

本版不新增模型能力，也不改变 baseline/candidate 的判定。候选当前仍是 `candidate_not_accepted`。v442 的意义是把“预期拒绝不是运行异常”这条契约纳入 CI，而不是只停留在本地归档。

## 前置链路

本版直接承接：

- v438：live baseline-candidate threshold boundary smoke。
- v439：复用既有 smoke summary 并输出 diagnosis。
- v440：strict diagnosis gate 返回预期退出码 `2`。
- v441：外层 expected-exit contract check 将内部 `2` 验证为通过证据。

v442 把 v441 的 wrapper 放进 CI workflow，并让 hygiene 报告承担守门职责。

## 关键文件

- `.github/workflows/ci.yml`
  - 新增 `Baseline candidate threshold boundary gate check` 步骤。
  - 命令使用 v438 归档的 tiny smoke summary，执行 `scripts/check_baseline_candidate_threshold_boundary_gate.py`。
  - 参数包含 `--require-diagnosis-pass`、`--expected-exit-code 2`、`--expected-diagnosis-decision candidate_not_accepted`、`--require-pass`。
- `src/minigpt/ci_workflow_hygiene.py`
  - `REQUIRED_COMMAND_FRAGMENTS` 新增 `baseline_candidate_threshold_boundary_gate_check`。
  - `REQUIRED_COMMAND_ORDER` 新增两条顺序约束：必须在 tiny-scorecard plan digest check 之后，且必须在 coverage 之前。
  - summary 新增 `baseline_candidate_threshold_boundary_gate_check_present`、`baseline_candidate_threshold_boundary_gate_check_order_ready`、`baseline_candidate_threshold_boundary_gate_check_ready`。
- `src/minigpt/ci_workflow_hygiene_artifacts.py`
  - Markdown 和 HTML 渲染新增 boundary gate check readiness 字段。
- `scripts/check_ci_workflow_hygiene.py`
  - CLI 输出新增三项 boundary gate check readiness 字段，方便 CI log 直接读。
- `tests/test_ci_workflow.py`
  - 覆盖当前 workflow 通过、老 workflow 缺少新步骤失败、步骤顺序错误被识别、Markdown 输出包含新字段。

## 核心字段

CI hygiene summary 里新增三项：

- `baseline_candidate_threshold_boundary_gate_check_present`
  - workflow 中是否包含 `scripts/check_baseline_candidate_threshold_boundary_gate.py`。
- `baseline_candidate_threshold_boundary_gate_check_order_ready`
  - 该步骤是否满足两条顺序约束：在 plan digest check 之后、coverage 之前。
- `baseline_candidate_threshold_boundary_gate_check_ready`
  - present 和 order ready 同时为真，说明这条 CI gate 既存在又位于合适位置。

v442 运行证据显示：

- `baseline_candidate_threshold_boundary_gate_check_present=True`
- `baseline_candidate_threshold_boundary_gate_check_order_ready=True`
- `baseline_candidate_threshold_boundary_gate_check_ready=True`
- `required_step_count=10`
- `required_order_count=7`
- `order_violation_count=0`

## 运行流程

GitHub Actions 中的相关顺序变为：

1. Source encoding and syntax check。
2. CI workflow hygiene check。
3. Promoted seed handoff assurance smoke。
4. Tiny scorecard comparison inline check smoke。
5. CI tiny scorecard plan digest check。
6. Baseline candidate threshold boundary gate check。
7. Release readiness drift contract smoke。
8. Unit tests / coverage gate。

新步骤用既有 v438 summary 作为输入，不重新训练，不扩大模型 smoke 成本。它会重建 threshold boundary smoke，再由 v441 gate check 校验内部 strict gate 的 `2` 是否等于预期退出码。外层通过时 CI 可以继续。

## 测试覆盖

测试覆盖的不是单纯字符串存在，而是 CI 契约：

- 当前 `.github/workflows/ci.yml` 必须通过 hygiene。
- 缺少新 gate check 的旧 workflow 会增加 `missing_step_count`。
- coverage 放在 evidence checks 之前时，新增 gate check 的 before-coverage order 会失败。
- plan digest check 和 boundary gate check 的先后顺序被单独检查。
- Markdown/HTML 输出包含新 readiness 字段。

本轮聚焦验证：

- `py_compile` 通过。
- `tests/test_ci_workflow.py` 与 `tests/test_baseline_candidate_threshold_boundary_gate_check.py` 共 `13 passed`。
- `.github/workflows/ci.yml` 通过 YAML 解析检查。
- 全量 `tests` 套件 `770 passed`。
- source encoding hygiene `status=pass`，`source_count=347`，无 BOM 和语法错误。

## 运行证据

`d/442` 保存两条证据：

- `ci-workflow-hygiene/`
  - 证明 workflow 静态策略已经接入新 gate check。
- `baseline-candidate-threshold-boundary-gate-check-ci/`
  - 证明新增 CI 命令本身按 CI 参数执行时返回外层 `0`，内部 expected exit 为 `2`。

Playwright MCP 截图分别对应这两条证据，保证 HTML 报告不是只写了文件，而是可以被浏览器实际读取。

## 一句话总结

v442 把 baseline-candidate strict gate 的 expected-exit 契约推进到 CI workflow 层，让这条治理证据从“本地归档”变成“CI 必跑且顺序受检”。
