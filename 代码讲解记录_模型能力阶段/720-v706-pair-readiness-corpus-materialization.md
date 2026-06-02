# v706 pair-readiness corpus materialization

## 本版目标和边界

v706 的目标是把 v705 的 train/eval contract materialize 成真实文件。它不是模型训练版，而是数据落地版。

本版解决的问题是：后续训练必须基于明确 corpus 与 heldout fixture，而不是脚本临时拼接字符串。

## 前置链路

v705 输出：

```text
decision=pair_readiness_split_contract_ready
training_row_count=12
evaluation_probe_count=3
heldout_pair_probe=fixed=|loss=
```

v706 读取这个 contract，按 `repeat=320` 展开训练行。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_readiness_corpus_materialization.py`
  - materialization builder。
  - 负责生成 corpus path、heldout fixture path、检查行泄漏、输出 summary。

- `src/minigpt/model_capability_required_term_pair_readiness_corpus_materialization_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 展示 materialized paths、checks 和 corpus preview。

- `scripts/run_model_capability_required_term_pair_readiness_corpus_materialization.py`
  - CLI。
  - 输入 v705 contract，输出 corpus 和 fixture。

- `tests/test_model_capability_required_term_pair_readiness_corpus_materialization.py`
  - 覆盖 ready、heldout leak 阻断、文件写入、输出格式。

## 核心数据结构

materialized paths：

```text
training_corpus
heldout_eval_fixture
```

training corpus summary：

```text
line_count
char_count
preview
```

heldout fixture：

```text
probes
heldout_pair_probe
promotion_requirement
training_rows
```

其中 `training_rows` 被保留在 fixture 里，是为了后续检查训练输入是否来自同一 contract。

## Check 设计

v706 检查：

```text
contract_passed
contract_decision
repeat_positive
training_rows_present
heldout_not_in_training_rows
heldout_not_in_corpus
```

最关键的是后两个检查：`fixed=|loss=` 不能作为 training row，也不能出现在展开后的 corpus line 中。

## 运行证据

输出：

```text
status=pass
decision=pair_readiness_corpus_materialized
training_line_count=3840
evaluation_probe_count=3
model_quality_claim=data_artifact_only
```

证据目录：

```text
e/706/解释/model-capability-required-term-pair-readiness-corpus-materialization/
e/706/图片/v706-pair-readiness-corpus-materialization.png
```

## 一句话总结

v706 把 pair-readiness contract 转成真实训练 corpus 和 heldout eval fixture，让下一步训练有清晰输入边界。
