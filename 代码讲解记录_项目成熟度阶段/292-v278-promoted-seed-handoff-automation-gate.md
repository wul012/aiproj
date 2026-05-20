# v278 promoted seed handoff automation gate

## 本版目标和边界

v278 的目标是把 promoted seed handoff 中已经存在的严格要求聚合为一个总门禁：`automation_gate`。

在 v216-v219 中，seed handoff 已经有了 clean-evidence requirement。v277 又加入了 clean batch-review requirement。问题是：当 CLI 同时要求两类严格条件时，如果第一类失败就直接退出，第二类诊断可能不会被打印出来。v278 解决这个信息不完整的问题。

本版不新增新的用户开关，不改变默认 handoff 行为，也不改变 plan command 的执行方式。`automation_gate` 只总结已经请求的两个 requirement：

- `--require-clean-evidence`
- `--require-clean-batch-review`

## 前置链路

相关前置版本：

- v216：CLI 有了 `--require-clean-evidence`。
- v219：clean-evidence requirement 成为可复用 library contract。
- v277：clean batch-review requirement 成为可选严格门禁。
- v278：把两类 requirement 聚合为一个总 gate，并保证 CLI 失败前输出完整诊断。

这版属于自动化体验和证据完整性增强，不是模型能力增强，也不是训练流程重构。

## 核心数据结构

### `SeedHandoffAutomationGate`

位置：`src/minigpt/promoted_training_scale_seed_handoff_review.py`

字段：

- `required`
  - 是否至少有一个 strict requirement 被请求。
- `status`
  - `not-required`、`pass`、`fail`。
- `failed_requirements`
  - 失败的 requirement 名称列表。
- `passed_requirements`
  - 已通过的 requirement 名称列表。
- `detail`
  - 总结性说明。
- `status_domain`
  - 稳定公开枚举，便于脚本、CI 或测试消费。

公开枚举：

```python
("not-required", "pass", "fail")
```

## 核心函数

### `build_seed_handoff_automation_gate(clean_evidence_requirement, clean_batch_review_requirement)`

输入是两个已计算好的 requirement object。

计算逻辑：

```text
required_names = all requirements where required == true
failed = required_names where status == "fail"
passed = required_names where status == "pass"

if no required_names:
    status = "not-required"
elif failed:
    status = "fail"
else:
    status = "pass"
```

这个函数不重新判断 clean evidence 或 clean batch-review。它只消费两个既有 requirement 的结果，因此不会和上游规则产生重复判断。

## Builder 变化

位置：`src/minigpt/promoted_training_scale_seed_handoff.py`

`build_promoted_training_scale_seed_handoff()` 现在在生成两个 requirement 后继续生成：

```text
automation_gate
```

report 顶层新增：

```json
"automation_gate": {
  "required": true,
  "status": "fail",
  "failed_requirements": ["clean_evidence", "clean_batch_review"],
  "passed_requirements": [],
  "detail": "failed automation requirement(s): clean_evidence, clean_batch_review",
  "status_domain": ["not-required", "pass", "fail"]
}
```

它是机器可读的最终自动化门禁摘要。

## CLI 变化

位置：`scripts/execute_promoted_training_scale_seed.py`

v278 前，如果 `--require-clean-evidence` 失败，CLI 会立即退出，后面的 `--require-clean-batch-review` 诊断不会出现。

v278 后，CLI 会先打印所有请求过的 requirement：

```text
clean_evidence_required=fail
clean_batch_review_required=fail
automation_gate_status=fail
automation_gate_failed_requirements=["clean_evidence", "clean_batch_review"]
```

然后根据 `automation_gate.status` 决定是否非零退出。

这对 CI 和截图很重要：失败日志不再只显示第一个失败原因，而是能完整暴露所有 gate 问题。

## Artifact 输出

位置：`src/minigpt/promoted_training_scale_seed_handoff_artifacts.py`

CSV 新增：

- `automation_gate_required`
- `automation_gate_status`
- `automation_gate_failed_requirements`
- `automation_gate_passed_requirements`
- `automation_gate_status_domain`

Markdown 新增：

- `Automation gate`
- detail
- failed requirements
- status domain

HTML 新增：

- `Automation gate`
- `Automation gate domain`

JSON 直接包含完整 `automation_gate` object。

这些输出是最终证据，不是临时调试日志。

## 测试覆盖

`tests/test_promoted_training_scale_seed_handoff.py` 增加或扩展了以下断言：

- public status domain 包含 automation gate 的 `not-required/pass/fail`。
- helper 能把未请求、单项失败、单项通过组合为正确总状态。
- 默认 handoff report 的 `automation_gate.status` 是 `not-required`。
- clean evidence strict pass 时，`automation_gate` 是 `pass`，passed list 包含 `clean_evidence`。
- clean batch-review strict pass 时，`automation_gate` 是 `pass`，passed list 包含 `clean_batch_review`。
- 两个 strict requirement 同时失败时，CLI stdout 同时包含两类 failure，并且 artifact 中 `failed_requirements` 是完整列表。

这组测试保护的是“严格自动化失败诊断完整性”。

## 运行证据

运行截图和解释归档在 `c/278`。

验证覆盖：

- seed handoff focused tests。
- promoted comparison/decision/seed/seed handoff 相关链路 tests。
- full unittest。
- source encoding hygiene。
- Playwright/Chrome 打开的 HTML artifact。

## 一句话总结

v278 把 promoted seed handoff 的多个 strict requirement 汇总成一个 `automation_gate`，让自动化失败既有总状态，也保留完整的逐项失败证据。
