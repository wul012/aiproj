# v911 target-hidden prompt-mutation holdout dry-run 代码讲解

## 本版目标和边界

v911 的目标是 dry-run v910 prompt-mutation target-hidden holdout suite。

v910 构造了 10 个 prompt mutation case，但还没有证明这些 case 的 scoring contract 仍然可用。v911 用固定正例/负例 continuation 做评分验证：

- 正例：` fixed loss`
- 负例：` fixed only`

明确不做：

- 不运行模型。
- 不读取 checkpoint。
- 不声明模型能力。
- 不批准 promotion。

本版只是评分器和 suite contract 的前置验证。

## 前置链路

```text
v910 prompt-mutation target-hidden suite
  -> v911 dry-run scoring contract
  -> next real checkpoint replay
```

## 关键文件

### `src/minigpt/target_hidden_prompt_mutation_holdout_dry_run.py`

这是本版核心 builder。

入口函数：

```python
build_target_hidden_prompt_mutation_holdout_dry_run(...)
```

输入：

- v910 suite report。
- positive continuation。
- negative continuation。

输出：

- `status`
- `decision`
- `check_rows`
- `dry_run_rows`
- `summary`
- `interpretation`

### `_dry_run_rows`

每个 case 都会分别使用正例和负例评分：

- 正例 ` fixed loss` 应同时命中 `fixed/loss`。
- 负例 ` fixed only` 只命中 `fixed`，必须失败。

每行记录：

- `positive_case_pass`
- `positive_hit_terms`
- `positive_missed_terms`
- `negative_case_pass`
- `negative_hit_terms`
- `negative_missed_terms`

### `_checks`

v911 checks 包括：

- v910 suite 必须 pass。
- `target_hidden_prompt_mutation_holdout_suite_ready=True`。
- benchmark suite ready。
- cases 存在。
- `candidate_case_count` 必须等于实际 case 数。
- `mutation_factor >= 2.0`。
- `prompt_mutated_case_count` 必须等于实际 case 数。
- `task_hint_case_count=0`。
- expected terms 必须是 `fixed/loss`。
- 正例必须全部通过。
- 负例必须全部不通过。

这些 checks 防止 v911 只验证字符串，而忽略 v910 作为 prompt-mutation suite 的关键属性。

### `_summary`

真实 v911 summary：

```text
target_hidden_prompt_mutation_holdout_dry_run_ready=True
case_count=10
source_mutation_factor=2.0
source_prompt_mutated_case_count=10
positive_passed_case_count=10
negative_passed_case_count=0
negative_control_passed=False
promotion_ready=False
model_quality_claim=dry_run_only
next_step=run_target_hidden_prompt_mutation_holdout_real_replay
```

这说明 10-case mutation suite 的评分器可以进入真实 replay。

### `src/minigpt/target_hidden_prompt_mutation_holdout_dry_run_artifacts.py`

这是渲染层。

输出：

- JSON
- CSV
- TXT
- Markdown
- HTML

HTML 展示：

- case 数。
- mutation factor。
- mutated case 数。
- positive passed。
- negative passed。
- negative control。
- next step。

### `scripts/dry_run_target_hidden_prompt_mutation_holdout.py`

这是 CLI。

真实归档命令：

```powershell
python scripts\dry_run_target_hidden_prompt_mutation_holdout.py --holdout-suite e\910\解释\target-hidden-prompt-mutation-holdout-suite --out-dir e\911\解释\target-hidden-prompt-mutation-holdout-dry-run --require-dry-run-ready --force
```

## 真实运行结果

```text
status=pass
decision=target_hidden_prompt_mutation_holdout_dry_run_passed
case_count=10
source_mutation_factor=2.0
source_prompt_mutated_case_count=10
positive_passed_case_count=10
negative_passed_case_count=0
negative_control_passed=False
next_step=run_target_hidden_prompt_mutation_holdout_real_replay
```

## 测试覆盖

`tests/test_target_hidden_prompt_mutation_holdout_dry_run.py` 覆盖：

- 正例全过、负例全不过。
- 如果负例也包含 `fixed loss`，dry-run 必须失败。
- source suite 如果没有完整标记 mutated case，必须失败。
- artifacts 和 CLI 可用。

这些测试保护了 v911 的边界：只有 scoring contract 和 mutation suite 结构都正确时，才允许进入真实 replay。

## 截图和归档

归档位置：

- `e/911/解释/说明.md`
- `e/911/图片/v911-target-hidden-prompt-mutation-holdout-dry-run.png`
- `e/911/解释/target-hidden-prompt-mutation-holdout-dry-run`

截图证明：

- `Cases=10`
- `Mutation factor=2.0`
- `Mutated=10`
- `Positive passed=10`
- `Negative passed=0`
- `Negative control=False`

## 后续链路

下一版应运行真实 checkpoint：

```text
run_target_hidden_prompt_mutation_holdout_real_replay
```

## 一句话总结

v911 证明 10-case prompt-mutation target-hidden suite 的评分契约可用，为真实模型 replay 清除了评分器层面的疑问。
