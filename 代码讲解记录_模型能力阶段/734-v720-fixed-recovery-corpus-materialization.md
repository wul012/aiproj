# v720 fixed-recovery corpus materialization

## 本版目标和边界

v720 的目标是把 v719 contract patch 写成真实训练数据。

本版不训练模型，不判断模型能力。它只保证：

- fixed-recovery patch 可以被 materializer 识别。
- training corpus 和 heldout fixture 都写入磁盘。
- heldout pair probe 没有泄漏进 corpus。

## 前置链路

```text
v719 fixed-recovery contract patch
 -> decision=pair_readiness_fixed_recovery_contract_patch_ready
v720 corpus materialization
 -> pair_readiness_training_corpus.txt
 -> pair_readiness_heldout_eval_fixture.json
```

## 输入输出

输入：

```text
e/719/解释/model-capability-required-term-pair-readiness-fixed-recovery-contract-patch/
```

输出：

```text
e/720/解释/model-capability-required-term-pair-readiness-fixed-recovery-corpus-materialization/
```

核心产物：

- `pair_readiness_training_corpus.txt`
  - 22 条 patched rows 重复 320 次。
  - 共 7040 行。

- `pair_readiness_heldout_eval_fixture.json`
  - fixed/loss/pair 三个 probes。

- `model_capability_required_term_pair_readiness_corpus_materialization.json`
  - materialization report。

## 校验逻辑

v720 的 materializer checks：

```text
contract_passed=pass
contract_decision=pair_readiness_fixed_recovery_contract_patch_ready
repeat_positive=320
training_rows_present=22
heldout_not_in_training_rows=False
heldout_not_in_corpus=False
```

这里的两个 False 表示“不存在泄漏”：

- heldout pair 不在 training rows。
- heldout pair 不在重复后的 corpus lines。

## 证据

运行截图：

- `e/720/图片/v720-fixed-recovery-corpus-materialization.png`

关键输出：

```text
status=pass
decision=pair_readiness_corpus_materialized
training_line_count=7040
evaluation_probe_count=3
model_quality_claim=data_artifact_only
```

## 一句话总结

v720 把 fixed-recovery patch 变成 7040 行真实训练 corpus，下一步必须通过 v721 真实训练验证 fixed 是否恢复且 loss 是否保留。
