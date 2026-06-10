# v1080 publication receipt check

## 本版目标

v1080 的目标很窄：对 v1079 receipt 做一次 contract check，确认它是否还能从源 review 重新推导出来，并且保持关键字段一致。

本版解决的是“receipt 可能被篡改、路径可能丢失、next_step 可能漂移”的问题。

本版不做的事：

- 不训练模型
- 不新增治理链
- 不扩大 promotion 边界

## 路线来源

这一版直接承接 v1079 receipt 和 v1078 review。v1079 已经把 v1078 的 review 落成 lookup-only receipt；v1080 则反过来检查这份 receipt 是否仍然可复原、可复核。

也就是说，v1080 是一个“反向验证层”，不是新产物层。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1080.py`
  - 核心检查逻辑。
  - 读取 receipt，定位源 review，重建 v1079 receipt，再逐项比对。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1080_artifacts.py`
  - 输出 JSON / CSV / TXT / MD / HTML。
  - 这些文件是 check 产物，不是训练产物，也不是模型能力证明，只是 contract check 的证据侧产物。

- `scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1080.py`
  - CLI 入口。
  - 支持 `--out-dir`、`--require-pass`、`--force`。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1080.py`
  - 覆盖通过、篡改、缺源、CLI sidecar 写出等场景。

## 核心数据流

1. 从 `receipt` 或 `receipt 目录` 找到 v1079 receipt。
2. 解析 receipt 中的 `source_review_path`。
3. 读取源 review，调用 v1079 receipt builder 重新生成一份 receipt。
4. 对比原始 receipt 与重建 receipt 的关键字段。
5. 若所有检查通过，`status=pass`；否则 `status=fail`。

关键比较字段主要包括：

- `status`
- `decision`
- `failed_count`
- `summary.granted_use`
- `summary.lookup_key_count`
- `summary.source_evidence_count`
- `summary.promotion_ready`
- `summary.next_step`
- `receipt.*` 对应字段

## 输入输出格式

输入是 v1079 receipt JSON，或者包含该 JSON 的输出目录。

输出目录 `e/1080/解释/receipt-check-v1080/` 中包含：

- `.json`
- `.csv`
- `.txt`
- `.md`
- `.html`

这些文件是同一份 check 结果的不同视图，供后续阅读、页面检查和归档索引使用。

## 测试覆盖

这版测试不是只看“跑没跑通”，而是盯着 contract 本身：

- 正常 receipt 能通过，说明 rebuild 路径闭合。
- 篡改 `granted_use` 会失败，说明 lookup-only 边界被守住。
- 删除 `source_review_path` 会失败，说明输入链路不可缺省。
- 篡改 `source_review_sha256` 会失败，说明源证据不是空口一致。
- CLI 能写出 sidecar 文件，说明证据可以落盘归档。

## 运行证据

v1080 的运行截图在 `e/1080/图片/v1080-receipt-check.png`。

Playwright snapshot 里可以直接看到：

- `Status pass`
- `Contract True`
- `Original use downstream_governance_lookup_only`
- `Rebuilt use downstream_governance_lookup_only`
- `Lookup keys 1`
- `Failed 0`
- `Next step ...v1080`

## 一句话总结

v1080 把 v1079 receipt 变成了一份可复核的 contract check，进一步降低了证据链被漂移或篡改的风险。
