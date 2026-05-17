# v188 training run evidence generation quality summary

## 本版目标

v188 的目标是把 v187 的真实训练运行证据，从“知道 checkpoint 已跑过固定 eval suite”继续推进到“能看到这次生成输出是否有明显质量风险”。

它解决的问题是：v187 已经能读取 `eval_suite/eval_suite.json`，但 fixed prompts 跑过并不等于输出质量没有问题。项目里早已有 `generation_quality` 模块，可以标记短输出、空输出、低多样性、重复 n-gram、长重复字符和 prompt echo。v188 把这份质量摘要接入 training run evidence，让训练证据页不需要另开报告，也能看到生成质量边界。

本版明确不做：

- 不扩大模型规模。
- 不修改 generation quality 的评分规则。
- 不把 generation quality 通过包装成模型能力强。
- 不把 generation quality fail 当成 checkpoint 文件缺失；它是质量 review 风险，不是训练产物不存在。

## 前置路线

v28-v30 建立 generation quality 检查，并把它接入 release-style 证据链。

v137-v141 给 generation quality 和 benchmark scorecard 增加 flag taxonomy 与 promotion decision 上下文。

v186 把真实训练 run 目录接入 training run evidence。v187 接入 fixed eval suite 摘要。v188 继续向后接入 generation quality 摘要，形成：

```text
real train -> eval suite -> generation quality -> training run evidence
```

## 关键文件

### `src/minigpt/training_run_evidence.py`

`build_training_run_evidence()` 现在会读取：

```text
<run_dir>/generation_quality/generation_quality.json
```

并生成新的 `quality` section。核心字段包括：

- `exists`：generation quality JSON 是否存在。
- `source_type`：通常是 `eval_suite`。
- `overall_status`：`pass`、`warn` 或 `fail`。
- `case_count`、`pass_count`、`warn_count`、`fail_count`：质量检查 case 分布。
- `avg_continuation_chars`：平均续写长度。
- `avg_unique_ratio`：平均唯一字符比例。
- `avg_repeated_ngram_ratio`：平均重复 n-gram 比例。
- `max_repeat_run`：最长重复字符 run。
- `total_flags`：总 flag 数。
- `dominant_flag`：出现最多的 flag id。

新增 `_quality_section()` 只做摘要抽取，不重新计算质量；真正的质量判断仍由 `generation_quality.py` 负责。这样 training evidence 是消费者，不复制上游规则。

新增 `_quality_check()` 的语义：

- quality 报告存在且 `overall_status=pass`：`pass`。
- quality 报告缺失：`warn`。
- quality 报告存在但 `warn/fail`：`warn`。

这让 evidence status 能反映质量风险：生成质量有问题时不把 run 标成完全 ready，但也不误判为 checkpoint、tokenizer、metrics 等训练核心产物缺失。

### `src/minigpt/training_run_evidence_artifacts.py`

artifact writer 现在把 `quality` section 写入：

- CSV：新增 `generation_quality_status`、`generation_quality_fail_count`、`generation_quality_warn_count`、`generation_quality_total_flags`、`generation_quality_dominant_flag`。
- Markdown：新增 `## Generation Quality` 表格。
- HTML：stats 卡片显示 Quality 状态，并新增 Generation Quality 面板。

这些输出是最终证据，可被人工审查或后续模块读取。

### `scripts/build_training_run_evidence.py`

CLI 新增：

```text
generation_quality_status=<status>
generation_quality_flags=<count>
```

这让命令行 smoke 可以直接看见训练 run 的生成质量风险。

### `tests/test_training_run_evidence.py`

测试 fixture 新增 `generation_quality/generation_quality.json`。

新增断言覆盖：

- 完整 run 的 `quality.overall_status` 是 `pass`。
- summary 中包含 `generation_quality_status`。
- 缺 generation quality 时，run 进入 `review` 而不是 `blocked`。
- Markdown 输出包含 `## Generation Quality`。

## 运行流程

v188 的真实链路是：

```text
scripts/train.py
 -> scripts/eval_suite.py
 -> scripts/analyze_generation_quality.py
 -> scripts/build_training_run_evidence.py
```

训练证据读取的目录结构是：

```text
run_dir/
  checkpoint.pt
  tokenizer.json
  train_config.json
  metrics.jsonl
  run_manifest.json
  sample.txt
  eval_suite/eval_suite.json
  generation_quality/generation_quality.json
```

## 测试和证据

v188 的截图归档在 `c/188`。

关键验证包括：

- focused tests：覆盖 quality pass、quality missing review、artifact 输出和 HTML 转义。
- real PyTorch train + eval + generation quality smoke：真实跑训练、固定 eval suite 和质量分析。
- evidence CLI smoke：输出 generation quality status 与 flags。
- Playwright/Chrome screenshot：确认 Generation Quality 面板能在浏览器打开。
- source encoding hygiene 和 full unittest discovery：确认新增代码通过全局门禁。

## 边界说明

v188 不把 generation quality 当成“最终模型质量证明”。它只是把自动发现的生成风险放进训练证据：短输出、重复、低多样性等问题能被看见。真正晋级仍需要 benchmark scorecard、rubric scoring、跨 run comparison 和人工审查。

## 一句话总结

v188 让真实训练 run evidence 同时看到固定评估覆盖和生成质量风险，把“跑过 eval”推进到“eval 输出质量也进入同一份训练证据”的层次。
