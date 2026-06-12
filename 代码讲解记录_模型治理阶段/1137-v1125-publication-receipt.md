# v1125 publication receipt

## 本版目标与边界
v1125 的目标是把 v1124 的 receipt index review 记录成新的 lookup-only downstream receipt。这个版本承接的是 v1121 到 v1124 形成的一轮治理链：先把上一轮 review 记录为 receipt，再对 receipt 做 contract check，再把 receipt/check 合并为 index，最后 review 这个 index。v1124 已经完成最后一步 review，本版从 review 回到 receipt，开始下一轮链条。这样做的价值不是让模型“变聪明”，而是让每一次治理证据的转交都有一个可追踪、可复核、可阻断的节点。

本版明确不做三件事。第一，不训练模型，也不新增任何模型参数、tokenizer、dataset 或推理能力。第二，不修改 v1124 review 的内容，不对上游证据进行重写，只读取 review 输出并生成新的 receipt。第三，不把 receipt 通过解释成生产发布许可。`receipt_ready=True` 的含义很窄，它只表示 v1124 review 可以被记录为一个 downstream governance lookup 用的 receipt；`promotion_ready` 和 `approved_for_promotion` 必须继续为 `False`。如果后续模块或读者把这个 receipt 当作 production approval 使用，那就是越界解释。

## 前置路线
本版的直接输入是 v1124 review，完整路线如下：

```text
v1121 receipt
  -> v1122 contract check
  -> v1123 receipt index
  -> v1124 receipt index review
  -> v1125 receipt
```

这条路线里的每一步职责都不一样。v1121 是对前一个 review 的记录，v1122 证明 v1121 能从源 review 重建，v1123 把 receipt 和 check 合并成索引，v1124 复核索引是否仍然满足只读查询边界，v1125 则把 v1124 的复核结论记录成新的 receipt。换句话说，v1125 不是孤立的一份报告，而是“上一轮治理闭环结束后，下一轮治理开始前”的交接件。

## 关键文件与职责
本版新增或更新的关键文件有四类。

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125.py
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125_artifacts.py
scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125.py
tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125.py
```

主 builder 文件负责核心逻辑。它读取 v1124 review JSON，拆出 `summary`、`review`、`receipt_index_rows` 和 `source_evidence_rows`，再构造检查项、receipt body、consumer receipts、summary 和 interpretation。artifact 文件只处理渲染，不决定业务结果。CLI 文件把目录输入和命令行参数接到 builder 上，并在 `--require-receipt-ready` 下把失败 receipt 转成非零退出码。测试文件覆盖正常路径和几类漂移场景，保证 receipt 不会在上游证据损坏、requested use 越界或 source path 漂移时继续通过。

常量文件也被更新，新增 `RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_V1125_NEXT_STEP`。这个常量不是装饰，它决定 v1125 summary 中的 `next_step`，也就是后续 v1126 contract check 的入口名称。没有这个常量，链路虽然能生成 receipt，但下一跳会变成隐含约定，不利于后续自动化消费。

## 输入模型
v1125 的输入是 `f/1124/解释/receipt-index-review-v1124`。当 CLI 接收到目录时，`locate_receipt_index_review_v1124()` 会自动拼接 v1124 review 的 JSON 文件名。这个设计让调用者不需要记住很长的 JSON 文件名，只需要传入输出目录即可。

builder 读取 JSON 后会先检查它是否是对象。如果不是对象，会抛出明确错误，避免把列表、字符串或空文件误当成 report。随后进入 `_checks()`。这一步不只是检查 `status=pass`，还会检查 review decision、ready key、review status、requested use、lookup-only granted use、lookup readiness、contract check readiness、source evidence 数量、source evidence digest、source evidence status、lookup key namespace、source receipt/index/check/review path、模型质量声明边界以及 source next step。这样的检查粒度比较细，原因是 receipt 是下游消费入口，一旦 receipt 生成出来，后续 check/index/review 都会把它当作事实来源，所以这里不能只看一个 `pass` 字段。

## 输出模型
v1125 输出 report 的核心结构包括 `receipt`、`summary`、`consumer_receipts`、`check_rows` 和 `interpretation`。

`receipt` 是最重要的主体。它记录 `receipt_ready`、`receipt_id`、`receipt_type`、`receipt_status`、`consumer_name`、`requested_use`、`granted_use`、`receipt_index_review_path`、`receipt_index_review_sha256`、`receipt_index_row_count`、`source_evidence_count`、`lookup_keys`、`review_id`、`review_status`、`promotion_ready`、`approved_for_promotion`、`consumer_boundary`、`model_quality_claim`、`source_receipt_index_path`、`source_receipt_path`、`source_receipt_check_path`、`source_review_path`、`source_receipt_index_origin_path` 和 `next_step`。这些字段看起来多，但每个都承担一个边界作用：路径字段保留证据来源，hash 字段用于后续重建校验，lookup key 给下游查询使用，no-promotion 字段阻止误读，model quality claim 把模型能力声明压回受限范围。

`summary` 是给自动化和 README 消费的压缩视图。它不保存全部细节，但会保留 ready key、receipt id、receipt status、consumer name、granted use、row count、source evidence count、lookup key count、promotion flags、consumer boundary、model quality claim、next step 和检查数量。后续 v1126 contract check 会大量依赖 summary，因为 contract check 的目标不是重新展示所有细节，而是证明 original receipt 与 rebuilt receipt 在关键字段上完全一致。

`consumer_receipts` 则是面向下游查询者的一组行。本版只有一条，因为 source index 只有一个 lookup key。这一行包含 consumer name、lookup key、source receipt id、当前 receipt id、granted use、promotion ready 和 receipt status。它的作用是把治理 receipt 从“内部报告”转换成“可查记录”。

## 核心检查逻辑
本版 `_checks()` 的第一类检查是文件和状态检查，包括 `receipt_index_review_file_exists`、`receipt_index_review_passed`、`receipt_index_review_decision_ready` 和 `receipt_index_review_summary_ready`。它们确保输入确实来自 v1124 review，且不是失败报告或半成品报告。

第二类检查是使用边界检查，包括 `review_status_allowed`、`requested_use_allowed`、`lookup_only_granted_use`、`receipt_index_lookup_ready` 和 `contract_check_ready`。这里尤其重要的是 `requested_use_allowed`。即使上游 review 是干净的，只要调用者在 CLI 中把 `--requested-use` 改成 `production_promotion`，builder 也必须失败。这个测试已经覆盖，防止 receipt 生成入口被当成提升权限的入口。

第三类检查是证据完整性检查，包括 `index_rows_present`、`source_evidence_count`、`source_evidence_digests_present`、`source_evidence_status_pass`、`lookup_keys_source_namespace` 和一组 source file exists 检查。它们保护的是“证据仍然可追溯”。如果 source evidence 丢了 digest，或者 review 里记录的 source path 指向不存在的文件，receipt 就不应该通过。因为这样的 receipt 不能支撑后续 contract check，也不能作为可信查阅入口。

第四类检查是模型治理边界检查，包括 `index_rows_not_promoted`、`promotion_still_false`、`consumer_boundary_governance`、`model_quality_claim_bounded` 和 `source_next_step_matches`。它们共同说明：本版可以生成 receipt，但不能越过治理边界。尤其是 `source_next_step_matches`，它要求 v1124 的 summary 明确指向 v1125 receipt。如果上游 next step 被篡改到别的路线，本版就会失败。

## CLI 入口
CLI 命令如下：

```text
python -B scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125.py f/1124/解释/receipt-index-review-v1124 --out-dir f/1125/解释/receipt-v1125 --require-receipt-ready --force
```

`--force` 只负责覆盖输出目录，不改变检查逻辑。`--require-receipt-ready` 会读取 builder 输出的 summary，如果 ready key 不为 true，就返回 1。这个行为让它可以放进 CI 或 release gate，而不是只生成一份看起来失败但进程仍然成功的报告。

## 真实运行证据
本版真实运行结果如下：

```text
status=pass
receipt_ready=True
receipt_status=publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125_lookup_receipted
granted_use=downstream_governance_lookup_only
receipt_index_row_count=1
source_evidence_count=2
lookup_key_count=1
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

这些结果说明 v1124 review 被成功记录成 v1125 receipt，但记录范围仍然是 lookup-only。截图 `f/1125/图片/v1125-receipt.png` 由 Playwright MCP 生成，页面中可以看到 `Receipt Boundary`、`Consumer Receipts` 和 `Checks`。这三个区域分别对应边界、下游消费行和检查明细，能证明 HTML 不是空产物，也能让人工读者快速确认 receipt 的用途。

## 测试覆盖
focused tests 覆盖六个方向。第一，合法 review 可以生成 ready receipt，并检查 receipt status、consumer name、granted use、lookup key count、source evidence count、next step 和 no-promotion。第二，requested use 被改成 production promotion 时失败。第三，source review path 漂移时失败。第四，source evidence status 改成 fail 时失败。第五，CLI 在 `--require-receipt-ready` 下遇到坏 review 会返回 1，同时仍然写出失败报告方便排查。第六，artifact writer 与 CLI 能写出 JSON、CSV、TXT、Markdown、HTML 五种输出，且目录定位函数可以消费输出目录。

这组测试不是为了证明模型质量，而是为了保护 receipt 的治理合同。它保证 receipt 只能从 ready review 生成，只能授予 lookup-only 使用，只能带着完整 source evidence 进入下一跳。

## 链路角色
v1125 是新一轮治理链的起点。它承接 v1124 review，把 review 记录成 receipt，并把下一跳固定为 v1126 contract check。后续 v1126 应该从 v1125 receipt 反向读取 source review，重新构建 receipt，并对 original/rebuilt 的关键字段做一致性比较。也就是说，v1125 的质量直接决定 v1126 是否能防篡改、v1127 是否能建立索引、v1128 是否能做 review。

本版也体现了为什么最近版本不能只做轻量文档更新。receipt 不是一行 README，而是一个可消费的治理对象。它需要 builder、artifact、CLI、测试、真实运行证据、截图和讲解共同证明。如果这些都缺失，后续即使继续推进版本号，也只是把薄弱证据往后传。

## 一句话总结
v1125 把 v1124 已复核的 receipt index 记录成新的 lookup-only receipt，让下一轮 contract check 可以从一个边界清晰、路径完整、promotion 关闭的输入开始。
