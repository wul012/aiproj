# v862：bounded objective loss signal bridge replay comparison

## 本版目标和边界

v862 的目标是把 v861 训练出的真实 checkpoint 接回 v836 bounded objective contract，做一次无 decoder-anchor 的 replay comparison。

v861 只证明“训练产物存在、loss 下降、checkpoint 可用”。这不足以说明 MiniGPT 已经学会目标能力。v862 因此补上能力验收：用固定 contract cases 要求模型直接输出 `fixed loss`，再按 case 统计完整通过、部分词命中和零命中。

边界：

- 不做新训练。
- 不修改 v836 contract。
- 不使用 decoder anchor。
- 不把 partial hit 解释成 contract recovered。
- 不 promotion。即使 contract recovered，也必须进入 unchanged holdout replay。

## 前置链路

```text
v859 profile sweep
 -> v860 loss signal bridge corpus
 -> v861 loss signal bridge training run
 -> v862 loss signal bridge replay comparison
```

这一版开始从“训练证据”回到“模型能力证据”。它回答的是：bridge corpus 训练后，模型是否能无辅助输出目标短语。

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge_replay_comparison.py`
  - v862 核心 adapter。
  - 复用已有 `build_model_capability_route_promotion_bounded_objective_replay_comparison`。
  - 把 v861 training run 的 ready 字段映射成 base replay builder 能识别的 `bounded_objective_training_ready`。
  - 把输出 decision、summary、interpretation 改写成 `loss_signal_bridge` 语义。

- `src/minigpt/bounded_objective_loss_signal_bridge_replay_comparison_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - 复用 bounded objective replay 的 CSV 和 render 逻辑，只替换短文件名和 ready 文案。

- `scripts/run_bounded_objective_loss_signal_bridge_replay_comparison.py`
  - CLI 入口。
  - 参数包括 `--objective-contract`、`--training-run`、`--checkpoint`、`--tokenizer`、`--device`、`--out-dir`、`--require-comparison-ready`、`--require-objective-pass`、`--force`。

- `tests/test_bounded_objective_loss_signal_bridge_replay_comparison.py`
  - 覆盖 partial hit、contract recovered 仍需 holdout、training run not ready 阻断、writer 和 CLI。

- `e/862/解释/bounded-objective-loss-signal-bridge-replay-comparison/`
  - v862 的真实 replay evidence。

- `e/862/图片/v862-bounded-objective-loss-signal-bridge-replay-comparison-html.png`
  - Playwright MCP 对 HTML 报告的运行截图。

## 核心数据结构

v862 输入两份主要报告：

```text
objective_contract_report
loss_signal_bridge_training_run_report
```

`objective_contract_report` 来自 v836，核心字段是：

```text
summary.bounded_objective_contract_ready
summary.contract_case_count
objective_contract.required_exact_completion
contract_cases[].case_id
contract_cases[].prompt
contract_cases[].expected_completion
contract_cases[].required_terms
```

`loss_signal_bridge_training_run_report` 来自 v861，核心字段是：

```text
summary.bounded_objective_loss_signal_bridge_training_ready
summary.final_train_loss
summary.final_val_loss
summary.train_loss_delta
run_dir
```

base replay builder 原本只认识：

```text
summary.bounded_objective_training_ready
```

所以 v862 的 `_adapt_training_run()` 做了字段映射：

```text
bounded_objective_training_ready
 <- bounded_objective_loss_signal_bridge_training_ready
```

这不是篡改语义，而是把“同一类训练 readiness”转换成通用 replay builder 的输入格式。

## replay 流程

运行流程：

```text
1. 定位 v836 contract JSON
2. 定位 v861 training-run JSON
3. 从 training-run 的 run_dir 找 checkpoint.pt 和 tokenizer.json
4. 对 contract_cases 逐个调用 MiniGPTGenerator
5. 截取 continuation
6. 检查 required_terms: fixed / loss
7. 生成 replay_rows
8. 汇总 passed_case_count / any_hit_case_count / zero_hit_case_count
9. 改写成 loss_signal_bridge 语义报告
10. 写出 JSON/CSV/TXT/Markdown/HTML
```

case pass 的判定非常严格：`fixed` 和 `loss` 都必须出现在 continuation 里。

只出现一个词，属于 partial required-term hit；两个词都没有，属于 zero-hit。

## 真实运行结果

命令：

```text
python -B scripts/run_bounded_objective_loss_signal_bridge_replay_comparison.py
  --objective-contract e/836/解释/model-capability-route-promotion-bounded-objective-contract
  --training-run e/861/解释/bounded-objective-loss-signal-bridge-training-run
  --device cpu
  --out-dir e/862/解释/bounded-objective-loss-signal-bridge-replay-comparison
  --require-comparison-ready
  --force
```

输出：

```text
status=pass
decision=bounded_objective_loss_signal_bridge_replay_partial_required_term_hit
case_count=3
passed_case_count=0
any_hit_case_count=2
zero_hit_case_count=1
pass_rate=0.0
promotion_ready=False
model_quality_claim=partial_required_term_signal
```

case 级别：

```text
canonical_direct_completion -> continuation=" lossswe", hit=loss, missed=fixed
minimal_direct_completion   -> continuation="\nfixed l", hit=fixed, missed=loss
completion_label_surface    -> continuation=" lonssss", hit=none, missed=fixed/loss
```

这说明 v861 checkpoint 已经不再是完全无信号，但还不能稳定输出完整目标短语。

## 为什么不晋级

晋级至少需要：

```text
passed_case_count == case_count
objective_contract_recovered == True
```

v862 是：

```text
passed_case_count=0
objective_contract_recovered=False
```

因此：

```text
promotion_ready=False
next_action=diagnose_bounded_objective_loss_signal_bridge_partial_hit_before_more_training
```

这里的“pass”只代表 replay 程序和证据链路执行成功，不代表模型能力通过。

## 测试覆盖

focused pytest 覆盖四类情况：

- partial replay：
  - 一个 case 命中 `fixed` 或 `loss` 之一。
  - report 必须 ready，但 contract 不能 recovered。

- recovered replay：
  - fake runner 返回 `fixed loss`。
  - contract 可以 recovered，但仍然要求 holdout，`promotion_ready=False`。

- training not ready：
  - v861 training ready 字段被置为 false。
  - replay 必须 fail，并暴露 `training_ready` issue。

- writer + CLI：
  - 验证 locate、JSON/CSV/TXT/Markdown/HTML 输出，以及 CLI wiring。

```text
4 passed
```

## 运行证据

产物：

```text
e/862/解释/bounded-objective-loss-signal-bridge-replay-comparison/
```

截图：

```text
e/862/图片/v862-bounded-objective-loss-signal-bridge-replay-comparison-html.png
```

Playwright MCP snapshot 确认 HTML 页面展示：

```text
Status=pass
Decision=bounded_objective_loss_signal_bridge_replay_partial_required_term_hit
Passed=0
Any hits=2
Zero hits=1
Claim=partial_required_term_signal
```

## 一句话总结

v862 把 loss-signal bridge 从训练产物推进到真实能力验收，结论是“有局部 required-term 信号，但 bounded objective contract 仍未恢复”。
