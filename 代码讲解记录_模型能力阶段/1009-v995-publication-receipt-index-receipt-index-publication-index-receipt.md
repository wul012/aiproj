# v995 publication receipt index receipt index publication index receipt

本版目标是把 v994 review 认可的 publication index 记录为一个 downstream consumer receipt。它解决的是“谁可以消费 v993/v994 产物、按什么用途消费”的问题：v995 明确只有 `publication_index_governance_lookup_reader` 可以按 `downstream_governance_lookup_only` 使用这个 index。

本版不训练模型，不生成新 checkpoint，不做 benchmark，不把 receipt 解释为 production promotion。

## 前置路线

v993 构建 publication index，把 v991 publication 和 v992 contract check 绑定为一条 `publication-index:` row。v994 review 确认这个 index 只能作为 lookup-only receipt 的前置证据。v995 在这个基础上记录 consumer receipt。

这一步的意义是让后续模块不只是“知道 index 存在”，还知道“哪个消费者确认接收了它，以及用途边界是什么”。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_v995.py`
  - 核心 receipt builder，输入 v994 review report，输出 v995 receipt report。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_v995_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown 和 HTML。
- `scripts/record_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_v995.py`
  - CLI 入口，支持 `--require-receipt-ready`、`--require-promotion-ready`、`--consumer-name`、`--requested-use`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_v995.py`
  - 覆盖 ready receipt、requested use 篡改、source publication 缺失、CLI 失败码和输出层。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 增加 v995 下一步常量。
- `src/minigpt/__init__.py`
  - 暴露 v995 build/write 包级入口。

## 输入输出

输入可以是 v994 输出目录，也可以是 v994 JSON 文件。目录模式下 `locate_publication_index_review_v995()` 会查找：

```text
randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_review_v994.json
```

输出的主结构包含：

- `publication_index_review_path`
- `publication_index_review_sha256`
- `source_publication_index_review_summary`
- `source_publication_index_review`
- `publication_index_rows`
- `source_evidence_rows`
- `consumer_receipts`
- `receipt`
- `summary`
- `interpretation`

`consumer_receipts` 是后续最容易被消费的列表，它把 consumer、lookup key、publication index id、receipt id、granted use、promotion 状态和 receipt status 放在同一行里。

## 检查范围

v995 的 `_checks()` 保护这些条件：

- v994 review 文件必须存在。
- v994 `status` 和 `decision` 必须 ready。
- v994 summary/body 都必须 `review_ready=True`。
- review status 必须是 `approved_for_publication_index_receipt_lookup_only`。
- requested use 必须是 `downstream_governance_lookup_only`。
- blocked uses 必须完整保留。
- publication 与 lookup ready 必须为真。
- contract check 必须 ready。
- 只能覆盖一条 publication index row。
- source evidence 必须仍是两条。
- lookup key 必须使用 `publication-index:` namespace。
- index row 不能 promotion。
- summary/review/approved 三处 promotion 都必须为 False。
- consumer boundary 与 model quality claim 必须保持 bounded。
- source publication 和 source publication check 必须仍然存在。
- v994 failed check count 必须为 0。
- v994 next step 必须指向 v995 receipt。

这些检查把 receipt 限定成“只读接收证明”，避免后续把它误当成生产授权。

## CLI 行为

运行入口：

```powershell
python scripts/record_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_v995.py <review-or-dir> --out-dir <dir> --require-receipt-ready --force
```

`--require-receipt-ready` 让 CI 或本地验证在 receipt 不满足条件时返回 1。`--require-promotion-ready` 预期返回 1，因为本版没有也不应该开放 promotion。

## 测试覆盖

测试覆盖了四类关键边界：

- ready v994 review 能生成 `receipt_ready=True`。
- `requested_use=production_promotion` 会触发 `requested_use_allowed`。
- source publication 路径改成不存在会触发 `source_publication_file_exists`。
- CLI 在坏 review 和 `--require-receipt-ready` 下返回 1。
- 输出层能生成 JSON、CSV、TXT、Markdown 和 HTML。

这些断言把用途、源文件、CLI exit code 和输出格式都纳入保护。

## 运行证据

真实运行使用 `e/994/解释/publication-receipt-index-receipt-index-publication-index-review-v994` 作为输入，输出写入 `e/995/解释/publication-receipt-index-receipt-index-publication-index-receipt-v995/`。

结果为：

- `status=pass`
- `receipt_ready=True`
- `receipt_status=publication_index_lookup_receipted`
- `consumer_name=publication_index_governance_lookup_reader`
- `granted_use=downstream_governance_lookup_only`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `promotion_ready=False`
- `failed_check_count=0`
- `passed_check_count=20`

Playwright MCP 截图保存在 `e/995/图片/`，证明 HTML 报告可打开，并展示 receipt boundary、consumer receipts 和 checks。

## 一句话总结

v995 为 v994-reviewed publication index 记录了 lookup-only 消费回执，让后续治理链知道“谁接收了证据、用来做什么、不能做什么”。
