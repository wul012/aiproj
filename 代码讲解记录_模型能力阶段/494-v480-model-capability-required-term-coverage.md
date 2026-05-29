# v480：model capability required-term coverage audit

## 本版目标和边界

v480 的目标是复核 v479 的核心阻塞：cap-12 之后 `must_include` 仍然主导失败，但这些 required terms 到底是没有进入 tiny corpus，还是进入了数据却没有被 tiny 模型稳定生成？本版新增一个只读 coverage audit，从 v479 的 rubric signal audit 回溯到 v478 的 cap-12 suite 和 tiny corpus，逐词统计覆盖情况。

本版不重训模型，不调整 prompt suite，不修改评分规则，也不宣称模型能力提升。它只回答一个更窄的问题：v479 中生成缺失的 required terms 是否在归档训练材料里可见。

## 前置能力

本版承接三层已有证据：

- v478 的 `model_capability_token_budget_stability`
  - 提供两个 seed 的 cap-12 token budget 归档。
  - 每个 seed 下都有 ladder rungs、standard suite 和 tiny corpus。
- v479 的 `model_capability_rubric_signal_audit`
  - 提供 case 级 `last_missing_terms`、`last_failed_checks` 和 `source_diagnostic`。
  - 判断剩余 flat score 被 required-term rubric 信号主导。
- v476/v477 的 stall diagnostic
  - 提供每个 case 的 prompt 失败原因和源 diagnostic 路径。

v480 不复制训练链路，只把这些路径重新串起来检查数据覆盖。

## 关键新增文件

- `src/minigpt/model_capability_required_term_coverage.py`
  - 核心审计逻辑。
  - 支持输入 `model_capability_rubric_signal_audit.json` 或其目录。
  - 对每个 case 的 `source_diagnostic` 回溯到 `token-cap-12` 根目录。
  - 收集 `ladder/rungs/max-iters-*/standard-zh-capped-suite.json` 和 `tiny_corpus.txt`。
  - 对 `last_missing_terms` 逐词统计 suite/corpus 出现次数。
- `src/minigpt/model_capability_required_term_coverage_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
  - CSV 保留 term row，HTML 用于 Playwright MCP 截图。
- `scripts/audit_model_capability_required_term_coverage.py`
  - CLI 入口。
  - 默认只读已有 evidence。
  - `--require-pass` 只要求审计结构完整；候选模型没有提升不算本 CLI 失败。
- `tests/test_model_capability_required_term_coverage.py`
  - 覆盖全覆盖、混合覆盖、缺源失败、输出产物、路径定位和空行 summary。

## 核心数据结构

最终报告是：

```text
model_capability_required_term_coverage.json
```

关键字段：

- `source_rows`
  - 每个 `source_diagnostic` 一行。
  - 记录 token cap 根目录、suite 数、corpus 数、suite case 数和字符数。
- `term_rows`
  - 每个 case missing term 一行。
  - 记录 `term`、`covered_in_corpus`、`covered_in_suite`、`corpus_occurrences`、`suite_occurrences`、prompt/expected 出现次数和源路径。
- `summary`
  - `missing_term_row_count`：case-term 总行数。
  - `unique_missing_term_count`：唯一 required term 数。
  - `corpus_missing_term_row_count`：corpus 中完全找不到的 term row 数。
  - `corpus_missing_unique_terms`：corpus 缺失的唯一词。
  - `coverage_decision`：将覆盖结论分为 present-but-not-generated、mixed、absent 或 no-gap。
- `interpretation`
  - 固定 `model_quality_claim=not_claimed`。
  - 只给出下一步排查方向，不把治理报告包装成模型能力结论。

## v480 真实运行结果

真实输入：

```text
source=e/479/解释/model-capability-rubric-signal-audit
resolved sources=e/478/解释/model-capability-token-budget-stability/seeds/*/token-cap-12
```

结果：

```text
status=pass
coverage_decision=required_terms_present_but_not_generated
missing_term_row_count=106
unique_missing_term_count=49
corpus_covered_term_row_count=106
corpus_missing_term_row_count=0
suite_covered_term_row_count=106
suite_missing_term_row_count=0
source_ready_count=2
source_missing_count=0
```

解释：v479 中 106 个 case-term 缺失行、49 个唯一缺失词，在两个 seed 的 cap-12 suite 和 tiny corpus 中全部可见。也就是说，当前 flat score 不能简单归因为“数据里没有 required terms”。更准确的判断是：tiny 数据里有词，但 tiny 模型在短训练预算和当前采样下没有稳定生成这些词。

## 测试覆盖

新增测试保护了以下边界：

- 当所有 missing terms 都在 corpus 里出现时，summary 必须输出 `required_terms_present_but_not_generated`。
- 当只有部分词在 corpus 中出现时，summary 必须输出 `mixed_required_term_coverage`，并列出缺失的唯一词。
- 当 `source_diagnostic` 无法解析到归档材料时，报告必须失败，`--require-pass` 返回非零。
- 输出函数必须生成 JSON/CSV/text/Markdown/HTML 五类产物。
- 路径定位函数必须同时接受文件和目录输入。

这些测试保证 v480 只是稳定复核归档材料，不会因为路径形态、缺字段或输出格式问题误判。

## 运行证据

运行证据位于：

```text
e/480/解释/model-capability-required-term-coverage/
e/480/图片/01-model-capability-required-term-coverage.png
e/480/解释/playwright-model-capability-required-term-coverage-snapshot.md
```

这些产物不是新训练结果，而是 v478-v479 归档证据的 coverage 解释层。它们适合作为下一步是否调整训练预算、采样策略、数据重复方式或 benchmark required terms 的依据。

## 一句话总结

v480 证明 required terms 已进入 tiny corpus，但没有稳定进入生成输出，把下一步从“补数据是否缺词”推进到“检查 tiny 训练和生成行为为什么学不出来”。
