# v728 objective-structure corpus materialization

## 本版目标和边界

v728 的目标是把 v727 objective-structure contract 物化成训练语料和 heldout eval fixture。

本版不新增代码、不训练模型、不做能力声明。它验证 v727 新 contract 已经被 materializer 接受，并生成下一版训练要用的实际数据文件。

## 前置链路

```text
v726 objective-structure plan
 -> contract requirements
v727 objective-structure contract
 -> 18 checked training rows
v728 corpus materialization
 -> 5760 training lines + heldout fixture
```

## 输入输出

输入：

```text
e/727/解释/model-capability-required-term-pair-readiness-objective-structure-contract/
```

输出：

```text
e/728/解释/model-capability-required-term-pair-readiness-objective-structure-corpus-materialization/pair_readiness_training_corpus.txt
e/728/解释/model-capability-required-term-pair-readiness-objective-structure-corpus-materialization/pair_readiness_heldout_eval_fixture.json
```

materializer 同时输出 JSON/CSV/TXT/Markdown/HTML 报告，用于审计本次物化。

## 核心参数

```text
repeat=320
contract training rows=18
training_line_count=5760
evaluation_probe_count=3
```

这里没有新增训练样本语义，只是重复 contract rows 形成 tiny training corpus。

## 泄漏检查

v728 继承 materializer 的检查：

```text
contract_passed
contract_decision
repeat_positive
training_rows_present
heldout_not_in_training_rows
heldout_not_in_corpus
```

最关键的是：

```text
heldout_not_in_training_rows pass False
heldout_not_in_corpus pass False
```

它证明 `fixed=|loss=` 没有作为训练行或 corpus line 出现。

## 证据

运行证据：

- `e/728/解释/model-capability-required-term-pair-readiness-objective-structure-corpus-materialization/`
- `e/728/图片/v728-objective-structure-corpus-materialization.png`

截图显示 `training_line_count=5760`、`evaluation_probe_count=3` 和全部 checks pass。

## 一句话总结

v728 把 objective-structure contract 变成可训练数据，同时保住 heldout direct/pair probe 边界。
