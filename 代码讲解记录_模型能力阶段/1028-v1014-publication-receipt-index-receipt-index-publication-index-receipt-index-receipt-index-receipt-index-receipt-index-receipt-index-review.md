# v1014 publication receipt index receipt index publication index receipt index receipt index receipt index receipt index receipt index review

## 目标与边界

v1014 的目标是 review v1013 digest-backed receipt index，判断它是否可以进入下一步 lookup-only receipt recording。v1013 已经把 v1011 receipt 和 v1012 contract check 合并成一个索引；v1014 负责在消费前再次确认这个索引没有 digest 漂移、路径漂移、scope 漂移或 promotion 越界。

本版不训练模型，不扩展 benchmark，不修改候选模型，也不提升模型质量声明。review 通过只说明治理证据可以被下一步只读消费。

## 前置路线

1. v1011 记录 lookup-only receipt。
2. v1012 证明 v1011 receipt 可从源 review 重建。
3. v1013 将 receipt/check 放入 digest-backed receipt index。
4. v1014 review v1013 index，为 v1015 receipt recording 提供入口。

## 关键新增文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1014.py`
  - 核心 review builder，读取 v1013 index report，执行检查并生成 review body。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1014_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
- `scripts/review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1014.py`
  - CLI 入口，支持输入 JSON 或输出目录，并提供 review/receipt-index/promotion 三种 require gate。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1014.py`
  - 覆盖成功 review、digest 篡改、lookup scope 篡改、row/body path 漂移、CLI failure 和 artifact 输出。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 v1014 review next-step 常量，指向下一步 receipt recording。

## 核心数据结构

v1014 report 包含：

- `source_receipt_index_summary`
  - v1013 summary 的只读快照。
- `source_receipt_index`
  - v1013 receipt index body，包含 index rows 和 source evidence rows。
- `receipt_index_rows`
  - review 看到的索引行，用于检查 lookup key、source receipt/check path 和 promotion flag。
- `source_evidence_rows`
  - v1013 记录的 source receipt/check digest 证据。
- `review`
  - v1014 的结论，包括 `review_ready`、`review_status`、`receipt_index_path`、`lookup_keys`、`source_receipt_path`、`source_receipt_check_path` 和 `next_step`。
- `summary`
  - 汇总 ready、lookup、contract、promotion 和 check count。

## 核心检查逻辑

`_checks()` 主要保护：

1. v1013 index 文件存在且 `status=pass`。
2. v1013 decision 与 ready key 匹配。
3. `lookup_scope` 和 `granted_use` 仍是 downstream governance lookup only。
4. `lookup_ready=True` 且 `contract_check_ready=True`。
5. 只有一个 receipt index row，且 lookup key namespace 保持稳定。
6. source evidence 数量为 2，状态为 pass，SHA-256 格式正确，源文件仍存在。
7. index body 中的 source receipt/check path 与 row 内 path 一致。
8. source review 和 source receipt index 路径仍存在。
9. model quality claim 仍是 bounded，promotion 字段全部为 False。
10. v1013 的 next step 必须正好指向 v1014 review。

任一检查失败都会让 report `status=fail`，`--require-review-ready` 返回 1。

## 输入输出链路

输入：

```text
e/1013/解释/receipt-index-v1013/...v1013.json
```

输出：

```text
e/1014/解释/review-v1014/...review_v1014.json
e/1014/解释/review-v1014/...review_v1014.csv
e/1014/解释/review-v1014/...review_v1014.txt
e/1014/解释/review-v1014/...review_v1014.md
e/1014/解释/review-v1014/...review_v1014.html
```

JSON 是后续 receipt recording 的输入；CSV 是检查结果；HTML 和截图用于人工复核。

## 测试覆盖

focused 测试覆盖：

- 正常 v1013 index 可以通过 review。
- source evidence digest 被篡改会失败。
- lookup scope 改成非 lookup-only 会失败。
- index body 和 row 内 source path 不一致会失败。
- CLI 在坏 index 且 `--require-review-ready` 下返回 1。
- artifact writer 输出五种格式，CLI 可以从目录定位 JSON。

测试保护的是治理证据的可消费性，不证明模型生成能力提升。

## 运行证据

真实运行输出：

```text
status=pass
failed_count=0
review_ready=True
receipt_index_ready=True
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

证据归档：

```text
e/1014/解释/review-v1014/
e/1014/图片/v1014-review.png
```

## 一句话总结

v1014 让 v1013 receipt index 具备了下一步 lookup-only receipt recording 的 review 入口，同时继续阻断 production promotion。
