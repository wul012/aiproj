# v537 required-term pair colon-immediate missed-seed diagnostic 代码讲解

## 本版目标和边界

v536 的三 seed 复验只有 `535` 达到 pair-full，`1535` 和 `2535` 没有复现。v537 的目标是解释这个差异：missed seed 是不是已经把 `fixed/loss` 的首 token 学对，只是在后续 continuation 里失败。

本版不重新训练，不调整 corpus，不宣称模型能力提升。它只读取 v536 stability JSON，复用已有 first-token preference 诊断，为每个 seed 生成 sidecar 证据。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic.py`
  - 核心 builder，读取 v536 的 `seed_rows` 和 `seed_reports`，逐 seed 调用 first-token diagnostic。
- `src/minigpt/model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML，并写出每个 seed 的 first-token sidecar。
- `scripts/run_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic.py`
  - CLI 入口，接受 v536 JSON 或输出目录。
- `tests/test_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic.py`
  - 用 fake scorer 覆盖 missed-after-top-token、first-token-gap、缺失 seed report 和 sidecar 输出。
- `e/537/解释/model-capability-required-term-pair-colon-immediate-missed-seed-diagnostic/`
  - 保存真实 v536 checkpoint 的只读诊断报告。

## 核心数据结构

顶层报告包含：

- `source_pair_colon_immediate_stability`：指向 v536 stability JSON。
- `seed_rows`：每个 seed 的汇总行。
- `first_token_reports`：每个 seed 的 first-token 诊断原始报告。
- `summary`：跨 seed 判断 missed seed 的原因。

每个 `seed_rows` 行记录：

- `pair_full_observed`：v536 refresh 是否达到 pair-full。
- `first_token_decision`：当前 seed 的 first-token 诊断结论。
- `expected_top_count / term_count`：`fixed/loss` 首 token 是否都排第一。
- `fixed_expected_rank`、`loss_expected_rank`：两个目标词首 token 的排名。
- `fixed_top_token`、`loss_top_token`：当前 prompt 下模型最偏好的首 token。
- `observed_continuation_hit_count`：v536 replay 中命中的 continuation 数量。

## 运行流程

`build_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic()` 的流程是：

1. 从 v536 stability report 读取 `seed_rows`。
2. 从嵌入的 `seed_reports` 按 `settings.seed` 建索引。
3. 对每个 seed 调用 `build_model_capability_required_term_pair_first_token_preference()`。
4. 抽取 fixed/loss 的 rank、top token、expected-top 计数。
5. 汇总 missed seed 是否都已经 expected-top。

如果 missed seed 也都 expected-top，说明问题更可能在第二 token 或更长 continuation；如果 missed seed 的 expected-top 不满，则先处理首 token 偏好。

## 真实结果

真实 v537 结果：

```text
decision=required_term_pair_colon_immediate_first_token_gap
missed_seed_count=2
missed_expected_top_count=0
missed_first_token_gap_count=2
```

seed 明细：

```text
535  -> fixed rank=1, loss rank=1
1535 -> fixed rank=2, loss rank=2
2535 -> fixed rank=1, loss rank=2
```

这说明 v536 的不稳定不是单纯的 continuation 问题；至少两个 missed seed 的 first-token 偏好还没稳定。

## 测试覆盖

单测覆盖：

- missed seed 的 expected token 已经全部 top-ranked，decision 应指向后续 continuation。
- missed seed 仍有 first-token gap，decision 应指向 first-token preference。
- v536 report 缺少 embedded `seed_reports` 时失败。
- 输出 writer 生成主报告和每个 seed 的 first-token sidecar。

真实证据由 `e/537` 的 PyTorch checkpoint 只读诊断覆盖，截图通过 Playwright MCP 生成。

## 链路角色

v537 是 v536 后的定位层：它把 partial stability 的原因拆成首 token 和 continuation 两类，并用真实 checkpoint logits 给出下一步方向。它不是新治理链，而是模型能力路线里的诊断闭环。

一句话总结：v537 把 colon-immediate missed seeds 的主要问题定位为 first-token 偏好不足。
