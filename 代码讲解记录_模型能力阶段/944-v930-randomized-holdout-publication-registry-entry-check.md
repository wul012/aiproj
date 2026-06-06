# v930 randomized holdout publication registry entry contract check 代码讲解

## 本版目标和边界

v930 的目标是给 v929 registry entry 增加 contract check：

```text
v928 publication decision index
  -> v929 publication registry entry
  -> v930 registry entry contract check
```

它回答的问题是：

```text
v929 的 registry entry 是否能从它记录的 source index 重新推导出来？
```

回答是可以：

```text
contract_check_ready=True
```

明确不做：

- 不重新训练。
- 不重新 replay。
- 不生成完整 registry manifest。
- 不批准 production promotion。
- 不把 registry entry 的存在当成模型可生产上线证明。

## 前置链路

v930 消费：

```text
e/929/解释/randomized-holdout-publication-registry-entry
```

v929 entry 里记录了 source index：

```text
e/928/解释/randomized-holdout-publication-decision-index/randomized_holdout_publication_decision_index.json
```

v930 做的事情是：

1. 读取 v929 registry entry。
2. 找到 v929 记录的 v928 source index。
3. 用 v928 index 重新调用 `build_randomized_holdout_publication_registry_entry(...)`。
4. 比较原始 entry 和 rebuilt entry 的稳定字段。

## 关键文件

### `src/minigpt/randomized_holdout_publication_registry_entry_check.py`

核心入口：

```python
build_randomized_holdout_publication_registry_entry_check(...)
```

输入：

- `registry_entry_report`：v929 entry JSON。
- `registry_entry_path`：可选源路径，用于辅助解析相对 source index。

输出：

```text
status
decision
failed_count
issues
source_registry_entry
source_publication_decision_index
source_summary
rebuilt_summary
source_registry_entry_body
rebuilt_registry_entry_body
check_rows
summary
interpretation
```

### source index 解析

`_resolve_source_index(...)` 会读取两个候选字段：

```text
publication_decision_index_path
registry_entry.source_index_path
```

只要其中一个能定位到文件，就作为重建来源。若路径缺失或文件不存在，check 会失败。

### 重建逻辑

```python
_rebuild_entry(...)
```

如果 source index 存在：

```python
build_randomized_holdout_publication_registry_entry(
    read_registry_source_json(source_index),
    publication_decision_index_path=source_index,
    entry_id=original_summary["entry_id"],
)
```

如果 source index 不存在，则构造一个失败的 rebuilt entry，用来让比较行明确失败。

### 比较字段

summary 级别比较：

```text
randomized_holdout_publication_registry_entry_ready
entry_id
registry_status
entry_type
bounded_publication_accepted
promotion_ready
approved_for_promotion
accepted_claim_count
blocked_claim_count
candidate_case_count
random_seed
pass_rate
allowed_use
model_quality_claim
decision_scope
source_count
source_kinds
consumer_boundary
next_step
```

registry_entry body 级别比较：

```text
entry_ready
entry_id
registry_status
entry_type
source_index_decision
bounded_publication_accepted
promotion_ready
approved_for_promotion
accepted_claim_count
blocked_claim_count
candidate_case_count
random_seed
pass_rate
allowed_use
model_quality_claim
decision_scope
source_count
source_kinds
consumer_boundary
next_step
```

此外还比较顶层：

```text
status
decision
failed_count
```

这也是 v930 真实运行有 44 个检查项的原因。

## Artifact writer

`src/minigpt/randomized_holdout_publication_registry_entry_check_artifacts.py` 输出：

- JSON：完整 contract check。
- CSV：check rows。
- text：命令行摘要。
- Markdown：人工审阅。
- HTML：截图归档。

HTML 中的重点是：

```text
status=pass
ready=True
original=registered
rebuilt=registered
boundary=governance_lookup_only
failed=0
```

## CLI

脚本：

```text
scripts/check_randomized_holdout_publication_registry_entry.py
```

真实运行：

```powershell
python scripts\check_randomized_holdout_publication_registry_entry.py `
  e\929\解释\randomized-holdout-publication-registry-entry `
  --out-dir e\930\解释\randomized-holdout-publication-registry-entry-check `
  --require-pass `
  --force
```

`--require-pass` 下，如果 entry 被篡改或 source index 不存在，CLI 会返回 1。

## 测试覆盖

新增：

```text
tests/test_randomized_holdout_publication_registry_entry_check.py
```

覆盖：

1. 干净 v929 entry 可以通过 contract check。
2. `consumer_boundary` 被篡改时失败。
3. source index 缺失时失败。
4. CLI `--require-pass` 在篡改 entry 下返回 1。
5. locator、artifact writer 和 CLI 输出 JSON/CSV/text/Markdown/HTML。

fixture 路线：

```text
ready_entry_inputs
  -> build_randomized_holdout_publication_registry_entry
  -> build_randomized_holdout_publication_registry_entry_check
```

测试仍然通过真实 v928-v929 构建路径产生 entry，而不是手写孤立 JSON。

## 真实运行证据

真实 v930 读取：

```text
e/929/解释/randomized-holdout-publication-registry-entry
```

结果：

```text
status=pass
decision=randomized_holdout_publication_registry_entry_contract_check_passed
contract_check_ready=True
original_registry_status=registered
rebuilt_registry_status=registered
original_consumer_boundary=governance_lookup_only
rebuilt_consumer_boundary=governance_lookup_only
passed_check_count=44
failed_check_count=0
```

截图：

```text
e/930/图片/v930-randomized-holdout-publication-registry-entry-check.png
```

## 一句话总结

v930 把 v929 registry entry 变成可复核产物，证明它能从 v928 source index 重建，并继续阻止 production promotion。
