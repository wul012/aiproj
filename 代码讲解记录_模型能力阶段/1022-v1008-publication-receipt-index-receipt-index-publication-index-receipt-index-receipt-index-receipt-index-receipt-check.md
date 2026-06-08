# v1008 publication receipt index receipt index publication index receipt index receipt index receipt index receipt check

## 目标与边界

v1008 的目标是复核 v1007 生成的 downstream lookup-only receipt 是否仍然能从源 v1006 receipt-index review 原样重建。v1007 已经把 v1006 review 转成 consumer receipt；v1008 不再新增消费权限，而是把这份 receipt 放回同一套 builder 里重跑一遍，检查原始 JSON 与 rebuilt JSON 的稳定字段是否一致。

本版不训练模型，不改 checkpoint，不做模型能力提升声明，不把 lookup-only receipt 扩大成 production promotion，也不创建新的治理链。它只是为 v1007 receipt 加一层可复核入口，避免 receipt artifact 被手动篡改、source review 路径丢失、digest 或 next-step 漂移后仍被后续索引消费。

## 前置路线

1. v1005 把 v1003 receipt 与 v1004 receipt check 收成 receipt index。
2. v1006 review v1005 index，确认它只适合 downstream lookup-only receipt recording。
3. v1007 从 v1006 review 记录 lookup-only downstream receipt。
4. v1008 从 v1007 receipt 内记录的 `receipt_index_review_path` 回读 v1006 review，再调用 v1007 builder 重建 receipt。

这条路线的核心不是证明模型更强，而是证明模型能力阶段的 publication receipt 证据链不会因为单个 JSON 被改动而失去可追溯性。

## 关键新增文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_check_v1008.py`
  - v1008 核心 check builder。
  - 负责定位源 review、重建 v1007 receipt、比较原始 receipt 与 rebuilt receipt。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_check_v1008_artifacts.py`
  - 负责 JSON、CSV、TXT、Markdown、HTML 输出。
  - 保持渲染与核心检查分离，避免把 core 文件做成难维护的大文件。
- `scripts/check_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1008.py`
  - CLI 入口。
  - 支持输入 receipt JSON 或 receipt 输出目录，支持 `--require-pass` 和 `--force`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_check_v1008.py`
  - 覆盖合法 receipt、granted use 篡改、source review 丢失、digest 篡改、CLI 失败码和 sidecar 输出。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 v1008 pass 后的下一步路由常量。

## 核心数据结构

v1008 输出的顶层 report 不是 receipt 本身，而是 receipt contract check。关键字段包括：

- `status`
  - 所有 check 通过时为 `pass`，任一字段不能重建时为 `fail`。
- `decision`
  - pass 时固定为 `randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_contract_check_v1008_passed`。
- `receipt_path`
  - 当前被检查的 v1007 receipt JSON 路径。
- `source_receipt_index_review`
  - 从 receipt 顶层或 receipt body 解析出的 v1006 review 路径。
- `original_summary` / `rebuilt_summary`
  - 原始 v1007 summary 与重建 v1007 summary。
- `original_receipt` / `rebuilt_receipt`
  - 原始 v1007 receipt body 与重建 v1007 receipt body。
- `check_rows`
  - 44 条检查行。
- `summary.contract_check_ready`
  - 只有 status pass 才为 `True`。

## 核心流程

CLI 流程：

```text
receipt-or-dir
 -> locate_receipt_v1008
 -> read_json_report
 -> build_*_receipt_check_v1008
 -> write_*_outputs
 -> resolve_exit_code
```

builder 流程：

```text
original receipt
 -> _resolve_source_review_path
 -> read v1006 review JSON
 -> build v1007 receipt again
 -> compare original vs rebuilt
 -> emit check report
```

`_resolve_source_review_path()` 会优先读顶层 `receipt_index_review_path`，再读 receipt body 内的同名字段。如果路径是相对路径，会以 receipt JSON 所在目录为参照补一次。这能覆盖归档目录、临时测试目录和后续下游模块的常见输入形态。

`_rebuild_receipt()` 不手写字段，也不复制 v1007 逻辑，而是直接调用：

```text
build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1007
```

这样 v1008 检查的是“v1007 的真实构建契约是否还能重跑”，而不是另写一套容易漂移的影子逻辑。

## 检查项含义

v1008 检查分三组。

第一组是顶层 rebuild 检查：

- source review 文件必须存在。
- 顶层 `status` 必须一致。
- 顶层 `decision` 必须一致。
- `failed_count` 必须一致。
- `receipt_index_review_sha256` 必须一致。
- `consumer_receipts` 必须一致。

第二组是 summary 字段检查，覆盖：

- v1007 ready 标记。
- receipt id/type/status。
- consumer name 与 granted use。
- receipt index row count、source evidence count、lookup key count。
- promotion 与 approved_for_promotion 必须保持 False。
- consumer boundary、blocked uses、next step。
- passed/failed check count。

第三组是 receipt body 字段检查，覆盖：

- receipt_ready。
- requested/granted use。
- receipt_index_review_path。
- lookup_keys。
- review id/status。
- source receipt index、source receipt、source receipt check 路径。
- model quality claim 和 no-promotion 边界。

这些检查让 v1008 可以识别两类问题：一类是 v1007 receipt 被改过；另一类是源 v1006 review 缺失或 digest 不再对应。

## 输入输出与证据角色

真实运行输入：

```text
e/1007/解释/receipt-v1007/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1007.json
```

真实运行输出：

```text
e/1008/解释/receipt-check-v1008/
```

该目录下的 JSON、CSV、TXT、Markdown、HTML 都是最终证据，不是临时文件。

- JSON 供后续 v1009 index 消费。
- CSV 用于审阅 44 条 check row。
- TXT 是命令行摘要。
- Markdown 用于人工归档。
- HTML 用于 Playwright MCP 截图和浏览器复核。

## 测试覆盖

focused 测试覆盖 6 个场景：

- 合法 v1007 receipt 可以从 v1006 review 重建，check pass。
- 篡改 summary/body 的 `granted_use` 会失败。
- 删除或改错 source review 路径会失败。
- 篡改 `receipt_index_review_sha256` 会失败。
- CLI 在 `--require-pass` 下遇到失败 report 返回 `1`。
- artifact writer 与 CLI 会写出 JSON/CSV/TXT/Markdown/HTML。

这些测试没有只断言“脚本能运行”，而是覆盖了 v1008 最关键的可重建契约。

## 运行证据

归档说明：

```text
e/1008/解释/说明.md
```

HTML 截图：

```text
e/1008/图片/v1008-receipt-check.png
```

真实运行摘要：

```text
status=pass
failed_count=0
contract_check_ready=True
original_receipt_status=publication_index_receipt_index_receipt_index_receipt_index_lookup_receipted
rebuilt_receipt_status=publication_index_receipt_index_receipt_index_receipt_index_lookup_receipted
original_granted_use=downstream_governance_lookup_only
rebuilt_granted_use=downstream_governance_lookup_only
passed_check_count=44
failed_check_count=0
```

## 一句话总结

v1008 让 v1007 lookup-only receipt 具备了可重建 contract check，后续索引消费的就不是一份孤立 JSON，而是一份能回到源 review 重跑验证的证据。
