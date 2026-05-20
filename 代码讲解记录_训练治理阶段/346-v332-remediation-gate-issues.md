# v332 remediation gate issues

## 本版目标和边界
v331 已经让 tiny scorecard comparison smoke 可以在严格模式下阻断 remaining remediation rows。v332 的目标是把这个阻断原因从单一文字说明升级为机器可读的 issue 列表，方便 CI、脚本和后续报告直接按 code、severity、owner scope 分类。

本版不做的事：
- 不改变 `--require-clean-remediation` 的默认行为
- 不改变 decision 的 promotion/review/blocked 规则
- 不改变 remediation plan 的生成和 CSV 输出
- 不把 gate issues 提升为新的模型质量判断

## 前置能力

本版沿用 v331 的 clean remediation gate：

```text
decision remediation_plan[]
  -> tiny smoke decision_summary
  -> remediation_gate
  -> remediation_gate.issues[]
```

## 关键文件

- `scripts/run_tiny_scorecard_comparison_smoke.py`
  - `remediation_gate_status()` 新增 `issue_count` 和 `issues`
  - `render_summary()` 新增 `remediation_gate_issue_count`
- `tests/test_tiny_scorecard_comparison_smoke.py`
  - 断言默认模式 `issues=[]`
  - 断言严格模式 issue 的 code、severity、category、action_code、owner_scope 和 count
- `README.md`
  - 去掉上一版重复的 v331 checkpoint
  - 增加 v332 checkpoint 和 tag 说明
- `d/332/`
  - 保存本版运行截图和解释

## 核心数据结构

新增 `remediation_gate.issues[]`：

```json
{
  "code": "remediation_rows_present",
  "severity": "blocker",
  "category": "threshold",
  "action_code": "raise_candidate_rubric_or_change_policy",
  "owner_scope": "model-eval",
  "count": 1
}
```

字段语义：
- `code`：稳定问题码，供 CI 分支判断
- `severity`：沿用首条 remediation metadata
- `category`：首条 remediation category
- `action_code`：建议动作编码
- `owner_scope`：建议处理责任域
- `count`：当前 remediation rows 数量

## 运行流程

```text
decision_summary()
  -> remediation_count
  -> remediation_gate_status()
  -> issue_count / issues[]
  -> render_summary()
```

当 gate 不阻断时，`issue_count=0` 且 `issues=[]`。
当 gate 阻断时，`issue_count=1`，第一条 issue 描述阻断 remediation 的主要分类。

## 测试覆盖

测试保护三件事：

1. 默认 smoke summary 仍然 `status=pass`
2. 默认 gate 不生成 issue rows
3. 严格 gate 失败时生成稳定 issue row

这些断言避免后续 CI 只能解析自然语言错误。

## 证据角色

`issues[]` 是 smoke gate 的执行证据，不是 decision report 的新事实来源。事实来源仍然是 decision JSON/CSV 和 remediation CSV；gate issue 只是为了让自动化更容易消费。

## 一句话总结
v332 把 clean remediation gate 的失败原因变成机器可读 issue row，让严格 tiny smoke 的 stop 更适合 CI 和后续自动化接入。
