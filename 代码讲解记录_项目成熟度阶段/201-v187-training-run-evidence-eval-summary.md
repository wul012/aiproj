# v187 training run evidence eval summary

## 本版目标

v187 的目标是把 v186 的真实训练运行证据，从“只知道 eval suite 是否存在”推进到“能读懂 eval suite 的固定评估摘要”。

它解决的问题是：真实 PyTorch 训练目录已经能被 `build_training_run_evidence()` 审计，但 v186 对 `eval_suite/eval_suite.json` 只做存在性判断。这样一个训练 run 即使真的跑过固定 prompt suite，报告也看不到 case 数、任务类型覆盖、难度覆盖和生成长度等基础评估上下文。

本版明确不做：

- 不扩大模型规模。
- 不调整 eval suite 的 prompt 内容和评分逻辑。
- 不把 eval suite 摘要包装成模型质量已经优秀的证明。
- 不继续做纯模块拆分。

## 前置路线

v16 引入固定 prompt eval suite，使 checkpoint 可以用同一组任务生成可比较输出。

v67-v82 建立 training portfolio 和 training scale 治理链，让训练、评估、比较和晋级可以串成证据链。

v186 新增 real training run evidence，把 `scripts/train.py` 的真实输出目录转为 promotion-review 报告。v187 直接接在 v186 后面，把 eval suite 输出接入这份报告，让真实训练后再跑固定评估的 run 可以从 `review` 进入更可信的 `ready`。

## 关键文件

### `src/minigpt/training_run_evidence.py`

这是本版核心修改。

`build_training_run_evidence()` 现在会读取：

```text
<run_dir>/eval_suite/eval_suite.json
```

并生成新的 `evaluation` section。核心字段包括：

- `exists`：eval suite JSON 是否存在。
- `suite_name`、`suite_version`、`language`：来自 `benchmark` metadata。
- `case_count`：固定 prompt case 数。
- `result_count`：实际 `results` 列表长度。
- `avg_continuation_chars`：平均生成续写字符数。
- `avg_unique_chars`：平均唯一字符数。
- `task_type_count`、`task_types`：任务类型覆盖。
- `difficulty_count`、`difficulties`：难度覆盖。

新增 `_evaluation_section()` 只做摘要抽取，不重新解释模型质量。它允许旧的简单 fixture 只提供 `case_count`，也能从完整 eval suite report 中读取 `benchmark.task_type_counts`、`difficulty_counts` 和 `results`。

`_eval_suite_check()` 替代 v186 的简单存在性检查：

- eval suite 存在且 `case_count > 0`：`pass`。
- eval suite 缺失：默认 `warn`，如果 CLI 使用 `--require-eval-suite` 则 `fail`。
- eval suite 文件存在但没有 case：默认 `warn`，强制要求时 `fail`。

这保留了项目边界：缺 eval 不代表训练证据完全不可用，但不能被当成完整模型质量证据。

### `src/minigpt/training_run_evidence_artifacts.py`

artifact writer 现在会把 evaluation 摘要写到多种输出：

- JSON：保留完整 `evaluation` section，供后续模块消费。
- CSV：新增 `eval_suite_case_count`、`avg_continuation_chars`、`avg_unique_chars`、`eval_task_type_count`、`eval_difficulty_count` 等列。
- Markdown：新增 `## Evaluation` 表格。
- HTML：stats 卡片显示 eval cases 和 task types，并增加 Evaluation 面板。

这些产物是最终证据，不是临时调试文件。它们不重新跑模型，只展示 builder 从训练目录和 eval suite report 中读到的事实。

### `scripts/build_training_run_evidence.py`

CLI 输出新增：

```text
eval_suite_cases=<n>
eval_task_types=<comma-separated task types>
```

这样终端 smoke 不打开 JSON/HTML，也能快速看到真实 run 是否已经跑过固定评估集。

### `tests/test_training_run_evidence.py`

测试 fixture 的 `eval_suite.json` 从最小 `{case_count: 1}` 扩展为带 metadata 的摘要：

- `case_count`
- `avg_continuation_chars`
- `avg_unique_chars`
- `task_type_counts`
- `difficulty_counts`
- `benchmark`

新增断言保护：

- 完整 run 的 `evaluation.case_count` 和 `task_type_count` 会进入 report。
- `summary.eval_suite_case_count` 会进入 summary。
- 缺 eval suite 且未强制要求时，run 是 `review`，不是 `blocked`。
- Markdown 输出包含 `## Evaluation`。

## 运行流程

v187 的真实链路是：

```text
scripts/train.py
 -> checkpoint/train_config/metrics/run_manifest/sample
 -> scripts/eval_suite.py
 -> eval_suite/eval_suite.json
 -> scripts/build_training_run_evidence.py
 -> evaluation-aware JSON/CSV/Markdown/HTML evidence
```

这比 v186 多了一步固定评估：

```text
real train evidence
 -> review if eval suite missing
 -> ready if eval suite has generated cases and all core evidence passes
```

## 测试和证据

v187 的截图归档在 `c/187`。

关键验证包括：

- focused tests：覆盖 eval 摘要抽取、缺 eval 的 review 边界、artifact 输出和 HTML 转义。
- real PyTorch train + eval smoke：CPU 跑 2 iter 训练后继续运行固定 eval suite。
- evidence CLI smoke：读取同一个真实 run，输出 `status=ready`、`eval_suite_cases` 和 eval task types。
- Playwright/Chrome screenshot：确认新的 Evaluation 面板在真实浏览器中可打开。
- source encoding hygiene 和 full unittest discovery：确认新增代码没有破坏全局测试和 CI 编码门禁。

## 边界说明

v187 仍然不声称 MiniGPT 模型质量已经强。eval suite 摘要只说明“这次 checkpoint 已经被固定 prompt suite 跑过，并且报告能看到覆盖信息”。真正判断质量，还需要后续 generation quality、benchmark scorecard、rubric scoring 和跨 run comparison。

这个边界很重要：治理证据不能代替模型能力，但它能让模型能力的讨论有可复查输入。

## 一句话总结

v187 让真实训练 run evidence 能消费固定 eval suite 摘要，把“训练完成”推进到“训练后已被固定评估集验证并可审计”的证据层。
