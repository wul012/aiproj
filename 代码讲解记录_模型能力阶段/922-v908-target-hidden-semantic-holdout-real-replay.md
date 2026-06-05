# v908 target-hidden semantic holdout real replay 代码讲解

## 本版目标和边界

v908 的目标是把 v906/v907 形成的 semantic target-hidden holdout 链路接到真实模型执行上。

前两版已经分别解决：

- v906：构造不含 `fixed/loss`、也不含明显 pair/target task hint 的 semantic prompt。
- v907：用正例/负例 continuation 验证评分器可用。

v908 继续使用 v890 的真实 checkpoint/tokenizer，在 CPU 上执行每个 prompt，并检查 continuation 是否同时包含 `fixed` 和 `loss`。

明确不做：

- 不训练新模型。
- 不改写 v906 suite。
- 不把 5/5 replay 直接解释成生产质量。
- 不批准 promotion。

本版解决的是“更少提示的 target-hidden semantic suite 是否仍能被当前 checkpoint 通过”。

## 前置链路

```text
v906 semantic target-hidden suite
  -> v907 dry-runs scoring contract
  -> v908 real checkpoint replay
  -> next review before wider holdout or promotion
```

v908 消费的真实输入是：

- `e/906/解释/target-hidden-semantic-holdout-suite`
- `e/907/解释/target-hidden-semantic-holdout-dry-run`
- `e/890/解释/.../run/checkpoint.pt`
- `e/890/解释/.../run/tokenizer.json`

## 关键文件

### `src/minigpt/target_hidden_semantic_holdout_real_replay.py`

这是本版核心 builder。

入口函数：

```python
build_target_hidden_semantic_holdout_real_replay(...)
```

输入：

- v906 suite report。
- v907 dry-run report。
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

### `locate_target_hidden_semantic_holdout_suite`

允许 CLI 输入目录或 JSON 文件。

如果输入目录，会自动定位：

```text
target_hidden_semantic_holdout_suite.json
```

这让真实运行命令可以直接指向 `e/906/解释/target-hidden-semantic-holdout-suite`。

### `locate_target_hidden_semantic_holdout_dry_run`

同样支持目录或 JSON 文件，自动定位：

```text
target_hidden_semantic_holdout_dry_run.json
```

它保证 v908 必须接在 v907 dry-run 之后，而不是绕过评分器验证直接跑模型。

### `_run_cases`

`_run_cases` 是真实 replay 的执行循环。

每个 case 会：

1. 读取 `prompt_case`。
2. 调用 `MiniGPTGenerator` 或测试注入的 fake runner。
3. 取出 `continuation`。
4. 用 `_score` 判断是否包含全部 expected terms。
5. 写入 `replay_rows`。

每行包含：

- `case_id`
- `source_case_id`
- `prompt`
- `continuation`
- `generated`
- `expected_terms`
- `hit_terms`
- `missed_terms`
- `case_pass`
- 采样参数

如果生成过程抛错，错误会进入 `replay_errors`，不会静默吞掉。

### `_generate_case`

这是接真实模型的边界。

它从 suite case 里构造 `GenerationRequest`：

- `prompt`
- `max_new_tokens`
- `temperature`
- `top_k`
- `seed`

然后调用：

```python
MiniGPTGenerator(checkpoint, tokenizer, device=device).generate(request)
```

所以 v908 不是 mock 结果，而是真实加载 checkpoint/tokenizer 执行。

### `_checks`

v908 的 checks 分为三类。

输入链路检查：

- v906 suite 必须 pass。
- `target_hidden_semantic_holdout_suite_ready=True`。
- `target_hidden_case_count` 必须等于 case 数。
- `task_hint_case_count=0`。
- v907 dry-run 必须 pass。
- `target_hidden_semantic_holdout_dry_run_ready=True`。

契约检查：

- expected terms 必须是 `fixed/loss`。
- cases 必须存在。

执行检查：

- checkpoint 文件存在。
- tokenizer 文件存在。
- 每个 case 都被执行。
- 没有 replay error。

这些 checks 的关键作用是防止 v908 看起来像模型结果，实际却绕过了 v906/v907 的证据链。

### `_summary`

summary 会把执行结果压成后续 review 能直接消费的字段：

```text
target_hidden_semantic_holdout_real_replay_ready
case_count
executed_case_count
passed_case_count
failed_case_count
any_hit_case_count
zero_hit_case_count
pass_rate
holdout_model_quality_ready
semantic_holdout_model_quality_ready
promotion_ready
model_quality_claim
next_step
failed_check_count
```

其中：

- `holdout_model_quality_ready=True` 表示本 suite 全部通过。
- `semantic_holdout_model_quality_ready=True` 说明通过范围限定在 semantic target-hidden holdout。
- `promotion_ready=False` 继续阻止直接 promotion。

### `_decision`

decision 分三层：

- 输入或执行失败：`fix_target_hidden_semantic_holdout_real_replay_inputs`
- 全部通过：`target_hidden_semantic_holdout_real_replay_passed_review_required`
- 部分命中：`target_hidden_semantic_holdout_real_replay_partial_model_gap`
- 完全无命中：`target_hidden_semantic_holdout_real_replay_zero_hit_model_gap`

这让 replay 失败时不只是给一个 fail，而是保留诊断方向。

### `src/minigpt/target_hidden_semantic_holdout_real_replay_artifacts.py`

这是渲染层。

输出：

- JSON
- CSV
- TXT
- Markdown
- HTML

HTML 页展示：

- status。
- quality ready。
- semantic ready。
- passed case 数。
- pass rate。
- promotion 状态。
- replay rows。
- checks。

CSV 复用已有 bounded real replay 的 CSV writer，避免为相同形状的 replay rows 再造一套重复逻辑。

### `scripts/run_target_hidden_semantic_holdout_real_replay.py`

这是 CLI 入口。

核心参数：

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

真实归档命令：

```powershell
python scripts\run_target_hidden_semantic_holdout_real_replay.py --holdout-suite e\906\解释\target-hidden-semantic-holdout-suite --dry-run e\907\解释\target-hidden-semantic-holdout-dry-run --checkpoint e\890\解释\bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-training-run\run\checkpoint.pt --tokenizer e\890\解释\bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-training-run\run\tokenizer.json --device cpu --out-dir e\908\解释\target-hidden-semantic-holdout-real-replay --require-execution-pass --force
```

本次真实运行只要求 `--require-execution-pass`，没有使用 `--require-model-pass` 作为进程退出门槛。原因是能力判断仍要进入 review，而不是让 CLI 直接替 review 下结论。

## 真实运行结果

```text
status=pass
decision=target_hidden_semantic_holdout_real_replay_passed_review_required
failed_count=0
case_count=5
executed_case_count=5
passed_case_count=5
failed_case_count=0
any_hit_case_count=5
zero_hit_case_count=0
pass_rate=1.0
holdout_model_quality_ready=True
semantic_holdout_model_quality_ready=True
promotion_ready=False
next_step=review_target_hidden_semantic_holdout_replay_result
```

真实 continuation 摘要：

```text
semantic-hidden-memory_answer      -> " fixed loss..."
semantic-hidden-stored_result      -> " fixed loss..."
semantic-hidden-learned_route      -> " fixed loss..."
semantic-hidden-final_words        -> " fixed loss..."
semantic-hidden-memory_self_check  -> " fixed loss..."
```

5 个 case 都命中 `fixed/loss`。

## 测试覆盖

`tests/test_target_hidden_semantic_holdout_real_replay.py` 覆盖：

- 缺 checkpoint 时，即使 fake runner 可用，也必须失败。
- fake runner 输出 ` fixed loss` 时，全 case pass，model quality ready。
- fake runner 输出 ` fixed only` 时，执行 pass 但 model pass 失败。
- source suite 如果 `task_hint_case_count` 不为 0，必须失败。
- artifacts 输出 JSON/CSV/TXT/Markdown/HTML。
- CLI 支持目录输入并能写出 sidecar 产物。

这些测试保护的是 replay 链路本身，而不是只验证字符串输出。

## 截图和归档

归档位置：

- `e/908/解释/说明.md`
- `e/908/图片/v908-target-hidden-semantic-holdout-real-replay.png`
- `e/908/解释/target-hidden-semantic-holdout-real-replay`

截图证明：

- `Status=pass`
- `Quality ready=True`
- `Semantic ready=True`
- `Passed=5/5`
- `Pass rate=1.0`
- `Promotion=False`

## 后续链路

下一版不应直接 promotion，而应做 review：

```text
review_target_hidden_semantic_holdout_replay_result
```

review 需要判断：

- v908 相比 v905 是否真正降低了 task-hint 风险。
- 当前 suite 是否仍然太窄。
- 是否需要更宽 holdout、更多 paraphrase、或严格 prompt mutation。

## 一句话总结

v908 用真实 v890 checkpoint 通过了更少提示的 semantic target-hidden holdout 5/5 replay，把“模型只靠明显任务提示输出 fixed/loss”的疑问进一步压缩到 review 阶段。
