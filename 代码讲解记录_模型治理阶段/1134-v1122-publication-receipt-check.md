# v1122 publication receipt contract check

## 本版目标与边界

v1122 的目标是对 v1121 lookup-only receipt 做重建式 contract check。它读取 v1121 receipt，找到其中记录的 v1120 review，再重新构建一份 receipt，并把原始 receipt 与重建 receipt 的关键字段逐项对比。

本版不训练模型，不修改 v1121 receipt，不把 contract check 解释成 production approval。`contract_check_ready=True` 只表示 receipt 可重建、可复核，并且仍然处在 downstream governance lookup 边界内。

## 前置路线

```text
v1120 review -> v1121 receipt -> v1122 contract check
```

## 关键文件

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1122.py
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1122_artifacts.py
scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1122.py
tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1122.py
```

builder 读取 v1121 receipt，解析 source review 路径，重新调用 v1121 receipt builder，并生成对比 summary、check rows 和 interpretation。artifact writer 输出 JSON/CSV/TXT/Markdown/HTML，CLI 的 `--require-pass` 用于阻断失败 contract check。

## 输入、输出与核心流程

真实输入是 `f/1121/解释/receipt-v1121`，真实输出是 `f/1122/解释/receipt-check-v1122`。流程是定位 receipt，读取 `receipt_index_review_path` 指向的 v1120 review，重新构建 receipt，对比 original 与 rebuilt 的 status、granted use、lookup key、source evidence、source hash、source paths 和 no-promotion 字段。

## 关键检查

本版重点保护 receipt file、source review file/hash、rebuilt receipt pass、receipt status、consumer name、granted use、lookup keys、source paths 和 promotion-ready-false。它让 contract check 成为 receipt 的防篡改入口。

## 运行证据

```text
status=pass
contract_check_ready=True
original_granted_use=downstream_governance_lookup_only
rebuilt_granted_use=downstream_governance_lookup_only
original_lookup_key_count=1
rebuilt_lookup_key_count=1
original_promotion_ready=False
rebuilt_promotion_ready=False
passed_check_count=46
failed_check_count=0
```

验证包括 py_compile、focused v1122 tests（`6 passed in 0.33s`）、source hygiene（`2343/2343 clean`）、真实 CLI、`git diff --check` 和 Playwright MCP 截图 `f/1122/图片/v1122-receipt-check.png`。

## 链路角色

v1122 位于 receipt 之后、index 之前。它证明 v1121 receipt 能从 v1120 review 重新推导出来，下一步 v1123 可以把 receipt 和 contract check 合并进 lookup-only index。

## 一句话总结

v1122 给 v1121 receipt 增加了可重建、可阻断的 contract check，保证后续 index 消费的是未漂移的 lookup-only receipt。
