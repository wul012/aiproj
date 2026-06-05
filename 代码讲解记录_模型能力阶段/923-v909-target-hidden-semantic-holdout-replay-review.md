# v909 target-hidden semantic holdout replay review 代码讲解

## 本版目标和边界

v909 的目标是 review v908 的真实 replay 结果。

v908 已经确认：v890 checkpoint 在 v906 semantic target-hidden holdout 上 5/5 命中 `fixed/loss`。但 5/5 replay 仍不能直接 promotion，因为还需要检查：

- prompt 是否真的没有 `fixed/loss` 目标泄漏。
- prompt 是否没有已知 pair/target task hint。
- 这个信号是否应该进入更宽的 prompt mutation holdout。

明确不做：

- 不重新训练。
- 不重新生成 replay。
- 不批准 promotion。
- 不把 clean semantic replay 解释成生产级模型质量。

本版是一个 review gate，不是新训练链。

## 前置链路

```text
v906 semantic target-hidden suite
  -> v907 dry-run scoring contract
  -> v908 real checkpoint replay
  -> v909 review clean signal and route to prompt mutation holdout
```

## 关键文件

### `src/minigpt/target_hidden_semantic_holdout_replay_review.py`

这是本版核心 builder。

入口函数：

```python
build_target_hidden_semantic_holdout_replay_review(...)
```

输入：

- v908 real replay report。
- v906 holdout suite report。

输出：

- `status`
- `decision`
- `check_rows`
- `review_rows`
- `summary`
- `interpretation`

### `locate_target_hidden_semantic_holdout_real_replay`

允许 CLI 传入目录或 JSON 文件。

目录输入会自动定位：

```text
target_hidden_semantic_holdout_real_replay.json
```

这让 review 可以直接消费：

```text
e/908/解释/target-hidden-semantic-holdout-real-replay
```

### `locate_target_hidden_semantic_holdout_suite`

同样支持目录或 JSON 文件。

目录输入会自动定位：

```text
target_hidden_semantic_holdout_suite.json
```

这保证 v909 review 的 prompt 检查来自原始 v906 suite，而不是从 replay 产物里推断 prompt。

### `_review_rows`

`_review_rows` 对每个 suite case 做静态复核。

它检查两类风险：

1. target leakage：
   prompt 是否直接包含 expected terms，例如 `fixed` 或 `loss`。
2. known task hint：
   prompt 是否包含已知 pair/target 类提示，例如 `target pair`、`learned pair`、`answer_terms`。

每行输出：

- `case_id`
- `source_case_id`
- `expected_terms`
- `leaked_terms`
- `target_leakage`
- `task_hint_terms`
- `task_hint`
- `review_status`
- `detail`

如果没有泄漏和 hint，行状态为：

```text
clean_semantic_target_hidden_prompt
```

### `_checks`

v909 的 checks 分成输入链路和 suite 静态质量两类。

输入链路：

- v908 replay 必须 `status=pass`。
- `target_hidden_semantic_holdout_real_replay_ready=True`。
- `semantic_holdout_model_quality_ready=True`。

suite 静态质量：

- v906 suite 必须 `status=pass`。
- `target_hidden_semantic_holdout_suite_ready=True`。
- `task_hint_case_count=0`。
- `target_hidden_case_count` 必须等于实际 case 数。
- cases 必须存在。
- review rows 必须覆盖每个 case。

这些 checks 防止 v909 只看 replay 成功，而忽略 prompt 本身是否干净。

### `_summary`

summary 是 v909 给后续版本的决策接口：

```text
target_hidden_semantic_holdout_replay_review_ready
source_holdout_model_quality_ready
source_semantic_holdout_model_quality_ready
case_count
passed_case_count
pass_rate
target_leakage_case_count
target_hidden_case_count
task_hint_case_count
clean_prompt_case_count
approved_for_prompt_mutation_holdout
approved_for_promotion
promotion_ready
model_quality_claim
next_step
failed_check_count
```

真实 v909 输出中：

- `target_leakage_case_count=0`
- `task_hint_case_count=0`
- `clean_prompt_case_count=5`
- `approved_for_prompt_mutation_holdout=True`
- `approved_for_promotion=False`

这说明 v908 的信号足够进入下一层 holdout，但还不足以 promotion。

### `_decision`

v909 的 decision 分支：

- 输入失败：`fix_target_hidden_semantic_holdout_replay_review_inputs`
- 目标泄漏：`target_hidden_semantic_holdout_replay_review_target_leakage_blocks_promotion`
- task hint：`target_hidden_semantic_holdout_replay_review_task_hint_blocks_promotion`
- clean signal：`target_hidden_semantic_holdout_replay_review_clean_signal_prompt_mutation_holdout_required`
- 其他：`target_hidden_semantic_holdout_replay_review_blocks_promotion`

本次真实运行进入 clean signal 分支。

### `src/minigpt/target_hidden_semantic_holdout_replay_review_artifacts.py`

这是渲染层。

输出：

- JSON
- CSV
- TXT
- Markdown
- HTML

HTML 页突出展示：

- semantic ready。
- leakage cases。
- hint cases。
- clean cases。
- prompt mutation approval。
- promotion approval。
- next step。

这张 HTML 是 v909 的人眼审查入口。

### `scripts/review_target_hidden_semantic_holdout_replay.py`

这是 CLI。

关键参数：

```powershell
--real-replay
--holdout-suite
--out-dir
--require-review-ready
--require-prompt-mutation-approval
--require-promotion-approval
--force
```

真实归档命令：

```powershell
python scripts\review_target_hidden_semantic_holdout_replay.py --real-replay e\908\解释\target-hidden-semantic-holdout-real-replay --holdout-suite e\906\解释\target-hidden-semantic-holdout-suite --out-dir e\909\解释\target-hidden-semantic-holdout-replay-review --require-review-ready --require-prompt-mutation-approval --force
```

本版使用 `--require-prompt-mutation-approval`，但没有使用 `--require-promotion-approval`。这与 v909 边界一致：允许进入下一层 holdout，不允许 promotion。

## 真实运行结果

```text
status=pass
decision=target_hidden_semantic_holdout_replay_review_clean_signal_prompt_mutation_holdout_required
failed_count=0
target_hidden_semantic_holdout_replay_review_ready=True
source_holdout_model_quality_ready=True
source_semantic_holdout_model_quality_ready=True
case_count=5
passed_case_count=5
pass_rate=1.0
target_leakage_case_count=0
task_hint_case_count=0
clean_prompt_case_count=5
approved_for_prompt_mutation_holdout=True
approved_for_promotion=False
promotion_ready=False
model_quality_claim=semantic_target_hidden_holdout_clean_signal_reviewed
next_step=build_prompt_mutation_target_hidden_holdout_suite
```

## 测试覆盖

`tests/test_target_hidden_semantic_holdout_replay_review.py` 覆盖：

- clean semantic signal 允许进入 prompt mutation holdout。
- known task hint 会阻止 prompt mutation approval。
- replay 输入失败会阻止 review。
- artifacts 和 CLI 可用。
- `require_prompt_mutation_approval` 与 `require_promotion_approval` 的退出码不同。

这保护了 v909 的核心边界：通过可以继续扩展 holdout，但不能直接 promotion。

## 截图和归档

归档位置：

- `e/909/解释/说明.md`
- `e/909/图片/v909-target-hidden-semantic-holdout-replay-review.png`
- `e/909/解释/target-hidden-semantic-holdout-replay-review`

截图证明：

- `Status=pass`
- `Semantic ready=True`
- `Leakage cases=0`
- `Hint cases=0`
- `Clean cases=5`
- `Prompt mutation=True`
- `Promotion=False`

## 后续链路

下一版应构造更宽的 prompt mutation holdout：

```text
build_prompt_mutation_target_hidden_holdout_suite
```

重点不是继续重复 review，而是把 prompt 扰动成更多形式，测试模型是否只记住了当前 5 个语义模板。

## 一句话总结

v909 把 v908 的 clean semantic 5/5 replay 收口成可审计 review 结论：可以进入更宽 prompt-mutation holdout，但仍不能 promotion。
