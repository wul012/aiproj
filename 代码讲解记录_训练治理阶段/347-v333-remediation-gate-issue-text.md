# v333 remediation gate issue text

## 本版目标和边界
v332 已经在 `remediation_gate.issues[]` 中保存了机器可读 issue row，但 line-oriented text summary 只输出了 `remediation_gate_issue_count`。v333 的目标是让不解析 JSON 的 CI 或 shell 脚本，也能直接从 stdout / `.txt` summary 里读取首条 gate issue 的关键字段。

本版不做的事：
- 不改变 `remediation_gate.issues[]` JSON 结构
- 不改变 strict gate 的 stop 条件
- 不改变 benchmark scorecard decision 或 remediation plan 生成规则
- 不把文本 summary 当作新的事实来源

## 前置能力

```text
v331 clean remediation gate
  -> v332 remediation_gate.issues[]
  -> v333 first issue fields in text summary
```

## 关键文件

- `scripts/run_tiny_scorecard_comparison_smoke.py`
  - `render_summary()` 从 `remediation_gate.issues[]` 取首条 issue
  - 输出 `remediation_gate_first_issue_code`
  - 输出 `remediation_gate_first_issue_severity`
  - 输出 `remediation_gate_first_issue_category`
  - 输出 `remediation_gate_first_issue_action_code`
  - 输出 `remediation_gate_first_issue_owner_scope`
- `tests/test_tiny_scorecard_comparison_smoke.py`
  - 覆盖默认模式字段为 `None`
  - 覆盖 strict 模式字段为稳定 issue metadata
- `README.md`
  - 更新当前版本和 v333 checkpoint
- `d/333/`
  - 保存运行截图和解释

## 输入输出格式

输入仍然来自：

```text
summary["remediation_gate"]["issues"]
```

文本 summary 新增输出：

```text
remediation_gate_first_issue_code=remediation_rows_present
remediation_gate_first_issue_severity=blocker
remediation_gate_first_issue_category=threshold
remediation_gate_first_issue_action_code=raise_candidate_rubric_or_change_policy
remediation_gate_first_issue_owner_scope=model-eval
```

当没有 issue row 时，上述字段输出为 `None`。

## 流程说明

```text
remediation_gate.issues[]
  -> first issue
  -> render_summary()
  -> stdout / tiny_scorecard_comparison_smoke_summary.txt
```

这只是可读性和自动化消费层的增强，不改变 JSON report 的事实。

## 测试覆盖

测试关注两条链路：

1. 默认路径：`issue_count=0`，first issue fields 为 `None`
2. 严格失败路径：first issue fields 输出 stable code/severity/category/action/owner

这样可以防止以后只有 JSON 可读，而 stdout 失去 CI 分流能力。

## 一句话总结
v333 把 clean remediation gate 的首条 issue metadata 镜像到文本 summary，让 shell-only CI 也能直接识别严格 gate 为什么 stop。
