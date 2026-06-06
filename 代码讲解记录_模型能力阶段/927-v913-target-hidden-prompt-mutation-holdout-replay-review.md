# v913 target-hidden prompt-mutation holdout replay review 代码讲解

## 本版目标和边界

v913 的目标是复核 v912 的真实 replay 结果。

v910 构造了 10-case prompt-mutation target-hidden suite，v911 证明 scoring contract 可用，v912 用真实 v890 checkpoint/tokenizer 跑出了 `10/10`。v913 在这条链路后面加 review gate，检查这些 prompt mutation case 是否仍然满足：

- 没有把 `fixed/loss` 写进 prompt。
- 没有出现已知 pair/target/task hint。
- 每条 case 都确实是从 source prompt mutation 得来。
- real replay 和 suite summary 一致。

明确不做：

- 不重新训练。
- 不重放模型生成。
- 不修改 v910 suite。
- 不批准 promotion。
- 不把 `10/10` 写成生产模型质量。

本版只决定是否可以进入下一层 randomized target-hidden holdout。

## 前置链路

```text
v910 prompt-mutation target-hidden suite
  -> v911 dry-run scoring contract
  -> v912 real checkpoint replay
  -> v913 replay review
  -> next randomized target-hidden holdout
```

v913 的输入是 v912 replay report 和 v910 suite report。它不读取训练数据，也不读取 checkpoint，因此是一个只读复核层。

## 关键文件

### `src/minigpt/target_hidden_prompt_mutation_holdout_replay_review.py`

这是本版核心 builder。

入口函数：

```python
build_target_hidden_prompt_mutation_holdout_replay_review(...)
```

输入：

- `real_replay_report`：来自 v912。
- `holdout_suite_report`：来自 v910。
- 可选 `real_replay_path` 和 `holdout_suite_path`，用于把源证据路径写入输出。

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

`_review_rows` 遍历 v910 的 benchmark cases，并把每条 case 与 coverage row 对齐。

每行会生成：

```text
case_id
source_case_id
expected_terms
leaked_terms
target_leakage
task_hint_terms
task_hint
prompt_mutated
review_status
detail
```

核心判断：

- `target_leakage=True` 表示 prompt 直接包含 expected terms，例如 `fixed` 或 `loss`。
- `task_hint=True` 表示 prompt 虽然隐藏目标词，但仍出现 pair/target 等已知任务提示。
- `prompt_mutated=True` 来自 v910 coverage row，用于确认它不是原始语义 prompt 的重复。

`review_status` 的优先级是：

```text
block_target_leakage
block_known_task_hint
block_unmutated_prompt
clean_prompt_mutation_target_hidden_prompt
```

这个顺序让最危险的问题先被解释，便于后续修复。

### `_checks`

`_checks` 负责结构性复核。

它要求：

- v912 real replay `status=pass`。
- `target_hidden_prompt_mutation_holdout_real_replay_ready=True`。
- `prompt_mutation_holdout_model_quality_ready=True`。
- v910 suite `status=pass`。
- `target_hidden_prompt_mutation_holdout_suite_ready=True`。
- `mutation_factor >= 2.0`。
- suite summary 报告无 task hints。
- suite summary 报告所有 case 都 mutated。
- suite summary 报告所有 case 都 target-hidden。
- case 和 review row 都存在且数量一致。

这些 checks 保护的是输入契约，不直接判断是否 promotion。

### `_summary`

真实 v913 summary：

```text
target_hidden_prompt_mutation_holdout_replay_review_ready=True
source_holdout_model_quality_ready=True
source_prompt_mutation_holdout_model_quality_ready=True
case_count=10
passed_case_count=10
pass_rate=1.0
source_mutation_factor=2.0
target_leakage_case_count=0
target_hidden_case_count=10
task_hint_case_count=0
prompt_mutated_case_count=10
clean_prompt_mutation_case_count=10
approved_for_randomized_prompt_holdout=True
approved_for_promotion=False
promotion_ready=False
model_quality_claim=prompt_mutation_target_hidden_holdout_clean_signal_reviewed
next_step=build_randomized_target_hidden_holdout_suite
```

`clean_prompt_mutation_case_count` 不是靠简单减法推导，而是按 `review_status == clean_prompt_mutation_target_hidden_prompt` 直接统计。这样即使未来某条 case 同时出现多个问题，汇总也不会被算歪。

### `_decision`

decision 分支：

- 输入失败：`fix_target_hidden_prompt_mutation_holdout_replay_review_inputs`
- prompt 泄漏：`target_hidden_prompt_mutation_holdout_replay_review_target_leakage_blocks_promotion`
- task hint：`target_hidden_prompt_mutation_holdout_replay_review_task_hint_blocks_promotion`
- 未 mutation：`target_hidden_prompt_mutation_holdout_replay_review_unmutated_prompt_blocks_promotion`
- 干净且 case 数达到门槛：`target_hidden_prompt_mutation_holdout_replay_review_clean_signal_randomized_holdout_required`
- 其余：`target_hidden_prompt_mutation_holdout_replay_review_blocks_promotion`

这里有一个刻意保守的边界：只有 10 条干净 prompt mutation case 才批准进入 randomized holdout。测试里保留了小样本分支，避免两三条样例误触发下一阶段。

### `src/minigpt/target_hidden_prompt_mutation_holdout_replay_review_artifacts.py`

这是输出层。

它把同一个 report 写成：

- JSON：后续模块消费。
- CSV：逐 case 查看。
- text：命令行摘要。
- Markdown：人工阅读。
- HTML：截图证据。

HTML 的卡片显示 `Status`、`Mutation ready`、`Leakage cases`、`Hint cases`、`Mutated cases`、`Clean cases`、`Randomized holdout`、`Promotion`。这些字段刚好对应本版最重要的判断：可以进入 randomized holdout，但不能 promotion。

### `scripts/review_target_hidden_prompt_mutation_holdout_replay.py`

这是 CLI 入口。

关键参数：

```powershell
--real-replay
--holdout-suite
--out-dir
--require-review-ready
--require-randomized-holdout-approval
--require-promotion-approval
--force
```

`--require-randomized-holdout-approval` 用于确保 v913 不是只生成报告，而是真的达到“可进入下一阶段”的条件。

`--require-promotion-approval` 目前应返回失败，因为本版仍然明确不批准 promotion。

## 测试覆盖

新增测试文件：

```text
tests/test_target_hidden_prompt_mutation_holdout_replay_review.py
```

覆盖点：

- 小样本 clean signal 只能 review ready，不能批准 randomized holdout。
- 10-case clean signal 可以批准 randomized holdout。
- unmutated prompt 会阻断 randomized holdout。
- source replay failure 会让 review 失败。
- outputs 和 CLI 都能写出 JSON/CSV/text/Markdown/HTML。

这些测试不是只测函数返回值，而是覆盖 builder、artifact writer、locator、CLI 和 exit code。

## 运行证据

真实命令：

```powershell
python scripts\review_target_hidden_prompt_mutation_holdout_replay.py --real-replay e\912\解释\target-hidden-prompt-mutation-holdout-real-replay --holdout-suite e\910\解释\target-hidden-prompt-mutation-holdout-suite --out-dir e\913\解释\target-hidden-prompt-mutation-holdout-replay-review --require-review-ready --require-randomized-holdout-approval --force
```

结果：

```text
status=pass
decision=target_hidden_prompt_mutation_holdout_replay_review_clean_signal_randomized_holdout_required
failed_count=0
case_count=10
passed_case_count=10
pass_rate=1.0
target_leakage_case_count=0
task_hint_case_count=0
prompt_mutated_case_count=10
clean_prompt_mutation_case_count=10
approved_for_randomized_prompt_holdout=True
approved_for_promotion=False
next_step=build_randomized_target_hidden_holdout_suite
```

截图：

```text
e/913/图片/v913-target-hidden-prompt-mutation-holdout-replay-review.png
```

## 链路角色

v913 是一次能力链路的“解释刹车”：

- v912 说明模型在 10 条 prompt mutation target-hidden case 上能输出目标。
- v913 说明这 10 条 case 没有明显泄漏、任务提示或未 mutation 问题。
- v913 仍然不把结果转成 promotion，而是要求继续做 randomized target-hidden holdout。

这让项目从“固定 suite 复现成功”走向“随机化抗过拟合验证”。

## 一句话总结

v913 把 prompt-mutation 10/10 replay 收束成一个干净但保守的 review gate：可以继续扩到 randomized holdout，仍不能 promotion。
