# v443 CI baseline-candidate threshold boundary wrapper plan

## 本版目标和边界

v442 已经把 baseline-candidate threshold boundary expected-exit gate check 接入 GitHub Actions，并让 CI workflow hygiene 检查它的存在和顺序。但 v442 的 workflow 里直接写了一整条很长的命令：source summary、thresholds、expected exit code、expected diagnosis decision、`--require-pass` 等参数全部摊在 YAML 中。

v443 的目标是把这条长命令收束成稳定 CI wrapper。这样 workflow 只保留一个短入口，固定参数和执行证据由 wrapper 自己记录。边界也很明确：本版不改变 gate 语义，不改变候选接受结论，不新增模型能力声明。

## 前置链路

本版承接 v441-v442：

- v441：新增 expected-exit gate check，证明内部 strict gate 返回 `2` 是预期拒绝，不是运行异常。
- v442：将 expected-exit gate check 接入 GitHub Actions 和 CI workflow hygiene。
- v443：把 v442 的长 CI 命令变成稳定 wrapper，并输出 invocation plan。

## 关键文件

- `scripts/run_ci_baseline_candidate_threshold_boundary_gate_check.py`
  - 新增稳定 CI wrapper。
  - 内置默认 source summary、thresholds、expected exit code、expected diagnosis decision 和 require-pass 策略。
  - 调用 `scripts/check_baseline_candidate_threshold_boundary_gate.py`，再写出 plan JSON/text。
- `.github/workflows/ci.yml`
  - CI 步骤从长命令改为：
    `python -B scripts/run_ci_baseline_candidate_threshold_boundary_gate_check.py --out-dir runs/baseline-candidate-threshold-boundary-gate-check-ci --force`
- `src/minigpt/ci_workflow_hygiene.py`
  - required command fragment 改为稳定 wrapper。
  - 顺序约束仍保持：在 tiny-scorecard plan digest check 之后、coverage 之前。
- `tests/test_ci_baseline_candidate_threshold_boundary_gate_check.py`
  - 新增 wrapper 测试，覆盖固定参数、缺失 gate-check 前的 plan、gate summary 读取、真实 wrapper 写出 plan。
- `tests/test_ci_workflow.py`
  - 更新 synthetic workflow，使 CI hygiene 测试检查 wrapper 入口。

## 核心数据结构

wrapper plan JSON 的核心字段：

- `wrapper`
  - 固定为 `run_ci_baseline_candidate_threshold_boundary_gate_check`。
- `config`
  - `thresholds=0:1:0.5`
  - `require_diagnosis_pass=True`
  - `expected_exit_code=2`
  - `expected_diagnosis_decision=candidate_not_accepted`
  - `require_pass=True`
- `gate_check_summary`
  - 从 gate-check JSON 读取 `status`、`decision`、`failed_count`、`actual_exit_code`、`expected_exit_code`、`diagnosis_decision`。
- `artifact_digest`
  - 记录 gate-check JSON/text/Markdown/HTML 和 boundary smoke JSON 的 SHA-256。

这些字段让 CI reviewer 不必展开 YAML 长命令，也能确认 wrapper 实际执行的契约。

## 运行流程

1. GitHub Actions 调用 `run_ci_baseline_candidate_threshold_boundary_gate_check.py`。
2. wrapper 组装固定命令，调用 `check_baseline_candidate_threshold_boundary_gate.py`。
3. 内层 gate-check 运行 strict diagnosis gate。
4. 内层 strict gate 因 candidate 未被接受返回 `2`。
5. gate-check 验证 `actual_exit_code=2` 与 `expected_exit_code=2` 一致，因此外层返回 `0`。
6. wrapper 写出 invocation plan 和 artifact digests。

这个流程让 CI YAML 更短，同时保留完整证据链。

## 输入输出

输入：

- 默认 source summary：`d/438/解释/baseline-candidate-threshold-boundary-smoke/tiny-scorecard-comparison-smoke/tiny_scorecard_comparison_smoke_summary.json`
- 默认 thresholds：`0:1:0.5`
- 默认 expected exit：`2`
- 默认 diagnosis decision：`candidate_not_accepted`

输出：

- `ci_baseline_candidate_threshold_boundary_gate_check_plan.json`
- `ci_baseline_candidate_threshold_boundary_gate_check_plan.txt`
- v441 gate-check artifacts
- threshold boundary smoke artifacts

plan 是 v443 新增的证据；gate-check artifacts 仍是 expected-exit contract 的最终判断。

## 测试覆盖

新增测试覆盖四个层面：

- command builder 必须保留固定 budget/threshold/expected-exit 契约。
- gate-check 尚未运行时，plan 能记录 missing summary，而不是假装通过。
- gate-check JSON 存在时，summary reader 能读取 `status=pass`、`decision=expected_exit_verified`、`actual_exit_code=2`。
- 真实 wrapper subprocess 能写出 plan，并且 plan 中 digest、gate summary 和 return code 都正确。

本轮聚焦验证：

- `py_compile` 通过。
- `tests/test_ci_baseline_candidate_threshold_boundary_gate_check.py`、`tests/test_ci_workflow.py`、`tests/test_baseline_candidate_threshold_boundary_gate_check.py` 共 `17 passed`。
- `.github/workflows/ci.yml` 通过 YAML 解析检查。
- 全量 `tests` 套件 `774 passed`。
- source encoding hygiene `status=pass`，`source_count=349`，无 BOM 和语法错误。
- `git diff --check` 通过，仅有 Git 换行提示。

## 运行证据

`d/443` 中保存：

- wrapper stdout 和 exit code。
- wrapper plan JSON/text。
- gate-check 输出和 threshold boundary smoke 输出。
- CI workflow hygiene 输出。
- Playwright MCP snapshot 和两张截图。

截图分别证明 wrapper plan 可读、CI hygiene 页面仍显示 boundary gate check ready。

## 一句话总结

v443 把 baseline-candidate expected-exit gate 的 CI 接入从“长 YAML 命令”升级为“稳定 wrapper + invocation plan + digest”，降低维护成本，同时保留严格证据链。
