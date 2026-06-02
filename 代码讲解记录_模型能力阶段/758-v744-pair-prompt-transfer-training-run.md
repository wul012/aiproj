# v744 pair prompt transfer training run 代码讲解

## 本版目标和边界

v744 的目标是用 v743 生成的 pair prompt transfer corpus 做一次真实 tiny 训练，并复核模型是否能在 heldout direct probes 上同时命中 `fixed` 和 `loss`。

这个版本的判断边界很重要：训练命令成功不等于模型能力成功。v744 的结果是 `status=pass`，因为训练、checkpoint 写入和报告生成都完成；但 `decision=pair_readiness_training_no_pair_full`，说明模型没有达到 pair-readiness promotion 条件。

本版不新增数据、不改 contract、不调参搜索。它沿用 v738 的 larger-tiny 配置，让 v744 可以和 v738 直接比较。

## 前置路线

v738 的 direct-completion surface training 首次在 heldout direct probes 上做到 pair-full，也就是 `fixed=` 命中 `fixed`，`loss=` 命中 `loss`。

v740 对同一个 checkpoint 做 pair-probe replay，发现 `fixed=|loss=` 和其它 pair prompt surfaces 不迁移，因此 v738 只能算 direct-probe-only。

v741-v742 增加 surrogate pair-transfer rows，试图在不泄漏 exact heldout pair prompt 的前提下让模型学习 fixed/loss 共现结构。

v743 把这个 patch contract 物化为 7680 行训练 corpus。

v744 负责回答一个简单问题：这些 surrogate transfer rows 是否真的提升了训练后的 heldout 能力？

## 关键文件

- `scripts/run_model_capability_required_term_pair_readiness_training_run.py`
  - v744 的真实训练入口。
  - 接收 v743 materialization 输出目录。
  - 调用通用训练脚本生成 checkpoint，再运行 heldout replay。

- `src/minigpt/model_capability_required_term_pair_readiness_training_run.py`
  - 训练运行的核心逻辑。
  - 负责读取 materialized corpus、拼接 `scripts/train.py` 命令、检查 checkpoint/tokenizer/metrics/train_config 是否存在。
  - 训练后读取 heldout eval fixture，对 default 和 `suppress_newline_tokens` 两个 replay profile 生成延续文本。

- `src/minigpt/model_capability_required_term_pair_readiness_training_run_artifacts.py`
  - 负责把训练 run report 写成 JSON、CSV、TXT、Markdown 和 HTML。
  - HTML 是本版 Playwright 截图的来源。

- `e/744/解释/model-capability-required-term-pair-readiness-pair-prompt-transfer-training-run/`
  - v744 的最终证据目录。
  - 包含训练 report、checkpoint 目录、日志、metrics、tokenizer、train_config 和 HTML 结果。

- `e/744/图片/v744-pair-prompt-transfer-training-run.png`
  - 浏览器截图证据。
  - 证明报告页面可读，并显示 `Pair-full=False` 与 `Claim=not_claimed`。

## 训练配置

v744 沿用 v738 的 larger-tiny 设置：

- `seed=3535`
- `max_iters=1800`
- `batch_size=16`
- `block_size=16`
- `n_layer=2`
- `n_head=2`
- `n_embd=96`
- `learning_rate=0.01`
- `temperature=0.2`
- `top_k=1`
- `device=cpu`

这个配置选择是为了控制变量。v744 和 v738 的主要差异应落在训练语料上，而不是模型容量或解码参数。

## 核心报告字段

v744 report 的关键字段如下：

- `training.status=pass`
  - 说明训练进程正常退出。

- `checkpoint_exists=True`
  - 说明训练确实写出了 checkpoint，不是空跑。

- `pair_full_observed=False`
  - default 和 newline suppression 两个 replay profile 都没有同时命中 fixed/loss。

- `default_continuation_hit_count=1`
  - default profile 只命中一个 term。

- `model_quality_claim=not_claimed`
  - 明确禁止把这次训练写成能力提升。

- `next_action=inspect heldout direct failures before changing corpus`
  - 下一步应先做失败诊断，而不是继续盲目加 rows。

## Replay 结果

v744 的 Markdown/CSV 都显示：

```text
default -> hit_terms=["loss"], missed_terms=["fixed"], pair_full_hit=False
suppress_newline_tokens -> hit_terms=["loss"], missed_terms=["fixed"], pair_full_hit=False
```

这说明新增 pair-transfer rows 没有让模型学会 pair prompt 迁移，反而把 v738 的 direct pair-full 变成了 loss-only。

这个结果和早期很多固定/损失双分支实验类似：一旦训练目标强化某一侧或改变表面形态，tiny 模型会把另一侧挤掉。v744 的问题不是训练失败，而是目标竞争失败。

## 测试和验证

真实运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_training_run.py e\743\解释\model-capability-required-term-pair-readiness-pair-prompt-transfer-corpus-materialization --out-dir e\744\解释\model-capability-required-term-pair-readiness-pair-prompt-transfer-training-run --seed 3535 --max-iters 1800 --eval-iters 2 --batch-size 16 --block-size 16 --n-layer 2 --n-head 2 --n-embd 96 --learning-rate 0.01 --max-new-tokens 12 --temperature 0.2 --top-k 1 --device cpu --require-pass --force
```

核心输出：

```text
status=pass
decision=pair_readiness_training_no_pair_full
checkpoint_exists=True
pair_full_observed=False
default_continuation_hit_count=1
```

Playwright 快照确认 HTML 中可见：

- `Status pass`
- `Decision pair_readiness_training_no_pair_full`
- `Training pass`
- `Checkpoint True`
- `Pair-full False`
- `Claim not_claimed`

这些断言保护了本版的真实边界：训练链路是通的，但能力结论是负结果。

## 证据链角色

v744 是 v741-v743 repair route 的真实训练判定点。它没有推翻 v738 的 direct-completion route价值，但证明 pair prompt transfer patch 不能直接作为推广路线。

这会影响下一版：应该先做 v744 对 v738/v740 的失败对比，找出 fixed 为什么被 surrogate transfer rows 挤掉，再决定是回退、轻量裁剪 transfer rows，还是改成更小的 pair-transfer 数据量。

一句话总结：v744 把 pair prompt transfer route 从“看起来合理的 patch”推进到真实训练负证据，说明下一步要诊断目标竞争，而不是继续堆 pair-transfer rows。
