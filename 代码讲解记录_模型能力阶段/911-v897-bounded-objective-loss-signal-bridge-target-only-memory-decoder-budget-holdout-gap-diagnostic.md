# v897 holdout gap diagnostic 代码讲解

## 本版目标与边界

v897 的目标是解释 v896 的真实 holdout 失败，而不是继续盲目训练。v895 已经证明 11-token decoder budget 能让 v890 checkpoint 在原三条 bounded objective contract 上输出 `fixed loss`；v896 则显示 unchanged v803 holdout suite 只有 1/5 通过。v897 要回答的是：这 4/5 失败到底是训练不足、prompt surface 未见过，还是 tokenizer 本身无法覆盖中文 prompt。

本版不修改 v803 suite，不重新 replay，不重新训练，也不做模型能力提升声明。它是诊断版，只读取已经归档的 v896 replay、v890 tokenizer 和 v890 prepared corpus。

## 前置链路

本版接在以下证据之后：

- v890: 训练产物，包含 `checkpoint.pt`、`tokenizer.json` 和 `prepared_corpus.txt`。
- v895: decoder-budget replay，证明原 contract 在 `max_new_tokens=11` 时恢复。
- v896: unchanged holdout replay，证明 holdout 只有 1/5 通过，promotion 被阻断。

v897 的价值在于把 v896 的失败拆成可行动的分类，而不是只留下“模型没过”这个粗结论。

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap_diagnostic.py`
  - 核心诊断构建器。
  - 读取 v896 replay rows，并加载 v890 tokenizer/corpus。
  - 对每条 holdout prompt 计算 unknown 字符数量、unknown rate、是否出现在 corpus、continuation replacement 字符数量和 failure class。

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap_diagnostic_artifacts.py`
  - 输出层，写 JSON/CSV/TXT/Markdown/HTML。
  - HTML 把 dominant gap、unknown token、replacement rows 和每条 case 的分类展示出来，用于截图和复核。

- `scripts/diagnose_bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap.py`
  - CLI 入口。
  - 输入为 `--holdout-replay`、`--tokenizer`、`--training-corpus`。
  - `--require-diagnostic-ready` 只要求诊断输入完整，不要求模型通过。

- `tests/test_bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap_diagnostic.py`
  - 覆盖 tokenizer coverage gap、unseen prompt surface gap、source report fail、CLI/output。

- `e/897/解释/bounded-objective-loss-signal-bridge-target-only-memory-decoder-budget-holdout-gap-diagnostic/*`
  - v897 真实诊断输出。

- `e/897/图片/v897-bounded-objective-loss-signal-bridge-target-only-memory-decoder-budget-holdout-gap-diagnostic.png`
  - Playwright MCP 截图证据。

## 核心数据结构

`diagnostic_rows` 是本版的主表，每行对应 v896 的一条 holdout replay row：

- `case_id`: holdout case 名称。
- `case_pass`: v896 replay 是否通过。
- `prompt_char_count`: prompt 字符长度。
- `prompt_unknown_count`: prompt 中不在 tokenizer 词表里的字符数量。
- `prompt_unknown_rate`: unknown 字符占比。
- `prompt_unknown_chars`: 具体 unknown 字符集合。
- `prompt_exact_in_corpus`: prompt 是否原样出现在 v890 prepared corpus。
- `expected_terms_missing_from_corpus`: `fixed/loss` 是否缺失于训练 corpus。
- `continuation_replacement_count`: continuation 中 `�` 的数量。
- `hit_terms` / `missed_terms`: v896 评分命中和漏掉的 required terms。
- `failure_class`: 本版诊断分类。

`summary` 汇总关键判断：

- `dominant_gap`: 主导缺口。
- `tokenizer_prompt_coverage_gap_count`: 因 tokenizer coverage 失败的 case 数。
- `prompt_unknown_row_count`: prompt 含 unknown 字符的行数。
- `prompt_unknown_token_count`: 总 unknown 字符数。
- `continuation_replacement_row_count`: continuation 里出现 `�` 的行数。
- `promotion_ready`: 诊断版固定为 false，不做 promotion。
- `next_step`: 下一步建议。

## 核心函数

`build_decoder_budget_holdout_gap_diagnostic()` 是总入口：

1. 定位并加载 tokenizer 与 training corpus。
2. 读取 v896 `replay_rows`。
3. 调用 `_diagnostic_rows()` 逐 case 诊断。
4. 调用 `_checks()` 确认 source report、tokenizer、corpus 和 rows 都存在。
5. 调用 `_summary()` 统计主导缺口和下一步。
6. 生成解释型 report。

`_diagnostic_rows()` 是核心逻辑：

- 通过 `tokenizer.stoi` 得到词表。
- 逐字符检查 prompt 是否在词表里。
- 检查 prompt 是否原样出现在 prepared corpus。
- 检查 expected terms 是否在 corpus。
- 统计 continuation 中的 replacement 字符。
- 调用 `_failure_class()` 给失败分类。

`_failure_class()` 的顺序很重要：

1. 已通过的 case 标为 `passed`。
2. 未通过且 prompt 有 unknown 字符，标为 `tokenizer_prompt_coverage_gap`。
3. 未通过且 prompt 未出现在 corpus，标为 `holdout_prompt_unseen_surface_gap`。
4. corpus 缺 required terms，标为 `training_corpus_required_term_gap`。
5. 以上都不是，才标为 `required_term_generation_gap`。

这个顺序体现了工程判断：如果 tokenizer 连 prompt 都无法表达，继续解释为“模型不会生成 loss”就太粗糙。

## 真实运行结果

v897 真实结果：

- `dominant_gap=tokenizer_prompt_coverage_gap`
- `case_count=5`
- `passed_case_count=1`
- `tokenizer_prompt_coverage_gap_count=4`
- `prompt_unknown_row_count=5`
- `prompt_unknown_token_count=96`
- `continuation_replacement_row_count=5`
- `promotion_ready=False`
- `next_step=build_tokenizer_coverage_aware_holdout_suite_before_more_training`

这说明 v803 holdout suite 和 v890 tokenizer/corpus 没有对齐：v890 tokenizer 是 49 字符的 char tokenizer，没有中文字符；v803 prompts 大量使用中文任务描述，所以 replay 里出现大量 `�`。

## 测试覆盖

本版测试覆盖四条链路：

- 中文 prompt + 英文 tokenizer 时，诊断为 `tokenizer_prompt_coverage_gap`。
- prompt 都在 tokenizer 词表里但不在 corpus 时，诊断为 `holdout_prompt_unseen_surface_gap`。
- source holdout report 结构失败时，诊断必须失败。
- CLI 和五类输出文件都能生成。

这些测试保护的是诊断边界：不要把 tokenizer/suite 不匹配误判成训练不足，也不要让诊断版绕过 source report 的结构失败。

## 截图与归档

本版运行证据放在：

- `e/897/解释/说明.md`
- `e/897/解释/bounded-objective-loss-signal-bridge-target-only-memory-decoder-budget-holdout-gap-diagnostic/`
- `e/897/图片/v897-bounded-objective-loss-signal-bridge-target-only-memory-decoder-budget-holdout-gap-diagnostic.png`

截图通过 Playwright MCP 打开本地 HTML 后生成。截图临时服务器已停止。

## 一句话总结

v897 把 v896 的 4/5 holdout 失败归因到 tokenizer prompt coverage gap，避免继续盲训，并把下一步收敛到 tokenizer-coverage-aware holdout suite。
