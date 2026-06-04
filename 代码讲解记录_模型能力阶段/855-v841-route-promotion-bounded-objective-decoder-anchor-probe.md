# v841：bounded objective decoder anchor probe

## 本版目标和边界

v841 的目标是补上 v840 之后最小、最关键的一步：确认 zero-hit 失败是否完全没有 decoder 信号，还是只是在无锚点普通 replay 中无法稳定生成 exact required terms。

本版明确不做三件事：

- 不重新训练模型。
- 不修改 v836 objective contract。
- 不把 anchor-assisted 命中解释为 unassisted replay 成功。

这条边界很重要。v839 已经证明普通 replay 是 zero-hit；v840 进一步指出 `wixed` 这类 near-miss。v841 只是在这个基础上问：如果给 `f`、`fixed `、`fixed l` 这样的输出锚点，模型能不能补齐 `fixed/loss`。

## 前置链路

本版输入来自三段真实证据：

- v839 replay comparison：提供真实失败 case、prompt、continuation、required terms。
- v840 zero-hit diagnostic：确认这些失败不是 prompt 缺失，而是 exact decoding/near-miss 问题。
- v838 training run：提供真实 checkpoint 和 tokenizer。

因此 v841 不是孤立报告，而是从 “训练产物 -> replay 失败 -> 失败诊断 -> decoder anchor probe” 顺着证据链继续往下压。

## 关键新增文件

- `src/minigpt/model_capability_route_promotion_bounded_objective_decoder_anchor_probe.py`
  - 定义核心 probe builder、输入定位、真实 generation 调用、check rows、summary、interpretation。
- `src/minigpt/model_capability_route_promotion_bounded_objective_decoder_anchor_probe_artifacts.py`
  - 负责 JSON、CSV、TXT、Markdown、HTML 输出。
- `scripts/run_model_capability_route_promotion_bounded_objective_decoder_anchor_probe.py`
  - CLI 入口，支持目录输入、`--require-probe-ready`、`--require-anchor-success` 和 `--force`。
- `tests/test_model_capability_route_promotion_bounded_objective_decoder_anchor_probe.py`
  - 覆盖 assisted completion signal、缺 checkpoint 失败、objective 已 recovered 时拒绝 probe、输出和 CLI wiring。
- `e/841/解释/model-capability-route-promotion-bounded-objective-decoder-anchor-probe/`
  - 保存真实运行产物。
- `e/841/图片/v841-bounded-objective-decoder-anchor-probe-html.png`
  - Playwright MCP 截图证据。

## 核心数据结构

### anchor profiles

本版固定三个 profiles：

```text
prefix_f           -> anchor = f
prefix_fixed_space -> anchor = fixed 
prefix_fixed_l     -> anchor = fixed l
```

这些 profiles 的作用不是让模型“作弊通过”，而是把 decoder 行为拆细：

- `prefix_f`：看模型能不能从首字母补出 `fixed`。
- `prefix_fixed_space`：给出第一个目标词，看模型能不能补 `loss`。
- `prefix_fixed_l`：进一步降低输出难度，看是否仍能稳定补齐。

### probe row

每条 probe row 记录：

```text
case_id
profile_id
anchor
continuation
combined
required_terms
anchor_assisted_hit_terms
new_text_hit_terms
completion_hit_terms
anchor_assisted_pass
new_text_pass
completion_pass
seed
max_new_tokens
temperature
top_k
```

这里有三个不同的 pass：

- `anchor_assisted_pass`：`anchor + continuation` 命中全部 required terms。
- `new_text_pass`：只看 continuation 自身是否命中全部 required terms。
- `completion_pass`：允许 anchor 中已有的 term 计入已给定前缀，但要求模型补出剩余 term。

这个拆分是本版最重要的工程边界。它防止我们把 “prompt 中已有 fixed” 误判成 “模型自己生成 fixed loss”。

## 核心流程

builder 的流程是：

1. 读取 v839 replay rows。
2. 校验 v840 diagnostic 是 ready 状态。
3. 校验 checkpoint/tokenizer 文件存在。
4. 对每个 replay case 运行三个 anchor profiles。
5. 对 `anchor + continuation`、`continuation` 和 completion 部分分别计分。
6. 生成 checks、probe、summary 和 interpretation。

如果输入不完整，`status=fail`。如果有 anchor completion signal，`status=pass`，但 `promotion_ready` 仍然固定为 `False`。

## 真实运行结果

v841 输出：

```text
status=pass
decision=model_capability_route_promotion_bounded_objective_decoder_anchor_probe_found_completion_signal
bounded_objective_decoder_anchor_probe_ready=True
case_count=3
probe_row_count=9
anchor_assisted_pass_count=9
completion_pass_count=9
new_text_pass_count=0
anchor_completion_success=True
promotion_ready=False
model_quality_claim=decoder_anchor_signal_only
next_action=build_bounded_objective_decoder_anchor_policy
```

这说明：

- anchor 之后确实有可用 completion signal。
- 但 continuation 自身没有通过完整 required-term replay。
- 模型没有获得 route promotion 资格。
- 下一步应把 anchor 信号转成受控 policy，再单独 replay，而不是直接升级主线。

## 测试覆盖

聚焦测试覆盖四类风险：

- 有 assisted completion signal 时，summary 标记成功，但 `promotion_ready=False`。
- checkpoint 缺失时，`checkpoint_exists` 失败。
- 如果 replay 已经 recovered，则拒绝运行 zero-hit anchor probe，避免错误使用。
- artifact writer 和 CLI 能输出 JSON、CSV、TXT、Markdown、HTML。

本版 focused pytest 结果是：

```text
4 passed
```

后续全量测试会继续保护与旧链路的兼容性。

## 运行证据

真实命令：

```text
python scripts/run_model_capability_route_promotion_bounded_objective_decoder_anchor_probe.py --replay-comparison e/839/解释/model-capability-route-promotion-bounded-objective-replay-comparison --zero-hit-diagnostic e/840/解释/model-capability-route-promotion-bounded-objective-replay-zero-hit-diagnostic --checkpoint e/838/解释/model-capability-route-promotion-bounded-objective-training-run/run/checkpoint.pt --tokenizer e/838/解释/model-capability-route-promotion-bounded-objective-training-run/run/tokenizer.json --device cpu --out-dir e/841/解释/model-capability-route-promotion-bounded-objective-decoder-anchor-probe --require-probe-ready --require-anchor-success --force
```

HTML 截图：

```text
e/841/图片/v841-bounded-objective-decoder-anchor-probe-html.png
```

## 链路角色

v841 的角色是“探测器”，不是“晋级器”：

- 它证明 v838 checkpoint 不是完全无信号。
- 它也证明普通 replay 仍未恢复。
- 它把下一步从盲目训练转为 policy 化验证。

## 一句话总结

v841 把 v840 的 zero-hit 诊断推进到 decoder 层：模型在锚点辅助下能补出 bounded objective terms，但这仍只是 assisted signal，下一步必须用受控 anchor policy 继续验证。
