# v285 promoted seed handoff receipt check report

## 本版目标和边界

v285 的目标是把 v284 的 inline receipt-check 结果写回 promoted seed handoff 主报告。

v284 已经做到：

- 执行脚本可以用 `--receipt-check-out-dir` 校验刚生成的 automation receipt。
- 校验结果可以写成 sidecar JSON/text。
- stop 决策退出前也能先留下 check artifact。

但 v284 还有一个证据阅读上的断点：主 handoff JSON/CSV/Markdown/HTML 只知道 handoff、gate、summary 和 receipt 文件路径，receipt-check 的结构化结果在 sidecar 里。v285 解决这个断点，让主报告本身也能说明 receipt 是否通过校验。

本版不改变 receipt schema，不改变 automation decision，也不改变默认 CLI 行为。只有传入 `--receipt-check-out-dir` 时，主 handoff artifact 才会额外携带 `receipt_check` 和 `receipt_check_outputs`。

## 前置链路

相关前置版本：

- v281：写出 compact automation receipt JSON/text。
- v282：新增 receipt checker CLI。
- v283：checker 支持目录输入和 check artifact 输出。
- v284：执行脚本可 inline 运行 checker。
- v285：inline checker 的结果进入主 handoff report。

这版属于证据可读性和 CI 诊断闭环增强。

## 关键修改文件

### `scripts/execute_promoted_training_scale_seed.py`

v285 调整执行顺序：

```text
build handoff report
  -> if --receipt-check-out-dir:
       build in-memory receipt check
       attach report["receipt_check"]
  -> write handoff outputs
  -> write receipt JSON/text
  -> write receipt-check JSON/text from persisted receipt
  -> attach report["receipt_check_outputs"]
  -> rewrite handoff outputs with receipt-check fields
  -> print diagnostics
  -> exit from automation_summary
```

这里有一个故意的两阶段写入：

1. 第一次写出 handoff outputs，目的是生成真实 receipt JSON。
2. 再读取真实 receipt JSON 做 check，并写出 receipt-check sidecar。
3. 第二次写出 handoff outputs，目的是把 check 结果写回主 JSON/CSV/Markdown/HTML。

这样主报告和 sidecar 都基于同一份落盘 receipt，而不是只基于内存对象。

### `src/minigpt/promoted_training_scale_seed_handoff_artifacts.py`

新增三个小 helper：

```python
def _receipt_check(report: dict[str, Any]) -> dict[str, Any]
def _receipt_check_outputs(report: dict[str, Any]) -> dict[str, Any]
def _receipt_check_fields(report: dict[str, Any]) -> dict[str, Any]
```

它们只负责从 report 中读取 receipt-check 相关字段，并转成 CSV/Markdown/HTML 可消费的结构。

新增/扩展输出：

- JSON：直接保留 `receipt_check` 和 `receipt_check_outputs`。
- CSV：新增 `receipt_check_status`、`receipt_check_decision`、`receipt_check_exit_code`、`receipt_check_blocking_source`、`receipt_check_json`、`receipt_check_text` 等列。
- Markdown：新增 receipt-check 状态、decision、exit code、blocking source、failed requirements 和 sidecar 路径。
- HTML：新增 `Receipt Check` section，并在顶部 stats 中显示关键结果。

## 输入输出格式

执行命令示例：

```powershell
python scripts/execute_promoted_training_scale_seed.py runs/training-scale-workflow/promoted-seed --execute --out-dir runs/training-scale-workflow/promoted-seed-handoff --receipt-check-out-dir runs/training-scale-workflow/promoted-seed-handoff/receipt-check
```

主 JSON 新增：

```json
{
  "receipt_check": {
    "status": "pass",
    "decision": "continue",
    "exit_code": 0,
    "checker_exit_code": 0,
    "blocking_source": null,
    "failed_requirements": [],
    "issue_count": 0,
    "issues": [],
    "receipt_path": "..."
  },
  "receipt_check_outputs": {
    "json": ".../promoted_training_scale_seed_handoff_automation_receipt_check.json",
    "text": ".../promoted_training_scale_seed_handoff_automation_receipt_check.txt"
  }
}
```

这两个字段只在用户显式请求 receipt-check 输出时出现。

## 测试覆盖

位置：`tests/test_promoted_training_scale_seed_handoff_receipt.py`

v285 扩展了 v284 的两个执行链路测试：

- continue 场景断言主 handoff JSON 带有 `receipt_check.status == "pass"` 和 `receipt_check.decision == "continue"`。
- stop 场景断言主 handoff JSON 带有 `receipt_check.decision == "stop"`、`blocking_source == "automation_gate"`。
- CSV 断言包含 receipt-check 列。
- Markdown 断言包含 `Receipt check status`。
- HTML 断言包含 `Receipt Check` section。

这些测试保护的是“sidecar 和主 artifact 同步可读”。

## 运行证据

运行截图和解释归档在 `c/285`。

本版验证包括：

- receipt focused tests。
- promoted seed handoff tests。
- promoted chain related tests。
- full unittest。
- source encoding hygiene。
- inline receipt-check report smoke。
- Playwright/Chrome handoff HTML 截图。
- 文档一致性检查。

## 一句话总结

v285 让 promoted seed handoff 主报告也能携带 receipt-check 诊断结果，减少 CI sidecar 和人工阅读之间的证据断点。
