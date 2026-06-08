# v1015：short-name publication receipt index receipt

## 本版目标和边界

v1015 的目标是把 v1014 已审核通过的 receipt index 记录成下一层 downstream governance lookup-only receipt，同时处理 v1014 暴露出来的维护风险：过长的 Python 文件名会在 Windows 上触发 pycache/路径长度问题。

本版明确不做三件事：

- 不提升模型质量结论，`model_quality_claim` 仍然只是 bounded randomized holdout publication claim。
- 不允许生产 promotion，`promotion_ready` 和 `approved_for_promotion` 继续保持 `False`。
- 不回头迁移 v1014 以前的历史长文件名，只从 v1015 起停止继续扩张新文件名。

## 前置能力

v1015 接在 v1014 后面。v1014 已经审核了 v1013 receipt index，确认它满足 lookup-only 下游 receipt recording 的前置条件：

- source receipt index 文件存在；
- source receipt 和 source receipt check 文件存在；
- lookup key namespace 正确；
- source evidence count 为 2；
- contract check ready；
- no-promotion 边界未被放开。

因此 v1015 不重新发明审核逻辑，而是把 v1014 review 作为输入，再记录一个面向下游读取者的 receipt。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_v1015.py`
  - v1015 的核心 builder。
  - 读取 v1014 review，执行 receipt recording 前校验，输出 JSON-ready report。
  - 采用短文件名，但保留 v1014 长 source key 作为追溯字段。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_v1015_artifacts.py`
  - 把 report 渲染成 JSON、CSV、Text、Markdown、HTML。
  - HTML 报告用于 Playwright MCP 截图，CSV 用于查看 consumer receipt row。

- `scripts/record_randomized_holdout_publication_receipt_index_receipt_v1015.py`
  - 命令行入口。
  - 支持输入 v1014 review JSON 或输出目录。
  - 支持 `--require-receipt-ready`，失败时返回非零退出码。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_v1015.py`
  - 覆盖成功 receipt、requested use 篡改、source receipt index 缺失、CLI 失败返回码和 artifact 输出。
  - 测试临时目录放到 `runs/test-temp-v1015` 下，避免 `%TEMP%` 的长路径把 v1014 历史长文件名重新放大。

- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 `RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_V1015_NEXT_STEP`。
  - 让 v1015 的 next step 从短名链路继续走，不再复制 v1014 的长命名。

## 核心数据结构

v1015 report 的主结构包括：

- `status` / `decision` / `failed_count`
  - 表示 v1015 receipt recording 是否通过。

- `source_receipt_index_review_summary`
  - 保存 v1014 review 的 summary。
  - 用来证明 v1015 没有绕过上一版审核。

- `source_receipt_index_review`
  - 保存 v1014 review body。
  - 用来读取 `receipt_index_path`、`source_receipt_path`、`source_receipt_check_path` 和 lookup keys。

- `consumer_receipts`
  - v1015 新增的下游 receipt row。
  - 字段包括 `consumer_name`、`lookup_key`、`source_receipt_id`、`receipt_id`、`granted_use`、`promotion_ready` 和 `receipt_status`。

- `summary`
  - 给 CLI、README 和后续 contract check 使用的稳定摘要。
  - 关键字段是 `randomized_holdout_publication_receipt_index_receipt_v1015_ready`、`receipt_status`、`lookup_key_count`、`source_evidence_count`、`promotion_ready` 和 `next_step`。

## 核心函数

`locate_receipt_index_review_v1015(path)` 负责把输入路径规范化。如果用户传入目录，它会自动定位 v1014 review JSON；如果传入文件，则直接使用该文件。

`build_randomized_holdout_publication_receipt_index_receipt_v1015(...)` 是主 builder：

1. 从 v1014 report 中读取 `summary`、`review`、`receipt_index_rows` 和 `source_evidence_rows`。
2. 调用 `_checks(...)` 验证源 review 和边界。
3. 若全部通过，调用 `_receipt(...)` 生成新 receipt。
4. 汇总 `consumer_receipts`、`summary` 和 `interpretation`。

`_checks(...)` 是本版的关键保护层。它检查：

- v1014 review 文件存在；
- v1014 review 自身是 pass；
- v1014 decision 和 ready key 没有漂移；
- review status 只允许 lookup-only receipt recording；
- requested use 必须是 `downstream_governance_lookup_only`；
- blocked uses 完整；
- receipt index ready、lookup ready、contract check ready；
- index row 为 1，source evidence 为 2；
- lookup key namespace 正确；
- source receipt index、source receipt、source receipt check 仍然存在；
- model quality claim 仍是 bounded claim；
- promotion 仍然被禁止；
- v1014 的 next step 与历史常量一致。

`resolve_exit_code(...)` 让 CLI 可以作为 gate 使用。`--require-receipt-ready` 下，如果 ready key 不是 true，就返回 `1`。

## 为什么短名是本版重点

v1014 运行时发现一个很具体的问题：`python -m py_compile` 会在 Windows 上因为超长模块名生成 `.pyc` 路径失败。这个问题不是语法错误，而是路径长度和文件名增长共同造成的维护风险。

v1015 因此采用短名：

```text
randomized_holdout_publication_receipt_index_receipt_v1015.py
randomized_holdout_publication_receipt_index_receipt_v1015_artifacts.py
record_randomized_holdout_publication_receipt_index_receipt_v1015.py
test_randomized_holdout_publication_receipt_index_receipt_v1015.py
```

这样做的边界是：新文件短名化，旧文件不迁移；新产物可维护，旧源证据仍可追溯。

## 测试覆盖

focused 测试包括五类保护：

- ready review 可以生成 receipt，且 `receipt_ready=True`。
- requested use 被改成 production promotion 时失败。
- source receipt index 路径被改错时失败。
- CLI 在 `--require-receipt-ready` 下遇到坏 review 返回 `1`。
- JSON、CSV、Text、Markdown、HTML 输出全部连通，目录输入能定位到 v1014 review JSON。

另外，`python -m py_compile` 覆盖了新增模块、artifact、脚本和测试，证明 v1015 的短名方案没有复现 v1014 的 pycache 路径问题。

全量回归结果为：

```text
2450 passed in 436.92s
```

## 运行证据

真实 CLI 运行写入：

- `e/1015/解释/receipt-v1015/randomized_holdout_publication_receipt_index_receipt_v1015.json`
- `e/1015/解释/receipt-v1015/randomized_holdout_publication_receipt_index_receipt_v1015.html`

核心结果：

```text
status=pass
decision=randomized_holdout_publication_receipt_index_receipt_v1015_ready
failed_count=0
receipt_ready=True
receipt_status=publication_receipt_index_receipt_v1015_lookup_receipted
lookup_key_count=1
source_evidence_count=2
promotion_ready=False
failed_check_count=0
```

Playwright MCP 截图归档在：

```text
e/1015/图片/v1015-receipt.png
```

截图证明 HTML 报告可打开，且能看到 `Receipt Boundary`、`Consumer Receipts` 和 `Checks` 三个关键区域。

## 一句话总结

v1015 一边继续推进 lookup-only receipt 链路，一边把新版本命名从不可维护的长链条中拉回来，为后续 check/index/review 版本留下更稳的工程入口。
