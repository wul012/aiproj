# v1033 publication receipt index receipt index receipt index receipt index receipt index receipt index 代码讲解

## 本版目标和边界

v1033 的目标是把 v1031 lookup-only receipt 与 v1032 contract check 编成新的 digest-backed receipt index。

它解决的问题是：v1031 证明 receipt 已记录，v1032 证明 receipt 可从源 review 重建，但下游审查需要一个索引入口来同时定位 receipt、contract check、lookup key 和源证据 digest。v1033 就是这层索引。

本版不做模型训练，不改变 hidden holdout 评估，不开放生产晋级。

## 前置能力

v1031 输出 lookup-only receipt：

```text
e/1031/解释/receipt-v1031/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1031.json
```

v1032 输出 contract check：

```text
e/1032/解释/receipt-check-v1032/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1032.json
```

v1033 只消费这两个文件，并记录它们的 SHA-256，不重新生成 receipt 或 check。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1033.py`
  - v1033 index 核心模块。
  - 检查 v1031 receipt 与 v1032 check 是否一致、可查、lookup-only 且无 promotion。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1033_artifacts.py`
  - 写出 JSON、CSV、Text、Markdown、HTML。
- `scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1033.py`
  - CLI 入口。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1033.py`
  - 覆盖 ready、granted use 篡改、contract check 不 ready、CLI/artifact 输出。
- `e/1033/解释/receipt-index-v1033/`
  - 真实运行产物。
- `e/1033/图片/v1033-receipt-index.png`
  - Playwright MCP 截图证据。

## 核心数据结构

`receipt_index` 是本版核心输出：

```text
index_ready
receipt_index_id
lookup_scope
lookup_key_count
receipt_index_rows
source_evidence_rows
source_evidence_count
receipt_path
receipt_check_path
receipt_id
receipt_status
granted_use
lookup_ready
contract_check_ready
promotion_ready
approved_for_promotion
consumer_boundary
model_quality_claim
source_next_step
next_step
```

`receipt_index_rows` 提供下游查找入口：

```text
receipt_index_id
lookup_key
receipt_id
receipt_status
granted_use
source_receipt_path
source_receipt_check_path
source_review_path
source_receipt_index_path
contract_check_ready
promotion_ready
```

`source_evidence_rows` 保存 receipt 与 check 两个源文件的 digest：

```text
kind
path
sha256
status
```

## 核心函数

`build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1033(...)` 是主入口。

它读取：

- `receipt_summary`
- `receipt`
- `check_summary`

然后调用 `_checks(...)`。检查项覆盖：

- v1031 receipt 文件存在；
- v1032 contract check 文件存在；
- receipt `status=pass`；
- receipt decision 是 v1031 ready；
- receipt summary/body 都 ready；
- receipt status 是 lookup receipted；
- contract check `status=pass`；
- contract check decision 是 v1032 passed；
- contract check ready；
- receipt status 与 check original/rebuilt status 一致；
- granted use 全部是 downstream lookup only；
- lookup key count 是 1；
- source evidence count 是 2；
- source review、source receipt index、source receipt、source check、origin index 路径仍存在；
- consumer boundary 和 model quality claim 保持 bounded；
- promotion 与 approval 都保持 false；
- source receipt 和 source check 的 failed count 都是 0；
- v1031/v1032 next step 正确衔接到 index。

通过后 `_index(...)` 构造索引行和 evidence rows。

## CLI 流程

真实运行命令：

```text
python scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1033.py --receipt e/1031/解释/receipt-v1031 --receipt-check e/1032/解释/receipt-check-v1032 --out-dir e/1033/解释/receipt-index-v1033 --require-index-ready --require-lookup-ready --force
```

CLI 支持目录输入，自动定位 v1031 receipt JSON 和 v1032 check JSON。

## 运行证据

真实 CLI 输出关键值：

```text
status=pass
decision=randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1033_ready
index_ready=True
receipt_index_id=randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-v1033
lookup_key_count=1
source_evidence_count=2
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

HTML 报告截图保存到：

```text
e/1033/图片/v1033-receipt-index.png
```

## 测试覆盖

focused 测试覆盖四条路径：

- ready receipt + ready check 可以生成 index；
- granted use 改成 production promotion 会失败；
- contract check 不 ready 会失败；
- artifact writer 和 CLI 都能写出 JSON、CSV、Text、Markdown、HTML。

当前 focused 测试结果：

```text
4 passed in 7.14s
```

全量回归结果：

```text
2544 passed in 597.78s
```

source encoding hygiene 结果：

```text
source_count=1994
clean_count=1994
bom_count=0
syntax_error_count=0
compatibility_error_count=0
```

## 一句话总结

v1033 把 v1031 receipt 和 v1032 check 变成可审查、可定位、带 digest 的 lookup index，但仍然明确阻断 production promotion。
