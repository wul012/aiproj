# v464 archived path portability readiness carryover 代码讲解

## 本版目标和边界

v464 的目标是把 v463 新增的 archived path portability CI gate 从单独的 CI hygiene 报告，继续带到 project audit、release bundle 和 release readiness。

它解决的问题是：CI workflow hygiene 已经能判断 `archived_path_portability_check_ready=True`，但发布审阅侧如果只看 audit/bundle/readiness，还不能直接看到这条路径可移植性信号。

本版不新增路径扫描规则，不改 v463 的 `scripts/check_archived_path_portability.py`，也不把该字段继续扩展到 release readiness comparison。comparison 是否需要回归对比，留到后续确认，避免把治理链继续无节制拉长。

## 前置能力

本版承接 v463：

- v463 新增 `scripts/check_archived_path_portability.py`。
- v463 在 CI workflow hygiene summary 中加入 `archived_path_portability_check_present`、`archived_path_portability_check_order_ready`、`archived_path_portability_check_ready`。
- v464 只消费这些 summary 字段，不重新计算路径可移植性。

## 关键修改文件

### `src/minigpt/project_audit_contexts.py`

`build_ci_workflow_hygiene_check()` 现在会读取：

```text
archived_path_portability_check_present
archived_path_portability_check_order_ready
archived_path_portability_check_ready
```

这些字段进入 CI workflow hygiene check 的 evidence，同时 detail 文本里新增：

```text
archived_path_portability_check_ready=True
```

`build_ci_workflow_context()` 也补齐同名字段，让后续 release bundle 可以从 audit context 中兜底读取。

### `src/minigpt/project_audit.py`

`_summarize_checks()` 新增 audit summary 字段：

```text
ci_archived_path_portability_check_ready
```

这个命名沿用 project audit 的既有风格：CI 原始字段进入 audit 后加 `ci_` 前缀。

### `src/minigpt/release_bundle_contexts.py`

`_ci_workflow_context()` 把 archived path portability 三个字段从直接 CI hygiene summary 或 audit context 中合并出来。

这保证两种输入方式都成立：

- release bundle 直接收到 `ci_workflow_hygiene.json`。
- release bundle 没有直接 CI hygiene，但 audit 里已经有 `ci_workflow_context`。

### `src/minigpt/release_bundle_support.py`

`_build_summary()` 新增：

```text
ci_workflow_archived_path_portability_check_ready
```

读取优先级是：

```text
CI hygiene summary -> audit ci_workflow_context -> audit summary
```

这与 boundary gate、boundary plan、receipt plan 的 carryover 模式保持一致。

### `src/minigpt/release_readiness.py`

release readiness summary 新增：

```text
ci_workflow_archived_path_portability_check_ready
```

CI workflow panel 的 detail 也显示：

```text
archived_path_portability_check_ready=True
```

当直接 CI hygiene 缺失时，panel 会从 bundle summary/context 中读取该字段，保证归档 bundle 自身仍能解释 readiness 状态。

### artifact 和 CLI 文件

以下文件只负责展示和命令行诊断：

- `src/minigpt/project_audit_artifacts.py`
- `src/minigpt/release_bundle_artifacts.py`
- `src/minigpt/release_readiness_artifacts.py`
- `scripts/audit_project.py`
- `scripts/build_release_bundle.py`
- `scripts/build_release_readiness.py`

它们不改变判断逻辑，只把新增 readiness 字段写进 Markdown、HTML 和 stdout。

## 数据流

```text
ci_workflow_hygiene.summary.archived_path_portability_check_ready
  -> project_audit.summary.ci_archived_path_portability_check_ready
  -> release_bundle.summary.ci_workflow_archived_path_portability_check_ready
  -> release_readiness.summary.ci_workflow_archived_path_portability_check_ready
```

同时，context 链路保留 fallback：

```text
ci_workflow_hygiene.summary
  -> project_audit.ci_workflow_context
  -> release_bundle.ci_workflow_context
  -> release_readiness panel detail
```

## 测试覆盖

本版更新了三组测试：

- `tests/test_project_audit.py`：验证 audit summary、CI workflow context 和 CLI stdout 都能看到 archived path readiness。
- `tests/test_release_bundle.py`：验证 release bundle summary、context fallback 和 CLI stdout 都能携带该字段。
- `tests/test_release_readiness.py`：验证 readiness summary、CI workflow panel detail、bundle-context fallback 和 CLI stdout 都能显示该字段。

聚焦测试命令：

```powershell
python -m pytest tests/test_project_audit.py tests/test_release_bundle.py tests/test_release_readiness.py -q -o cache_dir=runs/pytest-cache-v464-focused
```

结果：`39 passed`。

## 运行证据

运行证据归档在 `d/464`：

- `d/464/解释/ci-workflow-hygiene/ci_workflow_hygiene.json`
- `d/464/解释/project-audit-archived-path-carryover/project_audit.json`
- `d/464/解释/release-bundle-archived-path-carryover/release_bundle.json`
- `d/464/解释/release-readiness-archived-path-carryover/release_readiness.json`
- `d/464/解释/release-readiness-archived-path-carryover/playwright_snapshot.md`
- `d/464/图片/release-readiness-archived-path-carryover.png`

这些产物是本版最终证据，不是临时调试文件；后续版本可以直接读取其中的 JSON 或 HTML 来复核字段是否贯通。

## 一句话总结

v464 把 archived path portability 从 CI 层的单点检查，推进为 audit、bundle、readiness 都能看见的发布审阅信号。
