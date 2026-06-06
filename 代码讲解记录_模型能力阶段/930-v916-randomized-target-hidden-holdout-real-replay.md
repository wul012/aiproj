# v916 randomized target-hidden holdout real replay 代码讲解

## 本版目标和边界

v916 的目标是用真实 v890 checkpoint/tokenizer 跑 v914 的 20-case randomized target-hidden suite。

v914 构造 suite，v915 dry-run scoring contract，v916 才进入真实 replay。它检查模型在随机化 prompt 上是否仍能生成 `fixed/loss`。

明确不做：

- 不重新训练。
- 不修改 v914 suite。
- 不修改 v915 dry-run。
- 不批准 promotion。
- 不把 replay 结果跳过 review 直接写成最终能力结论。

本版是 real replay，不是 review gate。

## 前置链路

```text
v914 randomized target-hidden suite
  -> v915 dry-run scoring contract
  -> v916 real checkpoint replay
  -> next review gate
```

## 关键文件

### `src/minigpt/randomized_target_hidden_holdout_real_replay.py`

这是本版核心 builder。

入口函数：

```python
build_randomized_target_hidden_holdout_real_replay(...)
```

输入：

- v914 holdout suite report。
- v915 dry-run report。
- checkpoint 路径。
- tokenizer 路径。
- device。
- 可选 `generator_runner`，用于测试替换真实生成器。

输出：

- `status`
- `decision`
- `failed_count`
- `issues`
- `source_holdout_suite`
- `source_dry_run`
- `checkpoint`
- `tokenizer`
- `device`
- `check_rows`
- `replay_rows`
- `replay_errors`
- `summary`
- `interpretation`

### `_run_cases`

`_run_cases` 遍历 v914 的 20 条 randomized case。

每条 case 会：

1. 读取 `prompt_case`。
2. 调用真实 `MiniGPTGenerator` 或测试 fake runner。
3. 取出 `continuation`。
4. 用 `_score` 检查是否同时包含 `fixed` 和 `loss`。
5. 写入 `replay_rows`。

`replay_rows` 保留：

- `case_id`
- `source_case_id`
- `random_draw_index`
- `prompt`
- `continuation`
- `generated`
- `expected_terms`
- `hit_terms`
- `missed_terms`
- `case_pass`
- `seed`
- `max_new_tokens`
- `temperature`
- `top_k`

这让 v916 不只是给总分，也保留逐 case 生成证据。

### `_generate_case`

`_generate_case` 是真实模型入口。

它从 `prompt_case` 构造 `GenerationRequest`，再调用：

```python
MiniGPTGenerator(checkpoint, tokenizer, device=device).generate(request)
```

这说明 v916 不是 dry-run，也不是 fixture，而是真实 checkpoint replay。

### `_checks`

v916 checks 包括：

- v914 suite 必须 pass。
- `randomized_target_hidden_holdout_suite_ready=True`。
- `randomized_case_factor >= 2.0`。
- `unique_prompt_count` 等于实际 case 数。
- `target_hidden_case_count` 等于实际 case 数。
- v915 dry-run 必须 pass。
- `randomized_target_hidden_holdout_dry_run_ready=True`。
- `negative_control_passed=False`。
- expected terms 必须是 `fixed/loss`。
- checkpoint/tokenizer 文件存在。
- cases 必须存在。
- 所有 case 都执行。
- 没有 replay error。

这些 checks 保护真实 replay 的输入链路和执行完整性。

### `_summary`

真实 v916 summary：

```text
randomized_target_hidden_holdout_real_replay_ready=True
case_count=20
source_random_seed=914
source_randomized_case_factor=2.0
source_unique_prompt_count=20
executed_case_count=20
passed_case_count=20
failed_case_count=0
any_hit_case_count=20
zero_hit_case_count=0
pass_rate=1.0
holdout_model_quality_ready=True
randomized_holdout_model_quality_ready=True
promotion_ready=False
model_quality_claim=randomized_target_hidden_holdout_replay_only
next_step=review_randomized_target_hidden_holdout_replay_result
```

`randomized_holdout_model_quality_ready=True` 表示 v916 replay 范围内全部通过，不等于 promotion。

### `_decision`

decision 分支：

- 输入失败：`fix_randomized_target_hidden_holdout_real_replay_inputs`
- 全部通过：`randomized_target_hidden_holdout_real_replay_passed_review_required`
- 部分命中：`randomized_target_hidden_holdout_real_replay_partial_model_gap`
- 完全无命中：`randomized_target_hidden_holdout_real_replay_zero_hit_model_gap`

真实 v916 进入“通过但需要 review”分支。

### `src/minigpt/randomized_target_hidden_holdout_real_replay_artifacts.py`

这是输出层。

它写出：

- JSON：后续 review 消费。
- CSV：逐 case replay 行。
- text：命令行摘要。
- Markdown：人工阅读。
- HTML：截图证据。

HTML 卡片展示 `Status`、`Quality ready`、`Passed`、`Any hits`、`Zero hits`、`Pass rate`、`Promotion`、`Next`。

### `scripts/run_randomized_target_hidden_holdout_real_replay.py`

这是 CLI。

关键参数：

```powershell
--holdout-suite
--dry-run
--checkpoint
--tokenizer
--device
--out-dir
--require-execution-pass
--require-model-pass
--force
```

真实运行使用 `--require-execution-pass`，不强制 `--require-model-pass`，因为如果模型没有 20/20，也应该留下真实 gap 证据。本次实际结果是 20/20。

## 测试覆盖

新增测试：

```text
tests/test_randomized_target_hidden_holdout_real_replay.py
```

覆盖内容：

- fake runner 返回 ` fixed loss` 时标记 randomized model quality ready。
- fake runner 返回 ` fixed only` 时保留 partial gap，不标记 model ready。
- suite factor 太低时阻断 replay。
- artifact writer 和 CLI 能写出 JSON/CSV/text/Markdown/HTML。

测试同时覆盖 `resolve_exit_code` 的 execution pass 和 model pass 两种用法。

## 运行证据

真实命令：

```powershell
python scripts\run_randomized_target_hidden_holdout_real_replay.py --holdout-suite e\914\解释\randomized-target-hidden-holdout-suite --dry-run e\915\解释\randomized-target-hidden-holdout-dry-run --checkpoint e\890\解释\bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-training-run\run\checkpoint.pt --tokenizer e\890\解释\bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-training-run\run\tokenizer.json --device cpu --out-dir e\916\解释\randomized-target-hidden-holdout-real-replay --require-execution-pass --force
```

结果：

```text
status=pass
decision=randomized_target_hidden_holdout_real_replay_passed_review_required
randomized_holdout_model_quality_ready=True
case_count=20
executed_case_count=20
passed_case_count=20
failed_case_count=0
any_hit_case_count=20
zero_hit_case_count=0
pass_rate=1.0
promotion_ready=False
next_step=review_randomized_target_hidden_holdout_replay_result
```

截图：

```text
e/916/图片/v916-randomized-target-hidden-holdout-real-replay.png
```

## 链路角色

v916 是目前模型能力链路里最强的一层 replay 证据：

- 不是训练集 prompt。
- 不是固定 target-visible prompt。
- 不是只做 dry-run。
- 是 20 条 seeded randomized target-hidden prompt 的真实 checkpoint replay。

但它仍然不是最终 promotion。下一步需要 review gate 检查 replay 结果是否可以进入更正式的候选 promotion 判断。

## 一句话总结

v916 让 MiniGPT 的模型能力证据从固定 prompt mutation 10/10 推进到 seeded randomized target-hidden 20/20，但仍然保持 promotion 前 review。
