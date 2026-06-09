# v1041 publication receipt index receipt index receipt index receipt index receipt index receipt index receipt index receipt index 代码讲解

## 本版目标和边界

v1041 的目标是把 v1039 lookup-only receipt 和 v1040 contract check 打包成 digest-backed receipt index。

v1039 负责记录下游 receipt，v1040 负责证明这份 receipt 可以从 v1038 review 重建。v1041 把两者放入一个统一索引，方便后续 review 和再次 receipt recording 使用。

本版不训练模型，不改变模型能力评价，不允许 production promotion。

## 前置链路

v1041 读取两份真实归档：

```text
e/1039/解释/receipt-v1039/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1039.json
e/1040/解释/receipt-check-v1040/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1040.json
```

它要求 receipt ready、contract check ready、lookup-only granted use、source paths 存在、source check clean，并保持 `promotion_ready=False`。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1041.py`
  - v1041 index 核心模块。
  - 消费 v1039 receipt 和 v1040 check，生成索引行和 source evidence 行。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1041_artifacts.py`
  - 输出 JSON、CSV、Text、Markdown、HTML。
- `scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1041.py`
  - CLI 入口。
  - 支持 receipt/check 目录输入。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1041.py`
  - 覆盖 ready index、granted use 篡改、contract check not ready、CLI/artifact 输出。
- `e/1041/解释/receipt-index-v1041/`
  - 真实运行产物。
- `e/1041/图片/v1041-receipt-index.png`
  - Playwright MCP 截图证据。

## 核心数据结构

v1041 输出核心是：

```text
receipt_index
receipt_index_rows
source_evidence_rows
summary
check_rows
```

`receipt_index_rows` 记录：

- `receipt_index_id`
- `lookup_key`
- `receipt_id`
- `receipt_status`
- `granted_use`
- `source_receipt_path`
- `source_receipt_check_path`
- `source_review_path`
- `source_receipt_index_path`
- `contract_check_ready`
- `promotion_ready`

`source_evidence_rows` 记录 v1039 receipt 和 v1040 check 的路径、SHA-256 和状态，是后续 review 判断“源证据仍然存在”的基础。

## 核心函数

`build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1041(...)` 是主入口。

它执行四步：

1. 读取 v1039 receipt 的 summary/receipt。
2. 读取 v1040 contract check summary。
3. 调用 `_checks(...)` 验证 receipt ready、contract ready、lookup-only、source paths、bounded claim、no-promotion 和 next-step。
4. 调用 `_index(...)` 生成 lookup key、index rows、source evidence rows 和 summary。

关键检查包括：

- `receipt_file_exists`
- `receipt_check_file_exists`
- `receipt_decision_ready`
- `receipt_status_ready`
- `receipt_check_decision_ready`
- `contract_check_ready`
- `granted_use_lookup_only`
- `lookup_key_count`
- `source_receipt_index_review_file_exists`
- `source_receipt_index_file_exists`
- `source_receipt_file_exists`
- `source_receipt_check_file_exists`
- `promotion_still_false`
- `source_next_steps_match`

这些检查保证 v1041 只是治理 lookup index，不会把 receipt/check 误解释为模型生产发布。

## CLI 流程

真实运行命令：

```text
python scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1041.py --receipt e/1039/解释/receipt-v1039 --receipt-check e/1040/解释/receipt-check-v1040 --out-dir e/1041/解释/receipt-index-v1041 --require-index-ready --require-lookup-ready --force
```

真实输出摘要：

```text
status=pass
index_ready=True
lookup_key_count=1
source_evidence_count=2
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

## 测试覆盖

focused test 覆盖：

- ready receipt + ready check 可以生成 index；
- granted use 改成 production promotion 会失败；
- contract check not ready 会失败；
- CLI 和 artifact 输出可用。

## 运行证据

运行证据位于：

```text
e/1041/解释/receipt-index-v1041/
e/1041/图片/v1041-receipt-index.png
```

Playwright MCP 快照确认页面展示 `Status=pass`、`Index ready=True`、`Contract=True`、`Evidence=2`、`Failed=0`。

## 一句话总结

v1041 把 v1039 receipt 和 v1040 contract check 合并成 digest-backed lookup index，为下一步 review 提供稳定入口。
