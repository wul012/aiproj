# v1087 publication receipt

## 本版目标

v1087 的目标是把 v1086 的 receipt index review 记录为新的 lookup-only receipt。v1086 只是确认 v1085 index 可以进入 receipt recording，v1087 则把这个审阅结果固化为消费侧 receipt，供下一版 contract check 重建和比对。

本版不做的事：

- 不训练模型
- 不提升模型质量声明
- 不接受 candidate
- 不打开 production promotion
- 不修改 v1086 review，只读消费它

## 路线来源

v1083 记录了 v1082 review 的 receipt，v1084 对 receipt 做 contract check，v1085 将 receipt 和 check 做成 digest-backed index，v1086 审阅这个 index。v1087 延续同一条四步循环，把 v1086 review 变成下一轮可检查 receipt。

这仍然是模型能力阶段里的证据链治理。它证明的是 receipt 产物可追溯、可复核、可被后续工具消费，不证明 tiny GPT 本身已经具备生产级生成能力。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1087.py`
  - 核心 receipt builder。
  - 读取 v1086 review，验证 ready key、review status、lookup-only granted use、source evidence、source path 和 next-step。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1087_artifacts.py`
  - 生成 JSON/CSV/TXT/MD/HTML sidecar。
  - 这些 sidecar 是治理证据视图，不是训练 checkpoint。

- `scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1087.py`
  - CLI 入口。
  - 接收 v1086 review 文件或输出目录，写出 v1087 receipt evidence。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1087.py`
  - 覆盖正常通过、requested use 被篡改、source path 漂移、source evidence 状态变化和 CLI sidecar。

- `e/1087/解释/receipt-v1087/`
  - 真实运行输出目录。
  - 下一版 contract check 应消费这里的 JSON。

## 核心数据结构

receipt 结果包含：

- `summary`
  - 保存 `receipt_id`、`receipt_status`、`consumer_name`、`granted_use`、`lookup_key_count`、`source_evidence_count`、`promotion_ready` 和 `next_step`。
  - 其中 `promotion_ready` 固定为 `False`，保护 no-promotion 边界。

- `receipt`
  - 保存消费侧 receipt 主体。
  - 包括 `receipt_index_review_path`、`receipt_index_review_sha256`、`source_receipt_index_path`、`source_receipt_path`、`source_receipt_check_path`、`source_review_path` 和 `source_receipt_index_origin_path`。

- `consumer_receipts`
  - 将 v1086 review 中的 lookup key 映射到本次 receipt。
  - 只授予 `downstream_governance_lookup_only`，不允许 promotion。

- `check_rows`
  - 每一项都是一个 contract 断言。
  - 例如 review ready、lookup-only、source evidence count、source path exists、source next-step matches。

## 核心流程

1. CLI 定位 v1086 review JSON。
2. builder 读取 review summary、review body、receipt index rows 和 source evidence rows。
3. `_checks` 验证 review 已通过、ready key 为真、lookup-only 边界未漂移、source evidence 仍然是两条且状态为 pass。
4. `_receipt` 写出新的 receipt id、consumer name、granted use、source path 和下一步 contract-check 路由。
5. artifact writer 生成 JSON、CSV、TXT、Markdown 和 HTML。

## 测试覆盖

- 合法 v1086 review 可以生成 `receipt_ready=True`，保护正常 recording 流程。
- `requested_use` 改成 `production_promotion` 会失败，保护 lookup-only 边界。
- `source_review_path` 改到不存在路径会失败，保护 source path 可追踪性。
- `source_evidence_rows` 状态改成 fail 会失败，保护证据行不能被悄悄降级。
- CLI 测试确认目录输入、输出文件名和 `--require-receipt-ready` 行为可用。

## 运行证据

真实命令输出确认：

- `status=pass`
- `receipt_ready=True`
- `receipt_status=publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1087_lookup_receipted`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `promotion_ready=False`
- `passed_check_count=25`
- `failed_check_count=0`

Playwright MCP screenshot 已确认 HTML 页面可读，并能看到 receipt boundary、consumer receipt 和 checks。

## 验证

- focused v1087 tests：`6 passed in 0.66s`
- source hygiene：`2211/2211 clean`
- py_compile：新增模块、artifact writer、CLI、测试均通过。
- real CLI evidence：输出 JSON/CSV/TXT/MD/HTML sidecar。
- full pytest：`2828 passed in 643.54s`
- Playwright MCP screenshot：`e/1087/图片/v1087-receipt.png`
- `git diff --check` 会在提交前完成。

## 一句话总结

v1087 把 v1086 审阅过的 receipt index 固化为 downstream lookup-only receipt，使下一步 contract check 有稳定、可追溯、仍受 no-promotion 约束的输入。
