# v749 fixed-preserving transfer training run 代码讲解

## 本版目标和边界

v749 的目标是用 v748 物化出的 fixed-preserving transfer corpus 进行一次真实 tiny 训练，并判断训练脚本内的 heldout direct probes 是否出现 pair-full。

本版和 v748 的边界不同：v748 只证明训练输入干净，v749 开始产生模型 checkpoint，并记录模型在两个 replay variants 下是否命中 `fixed` 和 `loss`。

但是 v749 仍不是 promotion 版。它只给出 `direct_pair_probe_hit` 级别的模型质量 claim，下一版还必须用独立 replay 脚本加载 checkpoint 和 heldout fixture，再确认结果是否可复现。

## 前置路线

- v744 用 broad pair-transfer corpus 训练后只得到 loss-only，说明 full surrogate route 会破坏 direct surface。
- v745 将 v744 与 v738/v740 对比，关闭 broad route。
- v746 计划 fixed-preserving transfer route。
- v747 生成四行 fixed-preserving contract patch。
- v748 将 contract patch 物化成 6400 行 corpus。
- v749 在同一 larger-tiny 配置下训练，判断这条更克制路线是否恢复 pair-full。

这条路线的核心是：先定位退化来源，再缩小 transfer row 干扰面，最后用同配置训练比较。

## 关键复用文件

- `scripts/run_model_capability_required_term_pair_readiness_training_run.py`
  - CLI 入口。
  - 输入是 v748 的 materialization 输出目录。
  - 负责启动训练、保存 checkpoint/tokenizer/metrics/config，并生成报告。

- `src/minigpt/model_capability_required_term_pair_readiness_training_run.py`
  - 训练运行 orchestration。
  - 读取 corpus 与 heldout fixture。
  - 调用训练函数后对默认续写和 suppress-newline 续写做 probe 检查。

- `e/749/解释/model-capability-required-term-pair-readiness-fixed-preserving-transfer-training-run/`
  - 保存 v749 训练报告、checkpoint、tokenizer、metrics、train config。
  - 这是 v750 独立 replay 的输入目录。

## 训练配置

v749 延续 v744 的 larger-tiny 配置，避免把结果差异归因到模型规模或采样参数：

```text
seed=3535
max_iters=1800
eval_iters=2
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

输入 corpus 来自 v748：

```text
e/748/解释/model-capability-required-term-pair-readiness-fixed-preserving-transfer-corpus-materialization
```

## 核心输出字段

v749 的关键输出是：

```text
status=pass
decision=pair_readiness_training_pair_full_observed
training_status=pass
checkpoint_exists=True
pair_full_observed=True
default_continuation_hit_count=2
model_quality_claim=direct_pair_probe_hit
```

其中：

- `pair_full_observed=True`
  - 表示训练脚本内至少一个 replay variant 同时命中 `fixed` 和 `loss`。

- `default_continuation_hit_count=2`
  - 默认续写命中了两个目标词。

- `model_quality_claim=direct_pair_probe_hit`
  - 说明这只是 direct pair probe 级别的 hit，不是 promoted checkpoint。

- `next_action=run heldout pair-probe replay before promoting the checkpoint`
  - 明确下一步必须独立 replay。

## 与 v744 的差别

v744 的 broad pair-transfer route 结果是：

```text
decision=pair_readiness_training_no_pair_full
pair_full_observed=False
default_continuation_hit_count=1
```

v749 的 fixed-preserving transfer route 结果是：

```text
decision=pair_readiness_training_pair_full_observed
pair_full_observed=True
default_continuation_hit_count=2
```

这说明 fixed-preserving transfer rows 在同配置下比 broad pair-transfer rows 更适合当前 tiny 模型。但由于 tiny 训练方差高，仍需 v750 replay 和后续对比来确认稳定性。

## 运行证据

运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_training_run.py e\748\解释\model-capability-required-term-pair-readiness-fixed-preserving-transfer-corpus-materialization --out-dir e\749\解释\model-capability-required-term-pair-readiness-fixed-preserving-transfer-training-run --seed 3535 --max-iters 1800 --eval-iters 2 --batch-size 16 --block-size 16 --n-layer 2 --n-head 2 --n-embd 96 --learning-rate 0.01 --max-new-tokens 12 --temperature 0.2 --top-k 1 --device cpu --require-pass --force
```

Playwright 快照确认 HTML 中可见：

- `Status pass`
- `Decision pair_readiness_training_pair_full_observed`
- `Checkpoint True`
- `Pair-full True`
- default variant hit terms 为 `fixed` 和 `loss`
- suppress-newline variant hit terms 为 `fixed` 和 `loss`

截图位于：

```text
e/749/图片/v749-fixed-preserving-transfer-training-run.png
```

## 证据链角色

v749 是 fixed-preserving transfer route 的第一份正向训练证据。它把 v745 的路线关闭、v746 的计划、v747 的 contract patch、v748 的 corpus 连接到真实 checkpoint。

不过，这一版仍保留克制结论：它证明“训练脚本内观察到 pair-full”，下一版需要独立 replay 才能判断是否进入 checkpoint promotion 候选。

一句话总结：v749 将 fixed-preserving transfer route 从干净训练输入推进到正向训练观察，但真正的 promotion 还要等独立 replay。
