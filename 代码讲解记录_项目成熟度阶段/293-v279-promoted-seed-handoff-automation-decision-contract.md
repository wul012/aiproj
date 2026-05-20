# v279 promoted seed handoff automation decision contract

## 本版目标和边界

v279 的目标是把 v278 新增的 `automation_gate` 从状态摘要推进为自动化决策契约。

v278 已经解决了一个重要问题：当 `--require-clean-evidence` 和 `--require-clean-batch-review` 同时启用时，CLI 会先打印两个 requirement 的诊断，再由 `automation_gate` 给出总状态。v279 继续补上自动化调用方最需要的字段：

- `decision`
- `exit_code`
- requirement count
- blocking count
- `decision_domain`

本版不新增第三个 strict requirement，不新增 CLI 开关，也不改变默认非 strict handoff 行为。它的边界是“让已经存在的 gate 更容易被脚本/CI/上游编排消费”。

## 前置链路

相关前置版本：

- v216-v219：建立 clean-evidence requirement 和可复用 library contract。
- v277：建立 clean batch-review requirement。
- v278：把 clean-evidence 和 clean batch-review 聚合为 `automation_gate`。
- v279：给 `automation_gate` 增加可执行决策字段。

这版属于自动化契约增强，不是模型能力增强，也不是训练计划的策略变化。

## 核心数据结构

位置：`src/minigpt/promoted_training_scale_seed_handoff_review.py`

### `SeedHandoffAutomationGateDecision`

新增公开枚举：

```python
("not-requested", "continue", "stop")
```

字段含义：

- `not-requested`
  - 没有 strict requirement 被请求。
- `continue`
  - 至少一个 strict requirement 被请求，且全部通过。
- `stop`
  - 至少一个 strict requirement 被请求，且存在失败项。

### `SeedHandoffAutomationGate`

v279 后的 gate 既保留旧字段，也增加自动化消费字段：

- `required`
  - 是否至少请求了一个 strict requirement。
- `status`
  - 兼容 v278 的状态：`not-required/pass/fail`。
- `decision`
  - 给脚本和 CI 直接消费的动作建议：`not-requested/continue/stop`。
- `exit_code`
  - 当 decision 是 `stop` 时为 `1`，否则为 `0`。
- `required_requirement_count`
  - 被请求的 requirement 数。
- `passed_requirement_count`
  - 已通过的 requirement 数。
- `failed_requirement_count`
  - 失败的 requirement 数。
- `blocking_requirement_count`
  - 当前等于 failed count，用于表达阻塞自动化的 requirement 数。
- `failed_requirements`
  - 失败 requirement 名称列表。
- `passed_requirements`
  - 通过 requirement 名称列表。
- `status_domain`
  - status 的公开枚举。
- `decision_domain`
  - decision 的公开枚举。

## 核心函数

### `build_seed_handoff_automation_gate(...)`

函数仍然只消费两个已计算好的 requirement：

```text
clean_evidence_requirement
clean_batch_review_requirement
```

它不会重新判断 clean-evidence 或 clean batch-review 的业务规则。这样做的好处是 gate 只负责聚合，单项 requirement 仍然由各自 helper 负责。

v279 的决策映射：

```text
没有 requested requirement:
    status = not-required
    decision = not-requested
    exit_code = 0

有 requested requirement 且存在 fail:
    status = fail
    decision = stop
    exit_code = 1

有 requested requirement 且全部 pass:
    status = pass
    decision = continue
    exit_code = 0
```

## Builder 输出

位置：`src/minigpt/promoted_training_scale_seed_handoff.py`

report 顶层仍然写入：

```text
automation_gate
```

示例：

```json
{
  "status": "fail",
  "decision": "stop",
  "exit_code": 1,
  "required_requirement_count": 2,
  "passed_requirement_count": 0,
  "failed_requirement_count": 2,
  "blocking_requirement_count": 2,
  "failed_requirements": ["clean_evidence", "clean_batch_review"],
  "decision_domain": ["not-requested", "continue", "stop"]
}
```

这个对象是最终证据，不是临时日志。后续上游如果只想知道是否继续，可以读取 `decision`；如果想给 CI 退出码，可以读取 `exit_code`；如果想展示阻塞项，可以读取 `failed_requirements` 和 `blocking_requirement_count`。

## CLI 行为

位置：`scripts/execute_promoted_training_scale_seed.py`

strict 模式会打印新增字段：

```text
automation_gate_decision=stop
automation_gate_exit_code=1
automation_gate_required_requirement_count=2
automation_gate_failed_requirement_count=2
automation_gate_blocking_requirement_count=2
```

v279 后，CLI 退出逻辑从：

```text
status == fail
```

调整为：

```text
decision == stop
exit with exit_code
```

这样做让脚本行为和 JSON contract 保持一致。旧字段 `status` 继续保留，所以已有读者不会被迫迁移。

## Artifact 输出

位置：`src/minigpt/promoted_training_scale_seed_handoff_artifacts.py`

CSV 新增：

- `automation_gate_decision`
- `automation_gate_exit_code`
- `automation_gate_required_requirement_count`
- `automation_gate_passed_requirement_count`
- `automation_gate_failed_requirement_count`
- `automation_gate_blocking_requirement_count`
- `automation_gate_decision_domain`

Markdown 新增：

- `Automation gate decision`
- `Automation gate exit code`
- `Automation gate required count`
- `Automation gate blocking count`
- `Automation gate decision domain`

HTML 新增：

- `Automation decision`
- `Automation exit`
- `Automation required`
- `Automation blocking`
- `Automation decision domain`

JSON 直接包含完整 `automation_gate` object。

## 测试覆盖

`tests/test_promoted_training_scale_seed_handoff.py` 覆盖了：

- public decision domain 是 `not-requested/continue/stop`。
- 无 strict requirement 时，decision 是 `not-requested`，exit code 是 `0`。
- 单项通过时，decision 是 `continue`。
- 单项失败时，decision 是 `stop`，exit code 是 `1`。
- 两个 strict requirement 同时失败时，required/failed/blocking count 都是 `2`。
- CLI stdout 包含 decision、exit code、requirement count。
- CSV、Markdown、HTML 都包含新增决策字段。

这组测试保护的是“自动化读取字段稳定性”，不是模型质量。

## 运行证据

运行截图和解释归档在 `c/279`。

验证覆盖：

- seed handoff focused tests。
- promoted comparison/decision/seed/seed handoff 相关链路 tests。
- full unittest。
- source encoding hygiene。
- Playwright/Chrome 打开的 HTML artifact。
- 文档结构检查。

## 一句话总结

v279 把 promoted seed handoff 的 `automation_gate` 变成带 decision、exit code 和 requirement counts 的稳定自动化契约，让后续 CI 和脚本可以直接消费，而不用重新推导 gate 状态。
