# v821 route promotion bounded real replay decoder anchor probe

## 本版目标和边界

v821 的目标是验证 v820 的诊断：既然 prompt 和 required terms 都已经在 corpus 中，但 v819 仍然 0/5，问题可能出在生成首 token 或解码锚定上。本版对 v818 checkpoint 做三组 forced prefix / decoder anchor probe，观察给模型一点输出前缀后，它是否能补出剩余 required terms。

本版不把 anchor-assisted 结果当成 unassisted bounded replay success。它只证明“有锚点时模型可能补全目标词”，不能证明模型已经独立学会回答。

## 前置路线

- v819：v818 prompt-aligned checkpoint 真实 replay 仍为 0/5。
- v820：确认 5 个 prompt 都在 corpus 中，`fixed/loss` 各出现 47 次，但生成仍零命中且碎片化。
- v821：测试给输出端加入 `f`、`fixed `、`fixed l` 三种锚点后，模型是否能补全。

## 关键文件

- `src/minigpt/model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe.py`
  - 核心 probe。
  - 复用 `MiniGPTGenerator` 执行真实生成。
  - 支持 `generator_runner` 注入，方便单测不用加载真实 torch checkpoint。

- `src/minigpt/model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - CSV 按 case/profile 列出 assisted、completion、new-text 三种命中。

- `scripts/run_model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe.py`
  - CLI 入口。
  - 输入 v819 replay、v820 diagnostic、v818 checkpoint/tokenizer。

- `tests/test_model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe.py`
  - 覆盖 anchor completion 成功、checkpoint 缺失失败、输出与 locator。

- `e/821/解释/model-capability-route-promotion-bounded-real-replay-decoder-anchor-probe/`
  - 本版真实 probe 证据目录。

## Anchor Profiles

本版固定三组 probe：

- `prefix_f`
  - anchor 为 `f`。
  - 只给 `fixed` 的首字母，观察模型能否补出 `ixed loss`。

- `prefix_fixed_space`
  - anchor 为 `fixed `。
  - `fixed` 由锚点提供，真正要观察的是模型能否补出 `loss`。

- `prefix_fixed_l`
  - anchor 为 `fixed l`。
  - 给出 `fixed` 和 `loss` 的首字母，观察模型能否补出 `oss`。

这三个 profile 从弱到强逐步增加锚点，目的是定位失败点，而不是制造虚假的 pass。

## 核心数据结构

`probe_rows` 是 v821 的主表。每行包含：

- `case_id`
  - 原 bounded replay case。

- `profile_id`
  - 使用哪种 anchor profile。

- `anchor`
  - 实际拼到 prompt 后的 forced prefix。

- `continuation`
  - 模型在 anchor 后生成的新文本。

- `combined`
  - `anchor + continuation`。
  - 用来判断 anchor-assisted 是否包含完整 required terms。

- `anchor_assisted_hit_terms`
  - 在 `combined` 中命中的 terms。
  - 这个字段可能包含锚点本身贡献的词，因此不能单独当模型能力。

- `new_text_hit_terms`
  - 只在 continuation 中命中的 terms。
  - 更接近模型新生成能力。

- `completion_hit_terms`
  - 对 anchor 未完整提供的词，检查模型是否通过 continuation 把它补完整。
  - 这是本版最重要的信号。

- `anchor_assisted_pass` / `completion_pass` / `new_text_pass`
  - 三种不同口径的通过标记。

## 核心函数

`build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe()` 是主入口：

1. 读取 v819 prompt-aligned replay。
2. 读取 v820 failure diagnostic。
3. 确认 checkpoint/tokenizer 存在。
4. 对每个 replay row 执行三种 anchor profile。
5. 调用 `_probe_row()` 计算 assisted/new-text/completion 命中。
6. 汇总 `anchor_assisted_pass_count`、`completion_pass_count`、`new_text_pass_count`。
7. 生成 decision 和 interpretation。

`_probe_row()` 的三种评分口径是本版的关键：

- `anchor_assisted_pass`
  - anchor + continuation 覆盖 required terms。
  - 可能受人工 anchor 影响。

- `new_text_pass`
  - continuation 自己覆盖 required terms。
  - 最严格。

- `completion_pass`
  - anchor 可以给出一部分，但模型必须补完未完整提供的 term。
  - 适合判断 forced prefix 是否能引导目标词完成。

## 真实运行结果

真实 CLI 输出：

```text
status=pass
decision=model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe_found_completion_signal
probe_ready=True
probe_row_count=15
anchor_assisted_pass_count=2
completion_pass_count=2
new_text_pass_count=2
anchor_completion_success=True
next_step=build_decoder_anchor_policy
```

成功信号集中在：

- `objective-answer-check + prefix_fixed_space`
- `objective-answer-check + prefix_fixed_l`

这说明 v818 checkpoint 并非完全无法生成 `loss`，但它需要较强的输出锚点。无锚 bounded replay 仍然失败，所以能力结论必须保守。

## 测试覆盖

本版新增 3 个 focused tests：

- fake generator 下能识别 anchor completion signal。
- checkpoint 缺失时 probe fail。
- locator 和 artifact writer 能输出 JSON/CSV/TXT/MD/HTML。

测试重点不是证明模型表现，而是保护 scoring 规则不把 anchor 本身误算成 unassisted success。

## 运行证据

证据目录：

- `e/821/解释/说明.md`
- `e/821/解释/model-capability-route-promotion-bounded-real-replay-decoder-anchor-probe/`
- `e/821/图片/v821-bounded-real-replay-decoder-anchor-probe-html.png`

Playwright MCP 已打开 HTML 并截图，页面显示 15 条 probe、2 条 assisted/completion/new-text pass，以及下一步 `build_decoder_anchor_policy`。

## 一句话总结

v821 找到了有限的 anchor-assisted completion 信号，把下一步从“继续盲训”推进到“设计受控 decoder anchor policy 并再验证”。
