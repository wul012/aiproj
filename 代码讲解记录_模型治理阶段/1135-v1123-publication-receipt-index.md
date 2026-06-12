# v1123 publication receipt index

## 本版目标与边界
v1123 的目标是把 v1121 lookup-only receipt 与 v1122 contract check 聚合成新的 receipt index。上一版 v1122 已经证明 v1121 receipt 可以从 v1120 review 重新推导出来；这一版继续往后走一格，把“可重建的 receipt”和“重建检查结果”放进同一个只读索引，方便后续 review 或下游治理查询。

本版不训练模型，不扩大模型能力声明，不改变 v1121/v1122 的原始证据，也不允许 promotion。`index_ready=True` 只表示索引结构完整、输入可查、contract check 已通过，并且 granted use 仍然限定在 `downstream_governance_lookup_only`。

## 前置路线

```text
v1120 review
  -> v1121 receipt
  -> v1122 contract check
  -> v1123 receipt index
```

## 关键文件

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1123.py
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1123_artifacts.py
scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1123.py
tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1123.py
```

主 builder 负责定位 receipt/check JSON，读取 summary 与 receipt body，生成检查列表、索引行、source evidence rows、summary 和 interpretation。artifact writer 只负责把同一份 report 渲染成 JSON/CSV/TXT/Markdown/HTML。CLI 负责把真实目录输入转成输出目录，并用 `--require-index-ready`、`--require-lookup-ready` 阻断结构不完整的索引。

## 输入输出模型
输入是两份上游证据：

- v1121 receipt：提供 receipt status、lookup key、source paths、granted use 和 no-promotion 字段。
- v1122 contract check：提供 original/rebuilt receipt 对比结果，并证明 receipt 能从 v1120 review 重建。

输出 report 的核心字段包括：

- `status` / `decision`：索引构建是否通过。
- `receipt_index_rows`：下游 lookup 行，包含 receipt id、lookup key、source receipt/check path 和 promotion=false。
- `source_evidence_rows`：receipt 与 contract check 两个输入的路径和 hash。
- `summary`：压缩后的可消费结果，如 `lookup_ready`、`contract_check_ready`、`promotion_ready`、`next_step`。
- `check_rows`：逐项检查结果，用于定位失败原因。

## 核心检查
v1123 的 `_checks()` 保护以下边界：

- receipt 文件和 contract check 文件必须存在。
- v1121 receipt 必须是 pass，decision 必须等于 v1121 ready key。
- v1122 contract check 必须是 pass，decision 必须等于 v1122 passed decision。
- receipt status、granted use、lookup key count 必须与 contract check 的 original/rebuilt 摘要一致。
- source review、source receipt index、source receipt、source receipt check、origin index 等路径必须仍然可读。
- `promotion_ready` 与 `approved_for_promotion` 必须保持 false。
- v1121 与 v1122 的 next step 必须形成 receipt -> check -> index 的顺序。

## 运行证据
真实运行使用：

```text
python -B scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1123.py --receipt f/1121/解释/receipt-v1121 --receipt-check f/1122/解释/receipt-check-v1122 --out-dir f/1123/解释/receipt-index-v1123 --require-index-ready --require-lookup-ready --force
```

关键输出：

```text
status=pass
index_ready=True
lookup_scope=downstream_governance_lookup_only
lookup_key_count=1
source_evidence_count=2
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

Playwright MCP 截图保存为 `f/1123/图片/v1123-receipt-index.png`。HTML 页面展示 `Receipt Index Rows`、`Source Evidence` 和 `Checks`，说明这个索引既有下游 lookup 行，也保留了上游证据来源。

## 测试覆盖
focused tests 覆盖：

- 合法 receipt + contract check 可以生成 ready index。
- granted use 被改成非 lookup-only 时失败。
- contract check 不 ready 时失败。
- artifact writer 和 CLI 能写出五种输出，并且目录定位函数可消费输出目录。

这些测试保护的是“索引是否忠实消费上游 receipt/check”，而不是模型质量本身。模型质量边界仍然由 `bounded_randomized_target_hidden_holdout_claim_only` 约束。

## 链路角色
v1123 是 receipt/check 之后的下游查阅入口。它让后续 v1124 可以 review 这一份索引，而不是重复打开 v1121 和 v1122 的全部原始报告；同时，它把 source evidence 与 no-promotion 字段继续固定在索引里，防止治理链条在转交时丢失边界。

## 一句话总结
v1123 把 v1121 receipt 和 v1122 contract check 收束成可查、可复核、不可 promotion 的 lookup-only receipt index。
