# v379 release readiness drift smoke readiness 代码讲解

## 本版目标和边界

v379 的目标是把 v378 的 release readiness drift contract smoke 变成上层治理链路可直接消费的 readiness signal。

v378 已经做到了“CI 会跑这个 smoke”。但对 Project Audit、Release Bundle 和 Release Readiness 来说，这个信息仍然偏底层：它藏在 CI workflow hygiene 的 checks 列表和 order checks 中。v379 增加稳定 summary/context 字段，让上层不用解析 checks，就能判断这道门是否存在、是否顺序正确、是否 ready。

本版不新增 CI step，不改变 drift contract checker，不改变模型训练或评估逻辑，也不把治理字段当作模型质量证明。

## 前置能力

本版承接 v377-v378：

- v377 新增 drift contract checker。
- v378 新增 deterministic mixed-drift smoke，并把它接入 CI。

v379 的链路是：

```text
CI workflow hygiene checks
        |
        v
release_readiness_drift_contract_smoke_ready
        |
        v
project audit context / summary
        |
        v
release bundle context / summary
        |
        v
release readiness summary / panel
```

## 关键文件

### `src/minigpt/ci_workflow_hygiene.py`

summary 新增三项：

```text
release_readiness_drift_contract_smoke_present
release_readiness_drift_contract_smoke_order_ready
release_readiness_drift_contract_smoke_ready
```

计算方式很直接：

- `present` 来自 `command:release_readiness_drift_contract_smoke` 是否通过。
- `order_ready` 来自 `order:release_readiness_drift_contract_smoke_before_coverage` 是否通过。
- `ready = present and order_ready`。

这个设计与已有 tiny scorecard plan digest gate 的三元组一致，便于 reviewer 读懂。

### `src/minigpt/ci_workflow_hygiene_artifacts.py`

Markdown summary 表格新增三项 ready 字段。HTML stat cards 新增 `Drift smoke gate`。

这些是人工查看 artifact 时的证据，不改变 JSON 契约。

### `scripts/check_ci_workflow_hygiene.py`

CLI stdout 新增：

```text
release_readiness_drift_contract_smoke_present=True
release_readiness_drift_contract_smoke_order_ready=True
release_readiness_drift_contract_smoke_ready=True
```

这样 CI log 不需要下载 JSON，也能看到 drift-contract smoke gate 状态。

### `src/minigpt/project_audit.py`

audit summary 新增：

```text
ci_release_readiness_drift_contract_smoke_ready
```

这个字段说明 Project Audit 已经读到 CI workflow hygiene 的 drift smoke gate。

### `src/minigpt/project_audit_contexts.py`

CI workflow audit check detail 新增：

```text
release_readiness_drift_contract_smoke_ready=True
```

`ci_workflow_context` 同步携带 present/order_ready/ready 三项字段。

### `src/minigpt/release_bundle_contexts.py`

release bundle 的 CI context 透传三项字段。如果当前 bundle 没有直接传入 `ci_workflow_hygiene.json`，但 audit context 已经带了这些字段，也会回退使用 audit context。

### `src/minigpt/release_bundle_support.py`

release bundle summary 新增：

```text
ci_workflow_release_readiness_drift_contract_smoke_ready
```

它用于后续 release readiness dashboard 读取。

### `src/minigpt/release_readiness.py`

release readiness summary 新增：

```text
ci_workflow_release_readiness_drift_contract_smoke_ready
```

CI Workflow Hygiene panel detail 新增：

```text
drift_contract_smoke_ready=True
```

如果直接 CI workflow JSON 不存在，panel 仍能从 bundle summary/context 里读取这个字段。

## 测试覆盖

本版更新了四组测试：

- `tests/test_ci_workflow.py`
  - 断言 CI hygiene summary 暴露 present/order_ready/ready。
  - 断言 Markdown artifact 包含新字段。
  - 断言错误顺序时 ready 变为 false。
- `tests/test_project_audit.py`
  - 断言 audit summary 和 context 都携带 drift-contract smoke readiness。
- `tests/test_release_bundle.py`
  - 断言 release bundle summary 和 CI context 都保留该 signal。
- `tests/test_release_readiness.py`
  - 断言 release readiness summary 和 panel detail 都展示该 signal。
  - 覆盖直接 CI JSON 存在和从 bundle context fallback 两条路径。

阶段验证：

```text
41 passed
```

CI workflow hygiene CLI 输出：

```text
release_readiness_drift_contract_smoke_present=True
release_readiness_drift_contract_smoke_order_ready=True
release_readiness_drift_contract_smoke_ready=True
```

最终全量验证：

```text
678 passed
```

source encoding hygiene 结果：

```text
status=pass
source_count=312
clean_count=312
bom_count=0
syntax_error_count=0
```

## 运行证据

运行证据归档在：

```text
d/379/图片/01-release-readiness-drift-smoke-readiness-evidence.png
d/379/解释/说明.md
```

证据页展示了 CI summary、Project Audit、Release Bundle 和 Release Readiness 四层如何消费同一个 readiness signal。

## 一句话总结

v379 让 release readiness drift-contract smoke 从“CI 里有跑”升级为“治理链路能明确看见这道门已经 ready”，减少 reviewer 和后续自动化对底层 checks 表的依赖。
