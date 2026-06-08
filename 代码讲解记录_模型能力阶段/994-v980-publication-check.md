# v980 publication check

## 目标与边界

v980 的目标是给 v979 的 lookup-only publication 补一层 contract check。v979 已经把 v978 review 发布成下游可查的 publication；v980 负责证明这个 publication 可以从它记录的源 review 重新推导出来。

本版不做模型训练，不改变 tokenizer、checkpoint、loss 或 benchmark。它也不把 `publication_ready=True` 解释成模型质量提升。核心边界仍然是：

- `published_use=downstream_governance_lookup_only`
- `promotion_ready=False`
- `approved_for_promotion=False`
- `model_quality_claim=bounded_randomized_target_hidden_holdout_claim_only`

## 前置路线

这一版接在 v977-v979 后面：

1. v977 生成 receipt packet index。
2. v978 review index，确认可以进入 lookup-only publication。
3. v979 发布 publication，提供下游 lookup 入口。
4. v980 重新读取 v979 内的 v978 review 路径，重建 publication，并比较关键字段。

所以 v980 是“发布产物可复核”版本，不是新的治理链，也不是新的模型能力实验。

## 关键新增文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_check_v980.py`
  - 核心 contract check builder。
  - 输入 v979 publication JSON。
  - 自动定位 `receipt_packet_index_review_path`。
  - 调用 v979 publication builder 从 v978 review 重新构建 publication。
  - 比较 summary/publication 的关键字段，输出 `status`、`decision`、`failed_count`、`issues`、`summary`。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_check_v980_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML。
  - 使用短产物名 `randomized_holdout_publication_receipt_packet_index_publication_check_v980.*`。
- `scripts/check_randomized_holdout_publication_receipt_packet_index_publication_v980.py`
  - CLI 入口。
  - 支持输入 publication JSON 或 publication 输出目录。
  - 支持 `--require-pass`，失败时返回 1。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_check_v980.py`
  - 覆盖正常重建、篡改 published use、源 review 缺失、CLI 失败码和输出格式。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 v980 next step，指向后续 publication index。
- `src/minigpt/__init__.py`
  - 增加短模块函数的包级懒加载导出。

## 为什么 v980 改用短模块名

v978-v979 已经开始使用短 artifact 文件名。v980 在开发时进一步踩到了 Windows `.pyc` 路径长度上限：长模块名会让 Python 在 `src/minigpt/__pycache__/...cpython-313.pyc` 下生成过长路径，导致 `py_compile` 失败。

因此 v980 做了一个维护性转折：

- schema 字段、decision、status、next step 仍保留完整链路语义；
- Python 模块名、脚本名、测试名、artifact 文件名开始使用短名；
- 文档文件名也使用短名，正文再讲完整链路。

这不是降低证据精度，而是把“链路语义”和“文件系统可维护性”分开。

## 核心数据结构

### 输入 publication

输入来自 v979：

- 顶层 `status`、`decision`、`failed_count`。
- 顶层 `receipt_packet_index_review_path`。
- `summary` 中的 publication 状态、lookup 边界、行数和 no-promotion 字段。
- `publication` 中的源路径、发布用途、next step 和 bounded claim。

### 重建 publication

v980 先解析源 review 路径：

```text
report.receipt_packet_index_review_path
publication.receipt_packet_index_review_path
```

如果路径是相对路径，就以 publication JSON 所在目录为候选位置做一次解析。源 review 存在时，v980 调用 v979 的 builder：

```text
build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_publication(...)
```

重建结果只在内存中比较，不改写 v979 产物。

### 40 条检查

检查分三组：

1. 源 review 文件存在。
2. 顶层 `status`、`decision`、`failed_count`、`check_rows` 与重建结果一致。
3. `summary` 和 `publication` 的关键字段一致。

关键字段包括：

- publication status
- published use
- publish/lookup/contract readiness
- receipt packet index row count
- source packet row count
- source evidence count
- promotion_ready / approved_for_promotion
- consumer boundary
- model quality claim
- source packet/index/check 路径
- next step

这组断言保护的是“publication 没有从 lookup-only 漂移到 promotion，也没有丢失源路径”。

## CLI 运行流程

CLI 做四件事：

1. 定位输入 publication JSON。
2. 根据 `--force` 清理输出目录。
3. 构建 check report 并写出 JSON/CSV/text/Markdown/HTML。
4. 在 `--require-pass` 下，如果 `status != pass`，返回 1。

结构通过但 publication 本身仍是 no-promotion，不算失败。失败只来自 contract 不一致、路径缺失或字段漂移。

## 测试覆盖

测试不是只看脚本能跑，而是覆盖关键破坏路径：

- 正常 publication 能从源 review 重建，`contract_check_ready=True`。
- 手动把 `published_use` 改成 `production_promotion`，summary 和 publication 两处都会失败。
- 手动把源 review 路径改成不存在，`source_receipt_packet_index_review_exists` 会失败。
- CLI 在 `--require-pass` 下遇到篡改产物返回 `SystemExit(1)`，并仍写出失败证据。
- artifact writer 输出 JSON/CSV/text/Markdown/HTML，HTML 和 Markdown 至少包含 contract/check 信息。

## 运行证据

真实运行输入 v979 publication，输出在：

```text
e/980/解释/publication-receipt-packet-index-publication-check/
```

关键输出：

```text
status=pass
failed_count=0
contract_check_ready=True
original_published_use=downstream_governance_lookup_only
rebuilt_published_use=downstream_governance_lookup_only
original_promotion_ready=False
rebuilt_promotion_ready=False
passed_check_count=40
failed_check_count=0
```

Playwright MCP 截图保存到：

```text
e/980/图片/v980-randomized-holdout-publication-receipt-packet-index-publication-check.png
```

## 一句话总结

v980 把 v979 publication 从“已发布的 lookup artifact”推进为“可由源 review 重建并通过 40 条字段检查的 lookup artifact”，同时开始把超长 Python 模块名收敛为可维护短名。
