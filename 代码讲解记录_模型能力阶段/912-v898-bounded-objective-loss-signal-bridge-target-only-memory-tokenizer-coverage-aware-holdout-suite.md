# v898 tokenizer-coverage-aware holdout suite 代码讲解

## 本版目标与边界

v898 的目标是修正 v896/v897 暴露出来的评估口径问题。v897 已经证明 v803 中文 holdout prompt 与 v890 tokenizer 不对齐：5 条 prompt 都有 unknown 字符，4 条失败直接归因为 `tokenizer_prompt_coverage_gap`。因此，继续用这组中文 prompt 判断 v890 checkpoint 的 route 能力并不公平。

本版不训练模型，不运行 replay，不降低 `fixed/loss` 评分目标。它只构建一个 tokenizer-coverage-aware holdout suite：保留 5 条 case、保留 expected terms、保留 bounded scope，但把 prompt surface 改成 v890 tokenizer 能完整表达的 ASCII prompt。

## 前置链路

本版接在以下证据之后：

- v803: 原始 bounded benchmark suite，包含 5 条中文/混合 prompt。
- v890: 真实训练 checkpoint 和 49 字符 char tokenizer。
- v896: unchanged holdout replay 只有 1/5 通过。
- v897: 诊断出 dominant gap 是 tokenizer prompt coverage gap。

v898 的定位是“评估输入修复”，不是“模型能力提升”。

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite.py`
  - 核心 suite 构建器。
  - 读取 v897 diagnostic、v803 source suite 和 v890 tokenizer。
  - 生成 5 条 tokenizer-covered candidate cases。
  - 校验所有 candidate prompt 的 unknown token 数为 0。

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
  - HTML 展示每条 candidate case 的 source case、coverage 和 prompt。

- `scripts/build_bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite.py`
  - CLI 入口。
  - 输入为 `--holdout-gap-diagnostic`、`--source-benchmark-suite`、`--tokenizer`。
  - `--require-suite-ready` 用于 CI/本地 gate。

- `tests/test_bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite.py`
  - 覆盖 suite ready、diagnostic next step 错误、candidate prompt 不被 tokenizer 覆盖、CLI/output。

- `e/898/解释/bounded-objective-loss-signal-bridge-target-only-memory-tokenizer-coverage-aware-holdout-suite/*`
  - v898 真实 suite 输出。

- `e/898/图片/v898-bounded-objective-loss-signal-bridge-target-only-memory-tokenizer-coverage-aware-holdout-suite.png`
  - Playwright MCP 截图证据。

## 核心数据结构

本版 report 包含两个核心表。

`benchmark_suite` 是可被后续 dry-run/replay 消费的 suite：

- `suite_name=route-promotion-objective-level-contrast-tokenizer-coverage-aware-holdout-suite`
- `suite_version=v898`
- `boundary=ascii_tokenizer_coverage_aware_holdout_only`
- `model_quality_claim=not_claimed`
- `scoring_contract.expected_terms=["fixed", "loss"]`
- `cases`: 5 条 candidate case。

每条 case 包含：

- `case_id`: 新 case id。
- `source_case_id`: 对应 v803 原 case。
- `prompt_case`: 标准 `PromptCase.to_dict()` 输出。
- `expected_terms`: 仍是 `fixed/loss`。
- `required_term_count`: 2。

`coverage_rows` 是覆盖检查表：

- `case_id`
- `source_case_id`
- `prompt_char_count`
- `prompt_unknown_count`
- `prompt_unknown_rate`
- `prompt_unknown_chars`
- `tokenizer_covered`

## 核心函数

`build_tokenizer_coverage_aware_holdout_suite()` 是总入口：

1. 加载 v897 diagnostic，确认它要求进入 tokenizer-coverage-aware suite。
2. 加载 v803 source suite，读取原 case count 和 scoring contract。
3. 加载 v890 tokenizer。
4. 调用 `_candidate_cases()` 生成 5 条 ASCII prompt cases。
5. 调用 `_coverage_rows()` 逐 prompt 检查 unknown 字符。
6. 调用 `_checks()` 确认 source、diagnostic、case count 和 tokenizer coverage 全部通过。
7. 写出新的 `benchmark_suite` 和 summary。

`_candidate_cases()` 生成的 5 条 prompt 是：

- `answer with exactly two words: fixed loss\nanswer:`
- `return the two target words fixed loss\noutput:`
- `contrast route result fixed loss\nresult:`
- `jsonish answer_terms fixed loss\nanswer_terms:`
- `self check requires fixed and loss\nfinal answer:`

这些 prompt 只使用 v890 tokenizer 覆盖的字符，避免 v803 中文 prompt 带来的 `<unk>` 问题。

## 真实运行结果

v898 真实结果：

- `status=pass`
- `candidate_case_count=5`
- `tokenizer_covered_case_count=5`
- `candidate_prompt_unknown_token_count=0`
- `source_prompt_unknown_row_count=5`
- `source_prompt_unknown_token_count=96`
- `expected_terms=["fixed", "loss"]`
- `promotion_ready=False`
- `model_quality_claim=suite_construction_only`
- `next_step=run_tokenizer_coverage_aware_holdout_dry_run`

这说明新 suite 已经把 tokenizer 覆盖问题从评估输入中去掉，但还没有证明模型能通过这些 prompt。

## 测试覆盖

本版测试保护四个关键边界：

- 正常路径：候选 prompt 全部被 tokenizer 覆盖，suite ready。
- 错误路由：如果 v897 diagnostic 没有指向 tokenizer coverage suite，则不能构建。
- 词表不足：如果 tokenizer 不覆盖候选 prompt，suite 必须失败。
- 输出闭环：CLI 和五类输出文件全部可用。

这些测试避免 v898 变成“随手写一组 prompt”的文档版本，而是保证它确实解决 v897 指出的 tokenizer 覆盖问题。

## 截图与归档

本版运行证据放在：

- `e/898/解释/说明.md`
- `e/898/解释/bounded-objective-loss-signal-bridge-target-only-memory-tokenizer-coverage-aware-holdout-suite/`
- `e/898/图片/v898-bounded-objective-loss-signal-bridge-target-only-memory-tokenizer-coverage-aware-holdout-suite.png`

截图通过 Playwright MCP 打开本地 HTML 后生成。截图临时服务器已停止。

## 一句话总结

v898 把 v897 的 tokenizer coverage gap 收敛成一套 tokenizer-covered holdout suite，为下一步公平 dry-run/replay 铺好输入边界。
