# v928 randomized holdout publication decision index 代码讲解

## 本版目标和边界

v928 的目标是把 v925-v927 形成的 publication chain 收束成一个轻量索引：

```text
v925 publication packet
  -> v926 publication packet review
  -> v927 publication decision
  -> v928 publication decision index
```

它回答的问题是：

```text
这条 bounded randomized holdout publication decision 是否可以被下游通过统一索引查到？
```

回答是可以，但范围仍然很窄：

```text
bounded_randomized_holdout_publication_only
```

明确不做：

- 不重新训练。
- 不重新 replay。
- 不新增模型质量结论。
- 不批准 production promotion。
- 不把 governance artifact 当成真实生产模型能力证明。

## 前置链路

v928 消费三份真实产物：

```text
e/925/解释/randomized-holdout-acceptance-publication-packet
e/926/解释/randomized-holdout-acceptance-publication-packet-review
e/927/解释/randomized-holdout-publication-decision
```

这三个产物分别承担：

- v925：把 accepted/blocked claims 和 contract check 打包。
- v926：复核 packet 只允许 bounded downstream publication。
- v927：记录最终 bounded publication decision。

v928 的下一步路由到：

```text
build_randomized_holdout_publication_registry_entry
```

## 关键文件

### `src/minigpt/randomized_holdout_publication_decision_index.py`

核心入口：

```python
build_randomized_holdout_publication_decision_index(...)
```

输入：

- `publication_decision`：v927 decision JSON。
- `publication_review`：v926 review JSON。
- `publication_packet`：v925 packet JSON。
- `publication_decision_path` / `publication_review_path` / `publication_packet_path`：用于检查源文件存在性和写入 source row。

输出：

```text
status
decision
failed_count
issues
source_rows
check_rows
index
summary
interpretation
```

### locator

三个 locator 允许 CLI 既接收 JSON 文件，也接收产物目录：

```python
locate_randomized_holdout_publication_decision(...)
locate_randomized_holdout_publication_packet_review(...)
locate_randomized_holdout_acceptance_publication_packet(...)
```

如果输入是目录，locator 自动补齐标准 JSON 文件名。

### `source_rows`

v928 把三层来源标准化成 source row：

```text
kind
path
exists
status
decision
ready_key
ready_value
accepted_claim_count
blocked_claim_count
candidate_case_count
random_seed
pass_rate
promotion_ready
approved_for_promotion
allowed_use
model_quality_claim
next_step
failed_check_count
role
```

这些字段的作用是让下游不用重新理解 v925-v927 的内部结构，只需要读取统一 source row 即可确认链路状态。

### `_checks(...)`

主要检查：

1. 三个源 JSON 文件都存在。
2. v927 decision `status=pass`。
3. v927 decision 是 `randomized_holdout_publication_decision_accepted`。
4. v927 summary ready。
5. v927 只接受 bounded publication。
6. v926 review `status=pass` 且 ready。
7. v926 review 批准 bounded publication。
8. v925 packet `status=pass` 且 ready。
9. accepted claim count 三层一致且等于 1。
10. blocked claim count 三层一致且至少为 3。
11. candidate case count 三层一致且不低于 20。
12. random seed 三层一致。
13. pass rate 三层一致且等于 1.0。
14. allowed use 三层都是 `bounded_model_capability_governance_only`。
15. model quality claim 三层都是 `bounded_randomized_target_hidden_holdout_claim_only`。
16. promotion 和 approved_for_promotion 三层都保持 false。
17. source failed check count 全为 0。
18. next step 按 packet -> review -> decision -> index 的顺序对齐。

这些检查保护的是“交接链没有被改宽”，而不是证明模型有通用能力。

### `index`

通过时，index 的关键字段为：

```text
index_ready=True
indexed_decision=accept_bounded_randomized_holdout_publication
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
source_count=3
next_step=build_randomized_holdout_publication_registry_entry
```

这让后续 registry entry 可以直接消费一个小索引，而不是重新读取三层产物。

## Artifact writer

`src/minigpt/randomized_holdout_publication_decision_index_artifacts.py` 输出：

- JSON：完整 index report。
- CSV：source rows，方便后续表格或审计读取。
- text：命令行摘要。
- Markdown：人工审阅。
- HTML：截图归档。

HTML 中展示了 stats、source rows、checks 三个区域，用来确认：

```text
status=pass
index_ready=True
bounded_publication_accepted=True
promotion=False
source_count=3
```

## CLI

脚本：

```text
scripts/index_randomized_holdout_publication_decision.py
```

真实运行：

```powershell
python scripts\index_randomized_holdout_publication_decision.py `
  --publication-decision e\927\解释\randomized-holdout-publication-decision `
  --publication-review e\926\解释\randomized-holdout-acceptance-publication-packet-review `
  --publication-packet e\925\解释\randomized-holdout-acceptance-publication-packet `
  --out-dir e\928\解释\randomized-holdout-publication-decision-index `
  --require-index-ready `
  --require-bounded-publication `
  --force
```

`--require-index-ready` 和 `--require-bounded-publication` 让 CLI 可以用于 CI 或 release-style gate。

`--require-promotion-ready` 保留为反向保护：当前报告即使 pass，该参数也会返回失败，因为 v928 明确不允许 direct promotion。

## 测试覆盖

新增：

```text
tests/test_randomized_holdout_publication_decision_index.py
```

覆盖：

1. 干净 v925-v927 链路可以生成 index。
2. v927 decision 被改成未接受时失败。
3. v926 review allowed use 被扩大时失败。
4. v925 packet promotion_ready 被改成 true 时失败。
5. locator、artifact writer 和 CLI 输出 JSON/CSV/text/Markdown/HTML。

测试 fixture 不是手写大 JSON，而是沿用真实构建函数：

```text
ready_review_inputs
  -> build_randomized_holdout_acceptance_publication_packet_review
  -> build_randomized_holdout_publication_decision
  -> build_randomized_holdout_publication_decision_index
```

这样测试能覆盖同一条链路的字段传递。

## 真实运行证据

真实 v928 读取：

```text
e/927/解释/randomized-holdout-publication-decision
e/926/解释/randomized-holdout-acceptance-publication-packet-review
e/925/解释/randomized-holdout-acceptance-publication-packet
```

结果：

```text
status=pass
decision=randomized_holdout_publication_decision_index_ready
bounded_publication_accepted=True
promotion_ready=False
accepted_claim_count=1
blocked_claim_count=3
source_count=3
passed_check_count=21
failed_check_count=0
```

截图：

```text
e/928/图片/v928-randomized-holdout-publication-decision-index.png
```

## 一句话总结

v928 把 bounded randomized holdout publication decision 链条变成可查询索引，为后续 registry entry 做准备，并继续明确阻止 direct promotion。
