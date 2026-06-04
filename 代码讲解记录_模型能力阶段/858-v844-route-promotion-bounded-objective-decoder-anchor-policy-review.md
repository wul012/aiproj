# v844：bounded objective decoder anchor policy review

## 本版目标和边界

v844 的目标是给 v841-v843 的 decoder anchor 分支做一次收口判断。

边界：

- 不再继续重复证明 assisted anchor 能命中。
- 不训练新模型。
- 不把 policy replay success 当作能力提升。
- 不允许 route promotion。

v843 已经证明 policy replay 能通过 assisted anchors 命中 required terms，但 `new_text_pass_count=0`。这说明 anchor 是诊断工具，不是能力路线。v844 将这个判断写成可复核 review。

## 前置链路

输入只有 v843：

```text
e/843/解释/model-capability-route-promotion-bounded-objective-decoder-anchor-policy-replay/
```

v843 的关键结论是：

```text
policy_applied_pass_count=3
new_text_pass_count=0
promotion_ready=False
```

v844 的任务就是把这个结果转为下一步路线。

## 关键新增文件

- `src/minigpt/model_capability_route_promotion_bounded_objective_decoder_anchor_policy_review.py`
  - 读取 policy replay，抽取 signals，生成 recommendations、review、summary 和 interpretation。
- `src/minigpt/model_capability_route_promotion_bounded_objective_decoder_anchor_policy_review_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
- `scripts/review_model_capability_route_promotion_bounded_objective_decoder_anchor_policy.py`
  - CLI 入口，支持 `--require-review-ready` 和 `--require-branch-closed`。
- `tests/test_model_capability_route_promotion_bounded_objective_decoder_anchor_policy_review.py`
  - 覆盖 assisted-only path closure、出现 new-text recovery 时改走 holdout review、输出和 CLI。
- `e/844/解释/model-capability-route-promotion-bounded-objective-decoder-anchor-policy-review/`
  - 保存真实 review 产物。
- `e/844/图片/v844-bounded-objective-decoder-anchor-policy-review-html.png`
  - Playwright MCP 截图。

## 核心信号

review 会抽取这些信号：

```text
policy_replay_ready
policy_replay_success
case_count
policy_applied_case_count
policy_applied_pass_count
new_text_pass_count
promotion_ready
all_policy_cases_reproduced
unassisted_recovery_present
assisted_only_recovery
```

真实 v844 中：

```text
policy_applied_pass_count=3
new_text_pass_count=0
assisted_only_recovery=True
unassisted_recovery_present=False
```

这触发关闭 assisted anchor path。

## Recommendations

真实 recommendations 是：

- `close_assisted_anchor_path`
- `design_unassisted_objective_repair`
- `preserve_anchor_policy_as_diagnostic`

也就是说，锚点产物仍保留为诊断证据，但后续能力推进必须回到无锚点目标。

## 真实结果

```text
status=pass
decision=close_bounded_objective_decoder_anchor_policy_as_capability_path
bounded_objective_decoder_anchor_policy_review_ready=True
assisted_anchor_path_closed=True
selected_track=unassisted_objective_repair
promotion_ready=False
model_quality_claim=review_only
next_action=design_bounded_objective_unassisted_repair_plan
```

## 测试覆盖

测试覆盖：

- assisted-only replay 会关闭 anchor capability path。
- 如果出现 new-text recovery，则不会关闭，改走 holdout review。
- artifact writer 和 CLI 能输出完整产物。

focused pytest：

```text
3 passed
```

## 运行证据

真实命令：

```text
python scripts/review_model_capability_route_promotion_bounded_objective_decoder_anchor_policy.py --policy-replay e/843/解释/model-capability-route-promotion-bounded-objective-decoder-anchor-policy-replay --out-dir e/844/解释/model-capability-route-promotion-bounded-objective-decoder-anchor-policy-review --require-review-ready --require-branch-closed --force
```

HTML 截图：

```text
e/844/图片/v844-bounded-objective-decoder-anchor-policy-review-html.png
```

## 一句话总结

v844 把 decoder anchor 分支从“可复现的 assisted signal”收束为“诊断证据，不是能力路线”，下一步应设计无锚点 objective repair。
