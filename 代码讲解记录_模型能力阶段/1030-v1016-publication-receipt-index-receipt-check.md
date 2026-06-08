# v1016：publication receipt index receipt contract check

## 本版目标和边界

v1016 的目标是检查 v1015 生成的 short-name lookup-only receipt 是否能从它声明的 source review 重新推导出来。它相当于给 v1015 receipt 加一层可复核入口，防止 receipt JSON 被手动改宽、source review 路径丢失、source digest 漂移，或 `granted_use` 被改成 production promotion。

本版不做模型能力提升，不改变训练数据，不声明模型可以生产使用。它仍然只属于模型能力阶段里的治理证据链：验证 artifact 自身一致，而不是证明模型质量变强。

## 前置能力

v1015 已经记录了：

- `receipt_status=publication_receipt_index_receipt_v1015_lookup_receipted`
- `granted_use=downstream_governance_lookup_only`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `promotion_ready=False`
- `next_step=check_randomized_holdout_publication_receipt_index_receipt_v1015`

v1016 读取 v1015 receipt，找到里面的 `receipt_index_review_path`，再使用 v1015 builder 从 v1014 review 重建一个 receipt，并比较原始 receipt 与 rebuilt receipt。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_check_v1016.py`
  - v1016 contract check 核心模块。
  - 负责定位 receipt、读取 JSON、重建 receipt、比较字段并生成 check report。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_check_v1016_artifacts.py`
  - 把 check report 输出为 JSON、CSV、Text、Markdown、HTML。
  - HTML 用于运行截图，CSV 保存每条 check row。

- `scripts/check_randomized_holdout_publication_receipt_index_receipt_v1016.py`
  - CLI 入口。
  - 支持输入 receipt JSON 或 receipt 输出目录。
  - `--require-pass` 让失败 check 返回非零退出码。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_check_v1016.py`
  - 覆盖成功重建、用途篡改、source review 丢失、source digest 篡改、CLI 失败返回码和 artifact 输出。

- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 `RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_CHECK_V1016_NEXT_STEP`。
  - check 通过后进入 `index_randomized_holdout_publication_receipt_index_receipt_v1016`。

## 核心数据结构

v1016 report 包含：

- `original_summary` / `rebuilt_summary`
  - 保存原始 v1015 receipt summary 和重建 summary。

- `original_receipt` / `rebuilt_receipt`
  - 保存原始 receipt body 和重建 receipt body。

- `check_rows`
  - 每条字段级比较结果。
  - 字段包括 `id`、`status`、`actual`、`detail`。

- `summary`
  - 面向 CLI、README 和下一版 index 的稳定摘要。
  - 关键字段包括 `contract_check_ready`、`original_receipt_status`、`rebuilt_receipt_status`、`original_granted_use`、`rebuilt_granted_use`、`original_lookup_key_count`、`rebuilt_lookup_key_count`、`original_promotion_ready`、`rebuilt_promotion_ready` 和 `next_step`。

## 核心函数

`locate_receipt_v1016(path)` 负责把输入规范化。如果传入目录，会自动查找 `randomized_holdout_publication_receipt_index_receipt_v1015.json`；如果传入文件，则直接使用。

`build_randomized_holdout_publication_receipt_index_receipt_check_v1016(...)` 是主入口：

1. 从原始 receipt report 读取 `summary` 和 `receipt`。
2. 调用 `_resolve_source_review_path(...)` 找到 v1014 source review。
3. 调用 `_rebuild_receipt(...)`，重新执行 v1015 builder。
4. 调用 `_checks(...)` 比较原始和重建结果。
5. 输出 status、decision、issues、check_rows、summary 和 interpretation。

`_checks(...)` 先检查 source review 是否存在，再比较顶层字段：

- `status`
- `decision`
- `failed_count`
- `receipt_index_review_sha256`
- `consumer_receipts`

然后通过 `SUMMARY_FIELDS` 和 `RECEIPT_FIELDS` 批量比较稳定字段。这样新增字段清单集中在列表里，后续要扩展或裁剪比较范围时不会散落在很多 if 里。

`_rebuild_receipt(...)` 是本版的核心动作。它读取 source review，再调用：

```python
build_randomized_holdout_publication_receipt_index_receipt_v1015(
    read_review_json(source_review),
    receipt_index_review_path=source_review,
)
```

这说明 v1016 检查的不是“原 JSON 看起来像 pass”，而是“原 JSON 能从声明来源重新生成”。

## 测试覆盖

focused 测试保护了六个场景：

- ready receipt 可以通过 contract check。
- `granted_use` 被改成 `production_promotion` 时失败。
- `receipt_index_review_path` 指向不存在文件时失败。
- `receipt_index_review_sha256` 被篡改时失败。
- CLI `--require-pass` 对失败 report 返回 `1`。
- JSON/CSV/Text/Markdown/HTML 输出和目录定位都连通。

测试使用 `runs/test-temp-v1016` 作为短临时根，避免 Windows `%TEMP%` 路径和历史长 source filename 叠加后触发路径长度问题。

全量回归结果为：

```text
2456 passed in 410.54s
```

## 运行证据

真实 CLI 输出写入：

- `e/1016/解释/receipt-check-v1016/randomized_holdout_publication_receipt_index_receipt_check_v1016.json`
- `e/1016/解释/receipt-check-v1016/randomized_holdout_publication_receipt_index_receipt_check_v1016.html`

关键结果：

```text
status=pass
decision=randomized_holdout_publication_receipt_index_receipt_contract_check_v1016_passed
failed_count=0
contract_check_ready=True
original_receipt_status=publication_receipt_index_receipt_v1015_lookup_receipted
rebuilt_receipt_status=publication_receipt_index_receipt_v1015_lookup_receipted
original_granted_use=downstream_governance_lookup_only
rebuilt_granted_use=downstream_governance_lookup_only
passed_check_count=44
failed_check_count=0
```

Playwright MCP 截图归档在：

```text
e/1016/图片/v1016-receipt-check.png
```

截图证明 HTML 报告能打开，并显示 `Contract Summary` 和 `Checks` 两个关键区域。

## 一句话总结

v1016 让 v1015 的 short-name receipt 从“已生成”升级为“可从源 review 重建并逐字段复核”。
