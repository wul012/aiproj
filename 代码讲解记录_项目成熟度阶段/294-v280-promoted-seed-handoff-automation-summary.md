# v280 promoted seed handoff automation summary

## 本版目标和边界

v280 的目标是给 promoted seed handoff 增加一个最终自动化出口：`automation_summary`。

v278 建立了 `automation_gate`，v279 又让 gate 具备 `decision`、`exit_code` 和 requirement count。但 gate 只处理 strict requirement。如果计划命令执行失败、seed 被阻塞、或者命令超时，调用方仍然要同时读取：

```text
automation_gate
summary.handoff_status
execution
```

v280 把这些信息合成一个顶层 summary，让 CI、脚本或后续 orchestration 只读一个对象就能知道最终是否继续。

本版不新增用户开关，不改变 plan command 生成逻辑，不改变 clean-evidence 或 clean batch-review 的单项判断规则。它只新增最终自动化摘要。

## 前置链路

相关前置版本：

- v277：promoted seed handoff 有 clean batch-review strict requirement。
- v278：多个 strict requirement 聚合为 `automation_gate`。
- v279：`automation_gate` 增加 decision、exit code 和 requirement counts。
- v280：新增 `automation_summary`，把 gate blocker 和 handoff execution blocker 合成最终决策。

这版属于自动化契约收口，不是模型能力增强。

## 核心数据结构

位置：`src/minigpt/promoted_training_scale_seed_handoff_review.py`

### `SeedHandoffAutomationSummary`

字段：

- `decision`
  - `continue` 或 `stop`。
- `exit_code`
  - `continue` 为 `0`，`stop` 为 `1` 或 gate 提供的 exit code。
- `blocking_source`
  - `automation_gate`
  - `handoff_execution`
  - `None`
- `handoff_status`
  - 来自 report summary 的 handoff 状态。
- `gate_status`
  - 来自 `automation_gate.status`。
- `gate_decision`
  - 来自 `automation_gate.decision`。
- `gate_required`
  - 是否请求了 strict requirement。
- `gate_blocking_requirement_count`
  - gate 层阻塞 requirement 数。
- `failed_requirements`
  - gate 层失败 requirement 名称。
- `detail`
  - 给人读的最终说明。
- `decision_domain`
  - 稳定公开枚举。

公开枚举：

```python
("continue", "stop")
```

## 核心函数

### `build_seed_handoff_automation_summary(summary, automation_gate)`

输入：

- seed handoff report summary
- 已生成的 `automation_gate`

决策顺序：

```text
if automation_gate.decision == "stop":
    decision = "stop"
    blocking_source = "automation_gate"
    exit_code = automation_gate.exit_code or 1

elif handoff_status in {"blocked", "failed", "timeout"}:
    decision = "stop"
    blocking_source = "handoff_execution"
    exit_code = 1

else:
    decision = "continue"
    blocking_source = None
    exit_code = 0
```

这说明 gate blocker 优先，因为 strict requirement 是用户显式请求的自动化门禁；如果 gate 没阻塞，再看 handoff 执行状态。

## Builder 输出

位置：`src/minigpt/promoted_training_scale_seed_handoff.py`

report 顶层新增：

```text
automation_summary
```

示例：

```json
{
  "decision": "stop",
  "exit_code": 1,
  "blocking_source": "automation_gate",
  "handoff_status": "planned",
  "gate_status": "fail",
  "gate_decision": "stop",
  "gate_required": true,
  "gate_blocking_requirement_count": 2,
  "failed_requirements": ["clean_evidence", "clean_batch_review"]
}
```

这个对象是最终自动化证据，不是临时调试输出。

## CLI 行为

位置：`scripts/execute_promoted_training_scale_seed.py`

CLI 现在总会输出：

```text
automation_summary_decision=...
automation_summary_exit_code=...
automation_summary_blocking_source=...
automation_summary_gate_decision=...
automation_summary_failed_requirements=[...]
automation_summary_detail=...
```

最终退出逻辑改为：

```text
if automation_summary.decision == "stop":
    exit automation_summary.exit_code
```

这比之前更清晰：strict gate 失败、plan command 失败、seed 被 blocked，都会进入同一个最终出口。

## Artifact 输出

位置：`src/minigpt/promoted_training_scale_seed_handoff_artifacts.py`

CSV 新增：

- `automation_summary_decision`
- `automation_summary_exit_code`
- `automation_summary_blocking_source`
- `automation_summary_gate_decision`
- `automation_summary_gate_blocking_requirement_count`
- `automation_summary_failed_requirements`
- `automation_summary_decision_domain`

Markdown 新增：

- `Automation summary decision`
- `Automation summary exit code`
- `Automation summary blocking source`
- `Automation summary failed requirements`
- `Automation summary decision domain`

HTML 新增：

- `Automation summary`
- `Automation summary exit`
- `Automation blocking source`
- `Automation summary domain`

JSON 直接包含完整 `automation_summary` object。

## 测试覆盖

`tests/test_promoted_training_scale_seed_handoff.py` 覆盖：

- public summary decision domain 是 `continue/stop`。
- gate 通过且 handoff completed 时 summary 是 `continue`。
- gate 失败时 summary 是 `stop`，blocking source 是 `automation_gate`。
- gate 通过但 handoff failed 时 summary 是 `stop`，blocking source 是 `handoff_execution`。
- CLI stdout 总是包含 summary decision、exit code、blocking source。
- CSV、Markdown、HTML 都包含 automation summary 字段。

这组测试保护的是最终自动化出口一致性。

## 运行证据

运行截图和解释归档在 `c/280`。

验证覆盖：

- seed handoff focused tests。
- promoted comparison/decision/seed/seed handoff 相关链路 tests。
- full unittest。
- source encoding hygiene。
- smoke artifact。
- Playwright/Chrome HTML 截图。

## 一句话总结

v280 把 promoted seed handoff 的 gate 结果和 handoff 执行状态收束成 `automation_summary`，让后续自动化有一个稳定、统一、可解释的最终退出契约。
