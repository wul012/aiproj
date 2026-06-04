# v839：bounded objective replay comparison

## 本版目标和边界

v839 的目标是验证 v838 训练出的 checkpoint 是否真的能完成 v836 objective contract。v838 已经证明训练产物完整，但 loss 下降不能代表能力恢复；v839 把 checkpoint 放回 contract cases 里回放，给出真实输出结果。

本版不继续训练，也不做新的 seed。它只做 replay/comparison，并据实记录 zero-hit。

## 前置链路

输入来自两条证据：

- v836 contract：定义 3 个 objective contract cases，目标 completion 是 `fixed loss`。
- v838 training run：提供真实 checkpoint、tokenizer、metrics、manifest 和训练摘要。

v839 只有在 contract ready、training ready、checkpoint/tokenizer 存在时才执行 replay。

## 关键文件

- `src/minigpt/model_capability_route_promotion_bounded_objective_replay_comparison.py`
  - 负责加载 contract cases、调用 MiniGPTGenerator、打分 required terms，并生成 comparison summary。
- `src/minigpt/model_capability_route_promotion_bounded_objective_replay_comparison_artifacts.py`
  - 负责输出 JSON、CSV、TXT、Markdown、HTML。
- `scripts/run_model_capability_route_promotion_bounded_objective_replay_comparison.py`
  - CLI 入口，支持真实 checkpoint/tokenizer 或从 training run 自动定位。
- `tests/test_model_capability_route_promotion_bounded_objective_replay_comparison.py`
  - 覆盖 zero-hit、全通过但 holdout 仍阻断 promotion、training evidence 未 ready、输出和 CLI。
- `e/839/解释/model-capability-route-promotion-bounded-objective-replay-comparison/`
  - 保存真实 replay/comparison 产物。
- `e/839/图片/v839-bounded-objective-replay-comparison-html.png`
  - Playwright MCP 截图。

## 核心流程

builder 会先定位 checkpoint 和 tokenizer：

```text
checkpoint = training_run.run_dir / checkpoint.pt
tokenizer = checkpoint.parent / tokenizer.json
```

然后对每个 contract case 发起生成请求：

```text
max_new_tokens=8
temperature=0.2
top_k=20
seed=1839
```

每条 replay row 记录：

- `case_id`
- `prompt`
- `continuation`
- `generated`
- `expected_completion`
- `hit_terms`
- `missed_terms`
- `case_pass`
- `any_hit`

评分逻辑很直接：continuation 中必须同时包含 `fixed` 和 `loss`，case 才算 pass。

## 真实结果

v839 真实输出：

```text
case_count=3
passed_case_count=0
any_hit_case_count=0
zero_hit_case_count=3
pass_rate=0.0
objective_contract_recovered=False
```

在前置探针里，模型的 continuation 形如：

```text
wixed w
```

这说明模型接近了局部字符形态，但没有生成 required terms。它既没有 `fixed`，也没有 `loss`。

## 为什么不 promotion

本版明确设置：

```text
promotion_ready=False
model_quality_claim=not_improved
```

原因有两层：

1. objective contract 本身没有 recover。
2. 即使 objective contract recover，v836 也要求 unchanged v803 suite holdout 后才能考虑 route promotion。

所以 v839 的正确下一步不是发布，也不是继续扩大治理链，而是诊断 zero-hit。

## 测试覆盖

聚焦测试覆盖：

- zero-hit 时 comparison ready，但 `require_objective_pass` 返回失败。
- 全 case pass 时只标记 contract recovered，仍不 promotion ready。
- training evidence 未 ready 时失败。
- artifact writer 和 CLI 能输出全部格式。

本版聚焦测试结果是 `4 passed`。

## 运行证据

真实命令：

```text
python scripts/run_model_capability_route_promotion_bounded_objective_replay_comparison.py --objective-contract e/836/解释/model-capability-route-promotion-bounded-objective-contract --training-run e/838/解释/model-capability-route-promotion-bounded-objective-training-run --device cpu --out-dir e/839/解释/model-capability-route-promotion-bounded-objective-replay-comparison --require-comparison-ready --force
```

HTML 截图保存到：

```text
e/839/图片/v839-bounded-objective-replay-comparison-html.png
```

## 一句话总结

v839 证明 v838 checkpoint 虽然完成训练，但在 objective contract replay 上仍是 zero-hit，下一步必须先做失败诊断。
