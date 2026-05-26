# v445 CI boundary plan context carryover

## 本版目标和边界

v444 已经让 CI baseline-candidate threshold boundary wrapper plan 可被复核，但这个 ready 状态主要停留在 CI workflow hygiene 输出里。v445 的目标是把 `baseline_candidate_threshold_boundary_gate_check_ready` 和 `baseline_candidate_threshold_boundary_gate_plan_check_ready` 继续带到 project audit、release bundle 和 release readiness。

本版不新增新的治理链，不重新训练模型，不改变 candidate 是否可晋升的判断。它只是让已有 CI 契约门被上游发布证据消费，避免 reviewer 只能在原始 CI hygiene JSON 里找这两个字段。

## 前置链路

本版承接 v441-v444：

- v441：expected-exit gate check 证明内部 strict gate 返回 `2` 是预期候选拒绝。
- v442：把 expected-exit gate check 接入 GitHub Actions。
- v443：把长 CI 命令收束为 wrapper plan。
- v444：复核 wrapper plan 的 artifact digest 和 expected-exit summary。
- v445：把 v444 的 ready 状态带入审计、bundle 和 readiness。

## 关键文件

- `src/minigpt/project_audit_contexts.py`
  - `build_ci_workflow_hygiene_check()` 的 detail/evidence 增加 boundary gate check 与 boundary plan check ready。
  - `build_ci_workflow_context()` 增加 present/order_ready/ready 字段，缺失输入时返回 `None`。
- `src/minigpt/project_audit.py`
  - project audit summary 新增 `ci_baseline_candidate_threshold_boundary_gate_check_ready` 和 `ci_baseline_candidate_threshold_boundary_gate_plan_check_ready`。
- `src/minigpt/release_bundle_contexts.py`
  - `_ci_workflow_context()` 保留 tiny plan digest、boundary gate check、boundary plan check、drift smoke 四类 CI 门。
  - 使用 `first_present()`，避免 `False` 被 `or` 误当成缺失。
- `src/minigpt/release_bundle_support.py`
  - release bundle summary 新增 `ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready` 和 `ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready`。
- `src/minigpt/release_readiness.py`
  - release readiness summary 和 CI panel detail 展示 boundary gate/check ready。
- `src/minigpt/release_bundle_artifacts.py`
  - bundle Markdown/HTML 摘要展示 CI boundary plan check。
- `src/minigpt/release_readiness_artifacts.py`
  - readiness Markdown/HTML 摘要展示 CI boundary plan check。
- `scripts/audit_project.py`
  - CLI 输出 project audit 的 boundary gate/check ready 字段。
- `scripts/build_release_bundle.py`
  - CLI 输出 release bundle 的 boundary gate/check ready 字段。
- `scripts/build_release_readiness.py`
  - CLI 输出 release readiness 的 boundary gate/check ready 字段。

## 核心字段

本版沿用 v444 字段名，不另造一套含义：

- `baseline_candidate_threshold_boundary_gate_check_ready`
  - 表示 CI workflow 中 expected-exit boundary gate wrapper 已存在且顺序正确。
- `baseline_candidate_threshold_boundary_gate_plan_check_ready`
  - 表示 CI workflow 中 wrapper plan checker 已存在且顺序正确。
- `ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready`
  - release bundle/readiness 层的 summary 字段。
- `ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready`
  - release bundle/readiness 层的 summary 字段，用来证明 v444 plan-check 契约已被发布证据消费。

这些字段的语义是 CI 契约 readiness，不是模型质量、训练质量或 baseline 晋升结论。

## 运行流程

1. `check_ci_workflow_hygiene.py` 读取 GitHub Actions workflow，生成 CI hygiene summary。
2. `audit_project.py` 读取 CI hygiene JSON，把 boundary ready 字段写入 audit summary、check evidence 和 `ci_workflow_context`。
3. `build_release_bundle.py` 读取 project audit 与 CI hygiene，保留同一字段到 bundle summary/context。
4. `check_release_gate.py` 继续按现有 release gate 规则判断 bundle。
5. `build_release_readiness.py` 读取 bundle、gate、audit 和 CI hygiene，在最终 readiness summary/panel 中展示 boundary plan-check ready。

这个流程让 v444 的 checker 从“单点 CI 证据”变成“发布证据的一部分”。

## 测试覆盖

测试更新覆盖三层：

- `tests/test_project_audit.py`
  - 完整 audit 会在 summary/context/evidence 中看到 boundary gate/check ready。
  - CI hygiene fail 时 detail 明确显示 boundary plan check not ready。
- `tests/test_release_bundle.py`
  - bundle summary/context 保留 boundary gate/check ready。
- `tests/test_release_readiness.py`
  - readiness summary 和 CI panel detail 显示 boundary plan check ready。

聚焦测试结果：`39 passed`。
最终收口验证显示全量 `tests` 套件 `779 passed`，source encoding hygiene `source_count=351` 且无 BOM/语法错误，`git diff --check` 通过。

## 运行证据

`d/445` 保存：

- 当前 CI workflow hygiene 输出。
- 受控 `context-inputs/` fixture。
- project audit、release bundle、release gate、release readiness 输出。
- Playwright MCP snapshot 和两张截图。

运行结果显示：

- project audit：`overall_status=pass`，`checks=17 pass/0 warn/0 fail`。
- release bundle：`release_status=release-ready`，`artifacts=22 available/0 missing`。
- release gate：`gate_status=pass`，`decision=approved`。
- release readiness：`readiness_status=ready`，`decision=ship`。

## 一句话总结

v445 把 CI boundary wrapper plan check 的 ready 信号从底层 CI hygiene 提升到 audit、bundle 和 readiness，让发布审查能直接看到这条契约门已经接好。
