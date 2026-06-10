# v1069 publication receipt index 代码讲解

## 本版目标和边界

v1069 的目标是把 v1067 receipt 和 v1068 contract check 索引成 digest-backed lookup evidence。

这版不是新的训练能力，而是交接治理能力的继续收口：v1068 已经证明 receipt 可从 v1066 review 重建，v1069 再把 receipt 与 contract check 打包成 lookup index，方便下一轮 review 直接消费。

本版不训练模型，不修改 checkpoint，不批准 production promotion。

## 前置链路

1. v1067：记录 v1066 review 的 lookup-only receipt。
2. v1068：对 v1067 receipt 做 contract check。
3. v1069：把 v1067 receipt + v1068 check 编成 lookup index。

这条链路的核心价值是：receipt 和 check 不只是存在，而且能被编成下一步可消费的索引证据。

## 关键新增文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1069.py`
  - 核心 index builder。
  - 读取 v1067 receipt 和 v1068 check，校验它们仍然是 downstream lookup only。
  - 生成 `receipt_index_rows`、`source_evidence_rows`、`receipt_index`、`summary` 和 `interpretation`。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1069_artifacts.py`
  - 负责 JSON/CSV/TXT/Markdown/HTML 输出。
  - HTML 页面用于 Playwright 截图和人工审阅。

- `scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1069.py`
  - CLI 入口。
  - 接收 `--receipt` 和 `--receipt-check` 两个输入。
  - `--require-index-ready` 和 `--require-lookup-ready` 可作为 gate。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1069.py`
  - 覆盖 ready path、granted use 篡改、contract check 不 ready、artifact/CLI wiring。

- `e/1069/解释/receipt-index-v1069/`
  - 真实 CLI 输出，是本版最终证据。

- `e/1069/图片/v1069-receipt-index.png`
  - Playwright MCP 截图证据。

## 核心数据结构

### `receipt_index_rows`

`receipt_index_rows` 只有一行，但它承载了最关键的索引关系：

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

这里的目标是把 lookup key 和 source chain 绑定紧，不让后续模块拿到一份脱链索引。

### `source_evidence_rows`

`source_evidence_rows` 固定 2 条：

- receipt
- receipt_check

每条都保存 `kind`、`path`、`sha256`、`status`，便于后续审阅来源文件是否仍存在。

### `check_rows`

`check_rows` 保护以下边界：

- receipt 文件存在。
- receipt check 文件存在。
- receipt 和 receipt check 均为 pass。
- receipt decision 与 source ready key 对齐。
- lookup scope、granted use、consumer boundary、model quality claim 保持 downstream lookup only。
- source next steps 仍然是 `check_v1067` 和 `index_v1068`。

本版真实运行中共有 25 个检查通过，失败数为 0。

## 运行流程

1. CLI 接收 v1067 receipt 目录和 v1068 check 目录。
2. `locate_receipt_v1069()` 与 `locate_receipt_check_v1069()` 定位对应 JSON。
3. builder 读取两份 JSON，生成 check rows 和 receipt index。
4. artifact writer 输出 JSON/CSV/TXT/Markdown/HTML。
5. `resolve_exit_code()` 在 `--require-index-ready` / `--require-lookup-ready` 下决定是否返回非零退出码。

## 测试覆盖

focused 测试结果：

```text
4 passed in 0.45s
```

测试保护点：

- ready receipt + check 可以生成 index。
- `granted_use` 改成 production promotion 时失败。
- contract check 不 ready 时失败。
- sidecar 输出和 CLI wiring 都可用。

全量验证待回填：

- full pytest: `2733 passed in 633.92s`
- source hygiene: `2138/2138 clean`

## 运行证据

真实 CLI 输出确认：

- `status=pass`
- `index_ready=True`
- `lookup_scope=downstream_governance_lookup_only`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `lookup_ready=True`
- `contract_check_ready=True`
- `promotion_ready=False`
- `failed_check_count=0`

Playwright MCP 截图：

- `e/1069/图片/v1069-receipt-index.png`

## 一句话总结

v1069 把 v1067 receipt 和 v1068 contract check 编成 lookup index，让下一轮 review 拿到的是路径完整、digest 可查、边界清晰的治理证据。
