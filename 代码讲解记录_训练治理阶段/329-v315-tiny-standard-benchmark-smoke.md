# v315 tiny standard benchmark smoke

## 本版目标和边界

v268-v314 主要在强化 clean batch-review、CI-regression、receipt、embedded sidecar 和 assurance 这些治理链条。它们让证据越来越可靠，但也带来一个方向风险：项目容易继续“只加治理外壳”，而离真实模型能力证据越来越远。

v315 的目标是补一个轻量但真实的模型能力 smoke：

```text
tiny corpus -> train.py -> checkpoint.pt -> eval_suite.py -> generation quality -> benchmark scorecard -> summary
```

本版不追求训练出好模型，也不把 tiny smoke 的分数包装成质量达标。它只证明：在普通 CPU 环境里，项目能从一个真实训练出的 tiny checkpoint 出发，跑完整标准 suite、generation-quality 和 benchmark-scorecard 证据链。实际 `scorecard_overall_status=fail` 会被保留在 summary 中，避免把“链路可跑”误写成“模型能力强”。

## 前置能力

本版复用已有能力：

- `scripts/train.py`
  - 真实训练 MiniGPT checkpoint，并输出 tokenizer、manifest、history summary。
- `scripts/eval_suite.py`
  - 加载 checkpoint/tokenizer，对固定 prompt suite 生成结果。
- `src/minigpt/eval_suites.py`
  - 提供 `standard-zh` 内置 suite，覆盖 10 个中文任务类型。
- `scripts/analyze_generation_quality.py`
  - 从 eval suite 输出中生成 generation quality 报告。
- `scripts/build_benchmark_scorecard.py`
  - 汇总 eval suite、generation quality 和 pair/evidence completeness，给出 scorecard。

v315 把这些入口串成一个单命令 smoke。

## 关键文件

- `scripts/run_tiny_standard_benchmark_smoke.py`
  - 新增主脚本。
  - 负责构造 capped prompt suite、生成 tiny corpus、执行四个子命令、收集 stdout/stderr、汇总 artifacts 和写 summary。
- `tests/test_tiny_standard_benchmark_smoke.py`
  - 覆盖 suite cap、tiny corpus 构造、summary render 和真实脚本链路。
  - 真实脚本测试使用 `max_iters=1`、小 block/model size，保证 CPU 可跑。
- `README.md`
  - 当前版本更新到 v315。
  - 明确说明 tiny smoke 是 evidence readiness，不是模型质量达标声明。
- `d/315`
  - 保存本版运行截图和说明。
- `代码讲解记录_训练治理阶段/README.md`
  - 新增第 329 篇索引。

## 核心流程

`run_tiny_standard_benchmark_smoke.py` 的执行流程：

1. 读取内置 suite：

```python
suite = load_builtin_prompt_suite("standard-zh")
```

2. 对 suite 做 token cap：

```text
case.max_new_tokens = min(original, case_token_cap)
```

这保留 10 个标准 case 的任务覆盖，同时让 CPU smoke 更快。

3. 构造 tiny corpus：

```text
prompt + expected_behavior + evidence-chain helper line
```

corpus 会重复几轮，确保 char tokenizer 能编码 suite 中的 prompt 字符。

4. 依次执行四个子命令：

```text
train
eval_suite
generation_quality
benchmark_scorecard
```

每个命令的 stdout/stderr 都写入 `logs/`。

5. 读取关键产物并写 summary：

```text
tiny_standard_benchmark_smoke_summary.json
tiny_standard_benchmark_smoke_summary.txt
```

summary 中既有 artifact existence，也有训练、eval、generation quality 和 scorecard 摘要。

## 输入输出

输入主要来自脚本参数：

```text
--suite-name standard-zh
--case-token-cap 6
--max-iters 1
--device cpu
```

输出目录结构：

```text
out-dir/
  tiny_corpus.txt
  standard-zh-capped-suite.json
  run/
    checkpoint.pt
    tokenizer.json
    run_manifest.json
    history_summary.json
    eval_suite/eval_suite.json
    generation-quality/generation_quality.json
    benchmark-scorecard/benchmark_scorecard.json
  logs/
  tiny_standard_benchmark_smoke_summary.json
  tiny_standard_benchmark_smoke_summary.txt
```

其中 `checkpoint.pt` 是真实训练产物；`eval_suite.json`、`generation_quality.json` 和 `benchmark_scorecard.json` 是后续评估链消费的证据。

## Summary 语义

核心字段：

```text
status=pass
decision=evidence-ready
checkpoint_exists=True
eval_suite_case_count=10
eval_suite_coverage_status=pass
eval_suite_comparison_status=pass
generation_quality_status=pass
scorecard_overall_status=fail
scorecard_overall_score=59.34
```

这里 `status=pass` 表示 smoke 链路可跑、产物齐全。`scorecard_overall_status=fail` 表示 tiny 训练模型的 benchmark score 不足。两者刻意分开，避免把工程可运行性误判为模型能力达标。

## 测试覆盖

- `test_capped_standard_suite_keeps_all_cases_with_lower_token_budget`
  - 证明 capped suite 仍保留 10 个 standard-zh case。
- `test_render_summary_prints_model_capability_evidence_fields`
  - 证明 summary text 包含 eval、quality、scorecard 和 command 状态字段。
- `test_tiny_standard_benchmark_smoke_script_runs_real_chain`
  - 真实执行脚本，检查 checkpoint、eval suite、generation quality、scorecard 和 summary 都生成。
- 组合测试
  - `tests.test_tiny_standard_benchmark_smoke`
  - `tests.test_eval_suite`
  - `tests.test_generation_quality`
  - `tests.test_benchmark_scorecard`
  - 共 28 个 focused tests 通过。
- 全量测试
  - `python -B -m unittest discover -s tests` 通过。
- 编码与静态检查
  - source encoding hygiene 通过，285 个 Python source clean。
  - `git diff --check` 通过。

## 运行证据

运行截图和解释归档在 `d/315`：

- `d/315/图片/01-tiny-standard-smoke-tests.png`
- `d/315/图片/02-tiny-standard-smoke-summary.png`
- `d/315/图片/03-scorecard-summary.png`
- `d/315/图片/04-py-compile.png`
- `d/315/图片/05-source-encoding.png`
- `d/315/图片/06-full-unittest.png`
- `d/315/图片/07-focused-benchmark-tests.png`
- `d/315/图片/08-diff-check.png`
- `d/315/图片/09-static-scan.png`
- `d/315/解释/说明.md`

这些证据证明本版不只是新增函数，而是实际跑了一次 CPU tiny checkpoint 的标准 benchmark 证据链。

## 一句话总结

v315 给 MiniGPT 加了一个低成本、真实可运行的 tiny standard benchmark smoke，让项目从“治理证据很完整”回到“模型训练和评估链也必须真实跑通”。
