# v910 target-hidden prompt-mutation holdout suite 代码讲解

## 本版目标和边界

v910 的目标是构建 prompt-mutation target-hidden holdout suite。

v909 已经给出 review 结论：v908 的 semantic target-hidden replay 是 clean signal，可以进入 prompt mutation holdout，但不能直接 promotion。v910 承接这个结论，将原来的 5 个 semantic prompt 扩展为 10 个变体 prompt。

明确不做：

- 不运行模型。
- 不训练 checkpoint。
- 不声明模型能力。
- 不批准 promotion。

本版只构造下一层 suite，并验证它符合 tokenizer-covered、target-hidden、no task hint、prompt mutated 的边界。

## 前置链路

```text
v906 semantic target-hidden suite
  -> v907 dry-run
  -> v908 real replay
  -> v909 clean signal review
  -> v910 prompt-mutation target-hidden suite
```

## 关键文件

### `src/minigpt/target_hidden_prompt_mutation_holdout_suite.py`

这是本版核心 builder。

入口函数：

```python
build_target_hidden_prompt_mutation_holdout_suite(...)
```

输入：

- v909 replay review report。
- v906 semantic holdout suite report。
- v890 tokenizer 路径。

输出：

- `status`
- `decision`
- `check_rows`
- `coverage_rows`
- `benchmark_suite`
- `summary`
- `interpretation`

### `locate_replay_review`

支持目录或 JSON 文件输入。

目录输入会自动定位：

```text
target_hidden_semantic_holdout_replay_review.json
```

这确保 v910 必须从 v909 的 review 结果进入，而不是直接从 replay 进入。

### `locate_source_holdout_suite`

支持目录或 JSON 文件输入。

目录输入会自动定位：

```text
target_hidden_semantic_holdout_suite.json
```

v910 使用原始 v906 suite 来判断 mutation prompt 是否真的不同于 source prompt。

### `_candidate_prompt_specs`

这里定义 10 个 prompt mutation：

```text
memory answer
stored memory
learned final route
write final memory
complete stored route
self check stored memory
return learned memory
final words memory
stored final words
complete memory route
```

这些 prompt 的共同要求：

- 不包含 `fixed`。
- 不包含 `loss`。
- 不包含 `target pair`、`learned pair`、`answer_terms` 等已知 task hint。
- 字符都被 v890 tokenizer 覆盖。

v910 不是随便增加样例，而是在现有 tokenizer 和语义词面内做组合扰动，避免引入新的 tokenizer unknown gap。

### `_candidate_cases`

`_candidate_cases` 将 10 个 prompt specs 转成标准 `PromptCase`。

每个 case 保留：

- `case_id`
- `source_case_id`
- `prompt_case`
- `expected_terms`
- `required_term_count`
- `mutation_source_index`

`mutation_source_index` 用来说明这个 mutation case 是从哪个 source case 轮转承接来的。

### `_coverage_rows`

`_coverage_rows` 是本版最重要的质量检查数据。

每个 prompt 会记录：

- `prompt_unknown_count`
- `tokenizer_covered`
- `leaked_terms`
- `target_hidden`
- `task_hint_terms`
- `task_hint`
- `prompt_mutated`

其中 `prompt_mutated=True` 表示该 prompt 不等于 v906 的任一 source prompt，避免 v910 实际只是复制旧 suite。

### `_checks`

v910 checks 包括：

输入链路：

- v909 review 必须 pass。
- `approved_for_prompt_mutation_holdout=True`。
- v909 next step 必须是 `build_prompt_mutation_target_hidden_holdout_suite`。
- v906 source suite 必须 pass。
- v906 source suite ready。

构造质量：

- tokenizer 文件存在。
- candidate case 数至少是 source case 的两倍。
- coverage rows 覆盖全部 candidate。
- 全部 prompt tokenizer-covered。
- 全部 prompt target-hidden。
- 全部 prompt 没有已知 task hint。
- 全部 prompt 与 source prompt 不同。

这些 checks 防止 v910 变成“看起来扩展，实际上复制旧 prompt”的空转版本。

### `_summary`

真实 v910 summary：

```text
target_hidden_prompt_mutation_holdout_suite_ready=True
source_case_count=5
candidate_case_count=10
mutation_factor=2.0
tokenizer_covered_case_count=10
target_hidden_case_count=10
task_hint_case_count=0
prompt_mutated_case_count=10
candidate_prompt_unknown_token_count=0
source_clean_prompt_case_count=5
source_pass_rate=1.0
promotion_ready=False
model_quality_claim=suite_construction_only
next_step=run_target_hidden_prompt_mutation_holdout_dry_run
```

这里的 `mutation_factor=2.0` 是 v910 相比 v906 的主要增量：从 5 个 clean semantic case 扩到 10 个 prompt mutation case。

### `_suite`

`_suite` 输出后续 dry-run/replay 会消费的 benchmark suite。

关键字段：

- `suite_name=route-promotion-objective-level-contrast-prompt-mutation-target-hidden-holdout-suite`
- `suite_version=v910`
- `boundary=prompt_mutation_target_hidden_ascii_tokenizer_covered_holdout_only`
- `model_quality_claim=not_claimed`
- `proposed_next_artifact=target_hidden_prompt_mutation_holdout_dry_run`

这说明 v910 只是构造 suite，能力声明留给后续 replay 和 review。

### `src/minigpt/target_hidden_prompt_mutation_holdout_suite_artifacts.py`

这是渲染层。

输出：

- JSON
- CSV
- TXT
- Markdown
- HTML

HTML 展示：

- candidate case 数。
- mutation factor。
- tokenizer coverage。
- target-hidden case 数。
- task-hint case 数。
- prompt-mutated case 数。
- next step。

### `scripts/build_target_hidden_prompt_mutation_holdout_suite.py`

这是 CLI。

真实归档命令：

```powershell
python scripts\build_target_hidden_prompt_mutation_holdout_suite.py --replay-review e\909\解释\target-hidden-semantic-holdout-replay-review --source-holdout-suite e\906\解释\target-hidden-semantic-holdout-suite --tokenizer e\890\解释\bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-training-run\run\tokenizer.json --out-dir e\910\解释\target-hidden-prompt-mutation-holdout-suite --require-suite-ready --force
```

## 真实运行结果

```text
status=pass
decision=target_hidden_prompt_mutation_holdout_suite_ready
source_case_count=5
candidate_case_count=10
mutation_factor=2.0
tokenizer_covered_case_count=10
target_hidden_case_count=10
task_hint_case_count=0
prompt_mutated_case_count=10
candidate_prompt_unknown_token_count=0
next_step=run_target_hidden_prompt_mutation_holdout_dry_run
```

## 测试覆盖

`tests/test_target_hidden_prompt_mutation_holdout_suite.py` 覆盖：

- 正常构建 10-case prompt mutation suite。
- v909 如果没有批准 prompt mutation，必须失败。
- tokenizer coverage 不足时必须失败。
- artifacts 和 CLI 可用。

测试重点不是检查某个字符串，而是保护 suite 构造边界。

## 截图和归档

归档位置：

- `e/910/解释/说明.md`
- `e/910/图片/v910-target-hidden-prompt-mutation-holdout-suite.png`
- `e/910/解释/target-hidden-prompt-mutation-holdout-suite`

截图证明：

- `Candidates=10`
- `Mutation factor=2.0`
- `Covered=10`
- `Target-hidden=10`
- `Hints=0`
- `Mutated=10`

## 后续链路

下一版应 dry-run v910 suite：

```text
run_target_hidden_prompt_mutation_holdout_dry_run
```

dry-run 要先证明 `fixed/loss` scoring contract 在 10 个 mutation prompt 上仍然工作，再进入真实 replay。

## 一句话总结

v910 把 clean semantic replay 后的下一步从“继续重复 5 个 prompt”推进到 10-case prompt mutation holdout，让后续模型 replay 面对更宽的 target-hidden 测试。
