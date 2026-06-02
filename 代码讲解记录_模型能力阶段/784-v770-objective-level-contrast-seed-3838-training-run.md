# v770 objective-level contrast seed 3838 training run 代码讲解

## 本版目标和边界

v770 执行 v767 seed stability plan 的第二个补充训练 seed：`3838`。它验证同一 objective-level contrast corpus、同一 tiny GPT 配置下，第三个 seed 是否也能观察到训练内 pair-full。

本版不新增训练框架，不改 corpus，不改模型规模，不做 replay，也不接受 checkpoint。

## 前置路线

- v767 规划 seed stability，指定 `3636`、`3737`、`3838` 三个 seed。
- v768 训练 seed `3737`。
- v769 replay seed `3737`，得到 replay-ready。
- v770 训练 seed `3838`。

## 本版复用的关键文件

- `scripts/run_model_capability_required_term_pair_readiness_training_run.py`
  - 训练 run CLI。
  - 接收 v762 materialization 目录，并把训练命令、checkpoint 和 direct probes 组织成报告。

- `src/minigpt/model_capability_required_term_pair_readiness_training_run.py`
  - 核心 orchestration。
  - 负责运行 `scripts/train.py`，收集 checkpoint/tokenizer/metrics/config，并判断 direct pair-full。

- `src/minigpt/model_capability_required_term_pair_readiness_training_run_artifacts.py`
  - 负责 JSON、CSV、TXT、Markdown 和 HTML 输出。

v770 不新增代码文件，因为新增价值来自真实训练产物，而不是重复造新的训练 runner。

## 训练配置

本版配置：

```text
seed=3838
max_iters=1800
batch_size=16
block_size=16
n_layer=2
n_head=2
n_embd=96
learning_rate=0.01
max_new_tokens=12
temperature=0.2
top_k=1
device=cpu
```

除了 seed，其余配置与 v763、v768 保持一致。这样 v772 rollup 能把差异归因于 seed。

## 输入输出结构

输入：

```text
e/762/解释/model-capability-required-term-pair-readiness-objective-level-contrast-corpus-materialization
```

输出：

```text
e/770/解释/model-capability-required-term-pair-readiness-objective-level-contrast-seed-3838-training-run
```

核心字段：

```text
status=pass
decision=pair_readiness_training_pair_full_observed
checkpoint_exists=True
pair_full_observed=True
default_continuation_hit_count=2
model_quality_claim=direct_pair_probe_hit
```

## 运行证据和边界

Playwright 截图位于：

```text
e/770/图片/v770-objective-level-contrast-seed-3838-training-run.png
```

截图证明 HTML 报告中可以看到 checkpoint 存在、pair-full 为 true。它仍然是 direct probe 证据，不能替代 v771 的 heldout replay。

一句话总结：v770 让 objective-level contrast 拥有第三个 seed 的 direct training hit，下一步要用 replay 判断它是否稳定。
