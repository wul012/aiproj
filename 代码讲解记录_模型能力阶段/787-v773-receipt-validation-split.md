# v773 receipt validation split 代码讲解

## 本版目标和边界

v773 是维护性拆分路线的第一版，不做新功能。目标是处理当前最大文件 `promoted_training_scale_seed_handoff_receipt.py` 的职责混杂问题。

本版只拆 schema validation，不改变 receipt checker 的行为，不改变 CLI，不改变 JSON/text 输出格式，也不移动已有测试 fixture。

## 为什么先拆这里

扫描显示 `promoted_training_scale_seed_handoff_receipt.py` 有 941 行，是 `src/minigpt` 当前最大文件。它同时承担：

- receipt/handoff loader
- automation receipt checker
- receipt text renderer
- embedded receipt checker
- embedded receipt text renderer
- sidecar JSON/text/file 一致性检查
- schema v2-v5 字段校验
- compare-key normalization

其中 schema/normalization 是相对独立的基础层，最适合先拆，风险也最低。

## 关键新增文件

- `src/minigpt/promoted_training_scale_seed_handoff_receipt_validation.py`
  - 定义 `EMBEDDED_RECEIPT_CHECK_COMPARE_KEYS`。
  - 定义 `RECEIPT_SCHEMA_V2_REQUIRED_FIELDS` 到 `RECEIPT_SCHEMA_V5_REQUIRED_FIELDS`。
  - 定义 `RECEIPT_SCHEMA_V5_TEXT_FIELDS` 和 `EMBEDDED_RECEIPT_SCHEMA_V5_TEXT_FIELDS`。
  - 提供 `receipt_int()`、`normalized_receipt_check_value()`。
  - 提供 `v2_receipt_field_issues()` 到 `v5_receipt_field_issues()`。
  - 提供 `receipt_check_compare_keys()`。

## 主文件变化

- `src/minigpt/promoted_training_scale_seed_handoff_receipt.py`
  - 删除内联 schema 常量和版本字段校验函数。
  - 从 validation 模块导入同名常量，并用 alias 保持原来的私有函数调用形式。
  - 继续对外暴露原有 receipt API。

主文件行数从 941 行降到 774 行。这个文件仍然偏大，但职责已经少了一层，下一刀可以继续拆 render 或 sidecar。

## 契约保护

`RECEIPT_SCHEMA_V5_REQUIRED_FIELDS` 被 `promoted_training_scale_seed_handoff_assurance.py` 从 receipt 主模块导入。v773 没有破坏这个路径，因为主模块仍然 import 并 re-export 这些常量。

也就是说：

```python
from minigpt.promoted_training_scale_seed_handoff_receipt import RECEIPT_SCHEMA_V5_REQUIRED_FIELDS
```

仍然可用。

## 测试覆盖

Focused tests：

```powershell
python -m pytest tests\test_promoted_training_scale_seed_handoff_receipt.py tests\test_promoted_training_scale_seed_handoff_receipt_contract.py tests\test_promoted_training_scale_seed_handoff_receipt_contract_check.py tests\test_promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke.py tests\test_promoted_training_scale_seed_handoff_receipt_suite_design.py -q -o cache_dir=runs\pytest-cache-v773-focused
```

结果：

```text
50 passed
```

这些测试覆盖 continue/stop receipt、contract check、failure smoke、suite design regression 和 embedded receipt sidecar 一致性，能保护本版拆分不改变行为。

## 运行证据

- 归档说明：`e/773/解释/说明.md`
- HTML 摘要：`e/773/解释/refactor-summary.html`
- 截图：`e/773/图片/v773-receipt-validation-split.png`

一句话总结：v773 把最大 receipt 模块的 schema validation 责任切成独立层，降低主文件复杂度且保持外部契约不变。
