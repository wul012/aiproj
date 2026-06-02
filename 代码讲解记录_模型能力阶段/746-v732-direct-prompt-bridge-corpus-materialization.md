# v732 direct-prompt bridge corpus materialization

## 本版目标和边界

v732 的目标是把 v731 direct-prompt bridge contract patch 物化成训练 corpus。

本版不新增代码、不训练模型、不做能力声明。它验证 v731 patch 已被 materializer 接受，并生成下一版训练用的数据。

## 前置链路

```text
v730 surface mismatch diagnostic
 -> raw direct prompt bridge needed
v731 direct-prompt bridge contract patch
 -> 26 patched rows
v732 corpus materialization
 -> 8320 training lines
```

## 输入输出

输入：

```text
e/731/解释/model-capability-required-term-pair-readiness-direct-prompt-bridge-contract-patch/
```

输出：

```text
pair_readiness_training_corpus.txt
pair_readiness_heldout_eval_fixture.json
model_capability_required_term_pair_readiness_corpus_materialization.json
```

## 核心参数

```text
repeat=320
patched training rows=26
training_line_count=8320
evaluation_probe_count=3
```

## 泄漏检查

v732 的关键检查是：

```text
contract_decision pass pair_readiness_direct_prompt_bridge_contract_patch_ready
heldout_not_in_training_rows pass False
heldout_not_in_corpus pass False
```

它证明 materializer 消费的是 v731 patch，并且 `fixed=|loss=` 没有泄漏进训练语料。

## 证据

运行证据：

- `e/732/解释/model-capability-required-term-pair-readiness-direct-prompt-bridge-corpus-materialization/`
- `e/732/图片/v732-direct-prompt-bridge-corpus-materialization.png`

## 一句话总结

v732 把 direct-prompt bridge patch 转成 8320 行训练 corpus，同时保留 heldout pair probe 边界。
