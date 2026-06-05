# v899 tokenizer-coverage-aware holdout dry-run 代码讲解

## 本版目标与边界

v899 的目标是验证 v898 生成的 tokenizer-coverage-aware holdout suite 的评分规则是否可靠。v898 已经解决 tokenizer 覆盖问题，但 suite 还没有经过 scoring contract dry-run。v899 不运行模型，不训练，不做能力提升声明，只检查正反例能否被评分器正确区分。

本版的边界很明确：

- positive continuation 使用 `fixed loss`，必须让所有 case 通过。
- negative continuation 使用 `fixed only`，不能让任何 case 通过。
- 通过 dry-run 只能说明 suite 可用于下一步真实 replay，不能说明模型通过。

## 前置链路

本版接在：

- v897: 诊断 v803 中文 holdout 的 tokenizer coverage gap。
- v898: 构建 5 条 tokenizer-covered ASCII holdout prompts。

v899 是 v900 real replay 前的评分器自检。

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_dry_run.py`
  - 核心 dry-run 构建器。
  - 读取 v898 suite，提取 `fixed/loss` expected terms。
  - 对 positive/negative continuation 分别评分。
  - 输出 dry-run rows、checks、summary。

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_dry_run_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
  - HTML 展示 positive/negative case pass 和 hit terms。

- `scripts/dry_run_bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout.py`
  - CLI 入口。
  - 输入为 `--holdout-suite`。
  - 可覆盖 `--positive-continuation` 和 `--negative-continuation`。
  - `--require-dry-run-ready` 用于 gate。

- `tests/test_bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_dry_run.py`
  - 覆盖 dry-run pass、negative control 失效、source suite not ready、CLI/output。

- `e/899/解释/bounded-objective-loss-signal-bridge-target-only-memory-tokenizer-coverage-aware-holdout-dry-run/*`
  - v899 真实 dry-run 输出。

- `e/899/图片/v899-bounded-objective-loss-signal-bridge-target-only-memory-tokenizer-coverage-aware-holdout-dry-run.png`
  - Playwright MCP 截图证据。

## 核心数据结构

`dry_run_rows` 是本版主表：

- `case_id`
- `source_case_id`
- `expected_terms`
- `positive_continuation`
- `positive_case_pass`
- `positive_hit_terms`
- `positive_missed_terms`
- `negative_continuation`
- `negative_case_pass`
- `negative_hit_terms`
- `negative_missed_terms`

`summary` 汇总：

- `case_count`
- `positive_passed_case_count`
- `negative_passed_case_count`
- `negative_control_passed`
- `promotion_ready=False`
- `model_quality_claim=dry_run_only`
- `next_step=run_tokenizer_coverage_aware_holdout_real_replay`

## 核心函数

`build_tokenizer_coverage_aware_holdout_dry_run()` 是总入口：

1. 从 v898 report 中读取 `benchmark_suite`。
2. 提取 `scoring_contract.expected_terms`。
3. 调用 `_dry_run_rows()` 为每个 case 生成正反例评分行。
4. 调用 `_checks()` 确认 suite ready、case 存在、expected terms 是 `fixed/loss`、positive 全过、negative 全不过。
5. 调用 `_summary()` 输出 dry-run readiness。

`_score()` 是最小评分函数：

- continuation 中同时包含全部 expected terms 才算 pass。
- `fixed only` 只命中 `fixed`，缺 `loss`，因此必须 fail。

## 真实运行结果

v899 真实输出：

- `status=pass`
- `case_count=5`
- `positive_passed_case_count=5`
- `negative_passed_case_count=0`
- `negative_control_passed=False`
- `promotion_ready=False`
- `model_quality_claim=dry_run_only`
- `next_step=run_tokenizer_coverage_aware_holdout_real_replay`

这说明 v898 suite 的评分规则可用，可以进入真实 checkpoint replay。

## 测试覆盖

本版测试覆盖：

- 正常 dry-run：positive 全过、negative 全不过。
- negative control 错误：如果 negative continuation 也包含 `fixed loss`，dry-run 必须失败。
- source suite not ready：不能绕过 v898 readiness。
- 输出和 CLI：五类输出文件和命令行 gate 都可用。

这些测试保护了 v900 real replay 的前置条件：真实 replay 失败时，问题不应再归因于 scoring contract 本身。

## 截图与归档

本版运行证据放在：

- `e/899/解释/说明.md`
- `e/899/解释/bounded-objective-loss-signal-bridge-target-only-memory-tokenizer-coverage-aware-holdout-dry-run/`
- `e/899/图片/v899-bounded-objective-loss-signal-bridge-target-only-memory-tokenizer-coverage-aware-holdout-dry-run.png`

截图通过 Playwright MCP 打开本地 HTML 后生成。截图临时服务器已停止。

## 一句话总结

v899 证明 tokenizer-covered holdout suite 的评分规则能区分 `fixed loss` 与 `fixed only`，为 v900 真实模型 replay 清掉评分器变量。
