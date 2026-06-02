# v768 objective-level contrast seed 3737 training run 代码讲解

## 本版目标和边界

v768 执行 v767 seed stability plan 的第一步：用补充 seed `3737` 重新训练 objective-level contrast checkpoint。它验证的是同一 corpus、同一 tiny GPT 配置下，换一个 seed 后训练内 pair-full 信号是否还能出现。

本版不新增训练框架，不改 corpus，不改模型规模，也不直接接受 checkpoint。它的模型质量声明是 `direct_pair_probe_hit`，下一步必须 replay。

## 前置路线

- v762 materialized objective-level contrast corpus。
- v763 用 seed `3636` 训练并观察到 direct pair-full。
- v764 replay 证明 seed `3636` 的 pair probe 能独立复现。
- v766 promotion guard 禁止单 seed acceptance。
- v767 seed stability plan 指定补充 seed `3737` 和 `3838`。
- v768 训练 seed `3737`。

## 本版复用的关键文件

- `scripts/run_model_capability_required_term_pair_readiness_training_run.py`
  - 训练 run CLI。
  - 接收 materialization 目录，调用 `scripts/train.py`，再运行 direct pair probes。

- `src/minigpt/model_capability_required_term_pair_readiness_training_run.py`
  - 训练 orchestration。
  - 负责定位 corpus、构造训练命令、收集 checkpoint/tokenizer/metrics/config，并生成 pair-full 观察结果。

- `src/minigpt/model_capability_required_term_pair_readiness_training_run_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown 和 HTML。

v768 没有新增代码文件，因为现有训练 runner 已能表达 seed stability 训练步骤；本版的核心产物是新的真实训练证据。

## 训练配置

本版沿用 objective-level contrast 路线的训练配置：

```text
seed=3737
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

唯一有意变化是 seed。这样后续 rollup 才能把差异归因到随机种子，而不是 corpus 或模型配置变化。

## 输入输出结构

输入：

```text
e/762/解释/model-capability-required-term-pair-readiness-objective-level-contrast-corpus-materialization
```

输出：

```text
e/768/解释/model-capability-required-term-pair-readiness-objective-level-contrast-seed-3737-training-run
```

重要输出字段：

```text
status=pass
decision=pair_readiness_training_pair_full_observed
checkpoint_exists=True
pair_full_observed=True
default_continuation_hit_count=2
model_quality_claim=direct_pair_probe_hit
```

`checkpoint.pt`、`tokenizer.json`、`metrics.jsonl` 和 `train_config.json` 位于本版 training run 子目录中，是 v769 replay 的直接输入。

## 测试和验证

本版复用已测试过的 training runner，没有新增 Python 模块。验证重点是真实训练命令返回 `status=pass`，并确认 HTML 证据中可见：

- checkpoint 存在。
- pair-full 为 true。
- 质量声明仍是 direct probe，而不是 replay 或 acceptance。

Playwright 截图位于：

```text
e/768/图片/v768-objective-level-contrast-seed-3737-training-run.png
```

## 链路角色

v768 是 seed stability 的第一条补充训练证据。它不能单独提升结论层级，但为 v769 replay 提供新的 checkpoint。如果 v769 也通过，objective-level contrast 将拥有第二个 seed 的 replay 支撑。

一句话总结：v768 把 objective-level contrast 的稳定性验证从计划推进到第一个补充 seed 的真实训练证据。
