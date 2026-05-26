# v444 CI baseline-candidate boundary gate plan check

## 本版目标和边界

v443 把 baseline-candidate threshold boundary expected-exit gate 的长 CI 命令收束成稳定 wrapper，并写出 wrapper plan 和 artifact digest。v444 在它后面补一层轻量 contract check：不重新训练，不改变阈值矩阵，不改变 candidate 未被接受的结论，只验证 v443 plan 记录的产物摘要和 expected-exit 摘要是否仍然一致。

这版解决的是 CI 证据链的复核问题：如果 gate-check JSON、文本、Markdown、HTML 或 boundary smoke JSON 被改动、丢失，或者 wrapper plan 里的 expected-exit 摘要被篡改，新的 checker 会失败。

## 前置链路

本版承接 v441-v443：

- v441：把 strict diagnosis gate 的预期退出码 `2` 包装成可通过的 expected-exit gate check。
- v442：把 expected-exit gate check 接入 GitHub Actions 和 CI workflow hygiene。
- v443：用稳定 wrapper 替代 YAML 长命令，并记录 wrapper plan 与 artifact digest。
- v444：读取 v443 wrapper plan，逐项复核 digest、固定 config 和 gate-check summary。

## 关键文件

- `scripts/check_ci_baseline_candidate_threshold_boundary_gate_plan.py`
  - 新增 CLI 和 checker 实现。
  - 输入可以是 wrapper 输出目录，也可以是 `ci_baseline_candidate_threshold_boundary_gate_check_plan.json`。
  - 输出 JSON/text check artifact，失败时默认返回 `1`，`--no-fail` 可只写报告不阻断。
- `.github/workflows/ci.yml`
  - 在 `run_ci_baseline_candidate_threshold_boundary_gate_check.py` 之后新增 plan check 步骤。
  - 顺序仍保持在 release-readiness drift smoke 和 coverage 之前。
- `src/minigpt/ci_workflow_hygiene.py`
  - 新增 required command：`scripts/check_ci_baseline_candidate_threshold_boundary_gate_plan.py`。
  - 新增顺序约束：plan check 必须在 wrapper 之后、coverage 之前。
  - summary 新增 `baseline_candidate_threshold_boundary_gate_plan_check_present/order_ready/ready`。
- `src/minigpt/ci_workflow_hygiene_artifacts.py`
  - Markdown/HTML 输出展示新增 plan check ready 状态。
- `scripts/check_ci_workflow_hygiene.py`
  - CLI 文本输出打印新增 ready 字段，方便 CI 日志直接定位。
- `tests/test_ci_baseline_candidate_threshold_boundary_gate_plan_check.py`
  - 覆盖合法 plan、digest 被改、expected-exit 字段被改、目录解析、真实 wrapper 产物复核。
- `tests/test_ci_workflow.py`
  - 覆盖真实 workflow 和 synthetic workflow 中的新步骤、缺失步骤数量、顺序违规数量和渲染字段。

## 核心数据结构

plan check 报告的顶层字段包括：

- `status`
  - `pass` 表示 plan 可以被复核，`fail` 表示 digest、配置或 gate summary 有不一致。
- `decision`
  - 通过时为 `continue`，失败时为 `fix-ci-boundary-gate-plan`。
- `artifacts`
  - 对 `gate_check_json`、`gate_check_text`、`gate_check_markdown`、`gate_check_html`、`boundary_smoke_json` 分别记录 expected/actual exists、size 和 SHA-256。
- `gate_check`
  - 来自 wrapper plan 的 gate-check summary。
  - 关键字段必须为 `status=pass`、`decision=expected_exit_verified`、`failed_count=0`、`actual_exit_code=2`、`expected_exit_code=2`、`diagnosis_decision=candidate_not_accepted`。
- `issues`
  - 机器可读问题列表，包含 `artifact_digest_mismatch`、`config_mismatch`、`gate_summary_mismatch` 等。

## 运行流程

1. CI 先运行 v443 wrapper，生成 gate-check artifacts、boundary smoke JSON 和 wrapper plan。
2. v444 checker 解析 wrapper plan。
3. checker 重新读取 plan 中记录的 5 个 artifact 路径，计算当前文件 size 和 SHA-256。
4. checker 对比 plan 中的固定 CI config。
5. checker 对比 expected-exit gate summary，确认内部退出码 `2` 是预期候选拒绝。
6. 所有检查通过时输出 `status=pass`，否则输出具体 issue 并返回非零。

这个流程的重点是复核已有证据，而不是再跑一遍训练或扩大模型评估。

## 输入输出

输入：

- `ci_baseline_candidate_threshold_boundary_gate_check_plan.json`
- 或包含该 plan 的 wrapper 输出目录。

输出：

- `ci_baseline_candidate_threshold_boundary_gate_check_plan_check.json`
- `ci_baseline_candidate_threshold_boundary_gate_check_plan_check.txt`

这些输出是 CI contract sidecar。它们不是模型质量评估，也不是新的 baseline 选择依据；它们只说明 wrapper plan 与当前 artifact 文件和 expected-exit 摘要一致。

## 测试覆盖

新增测试覆盖：

- 完整 plan 与 artifact digest 一致时通过。
- 手动改动 gate-check 文本后，digest mismatch 会失败。
- 手动把 `expected_exit_code` 改错后，gate summary mismatch 会失败。
- 输入目录可以解析到默认 plan JSON，并写出 JSON/text sidecar。
- 真实 wrapper subprocess 生成的 plan 能被新 checker 复核通过。
- CI workflow hygiene 能识别新增命令、顺序、summary 和输出字段。

本轮运行证据显示聚焦测试 `17 passed`，其中覆盖新增 checker、边界 gate 和 CI workflow hygiene。
最终收口验证显示全量 `tests` 套件 `779 passed`，source encoding hygiene `source_count=351` 且无 BOM/语法错误，`git diff --check` 通过。

## 运行证据

`d/444` 保存本版证据：

- wrapper stdout/exit code。
- plan check stdout/exit code 与 JSON/text 输出。
- CI workflow hygiene JSON/CSV/Markdown/HTML。
- Playwright MCP snapshot 和两张截图。

截图证明 plan check 文本输出为 `status=pass`、`artifact_failure_count=0`、`issue_count=0`，CI hygiene HTML 中新增 plan check 也处于 ready 状态。

## 一句话总结

v444 把 v443 的 CI wrapper plan 从“记录执行”推进到“可被 CI 复核”，让 baseline-candidate threshold boundary expected-exit gate 多了一层防篡改和路径完整性保护。
