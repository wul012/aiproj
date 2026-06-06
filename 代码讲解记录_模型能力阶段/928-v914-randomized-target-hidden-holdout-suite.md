# v914 randomized target-hidden holdout suite 代码讲解

## 本版目标和边界

v914 的目标是构造随机化 holdout suite。

v913 已经复核 v912 的 10 条 prompt-mutation replay：没有目标词泄漏、没有已知 task hint、每条 prompt 都确实 mutated，并且模型 replay 结果是 `10/10`。这说明可以继续加压，但仍不能 promotion。v914 因此把下一步做成 seeded randomized target-hidden suite。

明确不做：

- 不重新训练。
- 不运行真实 checkpoint replay。
- 不 dry-run scoring contract。
- 不批准 promotion。
- 不使用不可复现随机。

本版只负责生成 20 条可复现随机化 prompt，并证明它们仍然 tokenizer-covered、target-hidden、无 task hint。

## 前置链路

```text
v913 prompt-mutation replay review
  -> v914 randomized target-hidden suite
  -> next dry-run randomized target-hidden holdout
```

v914 使用的输入：

- v913 replay review report。
- v910 prompt-mutation target-hidden suite。
- v890 tokenizer。

## 关键文件

### `src/minigpt/randomized_target_hidden_holdout_suite.py`

这是本版核心 builder。

入口函数：

```python
build_randomized_target_hidden_holdout_suite(...)
```

关键参数：

- `replay_review_report`：来自 v913。
- `source_holdout_suite_report`：来自 v910。
- `tokenizer_path`：真实 v890 tokenizer。
- `seed`：默认 `914`。
- `candidate_count`：默认 `20`。

输出：

- `status`
- `decision`
- `failed_count`
- `issues`
- `source_replay_review`
- `source_holdout_suite`
- `tokenizer_path`
- `random_seed`
- `check_rows`
- `coverage_rows`
- `benchmark_suite`
- `summary`
- `interpretation`

### `_candidate_cases`

`_candidate_cases` 用 `random.Random(seed)` 生成 prompt。

它从固定词池抽 3 个词，再随机选择一个 tail：

```text
memory answer stored route final result output complete learned write self check words
answer output result final
```

生成格式类似：

```text
<word1> <word2> <word3>
<tail>:
```

每条 case 会记录：

- `case_id`
- `source_case_id`
- `prompt_case`
- `expected_terms`
- `random_seed`
- `random_draw_index`
- `source_case_index`

这样随机不是黑箱：同一个 seed 生成同一批 prompt，不同 seed 会产生不同 prompt。测试里专门覆盖了这两点。

### `_coverage_rows`

`_coverage_rows` 是本版的质量门禁。

每行包括：

```text
case_id
source_case_id
random_draw_index
prompt_unknown_count
tokenizer_covered
leaked_terms
target_hidden
task_hint_terms
task_hint
unique_prompt
randomized_prompt
```

核心判断：

- `tokenizer_covered=True`：prompt 里的字符都在 tokenizer vocab 内。
- `target_hidden=True`：prompt 不包含 `fixed/loss`。
- `task_hint=False`：prompt 不出现已知 pair/target/task 提示词。
- `unique_prompt=True`：prompt 不等于 v910 source prompt。

这让随机化 suite 仍然可以被审计。

### `_checks`

`_checks` 要求：

- v913 review 必须 pass。
- v913 必须 `approved_for_randomized_prompt_holdout=True`。
- v913 的 next step 必须是 `build_randomized_target_hidden_holdout_suite`。
- v910 source suite 必须 pass。
- v910 source suite 必须 ready。
- tokenizer 文件必须存在。
- seed 必须是正数。
- candidate 数必须至少是 source case 的 2 倍。
- coverage rows 必须完整。
- 所有 prompt 必须 tokenizer-covered。
- 所有 prompt 必须 target-hidden。
- 没有 task hint。
- 所有 prompt 必须唯一。
- 所有 prompt 必须不同于 source prompt。

这些 checks 确保 v914 是“可用 suite”，而不是普通随机文本列表。

### `_suite`

`_suite` 输出给后续 dry-run/replay 消费的 benchmark suite。

关键字段：

```text
suite_name=route-promotion-objective-level-contrast-randomized-target-hidden-holdout-suite
suite_version=v914
boundary=seeded_randomized_target_hidden_ascii_tokenizer_covered_holdout_only
random_seed=914
model_quality_claim=not_claimed
proposed_next_artifact=randomized_target_hidden_holdout_dry_run
```

`model_quality_claim=not_claimed` 很重要：v914 只是构造评估集，不证明模型能力。

### `_summary`

真实 v914 summary：

```text
randomized_target_hidden_holdout_suite_ready=True
source_case_count=10
candidate_case_count=20
random_seed=914
randomized_case_factor=2.0
tokenizer_covered_case_count=20
target_hidden_case_count=20
task_hint_case_count=0
unique_prompt_count=20
new_vs_source_prompt_count=20
candidate_prompt_unknown_token_count=0
source_prompt_mutation_clean_case_count=10
source_pass_rate=1.0
promotion_ready=False
model_quality_claim=suite_construction_only
next_step=dry_run_randomized_target_hidden_holdout
```

这里的关键推进是：从固定 10 条 prompt mutation 扩到 20 条 seeded randomized prompt，同时保留所有工程边界。

### `src/minigpt/randomized_target_hidden_holdout_suite_artifacts.py`

这是输出层。

它写出：

- JSON：后续 dry-run/replay 消费。
- CSV：逐 case 查看 draw、coverage、prompt。
- text：命令行摘要。
- Markdown：人工阅读。
- HTML：截图证据。

HTML 卡片展示 `Status`、`Candidates`、`Seed`、`Covered`、`Target-hidden`、`Hints`、`Unique`、`Next`。这些字段覆盖 v914 的主要质量约束。

### `scripts/build_randomized_target_hidden_holdout_suite.py`

这是 CLI。

关键参数：

```powershell
--replay-review
--source-holdout-suite
--tokenizer
--seed
--candidate-count
--out-dir
--require-suite-ready
--force
```

真实运行时使用：

```powershell
--seed 914
--candidate-count 20
```

## 测试覆盖

新增测试：

```text
tests/test_randomized_target_hidden_holdout_suite.py
```

覆盖内容：

- 构造 seeded randomized target-hidden suite。
- 同一 seed 生成完全相同 prompt。
- 不同 seed 生成不同 prompt。
- v913 review 不批准 randomized holdout 时失败。
- tokenizer coverage 不足时失败。
- artifact writer 和 CLI 能写出 JSON/CSV/text/Markdown/HTML。

这些测试保护的是随机化 suite 的可复现性和边界，不只是 happy path。

## 运行证据

真实命令：

```powershell
python scripts\build_randomized_target_hidden_holdout_suite.py --replay-review e\913\解释\target-hidden-prompt-mutation-holdout-replay-review --source-holdout-suite e\910\解释\target-hidden-prompt-mutation-holdout-suite --tokenizer e\890\解释\bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-training-run\run\tokenizer.json --seed 914 --candidate-count 20 --out-dir e\914\解释\randomized-target-hidden-holdout-suite --require-suite-ready --force
```

结果：

```text
status=pass
decision=randomized_target_hidden_holdout_suite_ready
candidate_case_count=20
random_seed=914
tokenizer_covered_case_count=20
target_hidden_case_count=20
task_hint_case_count=0
unique_prompt_count=20
new_vs_source_prompt_count=20
next_step=dry_run_randomized_target_hidden_holdout
```

截图：

```text
e/914/图片/v914-randomized-target-hidden-holdout-suite.png
```

## 链路角色

v914 是从固定 holdout 走向随机化 holdout 的过渡层。

它没有提高模型本身，但提高了评估压力：模型下一步面对的不是固定的 10 条 prompt mutation，而是 20 条由 seed 控制、可复现、可审计的新 prompt。

## 一句话总结

v914 把 v913 的干净 prompt-mutation 信号扩展成 20 条 seeded randomized target-hidden holdout case，为下一步 dry-run 和真实 replay 提供更强评估入口。
