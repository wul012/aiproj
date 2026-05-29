# v481：model capability required-term uptake audit

## 本版目标和边界

v481 的目标是回答 v480 之后更具体的问题：required terms 已经进入 tiny corpus 和 suite，那它们有没有在 archived tiny generation 中被模型生成出来？本版新增 required-term uptake audit，从 v480 的 coverage report 出发，回溯到 v478 的 `eval_suite.json`，逐词检查 prompt、expected behavior、generated 和 continuation 的命中。

本版不重训模型，不改采样配置，不扩大 benchmark，也不宣称模型能力提升。它是一个只读生成行为审计层，用来判断下一步应该做训练/解码 probe，还是继续数据覆盖检查。

## 前置能力

本版承接两条前置链路：

- v480 的 `model_capability_required_term_coverage`
  - 提供 106 个 case-term 缺失行。
  - 证明 49 个唯一 required terms 在 suite/tiny corpus 中全覆盖。
- v478 的 cap-12 ladder archives
  - 每个 seed 下都有 `max-iters-1` 和 `max-iters-4` 的 `run/eval_suite/eval_suite.json`。
  - 这些 eval-suite 文件保留 prompt、expected behavior、generated、continuation 和生成长度字段。

v481 不重新调用模型，只验证已有生成结果是否吸收了 required terms。

## 关键新增文件

- `src/minigpt/model_capability_required_term_uptake.py`
  - 核心审计逻辑。
  - 支持输入 `model_capability_required_term_coverage.json` 或其目录。
  - 对每个 term row 解析 `token_cap_root`，收集 `ladder/rungs/max-iters-*/run/eval_suite/eval_suite.json`。
  - 输出 generation observation 行，记录每个 term 在 prompt、expected、generated、continuation 中的出现次数。
- `src/minigpt/model_capability_required_term_uptake_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
  - HTML 用于 Playwright MCP 截图确认。
- `scripts/audit_model_capability_required_term_uptake.py`
  - CLI 入口。
  - 默认只读 v480/v478 evidence。
  - `--require-pass` 只检查审计结构完整，不把“模型没有生成 required terms”当成脚本失败。
- `tests/test_model_capability_required_term_uptake.py`
  - 覆盖 never-generated、last-rung partial generation、缺失 eval-suite、输出产物和路径定位。

## 核心数据结构

最终报告是：

```text
model_capability_required_term_uptake.json
```

关键字段：

- `source_rows`
  - 每个 token-cap root 一行。
  - 记录 eval-suite 数、max-iters 值和 result 总数。
- `observations`
  - 每个 case-term-rung 一行。
  - 记录 `term`、`max_iters`、`continuation_occurrences`、`generated_occurrences`、`prompt_occurrences`、`expected_occurrences` 和 continuation preview。
- `summary`
  - `generation_observation_count`：生成观察总数。
  - `continuation_hit_count`：required terms 在 continuation 中出现的次数。
  - `generated_hit_count`：required terms 在 generated 全文中出现的次数。
  - `prompt_hit_count`：required terms 已经在 prompt 中出现的次数。
  - `expected_hit_count`：required terms 在 expected behavior 中出现的次数。
  - `uptake_decision`：将结果归类为 never-generated、partial-generated、missing-observations 或 no-gap。
- `interpretation`
  - 固定 `model_quality_claim=not_claimed`。
  - 给出下一步 probe 建议，不把治理报告包装成模型能力成果。

## v481 真实运行结果

真实输入：

```text
source=e/480/解释/model-capability-required-term-coverage
resolved eval suites=e/478/解释/model-capability-token-budget-stability/seeds/*/token-cap-12/ladder/rungs/max-iters-*/run/eval_suite/eval_suite.json
```

结果：

```text
status=pass
uptake_decision=required_terms_never_generated
required_term_row_count=106
generation_observation_count=212
continuation_hit_count=0
generated_hit_count=0
prompt_hit_count=0
expected_hit_count=212
last_rung_continuation_hit_count=0
expected_only_unique_term_count=49
source_ready_count=2
```

解释：每个 required term 都能在 expected behavior 中找到，但两个 seed、两个 rung 的生成结果里没有任何一次把这些词带入 generated/continuation。当前 tiny 模型的输出更像字符级噪声或局部片段拼接，还没有表现出按 benchmark required terms 完成任务的能力。

## 测试覆盖

新增测试覆盖：

- 当 required term 从不进入 continuation 时，summary 必须输出 `required_terms_never_generated`。
- 当最新 rung 的 continuation 出现 required term 时，summary 必须转为 `last_rung_required_terms_partially_generated`。
- 缺少 archived eval-suite source 时，报告必须失败，并让 `--require-pass` 返回非零。
- JSON/CSV/text/Markdown/HTML 五类输出必须全部生成。
- 输入路径必须同时支持文件和目录。

这些测试保护了 v481 的边界：它只解释 archived generation uptake，不重跑训练，不绕过 v480 的 coverage 结论。

## 运行证据

运行证据位于：

```text
e/481/解释/model-capability-required-term-uptake/
e/481/图片/01-model-capability-required-term-uptake.png
e/481/解释/playwright-model-capability-required-term-uptake-snapshot.md
```

这些产物不是新模型能力结果，而是 v478-v480 证据链上的生成吸收审计。它们为下一步 targeted decoding/training probe 提供明确理由。

## 一句话总结

v481 证明 required terms 已经出现在数据和 expected behavior 中，但 archived tiny generation 一次都没有生成它们，把下一步明确指向定向训练/解码实验。
