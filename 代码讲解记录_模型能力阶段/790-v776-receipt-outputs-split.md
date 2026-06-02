# v776 receipt outputs split 代码讲解

## 本版目标和边界

v776 是维护性拆分路线第四版，继续处理 `promoted_training_scale_seed_handoff_receipt.py`。v773 已经拆出 schema validation，本版拆出 text renderer。

本版不改变 receipt check 内容，不改变 JSON/text 文件名，不改变 sidecar 校验逻辑，也不改变公共导入路径。

## 为什么拆 outputs

receipt 主文件里有两段长 renderer：

- `render_promoted_training_scale_seed_handoff_automation_receipt_check`
- `render_promoted_training_scale_seed_handoff_embedded_receipt_check`

它们都是字段到文本行的展开，行数长、字段密集，但不参与 receipt 状态判断。留在主文件会遮挡真正的 checker 和 sidecar 逻辑。

## 关键新增文件

- `src/minigpt/promoted_training_scale_seed_handoff_receipt_outputs.py`
  - 承接 automation receipt check text renderer。
  - 承接 embedded receipt check text renderer。
  - 使用 `RECEIPT_SCHEMA_V5_TEXT_FIELDS` 和 `EMBEDDED_RECEIPT_SCHEMA_V5_TEXT_FIELDS` 保持 schema v5 文本过滤逻辑。

## 主文件变化

- `src/minigpt/promoted_training_scale_seed_handoff_receipt.py`
  - 从 outputs 模块导入两个 renderer。
  - 保留 write outputs 函数，这些函数仍负责路径、文件名和写出流程。
  - 保留 sidecar verification，因为它依赖 loader/check/render 的协作。

行数变化：

```text
774 -> 505
```

加上 v773 的 validation split，原 941 行 receipt 文件已经拆成：

```text
receipt.py: 505
receipt_outputs.py: 289
receipt_validation.py: 208
```

## 测试覆盖

Focused tests：

```powershell
python -m pytest tests\test_promoted_training_scale_seed_handoff_receipt.py tests\test_promoted_training_scale_seed_handoff_receipt_contract.py tests\test_promoted_training_scale_seed_handoff_receipt_contract_check.py tests\test_promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke.py tests\test_promoted_training_scale_seed_handoff_receipt_suite_design.py -q -o cache_dir=runs\pytest-cache-v776-focused
```

结果：

```text
50 passed
```

这组测试会比对 receipt text 和 embedded sidecar text，因此能保护 renderer 移动没有改变输出。

## 运行证据

- 归档说明：`e/776/解释/说明.md`
- HTML 摘要：`e/776/解释/refactor-summary.html`
- 截图：`e/776/图片/v776-receipt-outputs-split.png`

一句话总结：v776 把 receipt 输出渲染层独立出来，使原最大文件从 941 行连续降到 505 行。
