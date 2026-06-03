# v822 route promotion bounded real replay decoder anchor policy

## 本版目标和边界

v822 的目标是把 v821 的 decoder anchor probe 结果收束成一个可执行、可审计、带 guardrails 的 policy。它解决的是“probe 找到局部信号后，下一步怎么受控复验”的问题。

本版不运行新生成，也不把 policy 当作模型能力。policy 只是下一版 replay 的输入，且明确 `promotion_ready=False`。

## 前置路线

- v820 证明 prompt/corpus 覆盖已经存在，失败更像生成锚定问题。
- v821 用三种 anchor profile 跑 15 条 probe，发现 `objective-answer-check` 在两个 profile 下有 completion signal。
- v822 从 v821 probe rows 中选择最保守可复验的 policy row，并生成 guardrails。

## 关键文件

- `src/minigpt/model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy.py`
  - 核心 policy builder。
  - 读取 v821 probe，选择每个 case 的最短成功 anchor。
  - 生成 `policy_rows`、`uncovered_cases`、`guardrails`、`summary` 和 `interpretation`。

- `src/minigpt/model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 展示 policy rows 和 guardrails。

- `scripts/build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy.py`
  - CLI 入口。
  - 输入 `--decoder-anchor-probe`，输出 guarded policy。

- `tests/test_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy.py`
  - 覆盖最短 anchor 选择、无 completion signal 失败、CLI 输出。

- `e/822/解释/model-capability-route-promotion-bounded-real-replay-decoder-anchor-policy/`
  - v822 真实 policy 证据。

## 核心数据结构

`policy_rows` 是本版主产物。每行包含：

- `case_id`
  - 被 policy 覆盖的 bounded replay case。

- `profile_id`
  - 来自 v821 的成功 anchor profile。

- `anchor`
  - 实际要拼接到 prompt 后的 decoder anchor。

- `anchor_length`
  - 用于选择最短 anchor，避免过度人工干预。

- `completion_hit_terms`
  - 模型在 anchor 辅助下补全的 required terms。

- `claim_boundary`
  - 固定为 `anchor_assisted_only`。

- `recommended_use`
  - 固定为 `controlled_policy_replay_only`。

`guardrails` 明确三条限制：

- 不能当作 unassisted model capability。
- 当前覆盖是 partial coverage。
- 必须经过下一版 policy replay 复验。

## 核心函数

`build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy()` 是主入口：

1. 读取 v821 probe summary 和 probe rows。
2. 调用 `_policy_rows()` 从 completion-pass rows 中选出每个 case 的 policy。
3. 调用 `_uncovered_cases()` 标记没有成功 anchor 的 case。
4. 调用 `_guardrails()` 写入使用边界。
5. 调用 `_checks()` 确认 probe ready、probe rows 存在、至少有一个 completion signal。
6. 输出 policy summary 和 interpretation。

`_rank()` 是选择策略的核心：

- 优先选择 `new_text_pass=True` 的 row。
- 再选择 anchor 更短的 row。
- 最后按 profile id 稳定排序。

因此真实 v822 在 `prefix_fixed_space` 和 `prefix_fixed_l` 都成功时，选择了更短的 `prefix_fixed_space`。

## 真实运行结果

真实 CLI 输出：

```text
status=pass
decision=model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_ready_with_partial_coverage
policy_ready=True
policy_case_count=1
uncovered_case_count=4
coverage_is_partial=True
promotion_ready=False
next_step=run_decoder_anchor_policy_replay
```

真实 policy 只覆盖：

- `objective-answer-check`
- `profile_id=prefix_fixed_space`
- `anchor=fixed `
- `completion_hit_terms=["loss"]`

这证明 policy 是局部的、受控的，不是模型整体能力提升。

## 测试覆盖

本版新增 3 个 focused tests：

- 多个成功 profile 时选择最短可用 anchor。
- 没有 completion signal 时 policy fail。
- CLI 能定位 probe 目录并输出 JSON/CSV/TXT/MD/HTML。

测试保护的是 policy 边界：不能在没有成功 probe row 时生成空 policy，也不能把 partial coverage 误报成 promotion ready。

## 运行证据

证据目录：

- `e/822/解释/说明.md`
- `e/822/解释/model-capability-route-promotion-bounded-real-replay-decoder-anchor-policy/`
- `e/822/图片/v822-bounded-real-replay-decoder-anchor-policy-html.png`

Playwright MCP 已打开 HTML 并截图，页面显示 policy cases 1、uncovered 4、promotion False 和 guardrails。

## 一句话总结

v822 把 v821 的局部 anchor 信号整理成可复验 policy，同时把能力边界锁死在 anchor-assisted diagnostic 层。
