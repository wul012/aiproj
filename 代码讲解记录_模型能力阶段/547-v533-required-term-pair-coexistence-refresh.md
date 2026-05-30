# v533 required-term pair coexistence refresh 代码讲解

## 本版目标和边界

v532 已经证明 `suppress_newline_tokens` 不能修复 v502 fixed/loss pair-retention checkpoint。v533 因此回到训练目标本身：构造一个小型 fixed/loss 共存 corpus，训练新的 tiny checkpoint，再复用 v532 的 profile replay 去评估 pair-full。

本版不做大模型训练，也不扩展 profile registry。它只回答一个具体问题：直接共存训练能不能让 `fixed:` 生成 fixed、`loss:` 生成 loss。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_coexistence_refresh.py`
  - 构造 corpus、运行训练、生成 replay source report、调用 v532 replay builder。
- `src/minigpt/model_capability_required_term_pair_coexistence_refresh_artifacts.py`
  - 输出 JSON、text、Markdown、HTML，并把 v532 replay report 作为 sidecar 写出。
- `scripts/run_model_capability_required_term_pair_coexistence_refresh.py`
  - CLI 入口，暴露 repeat、bridge_repeat、训练参数和 `--require-pass`。
- `tests/test_model_capability_required_term_pair_coexistence_refresh.py`
  - 用 fake train/generate 覆盖 pair-full、no pair-full、corpus 平衡和输出渲染。
- `e/533/解释/model-capability-required-term-pair-coexistence-refresh/`
  - 真实训练与 replay 证据。
- `e/533/图片/01-model-capability-required-term-pair-coexistence-refresh.png`
  - HTML 报告截图。

## Corpus 设计

`build_pair_coexistence_refresh_corpus()` 生成两类行：

```text
fixed: fixed
loss: loss
comparison-baseline|fixed: fixed
factual-val-loss|loss: loss
term=fixed prompt=fixed: answer=fixed
term=loss prompt=loss: answer=loss
```

另有 bridge rows：

```text
fixed and loss are separate branches.
fixed: fixed ; loss: loss
When the prefix is fixed:, continue fixed.
When the prefix is loss:, continue loss.
```

这个设计的边界是清楚的：它仍然是 tiny direct corpus，不是自然语言泛化训练。

## 训练与评估链路

`build_model_capability_required_term_pair_coexistence_refresh()` 的流程是：

1. 写出 `required_term_pair_coexistence_refresh_corpus.txt`。
2. 调用 `scripts/train.py` 训练 `pair-coexistence-refresh-run`。
3. 用训练结果构造一个最小 source report，包含 fixed/loss 两个 terms 和一个训练变体。
4. 调用 v532 的 `build_model_capability_required_term_pair_generation_profile_replay()`。
5. 汇总 default/suppression 两个 profile 的 pair-full 结果。

复用 v532 replay builder 的好处是 pair-full 统计没有分叉，不会出现两个版本各算各的。

## 真实结果

真实命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_coexistence_refresh.py --out-dir e\533\解释\model-capability-required-term-pair-coexistence-refresh --seed 533 --repeat 260 --bridge-repeat 20 --max-iters 1400 --eval-iters 2 --batch-size 16 --block-size 16 --n-layer 1 --n-head 1 --n-embd 64 --learning-rate 0.02 --force --require-pass
```

结果：

```text
training_status=pass
checkpoint_exists=True
default_pair_full_variant_count=0
suppression_pair_full_variant_count=0
pair_full_observed=False
```

replay CSV 显示 `fixed:` 和 `loss:` 都生成了类似 `ansssssssss` 的 continuation。这说明本版训练跑通了，但 corpus 中的 `answer=` 模式可能把 first-token preference 带偏，下一步应检查 first token，而不是盲目增加 repeat。

## 测试覆盖

单测覆盖四个点：

- fake generation 同时命中 fixed/loss 时，decision 进入 `pair_full_observed`。
- fake generation 只输出 fixed 时，decision 进入 `no_pair_full`。
- corpus 至少包含 fixed/loss 平衡行和 bridge 行。
- 输出 writer 生成 JSON、text、Markdown、HTML，并写出 replay sidecar。

真实 PyTorch 训练由 `e/533` 的运行证据覆盖，单测负责锁住决策逻辑。

## 链路角色

v533 是一次真正回到模型训练的版本。它没有得到正向提升，但它把失败模式从“profile 不够”推进到“训练后 first-token 偏向 ans”，为下一版提供了更具体的诊断入口。

一句话总结：v533 让 fixed/loss pair 共存路线从解码 profile 回到训练目标，并暴露了新的 first-token 偏置问题。
