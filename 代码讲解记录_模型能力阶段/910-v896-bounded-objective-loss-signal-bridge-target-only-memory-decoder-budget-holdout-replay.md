# v896 decoder-budget holdout replay 代码讲解

## 本版目标与边界

v896 的目标是补上 v895 之后最关键的一道复核：v895 已经证明 v890 checkpoint 在 11-token decoder budget 下能恢复原三条 bounded objective contract，但这还不是模型泛化能力证明。本版把同一个 checkpoint 放回 v803 的 unchanged bounded holdout suite，检查它是否能在五条未改中文 prompt 上同时输出 `fixed` 与 `loss`。

本版不做新的训练，不修改 v803 suite，不调整 prompt，不放宽评分条件，也不把 constrained decoding 当作模型能力。它只给 v895 的 `run_unchanged_bounded_suite_holdout_replay` 下一步落一个可执行、可归档、可截图的证据入口。

## 前置链路

本版来自以下能力链：

- v803: 生成 bounded benchmark suite，五条 holdout prompt 均要求命中 `fixed/loss`。
- v804: suite review，确认 suite 可执行。
- v805: dry-run，确认评分器和 negative control 行为可检查。
- v890: 训练得到 stagnation-aware suffix checkpoint。
- v895: 在 `max_new_tokens=11` 下恢复原三条 objective contract，并明确要求 unchanged holdout replay。

因此 v896 的输入不是任意模型或任意 benchmark，而是“v895 source replay + v803/v804/v805 unchanged suite chain + v890 checkpoint/tokenizer”。

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_replay.py`
  - 本版核心构建器。
  - 负责读取 v895 source replay 的 summary，确认 `objective_contract_recovered=True`。
  - 复用 v806 的真实 replay runner 执行 v803 holdout suite。
  - 把结构执行状态、holdout 质量结果和 promotion 判断分开。

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_replay_artifacts.py`
  - 本版 JSON/TXT/CSV/Markdown/HTML 输出层。
  - TXT 用于命令行快速判断；HTML 用于截图；CSV/JSON 用于后续诊断消费。

- `scripts/run_bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_replay.py`
  - 本版 CLI。
  - 参数包含 `--decoder-budget-replay`、`--benchmark-suite`、`--suite-review`、`--dry-run`、`--checkpoint`、`--tokenizer`。
  - `--require-execution-pass` 只要求输入链和 replay 执行成功。
  - `--require-holdout-pass` 才要求 holdout 全部通过。

- `tests/test_bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_replay.py`
  - 覆盖 partial holdout、全通过 holdout、source replay 未恢复、CLI 输出四种路径。

- `e/896/解释/bounded-objective-loss-signal-bridge-target-only-memory-decoder-budget-holdout-replay/*`
  - 本版真实运行证据。
  - 使用 v890 checkpoint/tokenizer 和 unchanged v803/v804/v805 输入链生成。

- `e/896/图片/v896-bounded-objective-loss-signal-bridge-target-only-memory-decoder-budget-holdout-replay.png`
  - Playwright MCP 截图，证明 HTML report 可读且关键字段可见。

## 核心数据结构

`build_decoder_budget_holdout_replay()` 返回一个 report dict，关键字段如下：

- `status`
  - 表示本版输入链和真实 replay 是否结构通过。
  - holdout 没过不会让 `status` 失败；它会体现在 `promotion_ready=False`。

- `decision`
  - `...holdout_replay_passed_review_required`: holdout 全通过，但仍需 review。
  - `...holdout_replay_partial_model_gap`: replay 执行成功，但 holdout 只部分命中。
  - `...holdout_replay_zero_hit_model_gap`: replay 执行成功，但 holdout 完全未命中。
  - `fix_...holdout_replay_inputs`: 输入或执行失败。

- `source_decoder_budget_replay_summary`
  - v895 source replay 的 summary 快照。
  - 重点字段是 `objective_contract_recovered` 和 `next_step`。

- `replay_rows`
  - 来自真实 holdout suite 的逐 case 结果。
  - 每行包含 `case_id`、`continuation`、`hit_terms`、`missed_terms`、`case_pass`、`max_new_tokens`。

- `summary`
  - `source_objective_contract_recovered`: v895 是否真的恢复原 contract。
  - `holdout_model_route_quality_ready`: v803 holdout 是否全通过。
  - `passed_case_count`、`any_hit_case_count`、`zero_hit_case_count`: 细分模型表现。
  - `promotion_ready`: 只有 source recovered 且 holdout 全通过才为 true。
  - `model_quality_claim`: 本版允许的模型质量表述。

## 核心流程

1. CLI 定位四类输入：v895 source replay、v803 benchmark suite、v804 suite review、v805 dry-run。
2. `build_decoder_budget_holdout_replay()` 调用 v806 的 `build_model_capability_route_promotion_bounded_real_replay()`，用真实 checkpoint/tokenizer 执行五条 holdout case。
3. `_source_checks()` 确认 v895 的前置结论没有被跳过：source replay 必须结构 pass、comparison ready、contract recovered，并且 next step 必须指向 holdout replay。
4. `_hit_summary()` 统计 holdout replay 中至少命中一个 expected term 的 case 数，以及完全零命中的 case 数。
5. `_summary()` 决定 `promotion_ready`，但不把 holdout 模型缺口混同为输入失败。
6. artifacts 模块写出 JSON/CSV/TXT/Markdown/HTML，HTML 再由 Playwright MCP 截图归档。

## 真实运行结果

v896 的真实输出为：

- `status=pass`
- `decision=bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_replay_partial_model_gap`
- `source_objective_contract_recovered=True`
- `holdout_model_route_quality_ready=False`
- `passed_case_count=1`
- `failed_case_count=4`
- `any_hit_case_count=1`
- `zero_hit_case_count=4`
- `pass_rate=0.2`
- `promotion_ready=False`
- `model_quality_claim=objective_contract_recovered_holdout_failed`

五条 holdout case 中，只有 `objective-answer-check` 同时命中 `fixed` 和 `loss`。其余四条 prompt 产生大量 replacement 字符和杂散英文片段。这说明 v895 解决的是 decoder budget 截断问题，而不是中文 holdout prompt 上的泛化问题。

## 测试覆盖

本版测试保护了四个边界：

- partial runner: 执行成功但 holdout 不全过，`status=pass` 且 `promotion_ready=False`。
- passing runner: 五条 case 都命中 `fixed/loss` 时，才允许 `promotion_ready=True`。
- source replay 未恢复: 即使 holdout runner 可通过，也必须因为缺少 v895 前置恢复证据而失败。
- CLI/output: locators、JSON/TXT/Markdown/HTML 输出和 `--require-execution-pass` 行为都被覆盖。

这些测试的重点不是伪造“模型变好”，而是保护证据链不会把局部 contract 恢复误报成 route promotion。

## 截图与归档

本版运行证据放在 `e/896`：

- `e/896/解释/说明.md`
- `e/896/解释/bounded-objective-loss-signal-bridge-target-only-memory-decoder-budget-holdout-replay/`
- `e/896/图片/v896-bounded-objective-loss-signal-bridge-target-only-memory-decoder-budget-holdout-replay.png`

截图通过 Playwright MCP 打开本地 HTML 后生成。因为 MCP 阻止 `file://`，本版截图使用临时 `python -m http.server` 服务，截图完成后已停止。

## 一句话总结

v896 把 v895 的预算恢复成果放回 unchanged holdout suite 复核，证明当前模型只恢复局部 contract，还不能升级为可推广的 bounded route 能力。
