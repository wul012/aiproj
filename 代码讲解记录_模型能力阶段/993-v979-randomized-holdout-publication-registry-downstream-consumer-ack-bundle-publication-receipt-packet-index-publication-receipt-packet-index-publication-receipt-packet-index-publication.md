# v979 randomized holdout publication receipt packet index publication

## 目标与边界

v979 的目标是把 v978 review 发布成 lookup-only publication。v978 已经确认 v977 index 可进入 publication；v979 负责生成一个明确的 publication artifact，记录发布状态、发布用途、源 review/index/packet/check 路径以及下一步 contract check。

本版不做模型训练，不改变模型 checkpoint，不把候选模型提升为生产模型。`published_use=downstream_governance_lookup_only`，`promotion_ready=False`，`approved_for_promotion=False` 是本版的核心边界。

## 前置路线

这一版接在 v978 后面：

- v977 生成 receipt packet index。
- v978 review index，确认可进入 lookup-only publication。
- v979 发布 publication，给后续 v980 contract check 一个稳定输入。

这条路线仍然是治理证据链，不是模型能力提升链。

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_publication.py`
  - 核心 publication builder。
  - 读取 v978 review，运行 21 条检查，生成 `publication`、`summary` 和 `interpretation`。
- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_publication_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML。
  - 沿用短文件名 `randomized_holdout_publication_receipt_packet_index_publication_v979.*`。
- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_publication.py`
  - CLI 入口。
  - 支持目录输入，自动定位 v978 的短名 review JSON。
- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_publication.py`
  - 覆盖 ready publication、publish_ready 失败、index 文件缺失、allowed_use 漂移、输出格式和 CLI。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 v979 next step，指向 v980 contract check。
- `src/minigpt/__init__.py`
  - 增加包级懒加载导出。

## 核心数据结构

### `publication`

`publication` 是本版主产物：

- `publication_ready`：21 条检查全部通过时为 `True`。
- `publication_id`：v979 publication ID。
- `publication_status`：`published_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_lookup_only`。
- `receipt_packet_index_review_path`：v978 review 路径。
- `receipt_packet_index_path`：v977 index 路径。
- `source_packet_path` / `source_packet_check_path`：v975/v976 产物路径。
- `published_use`：固定为 `downstream_governance_lookup_only`。
- `publish_ready`、`lookup_ready`、`contract_check_ready`：全部来自 v978 review 的通过状态。
- `promotion_ready` / `approved_for_promotion`：固定为 `False`。
- `next_step`：进入 `check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_publication`。

### `summary`

`summary` 是后续 contract check 读取的摘要：

- `...publication_ready=True`
- `publication_status=...lookup_only`
- `published_use=downstream_governance_lookup_only`
- `receipt_packet_index_row_count=1`
- `source_packet_row_count=1`
- `source_evidence_count=2`
- `publish_ready=True`
- `lookup_ready=True`
- `contract_check_ready=True`
- `promotion_ready=False`
- `passed_check_count=21`
- `failed_check_count=0`

## 21 条检查保护什么

本版检查的重点是 publication 不能越权：

1. v978 review 文件必须存在，并且 `status=pass`。
2. v978 的 decision 和 ready summary 必须是 review ready。
3. `review_status` 必须批准 lookup-only publication。
4. v977 index、v975 packet、v976 packet check 文件仍然存在。
5. v978 review 必须同时具备 downstream、publish、lookup、contract 四个 ready。
6. index row、source packet row、source evidence 数量必须仍然是 1、1、2。
7. `allowed_use` 必须是 downstream lookup only。
8. consumer boundary 与 model quality claim 必须保持 bounded。
9. promotion 仍然必须为 False。
10. v978 failed check count 必须为 0。
11. v978 next step 必须指向 v979 publication。

这些检查让 publication 成为“受 review 约束的发布”，而不是把任意 review JSON 直接包装成已发布。

## 短 artifact 文件名

v978 已经暴露了 Windows 路径长度问题。v979 从一开始就采用短 artifact 文件名：

```text
randomized_holdout_publication_receipt_packet_index_publication_v979.json
randomized_holdout_publication_receipt_packet_index_publication_v979.csv
randomized_holdout_publication_receipt_packet_index_publication_v979.txt
randomized_holdout_publication_receipt_packet_index_publication_v979.md
randomized_holdout_publication_receipt_packet_index_publication_v979.html
```

模块名仍保留完整语义，运行产物文件名负责可维护性。

## 运行证据

真实运行输入 v978 review，输出在 `e/979/解释/publication-receipt-packet-index-publication-receipt-packet-index-publication-receipt-packet-index-publication/`。

关键结果：

```text
status=pass
publication_status=published_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_lookup_only
published_use=downstream_governance_lookup_only
publish_ready=True
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=21
failed_check_count=0
```

Playwright MCP 截图保存在 `e/979/图片/`，页面展示 publication boundary 和所有 check rows。

## 测试覆盖

本版测试覆盖：

- ready review 能生成 ready publication。
- review `publish_ready=False` 会导致失败。
- source index 文件缺失会失败。
- `allowed_use` 漂移为 production promotion 会失败。
- 输出函数写出五种格式。
- CLI 可从目录输入定位 v978 review，并在 require flags 下正常退出。

## 一句话总结

v979 把 v978 review 发布成 lookup-only publication，同时保持 no-promotion 和短 artifact 文件名策略，为 v980 contract check 做准备。
