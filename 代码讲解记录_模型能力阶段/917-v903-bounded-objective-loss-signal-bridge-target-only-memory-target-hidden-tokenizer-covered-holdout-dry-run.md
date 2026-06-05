# v903 target-hidden tokenizer-covered holdout dry-run 代码讲解

## 本版目标和边界

v903 接在 v902 后面，用 dry-run 验证新 target-hidden holdout suite 的 scoring contract。

v902 已经把 prompt 泄漏问题修掉：5 个 prompt 都不含 `fixed/loss`，但 scoring contract 仍要求生成 continuation 同时包含 `fixed` 和 `loss`。v903 要确认这个 contract 没有因为换 prompt 而失效。

明确不做：

- 不加载模型。
- 不运行 checkpoint replay。
- 不比较 v890 或后续 checkpoint。
- 不声明模型已经通过 target-hidden holdout。

本版只证明“评分器本身可用”，为真实 replay 做前置校验。

## 前置链路

本版消费 v902：

- `e/902/解释/bounded-objective-loss-signal-bridge-target-only-memory-target-hidden-tokenizer-covered-holdout-suite`

v902 的关键输出是：

- `candidate_case_count=5`
- `tokenizer_covered_case_count=5`
- `target_hidden_case_count=5`
- `candidate_prompt_unknown_token_count=0`
- `next_step=run_target_hidden_tokenizer_covered_holdout_dry_run`

v903 正是执行这个 next step。

## 关键文件

### `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_dry_run.py`

这是本版核心 dry-run builder。

入口函数：

```python
build_target_hidden_tokenizer_covered_holdout_dry_run(...)
```

输入：

- v902 holdout suite report。
- positive continuation，默认 ` fixed loss`。
- negative continuation，默认 ` fixed only`。
- 可选 source suite path，用于报告追溯。

输出：

- `status`
- `decision`
- `failed_count`
- `issues`
- `dry_run_rows`
- `check_rows`
- `summary`
- `interpretation`

### `locate_target_hidden_tokenizer_covered_holdout_suite`

这个 locator 允许 CLI 传入 JSON 文件或输出目录。如果传目录，它会自动拼接 v902 固定 JSON 文件名：

```text
bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_suite.json
```

这保持了 v902 -> v903 的产物消费一致性。

### `_dry_run_rows`

`_dry_run_rows` 对 suite 里的每个 case 都跑两次打分：

- positive continuation：应该命中 `fixed` 和 `loss`。
- negative continuation：只命中 `fixed`，应该缺失 `loss`。

每行记录：

- `positive_case_pass`
- `positive_hit_terms`
- `positive_missed_terms`
- `negative_case_pass`
- `negative_hit_terms`
- `negative_missed_terms`

这不是模型输出，只是用固定 continuation 测试 scoring contract。

### `_score`

`_score` 的规则很直接：

```python
hit_terms = [term for term in expected_terms if term.lower() in lowered]
missed_terms = [term for term in expected_terms if term not in hit_terms]
case_pass = bool(expected_terms) and not missed_terms
```

也就是 continuation 必须同时包含全部 expected terms 才算单 case 通过。

### `_checks`

v903 的检查比 v899 多一条 target-hidden 保护：

- `holdout_suite_passed`
- `holdout_suite_ready`
- `suite_ready`
- `cases_present`
- `target_hidden_cases_present`
- `expected_terms_complete`
- `positive_rows_pass`
- `negative_rows_fail`

其中 `target_hidden_cases_present` 会校验 v902 summary 里的 `target_hidden_case_count` 是否等于 case 数。这样可以防止误把 v898 的 leaked suite 接进 v903。

### `_summary`

summary 中最重要的字段是：

- `positive_passed_case_count`
- `negative_passed_case_count`
- `negative_control_passed`
- `model_quality_claim=dry_run_only`
- `next_step=run_target_hidden_tokenizer_covered_holdout_real_replay`

这里仍然没有 promotion claim，因为本版没有真实模型参与。

### `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_dry_run_artifacts.py`

这是报告渲染层，输出：

- JSON
- CSV
- TXT
- Markdown
- HTML

CSV/Markdown/HTML 会展示每个 case 的 positive/negative 打分结果，重点是正例全过、负例全不过。

### `scripts/dry_run_bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout.py`

这是本版 CLI。

典型命令：

```powershell
python scripts\dry_run_bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout.py --holdout-suite e\902\解释\bounded-objective-loss-signal-bridge-target-only-memory-target-hidden-tokenizer-covered-holdout-suite --out-dir e\903\解释\bounded-objective-loss-signal-bridge-target-only-memory-target-hidden-tokenizer-covered-holdout-dry-run --require-dry-run-ready --force
```

`--require-dry-run-ready` 会把 dry-run 失败转成退出码 1，方便 CI 或后续自动化调用。

### `tests/test_bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_dry_run.py`

测试覆盖 5 个场景：

- 正例通过、负例不通过。
- 负例如果也包含 `fixed loss`，必须失败。
- source suite 不 ready 时失败。
- source suite 不是全 target-hidden 时失败。
- artifacts 和 CLI 输出完整。

这些测试保护的是评分契约，而不是模型能力。

## 真实运行结果

v903 真实运行读取 v902 产物，结果：

```text
status=pass
case_count=5
positive_passed_case_count=5
negative_passed_case_count=0
negative_control_passed=False
promotion_ready=False
model_quality_claim=dry_run_only
next_step=run_target_hidden_tokenizer_covered_holdout_real_replay
```

这表示 scoring contract 可以区分完整目标对和不完整目标对。

## 截图和归档

运行证据放在：

- `e/903/解释/说明.md`
- `e/903/图片/v903-bounded-objective-loss-signal-bridge-target-only-memory-target-hidden-tokenizer-covered-holdout-dry-run.png`
- `e/903/解释/bounded-objective-loss-signal-bridge-target-only-memory-target-hidden-tokenizer-covered-holdout-dry-run`

截图显示：

- `Positive passed=5`
- `Negative passed=0`
- `Negative control=False`
- `Next=run_target_hidden_tokenizer_covered_holdout_real_replay`

## 后续链路

下一版应进入真实 replay：

- 输入 v902 suite。
- 输入 v903 dry-run。
- 输入 v890 checkpoint/tokenizer。
- 运行 target-hidden prompt。
- 判断真实 continuation 是否能生成 `fixed/loss`。

只有真实 replay 通过并经过 review 后，才可以讨论更强的模型能力结论。

## 一句话总结

v903 用正反 continuation 证明 v902 target-hidden suite 的评分契约有效，把下一步风险收窄到真实 checkpoint 是否能在不看见目标词的 prompt 下生成 `fixed/loss`。
