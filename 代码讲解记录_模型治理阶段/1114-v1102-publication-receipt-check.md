# v1102 publication receipt contract check

本版目标是对 v1101 lookup-only receipt 做重建式 contract check：读取原始 receipt，找到它引用的 v1100 review，重新构建一份 receipt，然后比较关键字段是否一致。

它不训练模型，不修改 v1101 receipt，不把 contract check 结果解释成模型能力提升。它只回答一个工程问题：v1101 receipt 是否仍能从上游 review 推导出来，且用途、路径、digest 和 no-promotion 边界没有漂移。

## 入口

本版入口是 CLI：

```text
scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1102.py
```

核心模块是：

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1102.py
```

CLI 输入 v1101 receipt 目录或 JSON 文件，输出 JSON/CSV/TXT/Markdown/HTML sidecar。`--require-pass` 会在 contract check 失败时返回非零退出码。

## 输出模型

最外层 report 包含：

```text
status
decision
failed_count
issues
source_receipt_path
source_receipt
rebuilt_receipt
comparison
check_rows
summary
interpretation
```

关键字段是：

```text
contract_check_ready=True
original_granted_use=downstream_governance_lookup_only
rebuilt_granted_use=downstream_governance_lookup_only
original_promotion_ready=False
rebuilt_promotion_ready=False
```

`comparison` 是本版的核心证据：它把原始 receipt 与重建 receipt 放在同一份 report 中，后续 index 不需要再猜测 check 是否真的比较过。

## 上游证据

本版读取真实上游证据：

```text
f/1101/解释/receipt-v1101
```

v1101 receipt 里保存了 source review 路径和 hash，指向：

```text
f/1100/解释/receipt-index-review-v1100
```

v1102 通过这条引用重建 receipt。它不直接信任 v1101 的展示字段，而是把 receipt builder 再跑一次。

## 核心流程

1. CLI 定位 v1101 receipt JSON。
2. builder 读取原始 receipt report、summary 和 receipt body。
3. 根据 `receipt_index_review_path` 读取 v1100 review。
4. 调用 v1101 receipt builder 重建 receipt report。
5. `_checks` 比较 status、decision、receipt id/status、consumer、granted use、lookup key count、source evidence count、source review hash、source路径和 promotion 字段。
6. artifact writer 输出 JSON/CSV/TXT/Markdown/HTML。
7. Playwright MCP 打开 HTML sidecar 并保存截图到 `f/1102/图片`。

## 关键检查

- `source_receipt_file_exists`：保护 v1101 receipt 文件存在。
- `source_review_file_exists`：保护 receipt 引用的 v1100 review 仍可读取。
- `rebuilt_receipt_passed`：保护重建过程本身成功。
- `status_matches` 和 `decision_matches`：保护原始报告与重建报告一致。
- `receipt_id_matches` 和 `receipt_status_matches`：保护 receipt 身份和状态未漂移。
- `granted_use_matches`：保护用途仍是 downstream governance lookup only。
- `lookup_key_count_matches`：保护 lookup key 数量没有丢失或膨胀。
- `source_evidence_count_matches`：保护源证据数量一致。
- `promotion_ready_matches_false`：保护原始和重建结果都没有打开 promotion。
- `source_review_sha256_matches`：保护 receipt 仍绑定同一份 v1100 review。

## 测试覆盖

专项测试覆盖：

- 合法 v1101 receipt 可以通过 contract check。
- 手动篡改 granted use 会失败。
- 删除 source review path 会失败。
- 改动 source evidence status 后重建比较会失败。
- CLI `--require-pass` 对失败 check 返回非零。
- artifact writer 和 CLI 输出 JSON/CSV/TXT/Markdown/HTML。

这些测试保护的是“重建一致性”，不是简单存在性检查。

## 运行证据

真实命令消费 `f/1101/解释/receipt-v1101`，输出确认：

- `status=pass`
- `contract_check_ready=True`
- `original_granted_use=downstream_governance_lookup_only`
- `rebuilt_granted_use=downstream_governance_lookup_only`
- `original_lookup_key_count=1`
- `rebuilt_lookup_key_count=1`
- `original_promotion_ready=False`
- `rebuilt_promotion_ready=False`
- `passed_check_count=46`
- `failed_check_count=0`

验证侧跑了 focused v1102 tests（`6 passed in 0.32s`）、py_compile、source hygiene（`2263/2263 clean`）、`git diff --check` 和真实 CLI。Playwright MCP 页面快照确认 HTML 中存在 `Contract Summary` 和 `Checks`，截图保存为 `f/1102/图片/v1102-receipt-check.png`。

## 链路角色

v1102 位于这一轮链路的 contract-check 位置：

```text
v1095 receipt -> v1096 contract check -> v1097 index -> v1100 review -> v1101 receipt -> v1102 contract check
```

下一步是 index，把 receipt 和 check 汇总成可查询入口，不是 promotion。

## 一句话总结

v1102 把 v1101 receipt 从“已记录”推进为“已被源 review 重建验证、可进入下一步 index”的治理证据。
