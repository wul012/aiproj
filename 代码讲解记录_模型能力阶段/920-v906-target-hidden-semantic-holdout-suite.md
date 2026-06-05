# v906 target-hidden semantic holdout suite 代码讲解

## 本版目标和边界

v906 的目标是构造一套更少任务提示的 target-hidden semantic holdout suite。

v905 review 认为 v904 的 5/5 是强信号，但 v902 的 5 个 prompt 都带有 `pair/target/answer_terms` 等任务提示。v906 不否定 v904，而是把它推进到更严格的下一层评估。

明确不做：

- 不运行模型。
- 不重新训练。
- 不声明 promotion。
- 不改变 `fixed/loss` scoring contract。

本版只构造更干净的 suite。

## 前置链路

```text
v904 real replay -> 5/5 target-hidden pass
v905 review -> strong signal, but task-hinted, wider holdout required
v906 -> build semantic paraphrase target-hidden suite
```

v906 消费：

- v905 review。
- v902 source target-hidden suite。
- v890 tokenizer。

## 关键文件

### `src/minigpt/target_hidden_semantic_holdout_suite.py`

这是本版核心 builder。

它使用了较短模块名，这是有意的：之前许多模块名过长，后续新能力会尽量使用短而清晰的命名，减少维护成本。

入口函数：

```python
build_target_hidden_semantic_holdout_suite(...)
```

输入：

- v905 replay review report。
- v902 source holdout suite report。
- tokenizer path。

输出：

- `status`
- `decision`
- `check_rows`
- `coverage_rows`
- `benchmark_suite`
- `summary`
- `interpretation`

### `TASK_HINT_TERMS`

v906 复用 v905 的 task hint 判断：

```python
("learned pair", "target pair", "answer_terms", "requires target pair", "pair")
```

它用于确认新 prompt 不再触碰已知提示词。

### `_candidate_prompt_specs`

v906 的 5 个 prompt 是：

```text
answer from memory
answer:

write stored result
output:

complete learned route
result:

return final words
answer:

self check memory result
final:
```

它们和 v902 prompt 的区别：

- 不含 `fixed/loss`。
- 不含 `pair`。
- 不含 `target`。
- 不含 `answer_terms`。
- 仍然能被 v890 tokenizer 覆盖。

### `_coverage_rows`

每个 candidate prompt 会被检查：

- `prompt_unknown_count`
- `tokenizer_covered`
- `leaked_terms`
- `target_hidden`
- `task_hint_terms`
- `task_hint`

v906 真实结果是：

```text
tokenizer_covered_case_count=5
target_hidden_case_count=5
task_hint_case_count=0
candidate_prompt_unknown_token_count=0
```

### `_checks`

本版检查项包括：

- v905 review 必须 pass。
- v905 必须批准 wider holdout。
- v905 next step 必须指向 semantic suite。
- v902 source suite 必须 pass。
- tokenizer 文件存在。
- case count preserved。
- coverage rows complete。
- all prompts tokenizer-covered。
- all prompts target-hidden。
- no prompt task hints。

最后一条 `no_prompt_task_hints` 是 v906 的核心新增保护。

### `_suite`

输出的 suite 使用：

```text
suite_name=route-promotion-objective-level-contrast-semantic-paraphrase-target-hidden-holdout-suite
suite_version=v906
boundary=semantic_paraphrase_target_hidden_ascii_tokenizer_covered_holdout_only
proposed_next_artifact=target_hidden_semantic_holdout_dry_run
```

这说明 v906 是更宽 holdout 的构造版本，不是最终模型判定。

### `src/minigpt/target_hidden_semantic_holdout_suite_artifacts.py`

这是渲染层，输出：

- JSON
- CSV
- TXT
- Markdown
- HTML

报告会同时展示：

- 新 suite 的 `task_hint_case_count=0`
- 来源 v905 的 `source_task_hint_case_count=5`

这个对比是 v906 的证明重点。

### `scripts/build_target_hidden_semantic_holdout_suite.py`

这是 CLI。

典型命令：

```powershell
python scripts\build_target_hidden_semantic_holdout_suite.py --replay-review e\905\解释\bounded-objective-loss-signal-bridge-target-only-memory-target-hidden-tokenizer-covered-holdout-replay-review --source-holdout-suite e\902\解释\bounded-objective-loss-signal-bridge-target-only-memory-target-hidden-tokenizer-covered-holdout-suite --tokenizer e\890\解释\bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-training-run\run\tokenizer.json --out-dir e\906\解释\target-hidden-semantic-holdout-suite --require-suite-ready --force
```

### `tests/test_target_hidden_semantic_holdout_suite.py`

测试覆盖：

- 正常 suite 构造：5 covered、5 hidden、0 hints。
- review 未批准 wider holdout 时失败。
- tokenizer 不覆盖新 prompt 时失败。
- artifacts 和 CLI 可用。

这些测试保护 v906 的新增边界：不能再把 task-hinted suite 伪装成 semantic holdout。

## 真实运行结果

```text
status=pass
decision=target_hidden_semantic_holdout_suite_ready
candidate_case_count=5
tokenizer_covered_case_count=5
target_hidden_case_count=5
task_hint_case_count=0
candidate_prompt_unknown_token_count=0
source_task_hint_case_count=5
next_step=run_target_hidden_semantic_holdout_dry_run
```

## 截图和归档

归档位置：

- `e/906/解释/说明.md`
- `e/906/图片/v906-target-hidden-semantic-holdout-suite.png`
- `e/906/解释/target-hidden-semantic-holdout-suite`

截图证明：

- `Task hints=0`
- `Source hints=5`
- `Covered cases=5`
- `Target-hidden=5`

## 后续链路

下一版应做 dry-run：

- 正例 `fixed loss` 应通过全部 case。
- 负例 `fixed only` 应失败。
- 不运行模型。
- 不声明 promotion。

dry-run 通过后，再真实 replay 这个更少提示的 semantic suite。

## 一句话总结

v906 把 target-hidden 评估从“仍有 pair/target 提示”的 5 条 prompt 推进到更少提示的 semantic holdout，为模型能力判断增加了一层更可信的挑战。
