# v842：bounded objective decoder anchor policy

## 本版目标和边界

v842 的目标是把 v841 的 decoder anchor probe 结果变成一个可执行、可审计、可 replay 的 policy。

本版边界：

- 不重新训练。
- 不重新采样 checkpoint。
- 不直接判定 objective contract recovered。
- 不把 injected anchor 当成 unassisted model capability。

v841 已经证明 `prefix_f`、`prefix_fixed_space`、`prefix_fixed_l` 这样的锚点能帮助 combined text 命中 `fixed/loss`，但 `new_text_pass_count=0`。因此 v842 只做控制面收敛：选 anchor、写 guardrails、给下一步 replay 一个明确输入。

## 前置链路

输入是 v841 的真实 probe：

```text
e/841/解释/model-capability-route-promotion-bounded-objective-decoder-anchor-probe/
```

v841 输出的关键信号是：

```text
probe_row_count=9
anchor_assisted_pass_count=9
completion_pass_count=9
new_text_pass_count=0
anchor_completion_success=True
promotion_ready=False
```

v842 只消费 `probe_rows`，不会重新解释训练 loss 或 corpus 质量。

## 关键新增文件

- `src/minigpt/model_capability_route_promotion_bounded_objective_decoder_anchor_policy.py`
  - 从 probe rows 中选择每个 case 的 winning anchor，生成 policy rows、uncovered cases、guardrails 和 summary。
- `src/minigpt/model_capability_route_promotion_bounded_objective_decoder_anchor_policy_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
- `scripts/build_model_capability_route_promotion_bounded_objective_decoder_anchor_policy.py`
  - CLI 入口，支持目录输入、`--require-policy-ready` 和 `--force`。
- `tests/test_model_capability_route_promotion_bounded_objective_decoder_anchor_policy.py`
  - 覆盖最短 anchor 选择、无 completion signal 失败、输出和 CLI。
- `e/842/解释/model-capability-route-promotion-bounded-objective-decoder-anchor-policy/`
  - 保存真实 policy 产物。
- `e/842/图片/v842-bounded-objective-decoder-anchor-policy-html.png`
  - Playwright MCP 截图。

## 核心数据结构

### policy row

每条 policy row 包含：

```text
case_id
profile_id
anchor
anchor_length
completion_hit_terms
new_text_hit_terms
combined_preview
policy_type
claim_boundary
recommended_use
```

`policy_type` 固定为：

```text
case_specific_bounded_objective_decoder_anchor
```

`claim_boundary` 固定为：

```text
decoder_anchor_signal_only
```

这两个字段是给后续 replay 和审计看的：policy 不是“模型学会了”的证据，只是“如何复现锚点补齐信号”的受控配置。

## 选择规则

policy builder 会对同一个 case 的多个 successful probe row 做排序：

```text
new_text_pass 优先
anchor_length 越短越优先
profile_id 字典序兜底
```

由于 v841 的真实结果里 `new_text_pass` 都是 False，排序会优先选择最短锚点。真实 v842 因此能为每个 case 选择 `prefix_f`，这代表模型补出的内容更多，policy 也更保守可解释。

## Guardrails

v842 写入四条 guardrails：

- `not_unassisted_model_capability`
  - injected anchors 不能算普通模型能力。
- `requires_policy_replay`
  - policy 必须被下一版 replay。
- `substring_scoring_not_final_exactness`
  - required-term substring hit 不是最终 exact contract 证明。
- `policy_coverage`
  - 记录 policy 覆盖了几个 case、剩余几个 uncovered。

这些 guardrails 的作用是防止后续把 policy 产物越权使用。

## 真实结果

```text
status=pass
decision=model_capability_route_promotion_bounded_objective_decoder_anchor_policy_ready
bounded_objective_decoder_anchor_policy_ready=True
policy_case_count=3
uncovered_case_count=0
coverage_is_partial=False
promotion_ready=False
model_quality_claim=decoder_anchor_policy_only
next_action=run_bounded_objective_decoder_anchor_policy_replay
```

这说明 v841 的三个 objective cases 都能形成 policy row，但这仍只是 replay 前的配置产物。

## 测试覆盖

测试覆盖三类关键风险：

- 从多个 successful profiles 中选择最短 successful anchor。
- 如果没有 completion signal，policy 失败并返回非零 exit code。
- artifact writer 和 CLI 能输出 JSON、CSV、TXT、Markdown、HTML。

本版 focused pytest 结果：

```text
3 passed
```

## 运行证据

真实命令：

```text
python scripts/build_model_capability_route_promotion_bounded_objective_decoder_anchor_policy.py --decoder-anchor-probe e/841/解释/model-capability-route-promotion-bounded-objective-decoder-anchor-probe --out-dir e/842/解释/model-capability-route-promotion-bounded-objective-decoder-anchor-policy --require-policy-ready --force
```

HTML 截图：

```text
e/842/图片/v842-bounded-objective-decoder-anchor-policy-html.png
```

## 链路角色

v842 的角色是“policy builder”：

- 上游：v841 decoder anchor probe。
- 下游：v843 decoder anchor policy replay。
- 当前能力：把锚点信号变成可执行 policy。
- 当前限制：不提供模型晋级结论。

## 一句话总结

v842 把 v841 的 assisted decoder signal 收敛成 3-case replay-only policy，并用 guardrails 明确阻止能力越权，为下一步真实 policy replay 铺路。
