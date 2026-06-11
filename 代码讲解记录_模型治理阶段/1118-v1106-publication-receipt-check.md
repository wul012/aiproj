# v1106 publication receipt contract check

## 本版目标与边界

v1106 的目标是给 v1105 lookup-only receipt 补一层重建式 contract check。它读取 v1105 receipt，再根据 receipt 内保存的 v1104 review 路径重新跑 v1105 receipt builder，最后比较原始 receipt 和重建 receipt 的关键字段。

本版解决的是“交接产物是否仍能从源证据推导出来”的问题。它不训练模型，不修改 v1105 receipt，不放宽 downstream 使用边界，也不把治理证据包装成模型质量提升。候选模型是否值得 promotion 仍然保持 blocked，v1106 只保护 receipt 的可复核性。

## 前置路线

这一版承接的路线是：

```text
v1103 index -> v1104 review -> v1105 receipt -> v1106 contract check
```

v1104 已经审阅 v1103 receipt index，v1105 把这份 review 记录为 lookup-only receipt。v1106 做的是下一步：不直接信任 v1105 的 JSON，而是回到 v1104 review 再生成一次 receipt，确认两者一致。

## 关键文件

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1106.py
```

核心 contract check 模块，负责定位 receipt、读取 JSON、重建 receipt、生成 comparison 和 check rows。

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1106_artifacts.py
```

artifact writer，负责把同一份 report 写成 JSON、CSV、TXT、Markdown 和 HTML。机器消费优先看 JSON，人工复核优先看 HTML/Markdown。

```text
scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1106.py
```

CLI 入口，支持 receipt JSON 或目录输入，`--require-pass` 会在 check 失败时返回非零退出码。

```text
tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1106.py
```

专项测试，覆盖合法 receipt、篡改字段、缺失 source review、篡改 source digest、CLI require-pass 和 artifact 输出。

```text
f/1106/解释/receipt-check-v1106
f/1106/图片/v1106-receipt-check.png
```

运行证据目录。前者是可复核 sidecar，后者是 Playwright MCP 打开的 HTML 截图。

## 入口与参数

本版 CLI：

```powershell
python -B scripts\check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1106.py f\1105\解释\receipt-v1105 --out-dir f\1106\解释\receipt-check-v1106 --require-pass --force
```

输入可以是：

- receipt JSON 文件。
- 包含 receipt JSON 的输出目录。

`locate_receipt_v1106` 会处理这两种输入。如果输入是目录，它会寻找 v1106 约定的 JSON 文件名；如果输入是文件，它直接读取该文件。

## 输出模型

v1106 report 的主要字段是：

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

其中最重要的是 `comparison` 和 `summary`。

`comparison` 同时保存原始 receipt 和重建 receipt 的对照值，例如：

```text
original_receipt_status
rebuilt_receipt_status
original_granted_use
rebuilt_granted_use
original_lookup_key_count
rebuilt_lookup_key_count
original_promotion_ready
rebuilt_promotion_ready
```

`summary` 给后续 index 一个稳定读取面：

```text
contract_check_ready=True
failed_check_count=0
next_step=index_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1106
```

这样 v1107 不需要重新理解所有字段，只要消费 v1106 的 JSON sidecar，就能知道 receipt/check 是否可以被索引。

## 上游证据

本版读取的真实上游输入是：

```text
f/1105/解释/receipt-v1105
```

v1105 receipt 内部指向：

```text
f/1104/解释/receipt-index-review-v1104
```

v1106 不是只检查文件存在，而是使用这条引用重新运行 v1105 receipt builder。只要 v1105 receipt 被篡改、source review 路径丢失、source hash 改变、granted use 被放宽，contract check 都会失败。

## 核心流程

1. CLI 调用 `locate_receipt_v1106` 定位 v1105 receipt JSON。
2. builder 读取原始 receipt report，并提取 `summary`、`receipt` 和 source review 路径。
3. builder 检查 source review 文件是否存在。
4. 调用 v1105 receipt builder，从 v1104 review 重建 receipt report。
5. `_checks` 逐项比较原始 report 与重建 report。
6. `_decision` 根据是否存在 failed checks 生成 pass/fix 决策。
7. artifact writer 输出 JSON、CSV、TXT、Markdown、HTML。
8. Playwright MCP 打开 HTML，确认 `Contract Summary` 和 `Checks` 可读，并保存截图。

## 关键检查

- `source_receipt_file_exists`：保护输入 receipt 真实存在。
- `source_review_file_exists`：保护 receipt 引用的 v1104 review 没有丢失。
- `rebuilt_receipt_passed`：保护从 v1104 review 重建 receipt 的过程成功。
- `status_matches`：保护 report 状态没有漂移。
- `decision_matches`：保护原始 decision 与重建 decision 一致。
- `receipt_id_matches`：保护 receipt 身份一致。
- `receipt_status_matches`：保护 lookup-only receipt 状态一致。
- `consumer_name_matches`：保护下游消费者身份没有被替换。
- `granted_use_matches`：保护用途仍是 `downstream_governance_lookup_only`。
- `lookup_key_count_matches`：保护 lookup key 没有丢失或膨胀。
- `source_evidence_count_matches`：保护 source evidence 数量一致。
- `source_review_sha256_matches`：保护 receipt 仍绑定同一份 v1104 review。
- `promotion_ready_matches_false`：保护原始和重建结果都没有打开 promotion。

这些检查比单纯“文件能读”更硬，因为它要求同一份上游证据能够重建出同一份 receipt 语义。

## 测试覆盖

focused tests 覆盖 6 个场景：

- 合法 v1105 receipt 可以通过 contract check。
- 手动篡改 granted use 后 check 失败。
- 删除 source review path 后 check 失败。
- 篡改 source evidence digest 后重建比较失败。
- `--require-pass` 在失败 check 下返回非零。
- artifact writer 和 CLI 生成完整 JSON/CSV/TXT/Markdown/HTML sidecar。

这些断言保护的是 contract check 的核心语义：同源重建、字段一致、失败可阻断。

## 运行证据

真实 CLI 输出确认：

```text
status=pass
contract_check_ready=True
original_granted_use=downstream_governance_lookup_only
rebuilt_granted_use=downstream_governance_lookup_only
original_lookup_key_count=1
rebuilt_lookup_key_count=1
original_promotion_ready=False
rebuilt_promotion_ready=False
passed_check_count=46
failed_check_count=0
```

验证命令包括：

```text
python -m py_compile ...
python -m pytest tests/test_..._receipt_check_v1106.py -q -o cache_dir=runs/pytest-cache-v1106-focused
python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-v1106
git diff --check
```

source hygiene 结果是 `2279/2279 clean`。Playwright MCP 打开 HTML sidecar 后，页面快照确认 `Contract Summary` 和 `Checks` 可见，截图保存到：

```text
f/1106/图片/v1106-receipt-check.png
```

## 链路角色

v1106 是 receipt 之后、下一轮 index 之前的 contract check。它让 v1105 receipt 不只是“被记录”，而是“可从上游 review 重建并逐字段验证”。后续 v1107 可以把 v1105 receipt 和 v1106 check 合并成 lookup index，但仍不触发模型 promotion。

## 一句话总结

v1106 把 v1105 lookup-only receipt 推进为可重建、可阻断、可索引的 contract-checked governance artifact。
