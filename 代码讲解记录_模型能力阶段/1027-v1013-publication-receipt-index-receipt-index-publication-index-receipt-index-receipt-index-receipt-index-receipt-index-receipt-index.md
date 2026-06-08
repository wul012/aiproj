# v1013 publication receipt index receipt index publication index receipt index receipt index receipt index receipt index receipt index

## 目标与边界

v1013 的目标是把 v1011 lookup-only receipt 和 v1012 receipt contract check 组合成一个新的 digest-backed receipt index。上一版 v1012 已经证明 v1011 receipt 可以从 v1010 review 重新构建并逐字段比对；v1013 在这个基础上再做一层索引化，把“已记录 receipt”和“已通过 contract check”合并成后续 review 可以消费的只读入口。

本版不训练模型，不调整 tokenizer、dataset、benchmark，也不改变候选模型是否可 promotion 的判断。`promotion_ready` 和 `approved_for_promotion` 仍然保持 `False`，所以这是一版治理证据索引，不是模型能力放行。

## 前置路线

1. v1010 review 了 v1009 receipt index，允许下一步 lookup-only receipt recording。
2. v1011 记录了 v1010 review 的 downstream lookup-only receipt。
3. v1012 从 v1010 review 重建 v1011 receipt，证明 receipt 没有漂移。
4. v1013 把 v1011 receipt 与 v1012 check 放入同一个 receipt index，作为后续 v1014 review 的输入。

## 关键新增文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1013.py`
  - 核心 builder，负责读取 receipt/check report，执行 contract 检查，生成 receipt index rows、source evidence rows、summary 和 interpretation。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1013_artifacts.py`
  - 报告渲染器，输出 JSON、CSV、TXT、Markdown 和 HTML。
- `scripts/build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1013.py`
  - CLI 入口，支持 receipt/check 输入目录或 JSON 文件，并提供 `--require-index-ready`、`--require-lookup-ready`、`--require-promotion-ready` 等退出码门禁。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1013.py`
  - 覆盖成功索引、granted use 篡改、contract check 不 ready、artifact writer 和 CLI 串联。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 v1013 next-step 常量，把后续动作路由到 v1014 review。

## 核心数据结构

v1013 report 主要字段：

- `receipt_index_rows`
  - 只有在所有检查通过时才生成，一行对应一个 lookup-only receipt 索引条目。
  - 字段包括 `receipt_index_id`、`lookup_key`、`receipt_id`、`receipt_status`、`granted_use`、`source_receipt_path`、`source_receipt_check_path`、`contract_check_ready` 和 `promotion_ready`。
- `source_evidence_rows`
  - 记录 v1011 receipt JSON 和 v1012 check JSON 的路径、SHA-256 和 pass/fail 状态。
  - 这是后续 review 复核源文件是否漂移的关键。
- `check_rows`
  - 每一项检查都以 `id`、`status`、`actual`、`detail` 输出。
  - 失败项会进入 `issues`，并让顶层 `status` 变成 `fail`。
- `summary`
  - 聚合 `index_ready`、`lookup_ready`、`contract_check_ready`、`promotion_ready`、`passed_check_count`、`failed_check_count` 和 `next_step`。

## 核心检查逻辑

`_checks()` 保护几类边界：

1. 源文件存在：
   - receipt JSON 必须存在。
   - receipt contract check JSON 必须存在。
2. 上游状态一致：
   - v1011 receipt 必须 `status=pass`，decision 必须是 v1011 ready。
   - v1012 contract check 必须 `status=pass`，decision 必须是 v1012 passed。
   - `contract_check_ready` 必须为 `True`。
3. receipt 与 contract check 对齐：
   - `receipt_status` 必须和 check 的 original/rebuilt status 一致。
   - `granted_use` 必须始终是 `downstream_governance_lookup_only`。
   - lookup key count 必须保持 1。
4. 源证据链仍可追溯：
   - receipt 内记录的 review、receipt index、source receipt、source check 路径都必须存在。
   - source next steps 必须继续指向 v1011 check 和 v1012 index 路线。
5. 不放开 promotion：
   - summary/body/check 中的 promotion 字段必须全部保持 `False`。

只要任一检查失败，v1013 就不会生成可用的 index row，也不会通过 `--require-index-ready`。

## 输入输出链路

输入：

```text
e/1011/解释/receipt-v1011/...receipt_v1011.json
e/1012/解释/receipt-check-v1012/...receipt_check_v1012.json
```

输出：

```text
e/1013/解释/receipt-index-v1013/...v1013.json
e/1013/解释/receipt-index-v1013/...v1013.csv
e/1013/解释/receipt-index-v1013/...v1013.txt
e/1013/解释/receipt-index-v1013/...v1013.md
e/1013/解释/receipt-index-v1013/...v1013.html
```

JSON 是后续 v1014 review 的机器输入；CSV 是索引行快照；HTML 与截图是人工复核材料。

## 测试覆盖

focused 测试覆盖：

- 正常 receipt/check 可以生成 `status=pass` 的 index。
- granted use 被改成非 lookup-only 时失败。
- contract check summary 不 ready 时失败。
- artifact writer 输出五种格式。
- CLI 可以从目录定位 JSON，并在 `--require-index-ready --require-lookup-ready` 下返回 0。
- `--require-promotion-ready` 仍返回 1，证明本版不会把治理索引误判为 promotion 许可。

这些测试保护的是证据链和消费边界，不证明模型生成质量。

## 运行证据

真实运行输出位于：

```text
e/1013/解释/receipt-index-v1013/
e/1013/图片/v1013-receipt-index.png
```

关键结果：

```text
status=pass
failed_count=0
index_ready=True
lookup_ready=True
contract_check_ready=True
lookup_key_count=1
source_evidence_count=2
promotion_ready=False
```

## 一句话总结

v1013 把 v1011/v1012 证据从“可独立验证”推进到“可索引、可检索、可继续 review 的 lookup-only receipt index”。
