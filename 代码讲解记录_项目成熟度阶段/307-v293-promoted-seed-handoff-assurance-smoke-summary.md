# v293 promoted seed handoff assurance smoke summary

## 本版目标和边界

v293 的目标是让 v292 新增的 promoted seed handoff assurance CI smoke 写出顶层 summary artifacts。

v292 已经把 smoke 接进 GitHub Actions，但复盘时主要依赖 stdout。v293 让 smoke 目录自己包含一个机器可读 JSON 和一个人眼友好的 key/value 文本，这样 CI 失败、人工查看或后续治理工具接入时，不需要从长日志里抓字段。

本版不改变 GitHub Actions 步骤，不改变 handoff schema，不改变 assurance checker 的判断规则，也不改变模型训练和评估逻辑。

## 前置链路

相关前置版本：

- v281-v285：automation receipt 与 inline receipt-check。
- v286-v289：embedded receipt-check 与 sidecar integrity。
- v290-v291：目录级 assurance checker 与 inline assurance。
- v292：GitHub Actions 中新增 assurance smoke。
- v293：smoke 自身写出 summary JSON/text。

这版属于“让 CI smoke 证据更容易被读取和归档”。

## 关键修改文件

### `scripts/check_promoted_seed_handoff_assurance_smoke.py`

新增常量：

```python
SMOKE_SUMMARY_JSON_FILENAME = "promoted_seed_handoff_assurance_smoke_summary.json"
SMOKE_SUMMARY_TEXT_FILENAME = "promoted_seed_handoff_assurance_smoke_summary.txt"
```

新增 summary 构建与输出函数：

```python
_build_smoke_summary(...)
_render_smoke_summary(...)
write_smoke_summary_outputs(...)
_print_smoke_summary(...)
```

成功路径会在检查完 handoff assurance 后写出 summary。

失败路径也会在 handoff 执行命令返回非零时先写出 summary，然后再退出。这一点很重要：CI 失败时仍有结构化证据可查。

summary JSON 的核心字段：

```json
{
  "schema_version": 1,
  "status": "pass",
  "decision": "continue",
  "issue_count": 0,
  "issues": [],
  "execute_returncode": 0,
  "seed": "runs/.../promoted_training_scale_seed.json",
  "handoff_report": "runs/.../promoted_training_scale_seed_handoff.json",
  "handoff_report_exists": true,
  "directories": {
    "handoff": "runs/.../handoff",
    "receipt_check": "runs/.../receipt-check",
    "embedded_receipt_check": "runs/.../embedded-receipt-check",
    "assurance": "runs/.../assurance"
  },
  "logs": {
    "stdout": "runs/.../execute_stdout.txt",
    "stderr": "runs/.../execute_stderr.txt"
  },
  "checks": {
    "handoff_assurance_status": "pass",
    "handoff_assurance_embedded_receipt_check_sidecar_status": "pass"
  },
  "outputs": {
    "summary_json": "runs/.../promoted_seed_handoff_assurance_smoke_summary.json",
    "summary_text": "runs/.../promoted_seed_handoff_assurance_smoke_summary.txt"
  }
}
```

stdout 仍保留旧字段：

```text
status=pass
decision=continue
seed=...
handoff_report=...
handoff_assurance_status=pass
```

同时新增：

```text
summary_json=...
summary_text=...
```

这保证旧读者不受影响，新读者可以直接定位 summary artifact。

### `tests/test_promoted_training_scale_seed_handoff_receipt.py`

增强测试：

```python
test_handoff_assurance_smoke_script_passes
```

新增断言：

- summary JSON 存在。
- summary text 存在。
- JSON 中 `status == pass`。
- JSON 中 `decision == continue`。
- JSON 中 `checks.handoff_assurance_status == pass`。
- text 中包含 `smoke_status=pass`。
- stdout 中包含 `summary_json=` 和 `summary_text=`。

测试保护的是 smoke 入口的外部契约，而不是内部 helper 的实现细节。

## 输入输出格式

本地命令不变：

```powershell
python scripts/check_promoted_seed_handoff_assurance_smoke.py --out-dir runs/promoted-seed-handoff-assurance-smoke
```

新增输出：

```text
runs/promoted-seed-handoff-assurance-smoke/
  promoted_seed_handoff_assurance_smoke_summary.json
  promoted_seed_handoff_assurance_smoke_summary.txt
```

这两个文件是本版新增的顶层 smoke 证据。

## 测试覆盖

本版验证包括：

- smoke 脚本 py_compile。
- smoke 脚本真实执行，并检查 summary JSON/text。
- focused receipt/embedded/assurance 测试。
- handoff 主链路测试。
- promoted comparison、decision、seed、handoff、receipt 相关链路测试。
- full unittest。
- source encoding hygiene。
- coverage gate。

## 运行证据

运行截图和解释归档在 `c/293`。

关键截图：

- `01-assurance-smoke.png`
- `02-smoke-summary-json.png`
- `03-smoke-summary-text.png`
- `04-focused-receipt-tests.png`
- `05-handoff-tests.png`
- `06-related-chain-tests.png`
- `07-full-unittest.png`
- `08-source-encoding.png`
- `09-coverage-gate.png`
- `10-docs-check.png`

## 一句话总结

v293 让 promoted seed handoff assurance smoke 从“CI 日志里可见”推进为“有顶层 summary artifact 可直接消费”。
