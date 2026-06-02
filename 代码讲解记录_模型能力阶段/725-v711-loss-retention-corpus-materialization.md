# v711 loss-retention corpus materialization

## 本版目标和边界

v711 的目标是把 v710 patched contract materialize 成新的训练 corpus 和 heldout eval fixture。

本版不新增 Python 模块，不训练模型；它验证 v710 的 patched contract 能被现有 materializer 接住。

## 前置链路

v710 输出：

```text
decision=pair_readiness_loss_retention_contract_patch_ready
base_training_row_count=12
patched_training_row_count=20
added_training_row_count=8
```

v711 直接把 v710 JSON 作为 materializer 输入。

## 关键命令

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_corpus_materialization.py e\710\解释\model-capability-required-term-pair-readiness-loss-retention-contract-patch\model_capability_required_term_pair_readiness_loss_retention_contract_patch.json --out-dir e\711\解释\model-capability-required-term-pair-readiness-loss-retention-corpus-materialization --repeat 320 --require-pass --force
```

## 输出产物

```text
pair_readiness_training_corpus.txt
pair_readiness_heldout_eval_fixture.json
model_capability_required_term_pair_readiness_corpus_materialization.json
```

核心指标：

```text
training_line_count=6400
evaluation_probe_count=3
model_quality_claim=data_artifact_only
```

## 这版的价值

v711 证明 v710 patch 不是停留在计划或报告层，它已经能进入同一条 corpus materialization 链路。这样 v712 可以直接复用 v707 training run CLI，比较 patched corpus 是否改善 loss retention。

## 一句话总结

v711 将 loss-retention patched contract 落成 6400 行训练 corpus，准备进入第二次 pair-readiness 实训。
