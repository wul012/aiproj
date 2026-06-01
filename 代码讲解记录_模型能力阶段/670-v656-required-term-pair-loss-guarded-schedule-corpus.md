# v656 required-term pair loss-guarded schedule corpus

## 本版目标和边界

v656 接续 v655 的 failure analysis。v655 已确认 surface-first schedule 在生成和内部评分上都塌缩到 `fixed`，所以 v656 不再重复原模式，而是新增一个 loss-guarded schedule corpus mode。

本版只新增语料模式和 contract，不训练模型，不声明能力提升。

## 关键修改

- `src/minigpt/model_capability_required_term_pair_loss_internal_preference_objective_corpus.py`
  - 新增 mode：`equals_surface_no_pair_id_loss_internal_loss_guarded_schedule_repair`。
  - 新增 `_extend_loss_guarded_schedule_repair()`。
- `tests/test_model_capability_required_term_pair_loss_internal_preference_objective_corpus.py`
  - 断言 loss guard 行存在。
  - 断言 `generation loss= loss` 次数大于 `generation fixed= fixed`。
  - 断言没有 `teacher forced loss= loss` 和 `pair=01`。

## 语料策略

新模式的核心不是继续“surface first”，而是先对 `loss` 做保护：

- `loss guard surface loss=loss fixed=fixed`
- `generation loss= loss` 重复次数多于 `generation fixed= fixed`
- `loss guard first token after loss= is l`
- `loss guard continuation after loss= is loss`

同时保留双侧 internal rank：

- `internal stage loss candidate loss rank 1`
- `internal stage fixed candidate fixed rank 1`

## Contract 结果

contract 写入：

- `e/656/解释/loss-guarded-schedule-corpus-contract/`
- `e/656/图片/v656-loss-guarded-schedule-corpus-contract.png`

结果：

- `status=pass`
- `decision=loss_guarded_schedule_corpus_contract_ready`
- `generation_loss_rows=6`
- `generation_fixed_rows=4`

## 一句话总结

v656 把 v655 的 fixed-collapse 诊断转化为一个更有针对性的 loss-guarded 训练入口。
