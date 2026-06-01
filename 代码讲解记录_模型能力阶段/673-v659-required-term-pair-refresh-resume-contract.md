# v659 required-term pair refresh resume contract

## 本版目标和边界

v659 的目标是让 required-term pair refresh 支持真实 checkpoint continuation。这里的关键点是：`scripts/train.py` 已经能 `--resume`，但模型能力实验 wrapper 之前没有暴露这个能力，所以 v649-v658 只能做单语料近似。

本版不训练新模型，只补入口、报告字段、测试和 contract。

## 关键修改

- `src/minigpt/model_capability_required_term_pair_coexistence_refresh.py`
  - 新增 `resume_checkpoint` 参数。
  - `_train_refresh_checkpoint()` 在命令里追加 `--resume <checkpoint>`。
  - training result 和 summary 标记 `checkpoint_continuation`。
- `scripts/run_model_capability_required_term_pair_coexistence_refresh.py`
  - 新增 `--resume-checkpoint` CLI 参数。
- `src/minigpt/model_capability_required_term_pair_coexistence_refresh_artifacts.py`
  - TXT/Markdown/HTML 显示 training mode 和 resume checkpoint 状态。
- `tests/test_model_capability_required_term_pair_coexistence_refresh.py`
  - 增加测试，确认 resume path 进入 training context 和报告。

## Contract

contract 使用 v630 checkpoint 作为 resume source 做 dry-run 级别验证，输出到：

- `e/659/解释/required-term-pair-refresh-resume-contract/`
- `e/659/图片/v659-refresh-resume-contract.png`

结果：

- `status=pass`
- `decision=required_term_pair_refresh_resume_contract_ready`
- `training_mode=checkpoint_continuation`
- `resume_checkpoint_exists=True`

## 一句话总结

v659 把 required-term pair 实验从“只能重训”推进到“可以真实续训”的入口层。
