# v907 target-hidden semantic holdout dry-run 代码讲解

## 本版目标和边界

v907 的目标是验证 v906 semantic target-hidden holdout suite 的 scoring contract。

v906 构造了更少任务提示的 prompt，但还没有证明这些 prompt 的打分规则仍然可用。v907 用固定正例/负例 continuation 做 dry-run：

- 正例：` fixed loss`
- 负例：` fixed only`

明确不做：

- 不运行模型。
- 不读取 checkpoint。
- 不声明模型能力。
- 不批准 promotion。

本版只是评分器层面的前置验证。

## 前置链路

```text
v906 builds semantic target-hidden suite
  -> v907 dry-runs scoring contract
  -> next real replay
```

v907 消费的是：

- `e/906/解释/target-hidden-semantic-holdout-suite`

## 关键文件

### `src/minigpt/target_hidden_semantic_holdout_dry_run.py`

这是本版核心 builder。

入口函数：

```python
build_target_hidden_semantic_holdout_dry_run(...)
```

输入：

- v906 suite report。
- positive continuation。
- negative continuation。

输出：

- `status`
- `decision`
- `dry_run_rows`
- `check_rows`
- `summary`
- `interpretation`

### `_dry_run_rows`

每个 case 都会分别使用正例和负例评分：

- 正例应同时命中 `fixed/loss`。
- 负例只命中 `fixed`，缺失 `loss`。

每行记录：

- `positive_case_pass`
- `positive_hit_terms`
- `positive_missed_terms`
- `negative_case_pass`
- `negative_hit_terms`
- `negative_missed_terms`

### `_checks`

v907 的检查项包括：

- v906 suite 必须 pass。
- v906 suite ready 字段必须为 true。
- benchmark suite ready。
- cases 存在。
- `task_hint_case_count=0`。
- expected terms 必须是 `fixed/loss`。
- positive rows 全部通过。
- negative rows 全部不通过。

其中 `semantic_no_task_hints` 是 v907 相比普通 dry-run 的关键保护，确保没有误接老的 task-hinted suite。

### `_summary`

真实 v907 输出：

```text
case_count=5
positive_passed_case_count=5
negative_passed_case_count=0
negative_control_passed=False
model_quality_claim=dry_run_only
next_step=run_target_hidden_semantic_holdout_real_replay
```

这说明 scoring contract 可用，但仍不代表模型通过。

### `src/minigpt/target_hidden_semantic_holdout_dry_run_artifacts.py`

这是渲染层，输出：

- JSON
- CSV
- TXT
- Markdown
- HTML

报告重点展示正例/负例结果，以及 checks 是否全部通过。

### `scripts/dry_run_target_hidden_semantic_holdout.py`

这是 CLI。

真实归档命令：

```powershell
python scripts\dry_run_target_hidden_semantic_holdout.py --holdout-suite e\906\解释\target-hidden-semantic-holdout-suite --out-dir e\907\解释\target-hidden-semantic-holdout-dry-run --require-dry-run-ready --force
```

### `tests/test_target_hidden_semantic_holdout_dry_run.py`

测试覆盖：

- 正例全过、负例全不过。
- 负例如果也包含 `fixed loss`，必须失败。
- source suite 如果仍有 task hints，必须失败。
- artifacts 和 CLI 可用。

这些测试保护 v907 的核心职责：只允许更少提示的 semantic suite 进入真实 replay。

## 真实运行结果

```text
status=pass
decision=target_hidden_semantic_holdout_dry_run_passed
case_count=5
positive_passed_case_count=5
negative_passed_case_count=0
negative_control_passed=False
next_step=run_target_hidden_semantic_holdout_real_replay
```

## 截图和归档

归档位置：

- `e/907/解释/说明.md`
- `e/907/图片/v907-target-hidden-semantic-holdout-dry-run.png`
- `e/907/解释/target-hidden-semantic-holdout-dry-run`

截图证明：

- `Positive passed=5`
- `Negative passed=0`
- `Negative control=False`

## 后续链路

下一版应运行真实 v890 checkpoint：

- 输入 v906 suite。
- 输入 v907 dry-run。
- 输入 v890 checkpoint/tokenizer。
- 判断模型在更少提示的 semantic prompt 下是否仍能输出 `fixed/loss`。

## 一句话总结

v907 证明更少提示的 semantic target-hidden suite 评分契约可用，下一步可以把风险聚焦到真实模型是否还能通过。
