# v922 randomized holdout decision index 代码讲解

## 本版目标和边界

v922 的目标是给 v918-v921 的 randomized holdout bounded acceptance 链路建立一个 decision index。

v921 已经接受了一个很窄的能力声明：

```text
bounded_randomized_target_hidden_holdout_claim_only
```

v922 不扩大这个声明。它做的是索引和复核，把四个真实上游产物并排放进同一个报告里，确认它们的 status、decision、ready 字段、case count、seed、pass rate 和 promotion boundary 没有漂移。

明确不做：

- 不重新训练模型。
- 不重新跑 v916 的真实 checkpoint replay。
- 不修改 v918-v921 的源产物。
- 不批准 production promotion。
- 不把 20-case tiny-checkpoint holdout 结论泛化成通用模型质量。

## 前置链路

```text
v914 randomized target-hidden holdout suite
  -> v915 dry-run
  -> v916 real replay
  -> v917 replay review
  -> v918 candidate promotion packet
  -> v919 candidate packet review
  -> v920 bounded promotion gate
  -> v921 bounded promotion decision
  -> v922 decision index
```

v922 只消费 v918-v921 这四层，因为这四层已经把 replay 信号收敛成 bounded acceptance 链。

## 关键文件

### `src/minigpt/randomized_holdout_decision_index.py`

核心入口：

```python
build_randomized_holdout_decision_index(...)
```

输入：

- `bounded_decision_report`：v921 decision。
- `bounded_gate_report`：v920 gate。
- `candidate_packet_review_report`：v919 review。
- `candidate_packet_report`：v918 packet。
- 四个可选 source path。
- `minimum_candidate_cases=20`。

输出字段：

```text
schema_version
title
generated_at
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

其中 `source_rows` 是本版的索引主体。它把四个来源统一为以下结构：

```text
kind
path
exists
status
decision
ready_key
ready_value
candidate_case_count
random_seed
pass_rate
promotion_ready
approved_for_promotion
model_quality_claim
failed_check_count
role
```

这样下游不用分别理解 v918、v919、v920、v921 的报告 shape，可以先消费统一索引。

### locator 函数

本版提供四个 locator：

```python
locate_randomized_holdout_bounded_promotion_decision(...)
locate_randomized_holdout_bounded_promotion_gate(...)
locate_randomized_holdout_candidate_packet_review(...)
locate_randomized_holdout_candidate_packet(...)
```

它们支持传入 JSON 文件或输出目录。传目录时会自动补上对应的标准 JSON 文件名。

### `_checks(...)`

本版最重要的保护逻辑在 `_checks(...)`。

它检查：

- 四个 source 文件都存在。
- v921 decision 是 `randomized_holdout_bounded_promotion_decision_accepted`。
- v921 summary 的 `bounded_promotion_accepted=True`。
- v920 gate ready 且 `approved_for_bounded_promotion_decision=True`。
- v919 review ready 且 `approved_for_bounded_promotion_gate=True`。
- v918 packet ready 且 `candidate_packet_authorized=True`。
- 四层 candidate count 一致并达到 20。
- 四层 random seed 一致。
- 四层 pass rate 一致并等于 `1.0`。
- gate/review/packet 的 clean randomized count 与 candidate count 一致。
- 四层 `failed_check_count` 都是 0。
- 四层 `promotion_ready=False`。
- 四层 `approved_for_promotion=False`。
- 四层 claim scope 分别保持在 expected bounded scope。

这个检查集的意义是：v922 不重新证明模型能力，而是防止上游任何一层被替换、篡改、或者悄悄扩大声明边界。

### `_index(...)`

`_index(...)` 在所有 check 通过后生成可消费索引：

```text
index_ready=True
indexed_decision=accept_bounded_randomized_holdout_claim
bounded_promotion_accepted=True
promotion_ready=False
approved_for_promotion=False
candidate_case_count=20
random_seed=914
pass_rate=1.0
claim_scope=randomized_target_hidden_20_case_tiny_checkpoint_only
model_quality_claim=bounded_randomized_target_hidden_holdout_claim_only
source_count=4
next_step=build_randomized_holdout_acceptance_summary
```

注意这里的 `model_quality_claim` 仍然是 bounded claim，不是 production claim。

### `src/minigpt/randomized_holdout_decision_index_artifacts.py`

这个文件只负责输出格式：

- text：给命令行和 CI 看。
- CSV：列出四个 source row。
- Markdown：适合人工审阅。
- HTML：适合截图和归档。
- JSON：保留完整机器可读结构。

它不做新的判定，避免 renderer 和 checker 职责混在一起。

### `scripts/build_randomized_holdout_decision_index.py`

CLI 参数：

```text
--bounded-decision
--bounded-gate
--candidate-packet-review
--candidate-packet
--minimum-candidate-cases
--out-dir
--require-index-ready
--require-bounded-acceptance
--require-promotion-ready
--force
```

本版真实运行时使用了 `--require-index-ready` 和 `--require-bounded-acceptance`，没有使用 `--require-promotion-ready`，因为 v922 的正确边界是 bounded acceptance，不是 production promotion。

## 测试覆盖

新增测试文件：

```text
tests/test_randomized_holdout_decision_index.py
```

测试覆盖了五类行为：

1. 干净链路可以生成 ready index。
2. v921 bounded acceptance 被改掉时失败。
3. v920 gate 的 seed 漂移时失败。
4. v918 packet 把 `promotion_ready` 改成 true 时失败。
5. artifact writer 和 CLI 都能写出 JSON/CSV/text/Markdown/HTML。

focused 测试命令覆盖 v918-v922：

```powershell
python -m pytest tests\test_randomized_holdout_candidate_promotion_packet.py `
  tests\test_randomized_holdout_candidate_promotion_packet_review.py `
  tests\test_randomized_holdout_bounded_promotion_gate.py `
  tests\test_randomized_holdout_bounded_promotion_decision.py `
  tests\test_randomized_holdout_decision_index.py `
  -q -o cache_dir=runs\pytest-cache-v922-focused
```

结果：

```text
25 passed
```

## 真实运行证据

v922 使用真实 v918-v921 归档产物运行：

```powershell
python scripts\build_randomized_holdout_decision_index.py `
  --bounded-decision e\921\解释\randomized-holdout-bounded-promotion-decision `
  --bounded-gate e\920\解释\randomized-holdout-bounded-promotion-gate `
  --candidate-packet-review e\919\解释\randomized-holdout-candidate-promotion-packet-review `
  --candidate-packet e\918\解释\randomized-holdout-candidate-promotion-packet `
  --out-dir e\922\解释\randomized-holdout-decision-index `
  --require-index-ready `
  --require-bounded-acceptance `
  --force
```

关键结果：

```text
status=pass
decision=randomized_holdout_decision_index_ready
failed_count=0
randomized_holdout_decision_index_ready=True
bounded_promotion_accepted=True
promotion_ready=False
candidate_case_count=20
random_seed=914
pass_rate=1.0
source_count=4
passed_check_count=23
failed_check_count=0
```

Playwright MCP 也打开了 HTML，并确认页面显示：

```text
Status pass
Index ready True
Bounded accepted True
Promotion False
Cases 20
Seed 914
Sources 4
```

截图位置：

```text
e/922/图片/v922-randomized-holdout-decision-index.png
```

## README 和归档作用

- `README.md` 记录 v922 是当前版本。
- `e/922/解释/说明.md` 记录运行命令、输入输出和截图。
- `e/README.md` 增加 v922 归档入口。
- `代码讲解记录_模型能力阶段/README.md` 增加本篇索引。

这些文档不是模型能力证据本身，真正的机器可读证据是：

```text
e/922/解释/randomized-holdout-decision-index/randomized_holdout_decision_index.json
```

## 一句话总结

v922 把 randomized holdout 的 bounded acceptance 链从“单个最终 decision”推进成“四层一致、可消费、可复核的 decision index”，但仍然坚持 direct promotion 不放行。
