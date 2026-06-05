# v912 target-hidden prompt-mutation holdout real replay 代码讲解

## 本版目标和边界

v912 的目标是运行真实 checkpoint replay。

v910 构造了 10-case prompt-mutation target-hidden suite，v911 证明它的 scoring contract 可用。v912 将这条链路接到真实 v890 checkpoint/tokenizer，检查模型是否能在更宽 prompt mutation 面上继续输出 `fixed/loss`。

明确不做：

- 不重新训练。
- 不改写 v910 suite。
- 不直接批准 promotion。
- 不把 10/10 replay 解释为生产模型质量。

本版是 replay 证据，不是最终 promotion 决策。

## 前置链路

```text
v910 prompt-mutation target-hidden suite
  -> v911 dry-run scoring contract
  -> v912 real checkpoint replay
  -> next review gate
```

## 关键文件

### `src/minigpt/target_hidden_prompt_mutation_holdout_real_replay.py`

这是本版核心 builder。

入口函数：

```python
build_target_hidden_prompt_mutation_holdout_real_replay(...)
```

输入：

- v910 suite report。
- v911 dry-run report。
- checkpoint 路径。
- tokenizer 路径。
- device。
- 可选 `generator_runner`，用于测试替换真实生成器。

输出：

- `status`
- `decision`
- `check_rows`
- `replay_rows`
- `replay_errors`
- `summary`
- `interpretation`

### `_run_cases`

`_run_cases` 遍历 v910 的 10 个 prompt mutation case。

每个 case 会：

1. 读取 `prompt_case`。
2. 调用真实 `MiniGPTGenerator` 或测试 fake runner。
3. 取出 `continuation`。
4. 检查是否同时包含 `fixed` 和 `loss`。
5. 写入 `replay_rows`。

错误不会静默消失，会写入 `replay_errors` 并由 checks 阻断。

### `_checks`

v912 checks 包括：

- v910 suite 必须 pass。
- `target_hidden_prompt_mutation_holdout_suite_ready=True`。
- `mutation_factor >= 2.0`。
- `prompt_mutated_case_count` 必须等于 case 数。
- v911 dry-run 必须 pass。
- `target_hidden_prompt_mutation_holdout_dry_run_ready=True`。
- expected terms 必须是 `fixed/loss`。
- checkpoint/tokenizer 文件存在。
- 所有 case 都被执行。
- 没有 replay error。

这些 checks 保证 v912 的 replay 证据确实来自 v910/v911 链路，而不是绕过 suite/dry-run。

### `_summary`

真实 v912 summary：

```text
target_hidden_prompt_mutation_holdout_real_replay_ready=True
case_count=10
source_mutation_factor=2.0
executed_case_count=10
passed_case_count=10
failed_case_count=0
any_hit_case_count=10
zero_hit_case_count=0
pass_rate=1.0
prompt_mutation_holdout_model_quality_ready=True
promotion_ready=False
model_quality_claim=prompt_mutation_target_hidden_holdout_replay_only
next_step=review_target_hidden_prompt_mutation_holdout_replay_result
```

`prompt_mutation_holdout_model_quality_ready=True` 只表示本 suite 范围内全通过，不是 promotion。

### `_decision`

decision 分支：

- 输入失败：`fix_target_hidden_prompt_mutation_holdout_real_replay_inputs`
- 全部通过：`target_hidden_prompt_mutation_holdout_real_replay_passed_review_required`
- 部分命中：`target_hidden_prompt_mutation_holdout_real_replay_partial_model_gap`
- 完全无命中：`target_hidden_prompt_mutation_holdout_real_replay_zero_hit_model_gap`

真实 v912 进入“通过但需要 review”分支。

### `src/minigpt/target_hidden_prompt_mutation_holdout_real_replay_artifacts.py`

这是渲染层。

输出：

- JSON
- CSV
- TXT
- Markdown
- HTML

HTML 展示：

- quality ready。
- passed case 数。
- any-hit/zero-hit。
- pass rate。
- promotion 状态。
- next step。

### `scripts/run_target_hidden_prompt_mutation_holdout_real_replay.py`

这是 CLI。

真实归档命令：

```powershell
python scripts\run_target_hidden_prompt_mutation_holdout_real_replay.py --holdout-suite e\910\解释\target-hidden-prompt-mutation-holdout-suite --dry-run e\911\解释\target-hidden-prompt-mutation-holdout-dry-run --checkpoint e\890\解释\bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-training-run\run\checkpoint.pt --tokenizer e\890\解释\bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-training-run\run\tokenizer.json --device cpu --out-dir e\912\解释\target-hidden-prompt-mutation-holdout-real-replay --require-execution-pass --force
```

本次只要求 `--require-execution-pass`，不使用 `--require-model-pass` 作为进程门槛，因为下一版 review 才负责解释模型信号。

## 真实运行结果

```text
status=pass
decision=target_hidden_prompt_mutation_holdout_real_replay_passed_review_required
case_count=10
passed_case_count=10
failed_case_count=0
any_hit_case_count=10
zero_hit_case_count=0
pass_rate=1.0
prompt_mutation_holdout_model_quality_ready=True
promotion_ready=False
next_step=review_target_hidden_prompt_mutation_holdout_replay_result
```

## 测试覆盖

`tests/test_target_hidden_prompt_mutation_holdout_real_replay.py` 覆盖：

- 全部 case 通过时 model-quality-ready 为 true。
- 部分命中时 execution pass 但 model pass 失败。
- mutation factor 不足时阻断输入。
- artifacts 和 CLI 可用。

这些测试保护 v912 的关键边界：执行成功、模型通过、promotion 审批不是同一件事。

## 截图和归档

归档位置：

- `e/912/解释/说明.md`
- `e/912/图片/v912-target-hidden-prompt-mutation-holdout-real-replay.png`
- `e/912/解释/target-hidden-prompt-mutation-holdout-real-replay`

截图证明：

- `Quality ready=True`
- `Passed=10/10`
- `Pass rate=1.0`
- `Promotion=False`

## 后续链路

下一版应 review v912：

```text
review_target_hidden_prompt_mutation_holdout_replay_result
```

review 需要判断 prompt mutation replay 是否足以进入更宽的 randomized prompt holdout 或仍需再扩展。

## 一句话总结

v912 用真实 v890 checkpoint 通过了 10-case prompt-mutation target-hidden replay，把模型信号从 5 个语义模板推进到更宽的 mutation prompt 面。
