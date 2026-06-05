# v905 target-hidden holdout replay review 代码讲解

## 本版目标和边界

v905 的目标是 review v904 的真实 replay 结果。

v904 在 target-hidden tokenizer-covered holdout suite 上得到 5/5，这是一个强信号。但工程上不能立刻把它写成 promotion，因为这套 suite 仍然很窄：只有 5 个 case，而且 prompt 都包含 `pair`、`target pair`、`answer_terms` 等任务提示。

所以 v905 的判断是：

- 承认 v904 是强模型证据。
- 确认没有目标词泄漏。
- 不批准 promotion。
- 批准进入更宽的 semantic paraphrase target-hidden holdout。

明确不做：

- 不重新运行模型。
- 不重新评分 continuation。
- 不做 promotion gate。
- 不把 5/5 解释成广义能力。

## 前置链路

本版接在：

- v902 target-hidden suite。
- v903 dry-run。
- v904 real replay。

链路含义：

```text
v902: suite prompts hide fixed/loss
v903: scoring contract works
v904: real checkpoint passes 5/5
v905: review whether this is enough for promotion
```

v905 给出的答案是：不足以 promotion，但足以进入更宽 holdout。

## 关键文件

### `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_replay_review.py`

这是本版核心 review builder。

入口函数：

```python
build_target_hidden_tokenizer_covered_holdout_replay_review(...)
```

输入：

- v904 real replay report。
- v902 holdout suite report。
- 可选 real replay path / suite path。

输出：

- `status`
- `decision`
- `check_rows`
- `review_rows`
- `summary`
- `interpretation`

### `TASK_HINT_TERMS`

本版新增一个非常重要的风险识别列表：

```python
TASK_HINT_TERMS = ("learned pair", "target pair", "answer_terms", "requires target pair", "pair")
```

它不是阻断条件，但会影响 review 结论。v902 的 prompt 没有泄漏 `fixed/loss`，但它们都在不同程度上提示“目标是一对词”。这就是为什么 v905 不批准 promotion。

### `_review_rows`

`_review_rows` 对每个 suite case 做两类检查：

- `leaked_terms`：prompt 是否直接包含 expected terms。
- `task_hint_terms`：prompt 是否包含任务提示词。

然后派生：

- `target_leakage`
- `task_hint`
- `review_status`
- `detail`

本版真实运行的结果是：

- `target_leakage=False` for all 5。
- `task_hint=True` for all 5。

这就是“强信号但仍需扩大 holdout”的依据。

### `_row_status`

每个 review row 有三种状态：

- `block_promotion_target_leakage`
- `strong_signal_but_task_hinted`
- `strong_signal_clean_prompt`

真实 v905 走的是 `strong_signal_but_task_hinted`。

### `_checks`

v905 的 check rows 只保护输入和覆盖完整性：

- v904 real replay 必须结构通过。
- v904 real replay ready 字段必须为 true。
- v902 suite 必须 pass。
- v902 suite ready 字段必须为 true。
- suite cases 必须存在。
- review rows 必须覆盖所有 cases。

这些 check 不会因为 task hint 而失败。task hint 是 review 风险，不是输入错误。

### `_summary`

summary 是本版最关键的判断层：

```text
source_holdout_model_quality_ready=True
target_leakage_case_count=0
target_hidden_case_count=5
task_hint_case_count=5
approved_for_wider_holdout=True
approved_for_promotion=False
next_step=build_semantic_paraphrase_target_hidden_holdout_suite
```

这里故意把 `approved_for_wider_holdout` 和 `approved_for_promotion` 分开。

v904 的 5/5 足以进入更宽评估，但不等于 route promotion。

### `_model_quality_claim`

真实 v905 的 claim 是：

```text
target_hidden_holdout_strong_signal_task_hinted_reviewed
```

这个名字带有两层含义：

- strong signal：v904 replay 确实强。
- task hinted：仍有提示风险。

这比简单写 `pass` 更准确。

### `_next_step`

无泄漏且强信号时，next step 是：

```text
build_semantic_paraphrase_target_hidden_holdout_suite
```

这说明后续不应该直接 promotion，而应该构造更宽的 prompt family。

### `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_replay_review_artifacts.py`

这是本版报告渲染层。

输出：

- JSON
- CSV
- TXT
- Markdown
- HTML

CSV/HTML 会展示：

- target leakage。
- leaked terms。
- task hint。
- task hint terms。
- review status。

这样截图不是只展示 5/5，而是展示为什么还不能 promotion。

### `scripts/review_bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_replay.py`

这是本版 CLI。

关键参数：

```powershell
--real-replay
--holdout-suite
--require-review-ready
--require-promotion-approval
--force
```

真实归档只使用 `--require-review-ready`，没有使用 `--require-promotion-approval`。因为 v905 的预期结论就是不批准 promotion。

### `tests/test_bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_replay_review.py`

测试覆盖：

- 强信号应进入 wider holdout，但不批准 promotion。
- target leakage 会阻断 wider holdout。
- real replay 失败会阻断 review。
- artifacts 和 CLI 可用。

这些测试保护 v905 的核心判断：不要把强信号误写成 promotion。

## 真实运行结果

v905 真实运行输出：

```text
status=pass
decision=bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_replay_review_strong_signal_wider_holdout_required
source_holdout_model_quality_ready=True
case_count=5
target_leakage_case_count=0
target_hidden_case_count=5
task_hint_case_count=5
approved_for_wider_holdout=True
approved_for_promotion=False
model_quality_claim=target_hidden_holdout_strong_signal_task_hinted_reviewed
next_step=build_semantic_paraphrase_target_hidden_holdout_suite
```

## 截图和归档

归档位置：

- `e/905/解释/说明.md`
- `e/905/图片/v905-bounded-objective-loss-signal-bridge-target-only-memory-target-hidden-tokenizer-covered-holdout-replay-review.png`
- `e/905/解释/bounded-objective-loss-signal-bridge-target-only-memory-target-hidden-tokenizer-covered-holdout-replay-review`

截图证明：

- `Model ready=True`
- `Leakage cases=0`
- `Hint cases=5`
- `Wider holdout=True`
- `Promotion=False`

## 后续链路

下一版应该构造 semantic paraphrase target-hidden holdout suite。

目标是减少提示同质性：

- 不总是使用 `pair`。
- 不总是使用 `target`。
- 增加不同表达方式。
- 继续隐藏 `fixed/loss`。
- 继续保持 tokenizer-covered。

然后再 dry-run、real replay、review。

## 一句话总结

v905 把 v904 的 target-hidden 5/5 从“看起来可以 promotion”的冲动里拉回工程审查：承认强信号，但要求更宽、更少提示的 holdout 继续验证。
