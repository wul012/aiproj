# v479：model capability rubric signal audit

## 本版目标和边界

v479 的目标是解释 v478 之后的剩余阻塞。v478 已经用两个 seed 证明 `case-token-cap=12` 可以稳定减少 token/shape stall，但 score-improved 和 pass-transition 仍然是 `0`。这说明下一步不该马上扩大模型，而应先看 cap 12 之后的失败主要落在哪些 rubric 和 data 信号上。

本版不重跑训练，不改模型参数，不调整 benchmark 规则，也不宣称模型能力提升。它是一个只读审计层：从 v478 的 token-budget stability report 出发，解析每个 seed 的 cap-12 stall diagnostic，再汇总剩余失败模式。

## 前置能力

本版承接两条前置链路：

- v478 的 `model_capability_token_budget_stability`
  - 提供 seed 级 token-budget probe 路径。
  - 证明 cap 12 的 token/shape relief 不是单 seed 偶然。
- v476/v477 的 `model_capability_stall_diagnostic`
  - 提供 prompt 级 `stall_reason`、`last_failed_checks`、`last_missing_terms` 和 generation preview 变化。

v479 不复制这些能力，只把它们聚合为一个“剩余 rubric 信号”审计入口。

## 关键新增文件

- `src/minigpt/model_capability_rubric_signal_audit.py`
  - 核心审计逻辑。
  - 支持输入 `model_capability_token_budget_stability.json` 或其目录。
  - 对每个 seed 读取 probe JSON，选择目标 token cap，加载对应 stall diagnostic。
  - 汇总 dominant failed checks、stall reasons、missing terms 和跨 seed 共同失败项。
- `src/minigpt/model_capability_rubric_signal_audit_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
  - CSV 保留 case 级审计行，HTML 用于 Playwright 截图确认。
- `scripts/audit_model_capability_rubric_signal.py`
  - CLI 入口。
  - 默认只读已有 evidence，不重跑 ladder/probe。
  - `--target-token-cap 12` 明确审计 v478 已稳定的 cap-12 结果。
- `tests/test_model_capability_rubric_signal_audit.py`
  - 覆盖 required-term 主导、默认选择最大 token cap、缺失输入失败、输出产物和进展分支。

## 核心数据结构

最终报告是：

```text
model_capability_rubric_signal_audit.json
```

关键字段：

- `seeds`
  - 每个 seed 一行。
  - 记录 probe 路径、diagnostic 路径、target token cap、case 数、persistent fail、preview changed 和 dominant checks。
- `cases`
  - 每个 prompt case 一行。
  - 保留 `stall_reason`、`last_failed_checks`、`last_missing_terms`、`score_delta`、`preview_changed` 和源 diagnostic 路径。
- `summary`
  - `dominant_failed_checks`：剩余失败的 check 频次。
  - `dominant_stall_reasons`：剩余阻塞原因频次。
  - `cross_seed_failed_checks`：所有 seed 都出现的 failed checks。
  - `decision`：将剩余阻塞归类为 required-term、generation unchanged、token shape residual 或人工复核。
- `interpretation`
  - 固定 `model_quality_claim=not_claimed`。
  - 给出下一步建议：先检查 required terms 和 tiny corpus coverage。

## v479 真实运行结果

真实输入：

```text
source=e/478/解释/model-capability-token-budget-stability
target-token-cap=12
seeds=1337,2026
```

结果：

```text
audit_decision=rubric_required_terms_dominate_flat_scores
case_count=20
score_improved_count=0
pass_transition_count=0
persistent_fail_count=2
preview_changed_count=8
top_failed_checks=must_include:20, task_shape:2
top_stall_reasons=generation_unchanged:11, required_terms_missing:5, case_passed:2, token_budget_or_shape_limit:2
cross_seed_failed_checks=must_include,task_shape
```

解释：cap 12 之后 token budget 已不是唯一主因。剩余 20 个 case 行里，`must_include` 每行都出现，说明当前 tiny 输出和 tiny corpus 覆盖很难满足标准中文 benchmark 的 required terms。还有 11 个 case 属于 generation unchanged，说明 tiny 训练步数和模型规模仍很弱。

## 测试覆盖

新增测试覆盖：

- 当两个 seed 的 cap-12 diagnostic 都被 `must_include` 主导时，报告必须输出 `rubric_required_terms_dominate_flat_scores`。
- 不指定 `--target-token-cap` 时，默认选择 seed probe 中最大的 token cap。
- 缺少 probe 或 diagnostic 时，报告必须失败，并指出 seed 输入不完整。
- 出现 score/pass progress 时，summary 必须转为 `some_rubric_progress_visible`。
- JSON/CSV/text/Markdown/HTML 五类输出必须全部生成。

这些测试保证 v479 是对既有证据的稳定只读审计，不会因为路径、token cap 或缺字段问题误判。

## 运行证据

运行证据位于：

```text
e/479/解释/model-capability-rubric-signal-audit/
e/479/图片/01-model-capability-rubric-signal-audit.png
e/479/解释/playwright-model-capability-rubric-signal-audit-snapshot.md
```

这些产物不是新训练结果，而是 v478 归档证据的二次解释层。它们适合作为 v480 是否要补数据覆盖、调整 benchmark prompt 或扩大训练预算的决策依据。

## 一句话总结

v479 把 cap-12 后的 flat score 定位到 required-term/data coverage/rubric 信号上，让下一步从“盲目扩模型”转向“先修评估输入和数据覆盖”。
