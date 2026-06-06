# v929 randomized holdout publication registry entry 代码讲解

## 本版目标和边界

v929 的目标是把 v928 的 publication decision index 变成一个 registry entry：

```text
v928 publication decision index
  -> v929 publication registry entry
```

它回答的问题是：

```text
下游系统能否通过一个小条目查到这条 bounded randomized holdout publication 决策？
```

回答是可以，但用途限定为：

```text
governance_lookup_only
```

明确不做：

- 不重新训练。
- 不重新 replay。
- 不生成完整 registry manifest。
- 不批准 production promotion。
- 不把 20-case tiny-checkpoint 结论改写成通用模型质量结论。

## 前置链路

v929 消费：

```text
e/928/解释/randomized-holdout-publication-decision-index
```

v928 已经把 v925-v927 三层链条压缩成 index。v929 不再回读 packet、review、decision 三个源文件，而是只消费 v928 的统一索引。

这样做的意义是：

- registry entry 不需要了解三层内部结构。
- 下游消费面更小。
- 检查仍能确认 v928 没有把 bounded publication 扩成 promotion。

v929 的下一步路由到：

```text
check_randomized_holdout_publication_registry_entry
```

## 关键文件

### `src/minigpt/randomized_holdout_publication_registry_entry.py`

核心入口：

```python
build_randomized_holdout_publication_registry_entry(...)
```

输入：

- `publication_decision_index`：v928 index JSON。
- `publication_decision_index_path`：可选源路径，用于检查文件存在性。
- `entry_id`：默认 `randomized-holdout-publication-v928`。

输出：

```text
status
decision
failed_count
issues
publication_decision_index_path
source_index_summary
source_index
source_rows
check_rows
registry_entry
summary
interpretation
```

### locator

```python
locate_randomized_holdout_publication_decision_index(...)
```

如果输入是目录，自动定位：

```text
randomized_holdout_publication_decision_index.json
```

### `_checks(...)`

主要检查：

1. v928 source index 文件存在。
2. v928 index `status=pass`。
3. v928 decision 是 `randomized_holdout_publication_decision_index_ready`。
4. v928 summary 和 index body 都 ready。
5. indexed decision 是 `accept_bounded_randomized_holdout_publication`。
6. bounded publication accepted 在 summary 和 index 中都为 true。
7. accepted claim count 等于 1。
8. blocked claim count 至少为 3。
9. candidate case count 不低于 20。
10. pass rate 等于 1.0。
11. allowed use 保持 `bounded_model_capability_governance_only`。
12. model quality claim 保持 `bounded_randomized_target_hidden_holdout_claim_only`。
13. promotion 和 approved_for_promotion 都是 false。
14. source count 是 3。
15. source kinds 顺序仍是 publication decision、review、packet。
16. v928 failed check count 为 0。
17. v928 next step 正确指向 registry entry build。

这些检查保护的是“登记时不扩大能力边界”。

### `registry_entry`

通过时，registry entry 的核心字段为：

```text
entry_ready=True
entry_id=randomized-holdout-publication-v928
registry_status=registered
entry_type=bounded_model_capability_publication
source_index_path=e/928/解释/randomized-holdout-publication-decision-index/randomized_holdout_publication_decision_index.json
source_index_decision=accept_bounded_randomized_holdout_publication
bounded_publication_accepted=True
promotion_ready=False
approved_for_promotion=False
accepted_claim_count=1
blocked_claim_count=3
candidate_case_count=20
random_seed=914
pass_rate=1.0
allowed_use=bounded_model_capability_governance_only
model_quality_claim=bounded_randomized_target_hidden_holdout_claim_only
decision_scope=bounded_randomized_holdout_publication_only
consumer_boundary=governance_lookup_only
next_step=check_randomized_holdout_publication_registry_entry
```

这个条目可以给后续 manifest 或 dashboard 消费，但不能作为 production promotion 凭据。

## Artifact writer

`src/minigpt/randomized_holdout_publication_registry_entry_artifacts.py` 输出：

- JSON：完整 registry entry report。
- CSV：单行 entry，方便索引或表格读取。
- text：命令行摘要。
- Markdown：人工审阅。
- HTML：截图归档。

HTML 展示 stats、registry entry、checks 三个区域，重点确认：

```text
entry_ready=True
registry_status=registered
promotion=False
consumer_boundary=governance_lookup_only
```

## CLI

脚本：

```text
scripts/build_randomized_holdout_publication_registry_entry.py
```

真实运行：

```powershell
python scripts\build_randomized_holdout_publication_registry_entry.py `
  --publication-decision-index e\928\解释\randomized-holdout-publication-decision-index `
  --out-dir e\929\解释\randomized-holdout-publication-registry-entry `
  --require-entry-ready `
  --require-bounded-publication `
  --force
```

`--require-promotion-ready` 仍然是反向保护：如果有人要求 promotion ready，本版应返回失败。

## 测试覆盖

新增：

```text
tests/test_randomized_holdout_publication_registry_entry.py
```

覆盖：

1. 干净 v928 index 可以生成 registry entry。
2. source index 不 ready 时失败。
3. allowed use 被扩大时失败。
4. promotion_ready 被改成 true 时失败。
5. locator、artifact writer 和 CLI 输出 JSON/CSV/text/Markdown/HTML。

fixture 路线：

```text
ready_index_inputs
  -> build_randomized_holdout_publication_decision_index
  -> build_randomized_holdout_publication_registry_entry
```

也就是说，测试通过真实 v925-v928 构建链产生 index，而不是手写一个脱离生产路径的 JSON。

## 真实运行证据

真实 v929 读取：

```text
e/928/解释/randomized-holdout-publication-decision-index
```

结果：

```text
status=pass
decision=randomized_holdout_publication_registry_entry_ready
entry_id=randomized-holdout-publication-v928
registry_status=registered
bounded_publication_accepted=True
promotion_ready=False
consumer_boundary=governance_lookup_only
passed_check_count=18
failed_check_count=0
```

截图：

```text
e/929/图片/v929-randomized-holdout-publication-registry-entry.png
```

## 一句话总结

v929 把 bounded randomized holdout publication index 登记成治理查询条目，并继续把它限制在 governance lookup，而不是 production promotion。
