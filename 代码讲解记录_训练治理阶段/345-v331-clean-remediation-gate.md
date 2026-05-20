# v331 clean remediation gate

## 本版目标和边界
v330 已经把 `remediation_plan` 单独导出成 CSV artifact，但这仍然只是“可消费的证据”。v331 的目标不是继续扩展评分逻辑，而是给 tiny scorecard comparison smoke 增加一个可选的 clean remediation gate，让严格模式可以在 remediation rows 还存在时直接 stop。

本版不做的事：
- 不改 decision 规则本身
- 不改 remediation plan 内容和排序
- 不改 scorecard comparison 的评分语义
- 不把 gate 设成默认阻断，默认仍保持原链路可通过

## 前置能力
本版基于：
- v327 remediation plan
- v328 remediation summary
- v329 remediation metadata
- v330 remediation CSV artifact

换句话说，v331 不是新的治理层，而是把已有 remediation 证据接到 smoke gate 上。

## 关键文件

- `scripts/run_tiny_scorecard_comparison_smoke.py`
  - 新增 `--require-clean-remediation`
  - `build_run_config()` 保存该开关
  - `build_summary()` 计算 `remediation_gate`
  - `render_summary()` 输出 gate 状态和首条 remediation metadata
- `tests/test_tiny_scorecard_comparison_smoke.py`
  - 覆盖默认模式、严格模式、summary 注入、真实 tiny smoke 路径
  - 保证 gate 不会误伤默认链路，也能在需要时 stop
- `README.md`
  - 更新当前版本说明
  - 把 v331 放进版本和成熟度叙述
- `d/331/`
  - 保存运行截图和解释，作为本版证据

## 核心数据结构

### `run_config`
新增字段：
- `require_clean_remediation: bool`

语义：
- `False`：remediation 只作为建议证据，不阻断 smoke
- `True`：如果 decision 里还有 remediation rows，smoke 进入 fail

### `remediation_gate`
这是本版新增的顶层摘要字段，包含：
- `required`
- `status`
- `decision`
- `remediation_count`
- `first_category`
- `first_action_code`
- `first_severity`
- `first_owner_scope`
- `reason`

它不是新的决策器，只是把 decision 里的 remediation_count 和首条 metadata 变成可读的 gate 状态。

## 运行流程

```text
tiny baseline smoke
  -> tiny candidate smoke
  -> scorecard comparison
  -> scorecard decision
  -> remediation plan
  -> remediation gate (optional)
  -> top-level smoke summary
```

当 `--require-clean-remediation` 未开启时，gate 总是 `continue`。
当该开关开启且 remediation_count > 0 时，gate 返回 `stop`，summary 进入 fail。

## 测试覆盖

本版测试覆盖了三层：

1. `build_run_config()` 能保留 `require_clean_remediation`
2. `remediation_gate_status()` 在 required + remediation rows 时会 stop
3. `build_summary()` 会把 gate 失败折叠进顶层 smoke 状态
4. 真实 tiny scorecard comparison smoke 仍能跑通默认链路

关键断言保护的是：
- 默认模式不被新 gate 误伤
- 严格模式真的会阻断带 remediation 的结果
- 顶层 summary 能把 gate 状态写出来，便于 CI 直接读

## 证据角色

- `benchmark_scorecard_decision_remediation.csv` 仍然是原始 remediation 证据
- `remediation_gate` 是 smoke 层的执行判断，不是新的模型判断
- `d/331` 记录的是这个 gate 的运行证据

## 一句话总结
v331 把 remediation 从“可导出证据”推进成“可选执行门禁”，让 tiny smoke 在严格模式下能真正拦住未清理的决策残留。
