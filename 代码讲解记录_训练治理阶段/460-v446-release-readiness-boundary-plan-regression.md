# v446 release readiness boundary plan regression

## 本版目标和边界

v445 已经把 CI workflow hygiene 里的 tiny plan digest、baseline-candidate threshold boundary gate check、boundary wrapper plan check 和 release-readiness drift smoke ready 状态带到了 release readiness。v446 的目标是继续向后一步：让 `release_readiness_comparison` 在比较两个 readiness dashboard 时，把这些 ready 字段当成可回归的契约信号。

本版不新增新的治理链，不重新跑训练，不改变 release readiness 自身的 `ready/review/blocked` 判定，也不把 CI 契约 readiness 解释成模型质量。它只解决一个发布审查问题：如果整体 readiness 仍然是 `ready`，但 CI boundary plan-check 从 ready 变成 not ready，比较报告必须能直接指出这是一条 CI workflow regression。

## 前置链路

本版承接 v441-v445：

- v441-v442：baseline-candidate threshold boundary gate check 被包装成 expected-exit CI 契约。
- v443-v444：长 CI 命令被 wrapper plan 和 plan-check 消化，可复核 artifact digest 与 expected-exit 语义。
- v445：这些 ready 字段进入 project audit、release bundle 和 release readiness。
- v446：release readiness comparison 消费这些字段，并把 ready -> not ready 变成 reason/count/delta evidence。

## 关键文件

- `src/minigpt/release_readiness_comparison.py`
  - `_row_from_report()` 新增三类 CI ready 字段。
  - `_delta_from_baseline()` 比较 baseline 与 compared 的 ready 状态，并生成 `*_changed` 与 `*_regressed` 字段。
  - `_summary()` 汇总 tiny plan digest、boundary gate check、boundary plan check 三类 regression count。
  - `_ci_workflow_regression_reasons()` 把 ready -> not ready 映射成稳定 reason：`tiny_scorecard_plan_digest_gate_not_ready`、`boundary_gate_check_not_ready`、`boundary_gate_plan_check_not_ready`。
- `src/minigpt/release_readiness_comparison_artifacts.py`
  - CSV row 输出新增三类 ready 字段。
  - delta CSV 输出新增三类 regressed 字段。
  - Markdown/HTML Summary、Readiness Matrix 和 Delta Matrix 展示 CI plan digest、boundary gate、boundary plan 的状态与回归。
- `scripts/compare_release_readiness.py`
  - CLI stdout 新增三类 CI ready regression counter，方便 CI 日志或命令行审查直接读到。
- `tests/test_release_readiness_comparison.py`
  - 测试 helper 的 readiness summary 补齐 v445 字段。
  - 新增 ready-vs-ready 场景：整体状态不变，但 boundary plan check 从 `True` 变 `False`，比较器必须输出 `boundary_gate_plan_check_not_ready`。
  - 输出测试覆盖 CSV、Markdown、HTML 的新字段。

## 核心字段

- `ci_workflow_tiny_scorecard_plan_digest_gate_ready`
  - 表示 tiny scorecard CI wrapper plan digest gate 是否 ready。
- `ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready`
  - 表示 baseline-candidate threshold boundary expected-exit gate check 是否 ready。
- `ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready`
  - 表示 boundary wrapper plan-check 是否 ready。

这些字段在 row 中代表单份 readiness 的状态，在 delta 中会派生出：

- `*_changed`
  - baseline 与 compared 是否不同。
- `*_regressed`
  - baseline 是 `True`，compared 不是 `True`。

其中 regressed 会计入 `ci_workflow_regression_count`，并进入 `ci_workflow_regression_reason_counts`。

## 运行流程

1. `scripts/compare_release_readiness.py` 读取两份 `release_readiness.json`。
2. `build_release_readiness_comparison()` 把每份 readiness summary 转为 row。
3. 比较器以第一份或显式 baseline 为基准生成 delta。
4. 当 boundary plan check 从 `True` 变为 `False` 时，delta 记录：
   - `ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_changed=True`
   - `ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regressed=True`
   - `ci_workflow_regression_reasons=["boundary_gate_plan_check_not_ready"]`
5. artifact writer 把该结果写入 JSON、CSV、Markdown 和 HTML，CLI 也打印对应 count。

## 测试覆盖

本版聚焦测试通过：`tests/test_release_readiness_comparison.py` 共 `18 passed`。

新增断言保护了以下行为：

- overall `delta_status` 仍可为 `same`，不强行把 ready-vs-ready 变成 readiness regression。
- CI workflow regression count 必须为 `1`。
- boundary plan check regression count 必须为 `1`。
- regression reason 必须是稳定的 `boundary_gate_plan_check_not_ready`。
- recommendation 必须包含 `boundary plan check readiness=1`。
- CSV/Markdown/HTML 必须暴露新字段，避免 JSON 有字段但人工报告不可见。

收口验证还跑了相关 release 链路测试、全量测试和源码编码检查：

- `tests/test_release_readiness_comparison.py tests/test_release_readiness.py tests/test_release_bundle.py tests/test_project_audit.py`：`57 passed`
- `tests` 全量：`780 passed`
- `check_source_encoding.py`：`source_count=351`，`clean_count=351`，`bom_count=0`，`syntax_error_count=0`
- `git diff --check`：无 whitespace error，仅有 Windows CRLF 提示。

## 运行证据

`d/446` 保存了受控样本和真实生成产物：

- baseline 样本：整体 `ready/ship/pass`，boundary plan check ready。
- candidate 样本：整体仍为 `ready/ship/pass`，boundary plan check not ready。
- CLI 输出显示：
  - `regressed=0`
  - `ci_workflow_regressions=1`
  - `ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regression_count=1`
  - `ci_workflow_regression_reason_counts={"boundary_gate_plan_check_not_ready": 1}`
- Playwright MCP 截图保存到 `d/446/图片/01-release-readiness-boundary-plan-regression.png`。

这说明 v446 检测的是契约门退化，而不是把整体 release readiness 判定改成失败。

## 一句话总结

v446 让 release readiness comparison 能在总体 ready 状态不变时识别 CI boundary plan-check 契约退化，把 v445 带上来的字段真正变成可审查、可归档、可回归计数的发布证据。
