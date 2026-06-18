# v1185 MiniGPT canonical grokking checkpoint 代码讲解

## 本版目标与边界

v1179 在 `a + b = c (mod 97)` 上复现了 grokking；v1183 扫描权重衰减强度，发现它不是“越大越好”而是一个内部最优（grok 最快在 wd=1.0）；v1180/81/82/84 则是对这两个实验的离线审计。到这里，grokking 这条线“研究”的部分已经相当充分。v1185 有意识地停止再做 sweep，转而把结果**产品化**：冻结默认配方、训练并保存一个标准 checkpoint、把 config/metrics/curve 一起存档、并加一个 demo 证明“先记忆、后泛化”。

这是用户明确给的方向：与其继续 WD / norm / phase-diagram 这类研究式扫描，不如把已有结论固化成一个可用工件。本版因此是工程，不是新科学：一次便宜的训练（确认 grok 后早停），一次 save/load 往返，一次 held-out 泛化 demo。`status=pass` 当且仅当模型真的 grok、held-out 准确率达标、且保存的 checkpoint 能重新加载到逐字节相同的 logits。

边界：`toy_scale_single_task_modular_addition_canonical_checkpoint_not_a_scaling_claim`——这是玩具规模单任务的标准 checkpoint，不是对大模型的能力或 scaling 声明。

## 冻结的配方为什么是这组数

核心模块 `src/minigpt/grok_checkpoint_v1185.py` 顶部定义：

```python
CANONICAL_CONFIG = GrokConfig(seeds=(1337,), wds=(1.0,))
```

它直接复用 v1179 的 `GrokConfig`（默认就是 grokking 区间：train_frac=0.2、1 层/128、lr=1e-3、max_steps=40000），只把 seed 固定成单个、weight_decay 固定成 1.0。`weight_decay=1.0` 的选择是有依据的：v1183 的剂量-反应实验证明它是内部最优（grok 最快，t_gen≈14920，显著快于 wd=0.3 的 26560）。也就是说，本版让 v1183 的发现“变现”成了出厂配方，而不是又测一遍。单一固定 seed 让出厂 checkpoint 唯一、可复现。

## 训练与早停

`train_to_grok(config, device)` 复用 v1179 的底层原语（`build_modular_task`、`split_indices`、`make_grok_model`、`answer_loss`、`answer_accuracy`），跑全 batch AdamW，每 `eval_every` 步评估 train/val 答案准确率，记录 `t_mem`（train 首次≥0.99）、`t_gen`（val 首次≥0.90），一旦确认稳定 grok（val≥0.95）就早停。它和 v1179 的 `train_arm` 逻辑一致，唯一区别是**它返回训练好的模型**（train_arm 只返回 metrics），因为 checkpoint 需要最终权重。这是刻意不去改 v1179 `train_arm` 合同、而在本版用底层原语另写一个返回模型的训练函数——保持 v1179 的测试不动。

真实单次训练：memorize_step=100、generalize_step=11400、final_train_acc=1.0、final_val_acc=0.966，和 v1179 里 seed 1337 的结果一致（确定性）。

## 自包含 checkpoint

`save_checkpoint` 用 `torch.save({"state_dict":..., "meta":...}, path)` 把权重和元数据存进一个 `.pt`。`CheckpointMeta` 是一个 dataclass，记录重建模型和复现划分所需的一切：p、train_frac、seed、weight_decay、vocab_size、n_layer/n_head/n_embd、block_size，外加 grokking metrics（t_mem、t_gen、final acc、steps_run）。

`load_checkpoint(path)` 只靠 meta 就能重建架构：

```python
config = GrokConfig(p=meta.p, ..., seeds=(meta.seed,), wds=(meta.weight_decay,))
model = make_grok_model(meta.vocab_size, config).to(device)
model.load_state_dict(payload["state_dict"])
```

不需要调用方额外传 config。这就是“自包含”的含义——把 .pt 文件单独发给别人，也能加载、推理、复现划分。

## 正确性守门：save/load 往返

本版最关键的正确性检查是 `logits_match(model_a, model_b, p)`：在完整任务上比较两个模型的答案 token logits 是否逐字节相同。训练脚本的流程刻意是“训练 → 保存 → **重新加载** → 验证 logits 一致 → 用重新加载的模型跑 demo”。也就是说，泛化 demo 用的是从磁盘加载回来的模型，不是内存里的训练态模型，所以证据链证明的是“保存的文件确实可加载、可泛化”。

`logits_match` 一开始有个 device bug：它在 CPU 上构造任务张量，但 GPU 训练时模型在 cuda 上，导致 `index_select` 设备不匹配崩溃。CPU 单测没触发（模型和数据都在 cpu）。修复方式是把数据搬到每个模型各自的 device，再在 CPU 上比较 logits——这样它对“两个模型在不同 device”也安全。这个 bug 提醒：device 处理要在真实 GPU 路径上验证，CPU 测试可能漏掉。

## Demo 与报告

`evaluate_generalization(model, meta, device)` 在 held-out 对上算准确率，并解码出若干 `(a, b, predicted, truth)` 样例。真实结果：held-out acc=0.966，覆盖 7527 个没见过的对；demo 行如 `36 + 37 = 73 (✓)`、`4 + 1 = 5 (✓)`。

`build_report` 把配方、metrics、demo 行、以及“先记忆后泛化”的 phase 叙述组装成可读性报告。verdict 阶梯：`canonical_grokking_checkpoint_ready`（grok + 往返一致 + held-out≥0.90）/ `checkpoint_memorized_but_did_not_grok` / `checkpoint_grokked_but_roundtrip_mismatch` / `checkpoint_grokked_but_weak_heldout` / `checkpoint_failed_to_memorize`。只有第一种才 `status=pass`。

## 测试

`tests/test_grok_checkpoint_v1185.py` 共 9 个，全部 CPU 且快：save/load 往返到逐字节相同 logits（核心守门）、加载后架构自包含（只靠 meta 重建）、held-out demo 解码正确（truth==(a+b)%p）、verdict 阶梯五种全覆盖（用合成 meta）、训练确定性（两次训练 meta 相同且 logits 一致）。

## CLI 与产物

脚本 `scripts/train_grok_checkpoint_v1185.py` 训练 → 保存 `.pt` → 重新加载验证 → demo → 写五件套报告。产物：

```text
f/1185/解释/grok_checkpoint_v1185/grok_checkpoint_v1185.pt    （约 835KB，权重+meta）
f/1185/解释/grok_checkpoint_v1185/grok_checkpoint_v1185.{json,csv,txt,md,html}
f/1185/图片/grok-checkpoint-v1185.png                          （单条训练曲线）
```

## 链路角色与一句话总结

v1179 复现 grokking → v1183 找到 wd 内部最优 → v1180-84 审计 → v1185 把这些收口成一个可加载、可复现、带 demo 的标准 checkpoint。这是从“研究结论”到“可用工件”的一步，也更贴合“真实 AI 开发技能”（训练 + 存档 + 加载 + demo）。

一句话总结：v1185 把 grokking 产品化为一个自包含的标准 checkpoint——配方冻结（wd=1.0 因 v1183 最优）、保存即可加载（logits 逐字节一致）、并用重新加载的模型在 7527 个没见过的模数加法对上拿到 0.966 准确率，证明“先记忆、后泛化”。
