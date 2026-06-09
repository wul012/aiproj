# v1043 publication receipt 代码讲解

## 本版目标和边界

v1043 的目标是把 v1042 已 review 的 digest-backed receipt index 记录成 downstream lookup-only receipt。

它解决的问题是：v1042 已经证明 v1041 index 可以进入下一步 receipt 记录，但下游模块仍需要一个明确的 consumer receipt，说明谁可以读取、以什么 use 读取、是否允许 promotion。

本版不做：

- 不训练模型。
- 不新增 benchmark 或 replay。
- 不把 lookup-only receipt 解释成模型质量提升。
- 不打开 production promotion。

## 前置链路

v1043 直接承接 v1042：

- v1041 生成 digest-backed receipt index。
- v1042 review 该 index，确认 lookup-only、source path、source evidence、contract check 都稳定。
- v1043 记录 consumer receipt，作为下游 lookup-only 消费凭证。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1043.py`
  - v1043 receipt builder。
  - 读取 v1042 review report，生成 receipt、consumer_receipts、summary、check_rows。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1043_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 用于截图，CSV 记录 consumer receipt 行。

- `scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1043.py`
  - CLI 入口。
  - 支持 `--require-receipt-ready`，失败时可作为 gate 返回非 0。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1043.py`
  - 覆盖 ready path、requested use 漂移、source path 漂移、source evidence 状态改变、CLI 失败退出和 output wiring。

- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 v1043 next-step 常量，路由到下一步 receipt contract check。

## 维护性调整

v1043 没有继续从 v1042/v1041 模块导入几个 source 常量，而是在本模块内定义：

- `SOURCE_REVIEW_JSON_FILENAME`
- `SOURCE_REVIEW_READY_KEY`
- `SOURCE_REVIEW_STATUS`
- `SOURCE_LOOKUP_KEY_PREFIX`

原因是这些值是 v1043 对 source artifact 的 contract 期望，本身是稳定字符串；直接导入 v1042/v1041 会触发更长的历史 governance import 链，在 Windows + pytest assertion rewrite 下容易出现递归过深问题。

这个调整是 contract-preserving 的：它不改变字段语义，只减少不必要的运行时依赖。

## 核心字段

`receipt` 字段包含：

- `receipt_ready`：本版 receipt 是否可消费。
- `receipt_id`：稳定 receipt ID。
- `receipt_status`：lookup receipted 状态。
- `consumer_name`：下游 lookup reader 名称。
- `requested_use` / `granted_use`：请求和实际授予的使用范围。
- `receipt_index_review_path` / `receipt_index_review_sha256`：source review 证据路径与 digest。
- `lookup_keys`：从 v1042 review 继承的 lookup key。
- `promotion_ready=False` 和 `approved_for_promotion=False`：明确阻断推广。
- `next_step`：路由到 v1043 contract check。

`consumer_receipts` 字段是给下游读取的行式凭证：

- consumer
- lookup key
- receipt index id
- source receipt id
- receipt id
- granted use
- promotion state
- receipt status

## 检查项说明

`_checks` 一共保护 25 个条件，重点包括：

- v1042 source review 文件仍存在。
- source review status 和 decision 都 ready。
- requested use 必须是 downstream governance lookup only。
- granted use 必须仍是 lookup-only。
- source index lookup ready 和 contract check ready。
- source evidence 必须是 2 条且都有 digest。
- lookup key 必须使用 v1041 source namespace。
- source receipt、source check、source review、origin index 路径都还存在。
- consumer boundary 和 model quality claim 不变。
- promotion 字段必须保持 false。

## 测试覆盖

聚焦测试验证：

- ready v1042 review 可以生成 receipt。
- requested use 改成 production promotion 会失败。
- source review path 漂移会失败。
- source evidence status 改成 fail 会失败。
- CLI 在 `--require-receipt-ready` 下遇到坏 review 会返回 `SystemExit(1)`。
- artifact writer 真实输出 JSON/CSV/TXT/Markdown/HTML。

## 运行证据

运行证据归档在：

- `e/1043/解释/receipt-v1043`
- `e/1043/图片/v1043-receipt.png`

真实 CLI 输出显示：

```text
receipt_ready=True
granted_use=downstream_governance_lookup_only
lookup_key_count=1
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

## 一句话总结

v1043 把 v1042 review 结果落成可消费的 downstream lookup-only receipt，同时把 source contract 常量局部化，减少长链导入带来的维护风险。
