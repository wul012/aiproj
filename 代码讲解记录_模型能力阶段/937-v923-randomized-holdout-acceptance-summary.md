# v923 randomized holdout acceptance summary 代码讲解

## 本版目标和边界

v923 的目标是把 v922 的 decision index 转成 acceptance summary。

v922 已经证明：

```text
v918 packet
v919 packet review
v920 bounded gate
v921 bounded decision
```

这四层一致，并且可以形成一个 bounded randomized holdout acceptance。v923 不重复四层检查，而是给下游一个更清晰的问题答案：

```text
现在到底接受了什么？
还有什么没有被接受？
这个结论能被谁使用？
```

明确不做：

- 不重新训练。
- 不重新 replay。
- 不重新构建 v918-v922 的源证据。
- 不批准 production promotion。
- 不扩大 tiny checkpoint 的 20-case holdout 结论。

## 前置链路

```text
v922 randomized holdout decision index
  -> v923 randomized holdout acceptance summary
```

v923 的唯一输入是 v922 index，因此它是一个 summary 层，不是新的 evaluator。

## 关键文件

### `src/minigpt/randomized_holdout_acceptance_summary.py`

核心入口：

```python
build_randomized_holdout_acceptance_summary(...)
```

输入：

- `decision_index`：v922 的 JSON report。
- `decision_index_path`：可选源路径。
- `minimum_candidate_cases=20`。

输出：

```text
status
decision
failed_count
issues
source_decision_index
index_summary
source_rows
accepted_claims
blocked_claims
check_rows
acceptance_card
summary
interpretation
```

其中最关键的是三块：

```text
accepted_claims
blocked_claims
acceptance_card
```

### `accepted_claims`

本版只生成一个 accepted claim：

```text
claim_id=bounded_randomized_target_hidden_holdout_claim
status=accepted
scope=randomized_target_hidden_20_case_tiny_checkpoint_only
model_quality_claim=bounded_randomized_target_hidden_holdout_claim_only
allowed_use=bounded_model_capability_governance_only
```

这避免下游误解为 production claim。

### `blocked_claims`

本版固定生成三条 blocked claim：

```text
production_promotion
general_model_quality
larger_corpus_transfer
```

这三条不是失败，而是边界说明。它们告诉后续消费者：当前证据不能用于生产推广、通用质量声明或大语料迁移结论。

### `_checks(...)`

本版 check 的重点是保证 v922 index 没被错误消费。

它检查：

- source decision index 文件存在。
- v922 index status 是 `pass`。
- v922 decision 是 `randomized_holdout_decision_index_ready`。
- v922 summary 的 `randomized_holdout_decision_index_ready=True`。
- `bounded_promotion_accepted=True`。
- `promotion_ready=False`。
- `approved_for_promotion=False`。
- candidate count 至少 20。
- random seed 存在。
- pass rate 等于 `1.0`。
- claim scope 仍是 `bounded_randomized_target_hidden_holdout_claim_only`。
- source rows 至少 4 条。
- source kinds 包含 packet、review、gate、decision。
- source rows 全部 passed and ready。
- source rows 全部保持 promotion false。

这组检查的意义是：summary 可以更易读，但不能损失 v922 index 的边界约束。

### `acceptance_card`

`acceptance_card` 是下游最容易消费的结构：

```text
card_ready
accepted
accepted_claim_count
blocked_claim_count
candidate_case_count
random_seed
pass_rate
promotion_ready
approved_for_promotion
model_quality_claim
allowed_use
source_count
next_step
```

真实 v923 输出中：

```text
accepted=True
accepted_claim_count=1
blocked_claim_count=3
promotion_ready=False
allowed_use=bounded_model_capability_governance_only
next_step=check_randomized_holdout_acceptance_summary_contract
```

## Artifact writer

`src/minigpt/randomized_holdout_acceptance_summary_artifacts.py` 输出五种文件：

- JSON：完整机器可读报告。
- CSV：accepted + blocked claim 表。
- text：命令行和 CI 友好摘要。
- Markdown：人工审阅版本。
- HTML：截图归档版本。

HTML 把 accepted claims、blocked claims、checks 分成三张表，避免把“被阻止的生产推广”藏在小字段里。

## CLI

脚本：

```text
scripts/build_randomized_holdout_acceptance_summary.py
```

关键参数：

```text
--decision-index
--minimum-candidate-cases
--out-dir
--require-summary-ready
--require-bounded-acceptance
--require-promotion-ready
--force
```

真实运行使用：

```powershell
python scripts\build_randomized_holdout_acceptance_summary.py `
  --decision-index e\922\解释\randomized-holdout-decision-index `
  --out-dir e\923\解释\randomized-holdout-acceptance-summary `
  --require-summary-ready `
  --require-bounded-acceptance `
  --force
```

没有使用 `--require-promotion-ready`，因为 v923 的正确状态仍然是 promotion blocked。

## 测试覆盖

新增：

```text
tests/test_randomized_holdout_acceptance_summary.py
```

覆盖：

1. 干净 v922 index 能生成 ready summary。
2. v922 index 未 ready 时 summary fail。
3. source row 把 `promotion_ready` 改成 true 时 summary fail。
4. CLI 和 artifact writer 都能写出 JSON/CSV/text/Markdown/HTML。

focused 测试：

```text
9 passed
```

## 真实运行证据

真实 v923 读取：

```text
e/922/解释/randomized-holdout-decision-index/randomized_holdout_decision_index.json
```

结果：

```text
status=pass
decision=randomized_holdout_acceptance_summary_ready
failed_count=0
accepted_claim_count=1
blocked_claim_count=3
promotion_ready=False
allowed_use=bounded_model_capability_governance_only
passed_check_count=15
failed_check_count=0
```

截图：

```text
e/923/图片/v923-randomized-holdout-acceptance-summary.png
```

## 一句话总结

v923 把 randomized holdout 的 bounded acceptance 从“机器索引”推进成“人和下游都能消费的接受摘要”，同时把生产推广、通用质量和大语料迁移三类扩大解释明确挡住。
