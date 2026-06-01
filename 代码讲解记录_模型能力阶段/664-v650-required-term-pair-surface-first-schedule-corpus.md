# v650 required-term pair surface-first schedule corpus

## 本版目标和边界

v650 接在 v649 的 schedule plan 后面，把计划里的“surface first, internal second”变成一个可被现有训练脚本调用的 corpus mode。

本版不训练模型，也不声明能力提升。它只保证新模式能被注册、能生成语料、能保留 `fixed=` / `loss=` 两个 source prompt，并在语料中写明 `no checkpoint resume` 边界。

## 关键修改

- `src/minigpt/model_capability_required_term_pair_loss_internal_preference_objective_corpus.py`
  - 新增 `equals_surface_no_pair_id_loss_internal_surface_first_schedule_repair`。
  - 新增 `_extend_surface_first_schedule_repair()`。
  - 语料顺序先写 surface stage，再写 internal rank stage。
- `tests/test_model_capability_required_term_pair_loss_internal_preference_objective_corpus.py`
  - 增加新模式断言。
  - 覆盖 surface generation 行、internal rank 行、no-resume 边界、无 pair id、无 heavy teacher-forced loss 行。
- `e/650/解释/surface-first-schedule-corpus-contract/`
  - 保存本版 corpus contract 的 JSON/CSV/TXT/Markdown/HTML。

## 语料设计

新模式的语料分三层：

- surface stage：
  - `surface stage fixed=fixed loss=loss`
  - `generation fixed= fixed`
  - `generation loss= loss`
- completion stage：
  - `fixed=f fixed=fi fixed=fix fixed=fixed`
  - `loss=l loss=lo loss=los loss=loss`
- internal stage：
  - `internal stage fixed candidate fixed rank 1`
  - `internal stage loss candidate loss rank 1`

bridge 行补充说明：

- `surface-first schedule approximates two-stage training in one corpus.`
- `generation pair-full remains the gate before internal repair.`
- `not checkpoint resume; this is a corpus schedule approximation.`

## 测试覆盖

本版单测重点不是训练结果，而是防止语料设计走偏：

- 新模式必须注册。
- 必须保留 `fixed=` / `loss=` prompt。
- 必须包含 `generation fixed= fixed` 和 `generation loss= loss`。
- 必须包含 internal rank 行。
- 不能包含 `teacher forced loss= loss`。
- 不能出现 `pair=01`。

## 运行证据

产物写入：

- `e/650/解释/surface-first-schedule-corpus-contract/`
- `e/650/图片/v650-surface-first-schedule-corpus-contract.png`

contract 显示 `status=pass`、`failed_count=0`，说明 v651 可以用这个 corpus mode 进入真实训练实验。

## 一句话总结

v650 把两阶段计划从“可审计方向”推进到“可训练语料入口”，同时保留了不声明续训的边界。
