# v977 randomized holdout publication receipt packet index

## 目标与边界

v977 的目标是给 v975/v976 形成的 `publication receipt packet` 交接产物补一个索引入口：读取 v975 packet 和 v976 contract check，确认二者一致且仍然只允许治理查询，然后生成一个 lookup-only `receipt_packet_index`。

它解决的是证据消费问题，不是模型能力问题。v977 不训练模型、不生成新 checkpoint、不扩大 hidden holdout 的质量声明，也不允许 promotion。所有输出都继续保留 `promotion_ready=False`、`approved_for_promotion=False` 和 `downstream_governance_lookup_only`。

## 前置路线

这一版接在 v975 和 v976 后面：

- v975 把 v974 receipt review 和 v973 receipt 打成 digest-backed receipt packet。
- v976 从 v974 review 重新推导 v975 packet，验证 packet contract 没有被篡改。
- v977 把 v975 packet 与 v976 check 组合成一个索引，让后续 review 不需要人工拼接两个目录。

因此 v977 不是新治理链，而是对既有 receipt packet 产物做“可查入口”的收口。

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index.py`
  - 核心 builder。
  - 负责定位 packet/check JSON、读取报告、运行 29 条一致性检查、生成 `receipt_packet_index` 和 `summary`。
- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_artifacts.py`
  - 输出层。
  - 负责 JSON、CSV、text、Markdown、HTML 五种证据格式。
- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index.py`
  - CLI 入口。
  - 支持目录或 JSON 文件输入，并提供 `--require-index-ready`、`--require-lookup-ready`、`--require-promotion-ready` 退出码控制。
- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index.py`
  - 单测。
  - 覆盖正常索引、contract check 失败、源 review 缺失、CLI 失败退出码、输出格式和 locator。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 v977 next-step 常量，指向下一步 review。
- `src/minigpt/__init__.py`
  - 补包级懒加载导出，保持和前序版本一致的导入方式。

## 核心数据结构

### `receipt_packet_index`

`receipt_packet_index` 是本版的主产物，核心字段包括：

- `index_ready`：所有检查通过时为 `True`。
- `receipt_packet_index_id`：v977 的索引 ID。
- `lookup_scope` / `granted_use`：都必须是 `downstream_governance_lookup_only`。
- `receipt_packet_index_rows`：真正给下游查找使用的索引行，本版应只有 1 行。
- `source_packet_rows`：来自 v975 packet 的原始 packet rows。
- `source_evidence_rows`：来自 v975 packet 的两条证据行，指向 receipt review 与 publication receipt。
- `contract_check_ready`：来自 v976 check，必须为 `True`。
- `promotion_ready` / `approved_for_promotion`：固定为 `False`。
- `next_step`：通过时进入 `review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index`。

### `summary`

`summary` 是 CLI、HTML 顶部卡片和后续模块读取的轻量摘要。关键字段是：

- `...publication_receipt_packet_index_ready=True`
- `receipt_packet_index_row_count=1`
- `source_evidence_count=2`
- `lookup_ready=True`
- `contract_check_ready=True`
- `promotion_ready=False`
- `passed_check_count=29`
- `failed_check_count=0`

## 29 条检查保护什么

本版检查分成几组：

1. 输入文件存在：packet 和 contract check JSON 必须可读。
2. packet 就绪：v975 的 `status`、`decision`、summary ready 和 packet body ready 必须一致。
3. contract check 就绪：v976 的 `status`、`decision`、`contract_check_ready` 必须通过。
4. packet 与 check 一致：packet status、granted use、promotion flag、source evidence count 必须和重建结果一致。
5. source evidence 不丢：receipt review、publication receipt、source index review、publication、publication check、source review、source index 等路径仍然存在。
6. lookup 约束不变：lookup key 必须保持 `publication:` 命名空间，consumer boundary 仍是治理查询，质量声明仍是 bounded hidden holdout claim。
7. 禁止 promotion：packet、original、rebuilt 三侧 promotion 都必须为 `False`。
8. 路由正确：v975 的下一步必须是 check，v976 的下一步必须是 index。

这些检查的意义是：索引不是简单复制 JSON，而是在生成前再次确认 packet、check、源证据和路由都还处在同一个治理闭环里。

## CLI 流程

CLI 的执行顺序是：

1. `locate_...receipt_packet()` 支持输入目录或 JSON 文件。
2. `locate_...receipt_packet_check()` 支持输入目录或 JSON 文件。
3. `prepare_output_dir()` 在 `--force` 下清空旧输出。
4. `read_json_report()` 读取两个报告。
5. `build_...receipt_packet_index()` 生成报告。
6. `write_...outputs()` 写 JSON、CSV、text、Markdown、HTML。
7. `resolve_exit_code()` 根据 `--require-index-ready`、`--require-lookup-ready`、`--require-promotion-ready` 决定是否返回失败。

`--require-promotion-ready` 在本版真实证据里会失败，这是有意的：v977 只允许 lookup，不允许 promotion。

## 运行证据

真实运行使用 v975 和 v976 的归档产物，输出在 `e/977/解释/publication-receipt-packet-index-publication-receipt-packet-index/`。关键结果：

```text
status=pass
decision=randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_ready
failed_count=0
lookup_ready=True
contract_check_ready=True
receipt_packet_index_row_count=1
source_evidence_count=2
passed_check_count=29
failed_check_count=0
promotion_ready=False
```

Playwright MCP 截图保存在 `e/977/图片/`，页面顶部卡片展示 pass/ready/failed 状态，表格展示索引行、source evidence 和 checks。

## 测试覆盖

本版定向测试覆盖：

- 合法 packet + contract check 生成 ready index。
- contract check 失败时 index 失败。
- 手动删除 source review 路径时报告 `source_review_file_exists`。
- CLI 在 `--require-index-ready` 下遇到篡改 packet 会返回 `1`。
- 输出函数写出 JSON、CSV、text、Markdown、HTML。
- locator 支持目录输入，能自动找到默认 JSON 文件。

这些测试保护了 v977 的核心合同：不能用失败的 check 生成索引，不能在源证据丢失时继续声称 ready，也不能因为 CLI 输入目录变化而破坏使用方式。

## 一句话总结

v977 把已通过 contract check 的 publication receipt packet 做成 lookup-only 索引入口，让后续 review 可以消费单一、可复核、仍然禁止 promotion 的治理产物。
