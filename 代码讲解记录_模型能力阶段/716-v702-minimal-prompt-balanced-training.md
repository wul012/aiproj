# v702 minimal prompt balanced training

## 本版目标和边界

v702 的目标是执行 v701 的 balanced repair plan，真实训练一个 tiny checkpoint，并观察 `fixed=` 与 `loss=` 是否能同时命中目标词。

本版不新增治理链，也不把训练成功等同于模型能力提升。只要 `pair_full_observed=False`，就必须保留为负结果。

## 前置链路

前置版本形成了一个很清楚的实验链：

```text
v696 minimal prompt training -> fixed-only
v699 loss-first-token repair training -> loss-only
v700 tradeoff comparison -> first_token_preference_tradeoff_confirmed
v701 balanced repair plan -> proposed_corpus_mode=minimal_prompt_balanced_first_token_repair_objective
```

v702 承接的是 v701 的 recommended next action：同 seed `3535`、同训练规模，改用 balanced corpus 真实训练。

## 输入和训练参数

核心输入：

```text
corpus_mode=minimal_prompt_balanced_first_token_repair_objective
seed=3535
repeat=260
bridge_repeat=20
max_iters=1400
temperature=0.2
top_k=1
```

这些参数刻意沿用 v696/v699，避免把实验变量扩大到模型大小、训练步数或采样策略。

## 关键产物

- `e/702/解释/model-capability-required-term-pair-minimal-prompt-balanced-training/model_capability_required_term_pair_coexistence_refresh.json`
  - v702 主报告。
  - 记录训练命令、checkpoint 路径、replay report、summary 和 interpretation。

- `e/702/解释/model-capability-required-term-pair-minimal-prompt-balanced-training/pair-coexistence-refresh-run/checkpoint.pt`
  - 本版真实训练出的 tiny checkpoint。
  - 它是实验产物，不是可宣称能力提升的模型。

- `e/702/解释/model-capability-required-term-pair-minimal-prompt-balanced-training/pair-generation-profile-replay/`
  - 对新 checkpoint 运行 default 与 suppress newline 两种 profile。
  - 用来判断 `fixed=`、`loss=` 的 continuation hit 和 pair-full。

- `e/702/图片/v702-minimal-prompt-balanced-training.png`
  - Playwright 截图证据，展示 HTML 报告。

## 核心结果

主报告输出：

```text
status=pass
decision=required_term_pair_coexistence_refresh_no_pair_full
training_status=pass
checkpoint_exists=True
pair_full_observed=False
model_quality_claim=not_claimed
```

关键 replay rows：

```text
fixed= -> fixed=lix=los=loss
loss=  -> loss=lossssss=los
```

`loss=` 命中 loss，但 `fixed=` 没有命中 fixed，反而被 loss-like 字符模式污染。因此 v702 不是能力提升，而是 balanced repair 的负结果。

## 为什么这个负结果有价值

v702 证明问题不是“没有跑训练”或“没有 balanced corpus”。训练链路成功，checkpoint 存在，replay 也成功，但 tiny 模型仍没有学到两个 minimal prompt 的稳定分离。

这会把下一步方向从“继续堆同类 first-token 行”推向更高价值的选择：

- 做 pair-readiness 诊断，判断 corpus 是否已经在训练前形成足够明确的双分支约束。
- 做更明确的 evaluation/training split，避免只看训练样本表面复读。
- 如果仍坚持 minimal prompt，应该先设计更强的反污染检查，而不是继续盲训。

## 测试和验证

本版的主要验证来自真实运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_coexistence_refresh.py ... --require-pass --force
```

它保护了三件事：

- 训练进程必须成功返回。
- checkpoint、tokenizer、metrics 和 train_config 必须存在。
- replay report 必须能读新 checkpoint 并产生 pair-full 判断。

因为输出是 `pair_full_observed=False`，所以本版没有模型质量 claim。

## 一句话总结

v702 用真实训练证明 balanced first-token repair 仍不足以让 tiny MiniGPT 同时稳定生成 `fixed` 和 `loss`。
