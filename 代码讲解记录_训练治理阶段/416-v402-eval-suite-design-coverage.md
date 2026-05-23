# v402 eval suite design coverage 代码讲解

## 本版目标和边界

v402 的目标是从 CI 包装层回到评估本身：在模型真正生成之前，先让 prompt suite 的设计覆盖情况可见。标准中文 benchmark suite 现在能在 tiny standard benchmark smoke 的顶层 summary 里说明它覆盖了哪些任务类型、难度、标签、token budget 和 seed。

本版不改变模型结构，不扩大训练预算，不新增治理链，也不声称 tiny smoke 的生成质量变好。它只补强“这套评估题本身是否足够代表性”的证据。

## 前置能力

v315 建立 CPU tiny standard benchmark smoke。v398-v401 补齐 tiny scorecard benchmark history 与 CI wrapper 边界。v402 回到最前面的评估输入：

```text
prompt suite design
        |
        +--> capped suite payload
        +--> tiny corpus
        +--> train
        +--> eval suite
        +--> generation quality
        +--> pair baseline
        +--> benchmark scorecard
```

如果 prompt suite 本身过窄，后续 scorecard 和 history 就不应该被过度解释。

## 关键文件

### `src/minigpt/eval_suite_design.py`

这是新增的小模块，避免继续撑大 `eval_suite.py` 或 smoke 脚本。核心函数：

```text
summarize_prompt_suite_design(suite)
```

输入可以是 `PromptSuite`，也可以是 suite payload dict。输出包括：

```text
suite_name
suite_version
language
case_count
task_type_counts
difficulty_counts
tag_counts
task_type_count
difficulty_count
tag_count
observed_task_types
observed_difficulties
observed_tags
min_new_tokens
max_new_tokens
unique_seed_count
duplicate_seed_count
all_cases_have_expected_behavior
all_cases_have_tags
coverage_status
comparison_status
decision
comparison_decision
missing_recommended_task_types
missing_recommended_difficulties
missing_comparison_difficulties
blockers
comparison_blockers
```

它复用 `eval_suite.py` 里已有的推荐覆盖阈值，例如最少 case 数、推荐任务类型、推荐难度、comparison 所需 hard 难度和 tag 数。

### `scripts/run_tiny_standard_benchmark_smoke.py`

`build_capped_prompt_suite_payload()` 现在会把 suite design summary 写进 capped suite JSON：

```text
design_summary
```

`build_summary()` 又把它提升到 smoke 顶层：

```text
suite_design
```

`render_summary()` 新增 line-oriented 字段：

```text
suite_design_case_count
suite_design_task_type_count
suite_design_difficulty_count
suite_design_tag_count
suite_design_coverage_status
suite_design_comparison_status
suite_design_min_new_tokens
suite_design_max_new_tokens
```

这样一次 tiny standard smoke 不只说“eval suite 跑过了”，还能说“这套 suite 的设计覆盖是否适合做 repeated checkpoint comparison”。

### `src/minigpt/__init__.py`

新增 lazy export：

```text
summarize_prompt_suite_design
```

方便后续脚本或交互式检查直接从 `minigpt` 入口调用。

### `tests/test_eval_suite.py`

新增测试：

- standard-zh suite 的 design summary 是 `pass/pass`；
- task type count 为 10，difficulty count 为 3；
- seed 无重复；
- expected behavior 和 tags 都存在；
- narrow suite 会进入 `warn`，并列出缺失任务类型和 hard 难度。

### `tests/test_tiny_standard_benchmark_smoke.py`

新增测试：

- capped standard suite payload 携带 `design_summary`；
- token cap 被反映为 `max_new_tokens=7` 或真实 smoke 的 `max_new_tokens=4`；
- top-level smoke summary 和 text output 均暴露 `suite_design_*` 字段；
- 真实 tiny smoke 链路仍然跑通。

## 输入输出格式

输入是内置或 JSON prompt suite：

```text
builtin:standard-zh
data/standard_zh_eval_prompts.json
```

输出新增在两个地方：

```text
<out-dir>/standard-zh-capped-suite.json
  design_summary

<out-dir>/tiny_standard_benchmark_smoke_summary.json
  suite_design
```

文本 summary 继续保持 key/value 形式，方便 CI 和人工检查。

## 运行流程

```text
scripts/run_tiny_standard_benchmark_smoke.py
        |
        +--> load builtin suite
        +--> cap max_new_tokens
        +--> summarize_prompt_suite_design()
        +--> write capped suite JSON
        +--> train / eval / quality / pair / scorecard
        +--> write smoke summary with suite_design
```

## 测试覆盖

定向验证：

```text
python -m py_compile src/minigpt/eval_suite_design.py scripts/run_tiny_standard_benchmark_smoke.py tests/test_eval_suite.py tests/test_tiny_standard_benchmark_smoke.py
python -m pytest tests/test_eval_suite.py tests/test_tiny_standard_benchmark_smoke.py -q
```

全量收口继续执行：

```text
python -m pytest -q
python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-v402
git diff --check
```

## 证据归档

运行截图和说明放在：

```text
d/402/图片
d/402/解释/说明.md
```

`d/402/解释/v402-eval-suite-design-coverage-evidence.html` 是给 Playwright MCP 截图的静态证据页。

## 一句话总结

v402 让 MiniGPT 的 benchmark 不只记录模型输出，也开始记录评估题本身是否有代表性，为后续真实 checkpoint comparison 打基础。
