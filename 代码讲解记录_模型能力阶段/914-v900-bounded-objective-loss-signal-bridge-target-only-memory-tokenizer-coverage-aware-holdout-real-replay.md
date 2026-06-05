# v900 tokenizer-coverage-aware holdout real replay 代码讲解

## 本版目标与边界

v900 的目标是运行真实 checkpoint replay。v898 构建了 tokenizer-covered holdout suite，v899 证明评分器正反例可用；v900 则用 v890 checkpoint/tokenizer 真正生成 continuation，并判断 5 条 case 是否都命中 `fixed/loss`。

本版不训练模型，不修改 suite，不放宽评分。它也不自动 promotion：即使 5/5 通过，也只说明 tokenizer-covered holdout replay 通过，仍需要 review suite 独立性和难度。

## 前置链路

- v890: 真实 checkpoint/tokenizer。
- v898: tokenizer-coverage-aware holdout suite。
- v899: scoring contract dry-run 通过。

v900 是排除 tokenizer/suite/scoring 问题后的真实模型 replay。

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_real_replay.py`
  - 核心 replay 构建器。
  - 前置检查 v898 suite 和 v899 dry-run。
  - 使用 `MiniGPTGenerator` 对每条 case 生成 continuation。
  - 只对 continuation 评分，不靠 prompt 中已有的 `fixed/loss`。

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_real_replay_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
  - HTML 展示 pass rate、hit terms、missed terms 和 continuation。

- `scripts/run_bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_real_replay.py`
  - CLI 入口。
  - 输入为 `--holdout-suite`、`--dry-run`、`--checkpoint`、`--tokenizer`。
  - `--require-execution-pass` 检查执行链，`--require-model-pass` 可作为更严格 gate。

- `tests/test_bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_real_replay.py`
  - 覆盖输入 gate、全通过、partial gap、CLI/output。

- `e/900/解释/bounded-objective-loss-signal-bridge-target-only-memory-tokenizer-coverage-aware-holdout-real-replay/*`
  - v900 真实 replay 证据。

- `e/900/图片/v900-bounded-objective-loss-signal-bridge-target-only-memory-tokenizer-coverage-aware-holdout-real-replay.png`
  - Playwright MCP 截图证据。

## 核心数据结构

`replay_rows` 是主表：

- `case_id`
- `source_case_id`
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

`summary` 汇总：

- `holdout_model_quality_ready`
- `case_count`
- `executed_case_count`
- `passed_case_count`
- `failed_case_count`
- `any_hit_case_count`
- `zero_hit_case_count`
- `pass_rate`
- `promotion_ready=False`
- `model_quality_claim=tokenizer_covered_holdout_replay_only`
- `next_step=review_tokenizer_coverage_aware_holdout_replay_result`

## 核心函数

`build_tokenizer_coverage_aware_holdout_real_replay()` 是总入口：

1. 读取 v898 `benchmark_suite` 和 v899 dry-run。
2. 检查 checkpoint/tokenizer 文件存在。
3. 调用 `_run_cases()` 逐 case 生成。
4. `_generate_case()` 使用 `MiniGPTGenerator` 和 case 自带的 `max_new_tokens`、`temperature`、`top_k`、`seed`。
5. `_score()` 只检查 continuation 是否包含全部 expected terms。
6. `_summary()` 决定 holdout 是否全通过。

这个设计刻意不把 prompt 中已有的 `fixed loss` 算作命中，避免“题干里有答案”导致误判。

## 真实运行结果

v900 真实输出：

- `status=pass`
- `decision=bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_real_replay_passed_review_required`
- `holdout_model_quality_ready=True`
- `passed_case_count=5`
- `any_hit_case_count=5`
- `zero_hit_case_count=0`
- `pass_rate=1.0`
- `promotion_ready=False`

典型 continuation：

- ` fixed loss\n\n\n\n\n\nfixed l`
- ` fixed loss\n\n\n\nfixed los`
- `\n\nanswer.\nfixed losss\n\nf`
- `\nfixed loss\n\n\n\n\nfixed lo`
- `\nfixed loss\n\n\n\n\n\n\nfixed `

每条 continuation 自身都含 `fixed/loss`，因此 5 条 case 全部通过。

## 测试覆盖

本版测试覆盖：

- fake runner 不能绕过 checkpoint/tokenizer 文件存在性。
- runner 输出 `fixed loss` 时，模型质量 ready。
- runner 输出 `fixed only` 时，execution pass 但 model pass 失败。
- CLI 能用真实 tiny checkpoint 执行，输出五类产物。

这些测试保护 v900 的核心边界：执行成功、模型通过、promotion review 是三件不同的事。

## 截图与归档

本版运行证据放在：

- `e/900/解释/说明.md`
- `e/900/解释/bounded-objective-loss-signal-bridge-target-only-memory-tokenizer-coverage-aware-holdout-real-replay/`
- `e/900/图片/v900-bounded-objective-loss-signal-bridge-target-only-memory-tokenizer-coverage-aware-holdout-real-replay.png`

截图通过 Playwright MCP 打开本地 HTML 后生成。截图临时服务器已停止。

## 一句话总结

v900 证明 v890 checkpoint 在 tokenizer-covered holdout suite 上 5/5 通过，但仍把下一步留给 replay result review，而不是直接 promotion。
