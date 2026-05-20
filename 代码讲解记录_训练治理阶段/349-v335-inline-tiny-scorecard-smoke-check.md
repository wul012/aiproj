# v335 inline tiny scorecard smoke check

## 本版目标和边界
v334 新增了 standalone `check_tiny_scorecard_comparison_smoke.py`，可以读取已完成的 smoke summary 并生成验收 sidecar。v335 的目标是把这个 checker 接回 `run_tiny_scorecard_comparison_smoke.py`，让一次 smoke 命令可以在生成 summary 后立刻写出 summary-check JSON/text，并把检查结果嵌回主 summary。

本版不做的事：
- 不改变 tiny training、scorecard comparison 或 decision 的计算逻辑
- 不改变默认 smoke 行为；只有传入 `--summary-check-out-dir` 才运行 inline checker
- 不复制一份 checker 逻辑
- 不把 tiny smoke 解释为真实模型能力提升

## 前置能力

```text
v334 completed summary checker
  -> v335 inline smoke summary-check sidecars
```

## 关键文件

- `scripts/run_tiny_scorecard_comparison_smoke.py`
  - 新增 `--summary-check-out-dir`
  - 新增 `--summary-check-allow-gate-stop`
  - 新增 `--summary-check-no-fail`
  - 新增 `write_summary_and_optional_check()`
  - 在 text summary 中输出 `summary_check_*` 字段
- `scripts/check_tiny_scorecard_comparison_smoke.py`
  - 作为唯一 checker 实现来源被复用
- `tests/test_tiny_scorecard_comparison_smoke.py`
  - 覆盖 inline checker sidecar 写出
  - 覆盖真实 tiny smoke 带 `--summary-check-out-dir` 的端到端链路
- `README.md`
  - 更新当前版本、v335 checkpoint 和 tag 说明
- `d/335/`
  - 保存本版运行截图和解释

## 核心参数

```text
--summary-check-out-dir <dir>
```

请求 inline checker 写出：

```text
tiny_scorecard_comparison_smoke_check.json
tiny_scorecard_comparison_smoke_check.txt
```

```text
--summary-check-allow-gate-stop
```

沿用 standalone checker 的语义：当 strict remediation gate 的 stop 是预期验证目标时，可以把结构化 stop 当作检查通过。

```text
--summary-check-no-fail
```

写出 check sidecar，但不因为 checker 自身失败而让 smoke 命令退出非零。这个参数适合先收集诊断、不立刻阻断的过渡期。

## 输出结构

主 summary 新增：

```text
summary_check
summary_check_outputs
```

文本 summary 新增：

```text
summary_check_status
summary_check_decision
summary_check_issue_count
summary_check_allowed_gate_stop
summary_check_first_issue_code
summary_check_json
summary_check_text
```

这些字段是 checker 消费后的验收结果；原始 smoke summary 仍然保存 benchmark、decision、remediation gate 和 artifact status。

## 运行流程

```text
run tiny baseline smoke
  -> run tiny candidate smoke
  -> compare scorecards
  -> build decision
  -> write tiny_scorecard_comparison_smoke_summary.json/txt
  -> optional inline summary checker
  -> write check JSON/txt
  -> rewrite summary with embedded check result
```

`write_summary_and_optional_check()` 会先写一次主 summary，让 checker 拿到真实 summary path；随后写出 check sidecar，再把 `summary_check` 和 `summary_check_outputs` 嵌回主 summary 并重写。

## 测试覆盖

`tests/test_tiny_scorecard_comparison_smoke.py` 增加两类覆盖：

1. 直接调用 `write_summary_and_optional_check()`，验证 summary-check sidecar 能写出并嵌回主 summary
2. 跑真实 tiny scorecard comparison smoke，传入 `--summary-check-out-dir`，验证端到端命令输出、summary JSON/text 和 checker sidecar 一致

这些测试保护的是 inline 消费契约，不要求模型分数变好。

## 一句话总结
v335 把 v334 的 summary checker 接回 tiny scorecard comparison smoke，让“生成评估证据”和“立刻验收评估证据”可以由一个命令完成。
