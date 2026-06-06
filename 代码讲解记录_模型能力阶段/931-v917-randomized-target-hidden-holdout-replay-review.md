# v917 randomized target-hidden holdout replay review 代码讲解

## 本版目标和边界

v917 的目标是 review v916 的 randomized real replay。

v916 已经证明真实 v890 checkpoint 在 20 条 seeded randomized target-hidden prompt 上 `20/20` 命中。v917 不重复 replay，而是检查这份强信号是否来自干净 prompt：没有目标词泄漏、没有已知 task hint、prompt 唯一，并且明确标记为 randomized。

明确不做：

- 不重新训练。
- 不运行模型生成。
- 不改写 v914 suite。
- 不批准 promotion。
- 不把 20/20 直接变成最终模型结论。

本版只批准进入 candidate promotion packet。

## 前置链路

```text
v914 randomized target-hidden suite
  -> v915 dry-run
  -> v916 real replay
  -> v917 replay review
  -> next candidate promotion packet
```

## 关键文件

### `src/minigpt/randomized_target_hidden_holdout_replay_review.py`

这是本版核心 builder。

入口函数：

```python
build_randomized_target_hidden_holdout_replay_review(...)
```

输入：

- v916 real replay report。
- v914 holdout suite report。
- 可选 `real_replay_path` 和 `holdout_suite_path`。

输出：

- `status`
- `decision`
- `failed_count`
- `issues`
- `source_real_replay`
- `source_holdout_suite`
- `source_real_replay_summary`
- `source_holdout_suite_summary`
- `check_rows`
- `review_rows`
- `summary`
- `interpretation`

### `_review_rows`

`_review_rows` 遍历 v914 的 cases，并与 coverage rows 对齐。

每行生成：

```text
case_id
source_case_id
random_draw_index
expected_terms
leaked_terms
target_leakage
task_hint_terms
task_hint
unique_prompt
randomized_prompt
review_status
detail
```

核心判断：

- `target_leakage=True`：prompt 包含 `fixed/loss`。
- `task_hint=True`：prompt 出现已知 pair/target/task 提示。
- `unique_prompt=True`：prompt 不重复、不等于 source。
- `randomized_prompt=True`：v914 明确把它标记为 randomized prompt。

### `_row_status`

row 状态优先级：

```text
block_target_leakage
block_known_task_hint
block_non_unique_prompt
block_non_randomized_prompt
clean_randomized_target_hidden_prompt
```

这让 review 先处理最危险的问题：目标词泄漏和任务提示。

### `_checks`

v917 checks 包括：

- v916 real replay 必须 pass。
- `randomized_target_hidden_holdout_real_replay_ready=True`。
- `randomized_holdout_model_quality_ready=True`。
- v914 suite 必须 pass。
- `randomized_target_hidden_holdout_suite_ready=True`。
- `candidate_case_count >= 20`。
- `randomized_case_factor >= 2.0`。
- suite summary 报告无 task hints。
- `unique_prompt_count` 等于 case 数。
- `target_hidden_case_count` 等于 case 数。
- cases 必须存在。
- review rows 必须覆盖所有 case。

这些 checks 保护输入链路和 suite 边界。

### `_summary`

真实 v917 summary：

```text
randomized_target_hidden_holdout_replay_review_ready=True
source_randomized_holdout_model_quality_ready=True
case_count=20
passed_case_count=20
pass_rate=1.0
source_random_seed=914
source_randomized_case_factor=2.0
target_leakage_case_count=0
target_hidden_case_count=20
task_hint_case_count=0
unique_prompt_count=20
randomized_prompt_count=20
clean_randomized_case_count=20
approved_for_candidate_promotion_packet=True
approved_for_promotion=False
promotion_ready=False
model_quality_claim=randomized_target_hidden_holdout_clean_signal_reviewed
next_step=build_randomized_holdout_candidate_promotion_packet
```

`approved_for_candidate_promotion_packet=True` 是 v917 的新能力。它不是 promotion，而是允许下一版把证据打包成候选 promotion 输入。

### `_decision`

decision 分支：

- 输入失败：`fix_randomized_target_hidden_holdout_replay_review_inputs`
- 目标词泄漏：`randomized_target_hidden_holdout_replay_review_target_leakage_blocks_promotion`
- task hint：`randomized_target_hidden_holdout_replay_review_task_hint_blocks_promotion`
- prompt 不唯一：`randomized_target_hidden_holdout_replay_review_non_unique_prompt_blocks_promotion`
- prompt 未标记 randomized：`randomized_target_hidden_holdout_replay_review_non_randomized_prompt_blocks_promotion`
- 干净信号：`randomized_target_hidden_holdout_replay_review_clean_signal_candidate_packet_required`
- 其他：`randomized_target_hidden_holdout_replay_review_blocks_promotion`

真实 v917 进入“干净信号，但仍需 candidate packet”分支。

### `src/minigpt/randomized_target_hidden_holdout_replay_review_artifacts.py`

这是输出层。

它写出：

- JSON：后续 candidate packet 消费。
- CSV：逐 case review。
- text：命令行摘要。
- Markdown：人工阅读。
- HTML：截图证据。

HTML 卡片展示 `Status`、`Quality ready`、`Leakage`、`Hints`、`Clean`、`Candidate packet`、`Promotion`、`Next`。

### `scripts/review_randomized_target_hidden_holdout_replay.py`

这是 CLI。

关键参数：

```powershell
--real-replay
--holdout-suite
--out-dir
--require-review-ready
--require-candidate-packet-approval
--require-promotion-approval
--force
```

真实运行使用 `--require-candidate-packet-approval`，不用 `--require-promotion-approval`。因为 v917 仍然不批准 promotion。

## 测试覆盖

新增测试：

```text
tests/test_randomized_target_hidden_holdout_replay_review.py
```

覆盖内容：

- 20 条 clean randomized signal 进入 candidate packet。
- 已知 task hint 会阻断 candidate packet。
- source real replay failure 会阻断 review。
- artifact writer 和 CLI 写出 JSON/CSV/text/Markdown/HTML。

测试同时覆盖 `resolve_exit_code`：candidate packet approval 通过，promotion approval 失败。

## 运行证据

真实命令：

```powershell
python scripts\review_randomized_target_hidden_holdout_replay.py --real-replay e\916\解释\randomized-target-hidden-holdout-real-replay --holdout-suite e\914\解释\randomized-target-hidden-holdout-suite --out-dir e\917\解释\randomized-target-hidden-holdout-replay-review --require-review-ready --require-candidate-packet-approval --force
```

结果：

```text
status=pass
decision=randomized_target_hidden_holdout_replay_review_clean_signal_candidate_packet_required
source_randomized_holdout_model_quality_ready=True
case_count=20
passed_case_count=20
pass_rate=1.0
target_leakage_case_count=0
task_hint_case_count=0
unique_prompt_count=20
randomized_prompt_count=20
clean_randomized_case_count=20
approved_for_candidate_promotion_packet=True
approved_for_promotion=False
next_step=build_randomized_holdout_candidate_promotion_packet
```

截图：

```text
e/917/图片/v917-randomized-target-hidden-holdout-replay-review.png
```

## 链路角色

v917 是从 real replay 到候选 promotion 输入之间的 review gate。

它承认 v916 的强信号，但没有跳过治理：下一步需要 candidate promotion packet，把 suite、dry-run、real replay、review 证据集中到一个可审计包里。

## 一句话总结

v917 把 randomized 20/20 replay 变成干净 review 结论，并把下一步推进到 candidate promotion packet，而不是直接 promotion。
