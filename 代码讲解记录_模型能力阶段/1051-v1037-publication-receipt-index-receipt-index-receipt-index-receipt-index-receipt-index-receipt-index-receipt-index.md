# v1037 publication receipt index receipt index receipt index receipt index receipt index receipt index receipt index 代码讲解

## 本版目标和边界

v1037 的目标是把 v1035 downstream lookup-only receipt 和 v1036 receipt contract check 打包成一份新的 digest-backed receipt index。

它解决的问题是：v1035 已经记录了对 v1034 review 的下游 lookup-only 消费，v1036 又证明这份 receipt 可以从源 review 原样重建。下游继续 review 前，需要一个稳定索引把 receipt、contract check、source evidence digest、lookup key 和 no-promotion 边界放在同一个可查入口里。

本版不训练模型，不扩大模型质量声明，不改变 randomized holdout 的 bounded claim，也不批准 production promotion。它只是索引已经验证过的 receipt/check 证据。

## 前置能力

v1035 输出：

```text
e/1035/解释/receipt-v1035/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1035.json
```

这份 receipt 记录：

- `granted_use=downstream_governance_lookup_only`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `promotion_ready=False`
- `approved_for_promotion=False`

v1036 输出：

```text
e/1036/解释/receipt-check-v1036/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1036.json
```

这份 contract check 证明 v1035 receipt 可以从 v1034 review 重建，且原始/重建结果在 receipt status、granted use、lookup key count 和 promotion 边界上完全一致。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1037.py`
  - v1037 核心 builder。
  - 读取 v1035 receipt 和 v1036 contract check，验证二者一致后构建新的 receipt index。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1037_artifacts.py`
  - 输出 JSON、CSV、Text、Markdown、HTML。
- `scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1037.py`
  - CLI 入口。
  - 支持目录输入，自动定位 v1035 receipt JSON 和 v1036 check JSON。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1037.py`
  - 覆盖 ready index、granted use 篡改、contract check not-ready 和 CLI/artifact 输出。
- `e/1037/解释/receipt-index-v1037/`
  - 真实运行产物。
- `e/1037/图片/v1037-receipt-index.png`
  - Playwright MCP 截图证据。

## 核心数据结构

v1037 输出里最重要的是三组字段：

```text
receipt_index
receipt_index_rows
source_evidence_rows
```

`receipt_index` 是聚合对象，保存：

- `index_ready`
- `receipt_index_id`
- `lookup_scope`
- `lookup_key_count`
- `source_evidence_count`
- `lookup_ready`
- `contract_check_ready`
- `promotion_ready`
- `approved_for_promotion`
- `next_step`

`receipt_index_rows` 是下游查询入口。当前只有一条 row，lookup key 以：

```text
publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index:
```

开头，并指向 v1035 receipt。

`source_evidence_rows` 保存两条 digest-backed source evidence：

- v1035 receipt JSON；
- v1036 receipt contract check JSON。

这两条证据是后续 review 判断路径是否漂移的基础。

## 核心函数

`build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1037(...)` 是主入口。

它执行五步：

1. 提取 v1035 receipt 的 `summary` 和 `receipt`。
2. 提取 v1036 contract check 的 `summary`。
3. 调用 `_checks(...)` 校验路径、状态、decision、lookup-only use、lookup key count、source evidence count、source path、bounded claim 和 no-promotion 字段。
4. 调用 `_index(...)` 构造 lookup-only receipt index row 和 source evidence rows。
5. 写入 `summary` 和 `interpretation`，明确下一步是 review，而不是 promotion。

关键检查包括：

- `receipt_file_exists`
- `receipt_check_file_exists`
- `receipt_decision_ready`
- `receipt_check_decision_ready`
- `receipt_status_matches_check`
- `granted_use_lookup_only`
- `lookup_key_count`
- `source_evidence_count`
- `promotion_still_false`
- `source_next_steps_match`

这些检查共同保护一件事：v1037 只能索引 v1035/v1036 已经验证过的 lookup-only 证据，不能把 contract check 误解释成生产推广许可。

## CLI 流程

真实运行命令：

```text
python scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1037.py --receipt e/1035/解释/receipt-v1035 --receipt-check e/1036/解释/receipt-check-v1036 --out-dir e/1037/解释/receipt-index-v1037 --require-index-ready --require-lookup-ready --force
```

目录输入会分别自动定位：

```text
randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1035.json
randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1036.json
```

`--require-index-ready` 要求索引结构通过。

`--require-lookup-ready` 要求 lookup key 可用。

本版没有提供 `--require-promotion-ready` 的成功路径，因为 `promotion_ready=False` 是受保护边界。

## 运行证据

真实 CLI 输出关键值：

```text
status=pass
decision=randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1037_ready
index_ready=True
lookup_key_count=1
source_evidence_count=2
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

HTML 报告截图保存到：

```text
e/1037/图片/v1037-receipt-index.png
```

## 测试覆盖

focused 测试覆盖四条路径：

- ready v1035 receipt + v1036 check 可以生成 index；
- receipt `granted_use` 被改成 production promotion 会失败；
- contract check ready 被改成 false 会失败；
- artifact writer 和 CLI 都能写出 JSON、CSV、Text、Markdown、HTML。

当前 focused 测试结果：

```text
4 passed in 6.40s
```

全量回归结果：

```text
2565 passed in 693.69s
```

source encoding hygiene 结果：

```text
source_count=2010
clean_count=2010
bom_count=0
syntax_error_count=0
compatibility_error_count=0
```

## 一句话总结

v1037 把“receipt 已记录、receipt check 已通过”推进到“receipt/check 已被 digest-backed index 收束”的状态，同时继续保持 lookup-only 和 no-promotion 边界。
