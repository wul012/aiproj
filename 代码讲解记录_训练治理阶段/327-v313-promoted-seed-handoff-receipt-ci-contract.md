# v313 promoted seed handoff receipt CI contract

## 本版目标和边界

v312 已经把 promoted seed handoff 的 CI 回归上下文写入 summary、CLI、HTML/Markdown/CSV 和 automation receipt。v313 继续收口一个更细但很关键的契约问题：receipt checker 之前只校验 `decision`、`exit_code`、`blocking_source`、`failed_requirements` 等通用自动化字段，没有把新增的 CI regression 字段纳入 integrity check。结果是 receipt sidecar 即使丢了 `handoff_batch_maturity_ci_regression_count` 或被篡改，也可能仍然通过结构检查。

本版只升级 promoted seed handoff automation receipt 的校验契约，不改变 handoff 执行命令、clean-evidence gate、clean-batch gate、assurance 入口和训练计划生成行为。为了兼容旧测试和旧最小 receipt，v313 采用 schema 分层：v1 receipt 保持旧通用契约，schema v2 receipt 强制要求 CI regression 字段。

## 前置能力

本版直接承接 v312：

- v312 handoff report 已经写出 selected、aggregate、comparison-ready CI regression context。
- v312 automation receipt 已经包含 `selected_handoff_batch_maturity_ci_regression_count`、`handoff_batch_maturity_ci_regression_count`、`comparison_exclusion_reasons`。

v313 的目标是让这些字段从“写出来”升级为“校验必须存在且 sidecar 必须一致”。

## 关键文件

- `src/minigpt/promoted_training_scale_seed_handoff_artifacts.py`
  - `build_promoted_training_scale_seed_handoff_automation_receipt()` 将 `schema_version` 从 1 升到 2。
  - v2 receipt 继续包含 v312 新增的 selected/aggregate CI regression counters 和 comparison exclusion reasons。

- `src/minigpt/promoted_training_scale_seed_handoff_receipt.py`
  - 新增 `RECEIPT_SCHEMA_V2_REQUIRED_FIELDS`，列出 v2 receipt 必须包含的 CI regression 字段。
  - `check_promoted_training_scale_seed_handoff_automation_receipt()` 对 schema v2 执行字段存在性、非负计数和 list 类型校验。
  - check payload 自身也输出 `selected_handoff_batch_maturity_ci_regression_count`、`handoff_batch_maturity_ci_regression_count`、`comparison_exclusion_reasons`。
  - `EMBEDDED_RECEIPT_CHECK_COMPARE_KEYS` 纳入这些新字段，所以 embedded receipt check 会比较主报告重建出来的 expected check、内嵌 check、receipt JSON sidecar 和 check JSON/text sidecar。

- `tests/test_promoted_training_scale_seed_handoff_receipt.py`
  - 新增 v2 missing-field rejection 测试。
  - 扩展 generated receipt/check payload 断言，确认 schema v2 字段存在并被渲染。
  - 新增 receipt sidecar tamper 测试：把 receipt JSON 里的 `handoff_batch_maturity_ci_regression_count` 篡改为 0，embedded check 必须失败。

## 输入输出语义

输入仍然是 promoted seed handoff report：

```text
promoted_training_scale_seed_handoff.json
```

automation receipt 是轻量自动化交接件：

```text
promoted_training_scale_seed_handoff_automation_receipt.json
promoted_training_scale_seed_handoff_automation_receipt.txt
```

v313 以后，schema v2 receipt 至少要带：

```text
selected_handoff_batch_maturity_ci_regression_count
handoff_batch_maturity_ci_regression_count
comparison_exclusion_reasons
```

checker 输出会把这些字段写入：

```text
promoted_training_scale_seed_handoff_automation_receipt_check.json
promoted_training_scale_seed_handoff_automation_receipt_check.txt
```

embedded receipt check 会继续比较主报告、receipt sidecar、check JSON sidecar 和 check text sidecar。v313 的变化是比较集合里加入 CI regression 字段，sidecar 少字段或被篡改都会成为 `status=fail`。

## 契约设计

v313 没有直接让所有旧 receipt 失败，而是用 `schema_version` 进行分层：

- `schema_version=1`：保留旧的通用 automation decision contract。
- `schema_version=2`：在旧契约基础上强制要求 CI regression 字段。

这样既不破坏历史最小 receipt 测试，也让当前 handoff 产物获得更严格的证据完整性。

## 测试覆盖

本版主要测试包括：

- `test_receipt_checker_requires_v2_ci_regression_contract_fields`
  - schema v2 缺少 CI 字段时必须失败。
  - 带完整 CI 字段时通过，并在 text diagnostics 中渲染计数。

- `test_script_checks_generated_receipt`
  - 当前生成的 receipt 必须是 `schema_version=2`。
  - check payload 中 selected/aggregate CI counters 和 exclusion reasons 必须存在。

- `test_execute_script_can_write_receipt_check_outputs`
  - inline receipt check 输出 JSON/text 时，也必须携带 CI regression check fields。

- `test_embedded_receipt_check_rejects_tampered_receipt_ci_regression_sidecar`
  - receipt sidecar 中的 CI count 被篡改后，embedded receipt check 必须 fail，并指出 sidecar 字段不一致。

## 运行证据

运行截图和解释归档在 `d/313`：

- `d/313/图片/01-receipt-tests.png`
- `d/313/图片/02-chain-tests.png`
- `d/313/图片/03-py-compile.png`
- `d/313/图片/04-source-encoding.png`
- `d/313/图片/05-full-unittest.png`
- `d/313/图片/06-static-scan.png`
- `d/313/解释/说明.md`

这些证据分别证明 receipt focused tests、seed handoff chain tests、语法编译、source encoding、全量测试和静态字段扫描都覆盖了 v313 的 schema-v2 receipt contract。

## 一句话总结

v313 把 promoted seed handoff 的 CI 回归证据从“receipt 中可见”升级为“receipt 和 embedded sidecar 校验必须一致”，让最后交接件更适合 CI/自动化消费。
