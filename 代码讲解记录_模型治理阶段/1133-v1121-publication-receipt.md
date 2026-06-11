# v1121 publication receipt

## 本版目标与边界

v1121 的目标是把 v1120 review 记录成下一份 lookup-only downstream receipt。v1120 已经审阅 v1119 index，v1121 负责把这份 review 转成可由下游消费、也可由下一步 contract check 重建验证的 receipt。

本版不训练模型，不修改 v1120 review，不把 receipt 解释成 production approval。receipt 的 `granted_use` 仍然是 `downstream_governance_lookup_only`，`promotion_ready` 仍然是 False。

## 前置路线

```text
v1119 index -> v1120 review -> v1121 receipt
```

## 关键文件

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1121.py
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1121_artifacts.py
scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1121.py
tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1121.py
```

builder 读取 v1120 review，生成 receipt boundary、consumer receipt、checks、summary 和 interpretation。artifact writer 负责 JSON/CSV/TXT/Markdown/HTML 输出。CLI 支持 `--require-receipt-ready`，测试覆盖 ready receipt、错误 requested use、source review path 漂移、source evidence 状态改变、CLI gating 和 artifact 输出。

## 输入、输出与核心流程

真实输入是 `f/1120/解释/receipt-index-review-v1120`，真实输出是 `f/1121/解释/receipt-v1121`。流程是定位 review JSON，读取 review summary/body、source index rows 和 source evidence，检查 requested/granted use 仍为 lookup-only，生成 consumer receipt 并绑定 source review path/hash，最后输出多格式产物。

## 关键检查

本版重点保护 review ready、requested use allowed、lookup-only granted use、source evidence digest/status、lookup key count 和 promotion still false。它让 receipt 成为可阻断的治理记录，而不是普通日志。

## 运行证据

```text
status=pass
receipt_ready=True
granted_use=downstream_governance_lookup_only
lookup_key_count=1
source_evidence_count=2
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

验证包括 py_compile、focused v1121 tests（`6 passed in 0.82s`）、source hygiene（`2339/2339 clean`）、真实 CLI、`git diff --check` 和 Playwright MCP 截图 `f/1121/图片/v1121-receipt.png`。

## 链路角色

v1121 位于 review 之后、contract check 之前。它把 v1120 review 记录为下游可读 receipt，下一步 v1122 会重新从 v1120 review 构建 receipt，验证 v1121 没有被篡改或误用。

## 一句话总结

v1121 把 v1120 review 转成 lookup-only receipt，为下一轮重建式 contract check 提供可复核输入。
