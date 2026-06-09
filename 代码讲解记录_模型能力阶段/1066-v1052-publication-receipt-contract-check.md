# v1052 publication receipt contract check 代码讲解

## 本版目标与边界

v1052 的目标是给 v1051 的 downstream lookup-only receipt 增加一层可复核入口。

v1051 做的是“记录消费”：它把 v1050 reviewed receipt index 作为 downstream governance lookup-only 的消费动作写成 receipt。v1052 做的是“复核消费”：它读取 v1051 receipt 指向的 v1050 review，重新调用 v1051 receipt builder，然后比较原始 receipt 与重建 receipt 是否一致。

本版不训练模型，不扩展生成能力，不把 lookup-only 证据升级为 production promotion。它只回答一个问题：当前归档里的 v1051 receipt 是否仍然能从 v1050 review 推导出来。

## 前置链路

本版来自 v1049-v1051 的 receipt index 路线：

- v1049：把 v1047 receipt 和 v1048 check 写成 digest-backed lookup index。
- v1050：review v1049 index，确认只允许 downstream governance lookup-only。
- v1051：把 v1050 reviewed index 记录成 downstream lookup-only receipt。
- v1052：重建 v1051 receipt，检查它与 v1050 review 的 contract 是否一致。

这条链路的核心边界仍然是 `promotion_ready=False`、`approved_for_promotion=False` 和 `granted_use=downstream_governance_lookup_only`。

## 关键文件

`src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1052.py`

这是 v1052 的核心 builder。它提供：

- `locate_receipt_v1052()`：允许 CLI 输入 v1051 receipt JSON，也允许输入 v1051 输出目录。
- `read_json_report()`：读取 UTF-8/UTF-8 BOM JSON，并要求输入是对象。
- `build_..._check_v1052()`：生成 contract check 报告。
- `resolve_exit_code()`：让 CLI 在 `--require-pass` 下把 check fail 转成进程退出码 1。

`src/minigpt/...receipt_check_v1052_artifacts.py`

这是渲染和输出层，负责把同一份 report 写成 JSON、CSV、text、Markdown 和 HTML。HTML 不是新决策来源，它只是运行截图的可视化载体。

`scripts/check_...receipt_v1052.py`

这是命令行入口。它接收 `receipt` 和 `--out-dir`，在 `--force` 下清空旧输出目录，再调用 builder 和 artifact writer。

`tests/test_...receipt_check_v1052.py`

这是本版的单测入口，覆盖合法重建、篡改字段、源 review 缺失、digest 篡改、CLI 失败退出码和输出文件生成。

`src/minigpt/randomized_holdout_publication_constants.py`

本版新增 v1052 next-step 常量，用于把 check pass 后的下一步路由到 v1052 index。这样脚本、报告和测试消费的是同一份常量，而不是各自写字符串。

## 核心数据结构

v1052 report 的主要字段包括：

- `status`：整体 check 状态，所有 check row 通过时为 `pass`。
- `decision`：check pass/fail 后的决策字符串。
- `failed_count`：失败 check 数量。
- `issues`：失败的 check rows；通过时为空列表。
- `receipt_path`：原始 v1051 receipt JSON 路径。
- `source_receipt_index_review`：从 v1051 receipt 内解析出的 v1050 review 路径。
- `original_summary` / `rebuilt_summary`：原始 receipt 与重建 receipt 的 summary。
- `original_receipt` / `rebuilt_receipt`：原始 receipt 与重建 receipt 的 receipt 对象。
- `check_rows`：逐项字段比较结果。
- `summary`：面向报告页和 CLI 的摘要。

这里的 `rebuilt_*` 不是从 v1051 JSON 复制出来的，而是通过 `build_randomized_holdout_publication_..._receipt_v1051()` 从 v1050 review 重新生成。

## 运行流程

1. CLI 定位输入。如果用户传目录，`locate_receipt_v1052()` 会拼接 v1051 JSON 文件名。
2. builder 提取 v1051 report 的 `summary` 和 `receipt`。
3. `_resolve_source_review_path()` 从顶层 `receipt_index_review_path` 或 receipt 内同名字段找到 v1050 review。
4. `_rebuild_receipt()` 读取 v1050 review，并调用 v1051 receipt builder 重建 receipt。
5. `_checks()` 比较顶层状态、decision、failed_count、source review digest、consumer receipts，以及 summary/receipt 的关键字段。
6. 所有 check 通过时，report 标记 `status=pass`，并把 `next_step` 指向 v1052 index。
7. artifact writer 输出 JSON/CSV/text/Markdown/HTML。

## 关键断言

本版最重要的 check 不是只看 `status=pass`，而是保护这些不应漂移的字段：

- `receipt_index_review_sha256`：证明 v1051 使用的源 v1050 review 没变。
- `summary.granted_use` 和 `receipt.granted_use`：证明 receipt 仍然是 lookup-only。
- `summary.promotion_ready` 和 `receipt.promotion_ready`：证明没有被解释成 promotion-ready。
- `summary.next_step` 和 `receipt.next_step`：证明 v1051 仍然把下一步交给 check，而不是跳到 promotion。
- `source_receipt_index_path`、`source_receipt_path`、`source_receipt_check_path`、`source_review_path` 和 `source_receipt_index_origin_path`：证明追溯路径没有丢。

## 测试覆盖

focused v1052 测试覆盖 6 个场景：

- 合法 v1051 receipt 可以从 v1050 review 重建，`resolve_exit_code(..., require_pass=True)` 返回 0。
- 篡改 `granted_use` 会让 summary 和 receipt 两处 check 同时 fail。
- 删除或改错源 review 路径会触发 `source_receipt_index_review_exists` fail。
- 篡改 source review digest 会触发 digest check fail。
- CLI 在 `--require-pass` 下遇到 fail 会返回 1。
- artifact writer 和 CLI 能生成 JSON、CSV、text、Markdown、HTML。

这些测试保护的是 contract check 的真实链路，而不是只验证渲染函数能运行。

## 运行证据

本版真实 CLI 证据在：

- `e/1052/解释/receipt-check-v1052/`

Playwright MCP 截图在：

- `e/1052/图片/v1052-receipt-check.png`

HTML 页面确认：

- `Status=pass`
- `Contract=True`
- `Failed=0`
- source review 指向 v1050
- original/rebuilt use 都是 `downstream_governance_lookup_only`
- original/rebuilt promotion 都是 `False`

## 边界说明

v1052 的 `pass` 只表示 v1051 receipt 与 v1050 review 一致。它不表示模型质量提升，不表示真实训练增强，也不表示可以生产推广。它把治理链路做得更可复核，但没有改变模型能力声明。

一句话总结：v1052 把 v1051 lookup-only receipt 加上一层可重建 contract check，让 receipt 消费证据从“已写入”变成“可复核”。
