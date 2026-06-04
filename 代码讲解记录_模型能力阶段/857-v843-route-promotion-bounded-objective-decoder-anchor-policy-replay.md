# v843：bounded objective decoder anchor policy replay

## 本版目标和边界

v843 的目标是运行 v842 生成的 decoder anchor policy，确认它是否能在真实 checkpoint 上复现 v841 的 assisted completion signal。

本版不做：

- 不新增训练。
- 不改 policy。
- 不改 objective contract。
- 不宣称 unassisted model capability。

v842 只是生成了 policy rows；v843 才是第一次把这些 policy rows 应用回真实 replay cases。

## 前置链路

v843 消费三类输入：

- v839 replay comparison：原始 objective replay cases。
- v842 decoder anchor policy：每个 case 的 selected anchor。
- v838 training run：checkpoint 和 tokenizer。

这里没有使用新语料，也没有换模型，因此 v843 是一个纯复核版本。

## 关键新增文件

- `src/minigpt/model_capability_route_promotion_bounded_objective_decoder_anchor_policy_replay.py`
  - 读取 replay comparison 和 policy，按 case 绑定 anchor，调用 generator，生成 replay rows、summary 和 interpretation。
- `src/minigpt/model_capability_route_promotion_bounded_objective_decoder_anchor_policy_replay_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
- `scripts/run_model_capability_route_promotion_bounded_objective_decoder_anchor_policy_replay.py`
  - CLI 入口，支持 checkpoint/tokenizer、目录输入、`--require-replay-ready` 和 `--require-policy-case-pass`。
- `tests/test_model_capability_route_promotion_bounded_objective_decoder_anchor_policy_replay.py`
  - 覆盖 assisted signal replay、无 policy rows 失败、输出和 CLI。
- `e/843/解释/model-capability-route-promotion-bounded-objective-decoder-anchor-policy-replay/`
  - 保存真实 policy replay 产物。
- `e/843/图片/v843-bounded-objective-decoder-anchor-policy-replay-html.png`
  - Playwright MCP 截图证据。

## 关键实现点

### seed offset 复用

v841 probe 运行时每个 profile 有固定 seed offset：

```text
prefix_f           -> 1100
prefix_fixed_space -> 1200
prefix_fixed_l     -> 1300
```

v842 policy row 只保存了 `profile_id` 和 `anchor`，没有保存 `seed_offset`。v843 因此在 replay module 内定义同一套 `PROFILE_SEED_OFFSETS`，用来复现同一类 decoder anchor 条件。

这样做的目的不是扩大成功率，而是让 policy replay 与 probe 的生成条件可对齐。

### replay row

每条 replay row 包含：

```text
case_id
policy_applied
profile_id
anchor
continuation
combined
required_terms
combined_hit_terms
new_text_hit_terms
missed_terms
case_pass
new_text_pass
seed
max_new_tokens
temperature
top_k
```

这里继续区分：

- `case_pass`：`anchor + continuation` 命中全部 required terms。
- `new_text_pass`：只看 continuation 自身是否命中全部 required terms。

v843 的真实结果是 `case_pass=3`，但 `new_text_pass=0`，所以 assisted signal 复现了，普通生成仍未恢复。

## 真实结果

```text
status=pass
decision=model_capability_route_promotion_bounded_objective_decoder_anchor_policy_replay_reproduced_assisted_signal
bounded_objective_decoder_anchor_policy_replay_ready=True
passed_case_count=3
policy_applied_case_count=3
policy_applied_pass_count=3
new_text_pass_count=0
policy_replay_success=True
promotion_ready=False
model_quality_claim=decoder_anchor_policy_replay_only
next_action=review_bounded_objective_decoder_anchor_policy_replay
```

这说明：

- v842 policy 不是空配置，确实能复现 assisted required-term hits。
- 但它没有改变无锚点 replay 失败的事实。
- 下一步应该做 review，判断 policy 是否值得进入训练策略或是否应关闭该分支。

## 测试覆盖

测试覆盖：

- policy replay 能复现 assisted signal，但 `promotion_ready=False`。
- policy rows 缺失时失败。
- artifact writer 和 CLI 输出 JSON、CSV、TXT、Markdown、HTML。

focused pytest 结果：

```text
3 passed
```

## 运行证据

真实命令：

```text
python scripts/run_model_capability_route_promotion_bounded_objective_decoder_anchor_policy_replay.py --replay-comparison e/839/解释/model-capability-route-promotion-bounded-objective-replay-comparison --decoder-anchor-policy e/842/解释/model-capability-route-promotion-bounded-objective-decoder-anchor-policy --checkpoint e/838/解释/model-capability-route-promotion-bounded-objective-training-run/run/checkpoint.pt --tokenizer e/838/解释/model-capability-route-promotion-bounded-objective-training-run/run/tokenizer.json --device cpu --out-dir e/843/解释/model-capability-route-promotion-bounded-objective-decoder-anchor-policy-replay --require-replay-ready --require-policy-case-pass --force
```

HTML 截图：

```text
e/843/图片/v843-bounded-objective-decoder-anchor-policy-replay-html.png
```

## 链路角色

v843 是 replay 验证器：

- 上游：v842 policy。
- 下游：v844 policy review。
- 当前结论：assisted signal 可复现。
- 当前限制：new-text success 为 0，promotion blocked。

## 一句话总结

v843 把 v842 的 replay-only policy 放回真实 checkpoint 中验证，证明 assisted signal 可复现，但模型仍没有通过 unassisted objective replay。
