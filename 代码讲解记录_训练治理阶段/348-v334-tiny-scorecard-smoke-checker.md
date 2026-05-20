# v334 tiny scorecard smoke checker

## 本版目标和边界
v331-v333 已经让 tiny scorecard comparison smoke 能生成 strict remediation gate，并把首条 gate issue 同时写入 JSON 与文本 summary。v334 的目标是补上下一层消费入口：给 CI 或人工复查一个独立 checker，用来读取已经完成的 smoke summary，确认它的命令状态、关键产物、remediation gate 和模型质量声明边界是否可信。

本版不做的事：
- 不重新训练 tiny model
- 不重新生成 benchmark scorecard 或 decision
- 不改变 `run_tiny_scorecard_comparison_smoke.py` 的输出结构
- 不把 tiny smoke 解释成真实模型能力提升

## 前置能力

```text
v331 clean remediation gate
  -> v332 remediation_gate.issues[]
  -> v333 first issue fields in text summary
  -> v334 completed summary checker
```

## 关键文件

- `scripts/check_tiny_scorecard_comparison_smoke.py`
  - 新增独立 CLI
  - 接收 smoke 输出目录或 `tiny_scorecard_comparison_smoke_summary.json`
  - 读取 summary 后生成 `tiny_scorecard_comparison_smoke_check.json`
  - 同步生成 line-oriented `tiny_scorecard_comparison_smoke_check.txt`
- `tests/test_tiny_scorecard_comparison_smoke_check.py`
  - 覆盖正常 pass summary
  - 覆盖 strict gate stop 默认失败
  - 覆盖 `--allow-gate-stop` 允许结构化 stop
  - 覆盖缺失 artifact 和错误模型质量声明
  - 覆盖 CLI 写出 check artifact
- `README.md`
  - 更新当前版本、成熟度说明、v334 checkpoint 和 tag 说明
- `d/334/`
  - 保存本版运行截图和解释

## 核心数据结构

checker 输出一个独立 report：

```text
schema_version
status
decision
summary_path
allow_gate_stop
allowed_gate_stop
smoke_status
smoke_decision
command_count
command_failure_count
remediation_gate_status
remediation_gate_decision
remediation_gate_issue_count
remediation_gate_first_issue_*
model_quality_claim
required_artifact_count
required_artifact_failure_count
decision_remediation_csv_exists
issue_count
issues[]
```

这里的 `issues[]` 是 checker 自己的诊断，不替代原 smoke summary 里的 `remediation_gate.issues[]`。原 summary 是事实来源，checker report 是消费后的验收结论。

## 关键函数

- `resolve_summary_path(path)`
  - 如果传入 JSON 文件，直接使用
  - 如果传入目录，则定位 `tiny_scorecard_comparison_smoke_summary.json`
  - 找不到时抛出 `FileNotFoundError`
- `check_summary(summary, allow_gate_stop=False)`
  - 校验 top-level `status`
  - 校验 `commands[]` 是否全部 pass
  - 校验 `remediation_gate` 是否存在且通过
  - 校验 `interpretation.model_quality_claim == "not_claimed"`
  - 校验 baseline/candidate/comparison/decision 的关键 artifact flags
  - 在 `allow_gate_stop=True` 时，把严格 remediation gate 的预期 stop 视为结构有效
- `render_check(report)`
  - 输出稳定 key/value 文本，适合 shell-only CI 读取
- `write_check_outputs(report, out_dir)`
  - 写出 JSON 和 text 两个 sidecar

## 输入输出流程

```text
tiny_scorecard_comparison_smoke_summary.json
  -> check_tiny_scorecard_comparison_smoke.py
  -> tiny_scorecard_comparison_smoke_check.json
  -> tiny_scorecard_comparison_smoke_check.txt
  -> CLI exit code
```

默认规则：summary 必须 pass、命令必须 pass、remediation gate 必须 pass、关键产物必须存在、模型质量声明必须保持 `not_claimed`。

如果 CI 专门在验证 strict gate 是否能阻断，可以加 `--allow-gate-stop`。这时 `status=fail + remediation_gate.decision=stop + commands pass` 会被视为结构有效，checker 输出 `decision=allowed-gate-stop`。

## 测试覆盖

`tests/test_tiny_scorecard_comparison_smoke_check.py` 覆盖了五个风险点：

1. 正常 summary 能输出 `status=pass` 和 `decision=continue`
2. 未允许的 strict gate stop 会被 checker 阻断
3. 显式 `allow_gate_stop` 后，结构化 stop 可以通过
4. 缺 artifact 或模型质量声明越界会产生 blocker issue
5. CLI 能从目录解析 summary 并写出 JSON/text check artifact

这些断言保护的是“产物消费契约”，不是模型分数本身。

## 证据链角色

v334 的新增 checker 位于 smoke 之后：

```text
run tiny scorecard comparison smoke
  -> produce summary
  -> check summary contract
  -> archive check result
```

它让后续 CI 不必每次重新训练，也能判断已有 tiny smoke evidence 是否完整、边界是否守住、严格 gate stop 是否属于预期。

## 一句话总结
v334 把 tiny scorecard comparison smoke 从“能生成 summary”推进到“summary 可以被独立验收”，让模型评估管线多了一层可复用的 CI 消费契约。
