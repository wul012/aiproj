# v1064 publication receipt check 代码讲解

## 本版目标与边界

v1064 的目标是对 v1063 receipt 做 contract check，验证它能从 v1062 review 重新构造出来。

v1063 已经把 v1062 review 记录成 downstream lookup-only receipt。v1064 不修改 receipt 内容，而是读取 v1063 receipt，重建它对应的 receipt 对象，并逐项比较 status、decision、failed_count、source digest、consumer receipts、summary 和 receipt body。

本版不训练模型，不做 benchmark，不扩大模型质量声明，不批准 production promotion。

## 前置链路

本版承接：

- v1062：review v1061 digest-backed receipt index。
- v1063：记录 v1062 review 结果为 downstream lookup-only receipt。
- v1064：contract-check v1063 receipt，验证它能稳定从 v1062 review 重建。

这仍然是治理证据链，不是模型能力提升链。

## 关键文件

`src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1064.py`

这是 v1064 核心 builder，负责读取 v1063 receipt、重建 receipt、比较原始值和重建值，并生成 contract-check report。

`src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1064_artifacts.py`

这是渲染层，输出 JSON、CSV、text、Markdown、HTML。HTML 是截图对象，CSV 存 check rows。

`scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1064.py`

这是 CLI 入口。真实运行时输入 `e/1063/解释/receipt-v1063`，输出 `e/1064/解释/receipt-check-v1064`。

`tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1064.py`

这是 focused 测试，覆盖 rebuildable receipt、granted use 篡改、source review 缺失、source digest 篡改、CLI exit code 和 artifact wiring。

`src/minigpt/randomized_holdout_publication_constants.py`

本版新增 v1064 next-step 常量，check 通过后指向 v1064 index。

## 核心数据结构

v1064 report 的核心字段：

- `receipt_path`：输入的 v1063 receipt JSON 路径。
- `source_receipt_index_review`：源 v1062 review 路径。
- `original_summary` / `rebuilt_summary`：原始与重建 summary。
- `original_receipt` / `rebuilt_receipt`：原始与重建 receipt。
- `check_rows`：46 项 contract checks。
- `summary`：CLI/HTML 使用的压缩摘要。
- `interpretation`：对通过/失败的简短解释。

## 运行流程

1. CLI 定位 v1063 receipt JSON。
2. builder 读取 receipt report，提取 original summary 和 original receipt。
3. `_resolve_source_review_path()` 找到源 v1062 review。
4. `_rebuild_receipt()` 调用 v1063 builder 从源 review 重建 receipt。
5. `_checks()` 比较原始与重建值，检查路径、digest、consumer receipts 和 no-promotion 字段。
6. `_summary()` 汇总 contract-check 状态和下一步。
7. artifact writer 输出 JSON、CSV、text、Markdown、HTML。

## 关键断言

v1064 最关键的保护点：

- `source_receipt_index_review_exists`：源 review 文件必须存在。
- `status` / `decision` / `failed_count`：原始与重建必须一致。
- `receipt_index_review_sha256`：源 review digest 必须一致。
- `consumer_receipts`：消费行必须重建一致。
- `summary.*` 与 `receipt.*`：原始与重建字段必须逐项一致。
- `next_step`：通过后必须把下一步指向 v1064 index。

## 测试覆盖

focused v1064 测试覆盖 6 个场景：

- v1063 receipt 可以被重建。
- 篡改 `granted_use` 会 fail。
- 源 review 缺失会 fail。
- 源 digest 篡改会 fail。
- `--require-pass` 对失败 report 返回 1。
- CLI 和 artifact writer 能生成完整输出。

真实证据使用 `e/1063` 归档产物运行，不只依赖测试夹具。

## 运行证据

真实 CLI 证据在：

- `e/1064/解释/receipt-check-v1064/`

Playwright MCP 截图在：

- `e/1064/图片/v1064-receipt-check.png`

页面显示：

- `Status=pass`
- `Contract check ready=True`
- `Original/ rebuilt status` 一致
- `Original/ rebuilt granted use` 一致
- `Original/ rebuilt lookup key count` 一致
- `Failed=0`

补充验证：

- focused v1064 tests: `6 passed in 0.39s`
- full pytest: `2708 passed in 574.97s`
- source hygiene: `2118/2118 clean`

## 边界说明

v1064 的通过结论只表示 v1063 receipt 可重建且仍保持 lookup-only。它不表示模型质量提高，不表示训练成功，也不表示生产推广。

一句话总结：v1064 用 contract check 锁住 v1063 receipt 的一致性，把链路继续关在 lookup-only 边界内。
