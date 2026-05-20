# v288 promoted seed handoff inline embedded receipt check

## 本版目标和边界

v288 的目标是让 promoted seed handoff 执行脚本直接运行 embedded receipt-check sidecar integrity 验证，并把结果作为一等证据保存下来。

v287 已经做到：

- embedded receipt-check 会打开并比较 receipt JSON、check JSON、check text sidecar。
- CLI 可以独立发现 missing/tampered sidecar。

但 v287 仍需要用户再单独跑一次 embedded checker。v288 把这一步接回 `execute_promoted_training_scale_seed.py`，让执行脚本在生成主报告和 receipt-check 之后可选直接产出 embedded sidecar integrity 证据。

本版不改变 receipt schema，不改变默认执行行为，不改变 automation decision，也不把治理证据说成模型能力提升。

## 前置链路

相关前置版本：

- v281：写出 compact automation receipt JSON/text。
- v282：新增 receipt checker CLI。
- v283：checker 支持目录输入和 check artifact 输出。
- v284：执行脚本可 inline 运行 checker。
- v285：inline checker 的结果进入主 handoff report。
- v286：主 handoff report 内嵌 checker 结果可被独立复核。
- v287：主报告引用的 receipt/check sidecar 文件也被校验。
- v288：执行脚本可 inline 运行 embedded receipt-check sidecar integrity 验证。

这版属于证据链归档效率增强。

## 关键修改文件

### `scripts/execute_promoted_training_scale_seed.py`

新增参数：

```python
--embedded-receipt-check-out-dir
```

语义：

- 只有显式传入 `--embedded-receipt-check-out-dir` 时才运行 embedded checker。
- 这个参数依赖 `--receipt-check-out-dir`，因为 embedded checker 要验证 receipt/check sidecar。
- 如果 receipt-check 未启用，embedded checker 不能单独运行。

执行顺序变成：

```text
build handoff report
  -> optional receipt check
  -> write handoff outputs
  -> optional receipt-check outputs
  -> optional embedded receipt-check sidecar outputs
  -> print diagnostics
  -> exit from automation_summary / receipt / embedded check
```

新增两个 helper：

```python
_write_embedded_receipt_check_outputs(...)
_print_embedded_receipt_check(...)
```

`_write_embedded_receipt_check_outputs()` 会：

- 重新载入主 handoff JSON。
- 调用 `check_promoted_training_scale_seed_handoff_embedded_receipt_check(..., base_dir=report_path.parent)`。
- 把结果写成 `promoted_training_scale_seed_handoff_embedded_receipt_check.json` 和 `.txt`。

`_print_embedded_receipt_check()` 会把校验结果打印成稳定 key/value 格式，便于 shell/CI 读取。

### `src/minigpt/promoted_training_scale_seed_handoff_receipt.py`

v288 复用了 v287 的 embedded checker，不改校验 contract，只把它接回执行脚本。

### `tests/test_promoted_training_scale_seed_handoff_receipt.py`

新增三类执行入口测试：

- continue 场景：确认 embedded check JSON/text 被写出。
- stop 场景：确认 embedded check 在 stop 前也会写出。
- 参数错误场景：确认没有 `--receipt-check-out-dir` 时，`--embedded-receipt-check-out-dir` 会明确失败。

这些测试保护的是“一条执行命令能同时完成 handoff、receipt-check 和 embedded sidecar integrity 归档”。

## 输入输出格式

新增命令：

```powershell
python scripts/execute_promoted_training_scale_seed.py runs/training-scale-workflow/promoted-seed --execute --out-dir runs/training-scale-workflow/promoted-seed-handoff --receipt-check-out-dir runs/training-scale-workflow/promoted-seed-handoff/receipt-check --embedded-receipt-check-out-dir runs/training-scale-workflow/promoted-seed-handoff/embedded-receipt-check
```

新增嵌入证据：

```json
{
  "status": "pass",
  "sidecar_status": "pass",
  "receipt_path_exists": true,
  "receipt_check_json_exists": true,
  "receipt_check_text_exists": true,
  "issue_count": 0,
  "issues": []
}
```

这份输出仍然是验证证据，不是新的 handoff 决策源。

## 测试覆盖

本版验证包括：

- `tests.test_promoted_training_scale_seed_handoff_receipt`
- `tests.test_promoted_training_scale_seed_handoff`
- promoted comparison / decision / seed / handoff / receipt 相关链路测试
- full unittest
- source encoding hygiene
- inline embedded receipt-check smoke
- Playwright/Chrome HTML 渲染截图
- 文档一致性检查

## 运行证据

运行截图和解释归档在 `c/288`。

关键截图：

- `01-focused-tests.png`
- `02-handoff-tests.png`
- `03-related-chain-tests.png`
- `04-full-unittest.png`
- `05-source-encoding.png`
- `06-inline-embedded-receipt-check-smoke.png`
- `07-promoted-seed-handoff-html.png`
- `08-docs-check.png`

## 一句话总结

v288 把 promoted seed handoff 的 receipt-check 证据推进到“一条执行命令即可归档主报告、receipt-check 和 embedded sidecar integrity 校验”。
