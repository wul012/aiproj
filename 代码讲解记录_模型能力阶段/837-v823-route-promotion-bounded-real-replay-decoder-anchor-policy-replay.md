# v823 route promotion bounded real replay decoder anchor policy replay

## 本版目标和边界

v823 的目标是复验 v822 decoder anchor policy。v822 只是从 v821 probe 中选出 policy，v823 则把 policy 真正应用回 bounded replay cases，确认局部 anchor signal 是否能在独立 replay 中复现。

本版不把 anchor-assisted pass 作为模型无锚能力，也不允许 route promotion。即使 policy covered case 通过，`promotion_ready` 仍然固定为 `False`。

## 前置路线

- v821 找到 `objective-answer-check` 的 anchor-assisted completion signal。
- v822 从多个成功 profile 中选择更短的 `prefix_fixed_space`，生成 partial policy。
- v823 将该 policy 应用回 v819 的 5 个 replay cases。

## 关键文件

- `src/minigpt/model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay.py`
  - 核心 policy replay。
  - 读取 v819 replay rows 和 v822 policy rows。
  - 对 covered case 注入 anchor，对 uncovered case 保持原 prompt。

- `src/minigpt/model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - CSV 展示每个 case 是否应用 policy、是否通过、命中 terms 和 misses。

- `scripts/run_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay.py`
  - CLI 入口。
  - 输入 replay、policy、checkpoint、tokenizer。

- `tests/test_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay.py`
  - 覆盖 policy replay 复现局部信号、缺 policy rows 失败、输出与 locator。

- `e/823/解释/model-capability-route-promotion-bounded-real-replay-decoder-anchor-policy-replay/`
  - 本版真实 replay 证据。

## 核心数据结构

`replay_rows` 是 v823 主表：

- `policy_applied`
  - 当前 case 是否命中 v822 policy。

- `profile_id` / `anchor`
  - 应用的 policy profile 和 forced prefix。

- `continuation`
  - 模型在 policy prompt 后生成的新文本。

- `combined`
  - `anchor + continuation`，用于 anchor-assisted scoring。

- `combined_hit_terms`
  - combined 中命中的 required terms。

- `new_text_hit_terms`
  - continuation 自身命中的 terms。

- `case_pass`
  - combined 是否覆盖 required terms。

`summary` 聚合：

- `passed_case_count`
- `policy_applied_case_count`
- `policy_applied_pass_count`
- `policy_replay_success`
- `promotion_ready=False`

## 核心函数

`build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay()` 是主入口：

1. 读取 v819 prompt-aligned replay。
2. 读取 v822 decoder anchor policy。
3. 根据 `case_id` 建立 policy map。
4. 对每个 source replay row 调用 `_generate_policy_case()`。
5. 调用 `_policy_replay_row()` 计算 combined hits 和 misses。
6. 调用 `_replay()` 汇总 pass count 和 policy applied pass count。
7. 输出 decision、summary 和 interpretation。

`_generate_policy_case()` 对 covered case 拼接 anchor；对 uncovered case 不加 anchor。这一点很重要，因为 v823 的 pass count 不能只看 covered case，必须保留完整 5-case suite 视角。

## 真实运行结果

真实 CLI 输出：

```text
status=pass
decision=model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_reproduced_partial_signal
replay_ready=True
passed_case_count=1
policy_applied_case_count=1
policy_applied_pass_count=1
policy_replay_success=True
promotion_ready=False
next_step=review_decoder_anchor_policy_replay
```

结论是：policy 信号能复现，但只覆盖 1/5。它把 v819 的 0/5 变成 anchor-assisted 1/5，却没有产生可推广的无锚提升。

## 测试覆盖

本版新增 3 个 focused tests：

- policy replay 能复现一个 partial signal 且 promotion blocked。
- 没有 policy rows 时 replay fail。
- locator 和 artifact writer 能输出 JSON/CSV/TXT/MD/HTML。

这些测试保护 v823 的边界：policy replay 成功不是 promotion 成功。

## 运行证据

证据目录：

- `e/823/解释/说明.md`
- `e/823/解释/model-capability-route-promotion-bounded-real-replay-decoder-anchor-policy-replay/`
- `e/823/图片/v823-bounded-real-replay-decoder-anchor-policy-replay-html.png`

Playwright MCP 已打开 HTML 并截图，页面显示 1/5 pass、policy applied 1、applied pass 1、promotion False。

## 一句话总结

v823 复现了局部 anchor-assisted signal，但同时证明当前路线仍停留在受控诊断层，距离无锚模型能力提升还有明显差距。
