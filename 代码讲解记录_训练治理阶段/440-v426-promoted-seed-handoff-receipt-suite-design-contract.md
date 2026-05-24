# v426 promoted seed handoff receipt suite-design contract 代码讲解

## 本版目标与边界

v426 的目标是把 v425 promoted seed handoff 中已经可见的 suite-design regression context，继续提升到 automation receipt、receipt check、embedded receipt check 和 handoff assurance。主报告里能看到 suite-design 字段还不够；自动化侧真正会消费的是收据和 sidecar，如果这些 sidecar 只验证 CI regression，就会产生“主报告有解释、收据合同没解释”的断层。

本版不执行训练，不改 seed handoff baseline，不新增新的治理链。它只升级 receipt schema 到 v3，并让所有收据校验层同步验证 selected/global/comparison-ready suite-design 字段。

## 前置链路

本版接在 v417-v425 后面：

- v417-v424：suite-design regression context 从 portfolio comparison 一路传到 promoted next-cycle seed。
- v425：final seed handoff 报告、strict clean-batch gate、CSV/Markdown/HTML/CLI 看到 suite-design context。
- v426：automation receipt 和 assurance sidecar 也必须看到并校验同一份 suite-design context。

## 关键文件

### `src/minigpt/promoted_training_scale_seed_handoff_receipt_artifacts.py`

`build_promoted_training_scale_seed_handoff_automation_receipt()` 把 `schema_version` 从 2 升到 3，并新增 6 个字段：

```text
selected_handoff_batch_maturity_suite_design_regression_count
selected_handoff_batch_maturity_suite_design_regression_names
handoff_batch_maturity_suite_design_regression_count
handoff_batch_maturity_suite_design_regression_names
comparison_ready_handoff_batch_maturity_suite_design_regression_count
comparison_ready_handoff_batch_maturity_suite_design_regression_names
```

这些字段分别表达 selected baseline、全部 handoff context、comparison-ready context 三层 suite-design 状态。receipt text 也输出这些字段，方便 shell-only 检查。

### `src/minigpt/promoted_training_scale_seed_handoff_receipt.py`

新增 `RECEIPT_SCHEMA_V3_REQUIRED_FIELDS`，并在 `check_promoted_training_scale_seed_handoff_automation_receipt()` 中做三类校验：

- schema v3 必须包含全部 suite-design 字段。
- suite-design regression count 不能为负。
- suite-design regression names 必须是 list。

`EMBEDDED_RECEIPT_CHECK_COMPARE_KEYS` 也加入这些字段，所以 embedded receipt check 会把主报告重算得到的 receipt check 和嵌入 sidecar 逐字段比较。

### `src/minigpt/promoted_training_scale_seed_handoff_assurance.py`

handoff assurance 的 compare keys、JSON 输出、text 输出和归一化逻辑都新增 suite-design 字段。这样 assurance 不只是确认 embedded receipt check 存在，还会确认 schema-v3 suite-design 字段在主报告、receipt JSON、receipt-check JSON/text、embedded check JSON/text 之间一致。

### `src/minigpt/promoted_training_scale_seed_handoff_artifacts.py`

CSV 输出新增 handoff assurance 的 suite-design receipt 字段，例如：

```text
handoff_assurance_embedded_receipt_check_receipt_handoff_batch_maturity_suite_design_regression_count
handoff_assurance_embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_count
```

这样 release evidence 可以只读 CSV，也能看到 receipt contract 的 suite-design 校验结果。

### `src/minigpt/promoted_training_scale_seed_handoff_sections.py`

Markdown 和 HTML 增加 assurance receipt suite-design 行。截图中可见：

```text
Assurance receipt schema = 3
Assurance selected suite-design regressions = 0
Assurance suite-design regressions = 2
Assurance ready suite-design regressions = 0
```

### `scripts/check_promoted_seed_handoff_assurance_smoke.py`

smoke summary 从 schema v2 更新到 schema v3，并增加 selected/global/ready suite-design regression count 检查。这个脚本继续证明完整 receipt/embedded/assurance 链路能在本地复算。

### `tests/test_promoted_training_scale_seed_handoff_receipt_suite_design.py`

新增聚焦测试文件，没有继续扩充 1170 行的 receipt 主测试。测试覆盖两件事：

- schema v3 receipt 缺少 suite-design 字段时会失败，字段完整时通过。
- `execute_promoted_training_scale_seed.py` 生成的 receipt、receipt check、embedded check、assurance 和主报告都携带并校验 suite-design 字段。

## 核心数据流

```text
promoted seed handoff summary
  -> automation receipt schema v3
  -> receipt check
  -> embedded receipt check
  -> handoff assurance
  -> JSON / text / CSV / Markdown / HTML / CLI evidence
```

这条链路不证明模型能力提升；它证明最终自动化侧拿到的收据合同没有丢失 suite-design rejected evidence。

## 测试覆盖

本轮定向验证：

- `python -m pytest tests\test_promoted_training_scale_seed_handoff_receipt_suite_design.py -q`：`2 passed`
- `python -m pytest tests\test_promoted_training_scale_seed_handoff_receipt.py tests\test_promoted_training_scale_seed_handoff.py tests\test_promoted_training_scale_seed_handoff_suite_design.py -q`：`57 passed`
- 语法编译：通过

收口验证：

- `python -m pytest -q`：`720 passed`
- `python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-v426`：`status=pass`
- `git diff --check`：通过

## 运行证据

`d/426` 归档了本版截图和说明：

- `d/426/图片/01-promoted-seed-handoff-receipt-suite-design.png`
- `d/426/解释/v426-promoted-seed-handoff-receipt-suite-design.html`
- `d/426/解释/v426-promoted-seed-handoff-receipt-suite-design-automation-receipt.json`
- `d/426/解释/v426-promoted-seed-handoff-receipt-suite-design-receipt-check.json`
- `d/426/解释/v426-promoted-seed-handoff-receipt-suite-design-embedded-check.json`
- `d/426/解释/v426-promoted-seed-handoff-receipt-suite-design-assurance.json`
- `d/426/解释/v426-promoted-seed-handoff-receipt-suite-design-snapshot.md`
- `d/426/解释/说明.md`

一句话总结：v426 把 suite-design blocker 从 final seed handoff 主报告推进到 receipt/embedded/assurance 合同层，让自动化收据本身也能证明 selected clean、rejected dirty、comparison-ready clean 三层边界。
