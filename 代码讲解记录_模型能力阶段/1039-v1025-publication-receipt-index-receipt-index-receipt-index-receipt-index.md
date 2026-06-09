# v1025 publication receipt index receipt index receipt index receipt index 代码讲解

## 本版目标和边界

v1025 的目标是把 v1023 lookup-only receipt 与 v1024 receipt contract check 合并成一个 digest-backed receipt index。

它解决的问题是：下游 review 不应直接散读 receipt 和 check 两个文件，而应该通过一个带 source evidence digest 的索引入口读取。

本版不做模型训练，不修改推理逻辑，不放宽 promotion。`promotion_ready` 和 `approved_for_promotion` 继续保持 `False`。

## 前置能力

v1023 已经把 v1022 review 记录成 lookup-only receipt。v1024 又证明该 receipt 可以从 v1022 review 稳定重建。

v1025 接在这两者之后，做的不是重新验证 receipt 内容，而是把“receipt + contract check”打包成可复核索引，并记录两个输入文件的 SHA-256。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_v1025.py`
  - 构建 v1025 index 的核心模块。
  - 负责读取 receipt/check、校验边界、生成 `receipt_index_rows` 和 `source_evidence_rows`。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_v1025_artifacts.py`
  - 输出 JSON、CSV、Text、Markdown、HTML。
  - HTML 只用于人工检查和截图，不作为 promotion 依据。
- `scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_v1025.py`
  - CLI 入口，支持 `--receipt`、`--receipt-check`、`--require-index-ready`、`--require-lookup-ready`、`--force`。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_v1025.py`
  - 覆盖 ready 路径、篡改失败路径、contract check 未 ready 路径和 CLI 输出路径。
- `e/1025/解释/receipt-index-v1025/`
  - 真实运行产物目录。
- `e/1025/图片/v1025-receipt-index.png`
  - Playwright MCP 截图证据。

## 核心数据结构

`receipt_index_rows` 是下游实际消费的索引行：

```text
receipt_index_id
lookup_key
receipt_id
receipt_status
granted_use
source_receipt_path
source_receipt_check_path
source_review_path
source_receipt_index_path
contract_check_ready
promotion_ready
```

其中 `lookup_key` 使用固定前缀：

```text
publication-receipt-index-receipt-index-receipt-index-receipt-index:
```

这让后续 review 可以按命名空间查找 v1025 这一层 receipt index，而不是猜测文件路径。

`source_evidence_rows` 记录两个输入文件：

```text
kind=receipt
kind=receipt_check
path
sha256
status
```

这里的 SHA-256 是本版证据链的关键：它证明 v1025 index 消费的是当前记录的 v1023/v1024 文件，而不是只保存一段文字说明。

## 关键函数

`build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_v1025(...)` 是主入口。

它先提取：

- `receipt_summary`
- `receipt`
- `check_summary`

然后调用 `_checks(...)` 生成检查清单。只要任意检查失败，`status` 就变成 `fail`，`receipt_index_rows` 为空。

`_checks(...)` 保护以下边界：

- receipt 文件存在；
- receipt check 文件存在；
- v1023 receipt 自身通过；
- v1024 contract check 自身通过；
- receipt status 与 check 的 original/rebuilt status 一致；
- granted use 始终是 `downstream_governance_lookup_only`；
- lookup key 数量仍然是 1；
- source evidence 数量仍然是 2；
- source review、source receipt index、source receipt、source check 等上游路径仍存在；
- model quality claim 保持 bounded；
- promotion 继续关闭；
- v1023/v1024 的 next step 符合 check -> index 路由。

`_index(...)` 只在所有检查通过时生成索引行。它同时写入：

- `lookup_scope=downstream_governance_lookup_only`
- `lookup_ready=True`
- `contract_check_ready=True`
- `promotion_ready=False`
- `next_step=review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_v1025`

这说明 v1025 是 lookup/review 入口，不是模型上线入口。

## CLI 流程

CLI 的运行方式是：

```text
python scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_v1025.py --receipt <receipt-or-dir> --receipt-check <check-or-dir> --out-dir <dir> --require-index-ready --require-lookup-ready --force
```

如果传入目录，locator 会自动解析到对应 JSON 文件：

- `randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_v1023.json`
- `randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_check_v1024.json`

`--require-index-ready` 和 `--require-lookup-ready` 让脚本在结构不满足时返回非零值，适合 CI 或后续自动化链路使用。

## 运行证据

真实 CLI 输出关键值：

```text
status=pass
decision=randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_v1025_ready
index_ready=True
lookup_key_count=1
source_evidence_count=2
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

HTML 报告由 Playwright MCP 截图保存到：

```text
e/1025/图片/v1025-receipt-index.png
```

## 测试覆盖

focused 测试覆盖四条关键路径：

- 正常 receipt + check 可以生成 ready index；
- receipt 的 `granted_use` 被改成 `production_promotion` 时失败；
- check 的 `contract_check_ready` 被改成 `False` 时失败；
- CLI 可以从目录定位输入并写出 JSON、CSV、Text、Markdown、HTML。

当前 focused 测试结果：

```text
4 passed in 8.16s
```

全量回归结果：

```text
2502 passed in 565.89s
```

source encoding hygiene 结果：

```text
source_count=1962
clean_count=1962
bom_count=0
syntax_error_count=0
compatibility_error_count=0
```

## 一句话总结

v1025 把 v1023/v1024 从两个单独证据文件推进为一个可检索的 digest-backed receipt index，同时继续把模型能力结论限制在治理查阅范围内。
