# v1085 publication receipt index

## 本版目标

v1085 的目标是把 v1083 receipt 和 v1084 contract check 做成一份新的 receipt index。它解决的是“下游模块要同时找 receipt、找 check、校验路径和 digest”带来的检索成本。

本版不做的事：

- 不训练模型
- 不声明模型能力变强
- 不打开 promotion
- 不把 lookup-only 证据当成生产模型验收

## 路线来源

v1083 已经把 v1082 review 记录成 lookup-only receipt。v1084 又证明这份 receipt 可以从源 review 重建，且关键字段一致。v1085 在这两份产物之上建立索引，让后续 v1086 review 可以只读消费一份 digest-backed source evidence。

这仍然是证据链治理，不是模型质量提升链。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1085.py`
  - 核心 index builder。
  - 读取 receipt 和 receipt check，验证 lookup-only use、contract check ready、source path、digest 和 no-promotion 边界。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1085_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - JSON 给后续 review 消费，HTML 用于截图归档。

- `scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1085.py`
  - CLI 入口。
  - 使用 `--receipt` 和 `--receipt-check` 明确输入，避免位置参数误传。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1085.py`
  - 覆盖正常索引、篡改 use、contract check 未 ready、CLI 输出等场景。

- `e/1085/解释/receipt-index-v1085/`
  - 本版真实 CLI 产物。
  - 包含 JSON/CSV/TXT/MD/HTML 五种视图。

## 核心数据结构

index 结果主要有三层：

- `summary`
  - 汇总 `lookup_scope`、`lookup_key_count`、`receipt_status`、`granted_use`、`source_evidence_count`、`contract_check_ready`、`promotion_ready`、`next_step`。

- `receipt_index`
  - 记录 lookup key、consumer boundary、allowed use 和 source receipt/check 的关系。
  - 本版只有一个 lookup key，仍然限定为 downstream governance lookup。

- `source_evidence`
  - 记录 v1083 receipt 和 v1084 contract check 的路径与 SHA-256。
  - 这部分是后续 review 判断“源证据有没有换”的主要依据。

## 核心流程

1. CLI 读取 `--receipt` 和 `--receipt-check`。
2. locator 支持输入目录或 JSON 文件。
3. builder 解析 receipt summary、receipt body 和 check summary。
4. `_checks` 验证 receipt ready、contract check ready、lookup-only use、source path、digest、promotion boundary。
5. `_index` 生成 receipt index row 和 source evidence rows。
6. artifact writer 输出多格式 sidecar。

## 测试覆盖

- 合法 receipt + check 会通过，保护正常链路。
- 篡改 `granted_use` 会失败，保护 lookup-only 边界。
- contract check 不 ready 会失败，保护不能绕过 v1084。
- CLI 能写出 sidecar，保护归档链路真实可用。

## 运行证据

真实命令输出确认：

- `status=pass`
- `index_ready=True`
- `lookup_scope=downstream_governance_lookup_only`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `contract_check_ready=True`
- `promotion_ready=False`
- `passed_check_count=25`
- `failed_check_count=0`

Playwright MCP snapshot 确认页面显示 `Status pass`、`Index ready True`、`Lookup keys 1`、`Contract True`、`Evidence 2`、`Failed 0`。

## 验证

- focused v1085 tests：`4 passed in 1.67s`
- full pytest：`2817 passed in 592.68s`
- source hygiene：`2203/2203 clean`
- py_compile：新增模块、artifact writer、CLI、测试均通过。
- `git diff --check` 会在提交前执行。

## 一句话总结

v1085 把 v1083 receipt 和 v1084 contract check 收束成下一轮 review 可以直接消费的 digest-backed lookup index。
