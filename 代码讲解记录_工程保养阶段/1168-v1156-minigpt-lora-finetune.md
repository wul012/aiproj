# 1168 · v1156 · MiniGPT LoRA 微调能力

## 本版目标与不做什么

本版给 MiniGPT 项目补上一个真正属于“模型能力”的增量：从零实现 LoRA（Low-Rank Adaptation，低秩适配），冻结已训练基座的全部权重，只在注意力层的两个线性投影 `c_attn` 与 `c_proj` 上挂可训练的低秩矩阵，并在真实 GPU（RTX 4060 Laptop GPU，torch 2.6.0+cu124）上跑一次完整的“基座训练 → 冻结 → LoRA 微调”流程，用 before/after 训练损失作为能力证据。

为什么是 LoRA。此前从 v1098 到 v1155，项目的大部分版本是治理、报告、receipt、cadence、回归清单一类“围绕模型的工程脚手架”，模型本身始终停在 CPU 上的 tiny GPT。LoRA 是把同一套工程纪律真正接到“模型变得更有能力”上的最小一步：它是现代大模型微调的主流手段，实现量可控，可在本机 GPU 上跑出真实损失曲线，并且能用单元测试把“低秩更新的数学契约”钉死。

本版明确不做的事：不引入更大的真实语料、不做 held-out 泛化评估、不做任何 promotion 决策、不改动 `model.py` 的基座结构、不替换现有的 `scripts/train.py` 全量训练入口。本版只回答一个有界问题——在只训练约 3% 参数的前提下，LoRA adapter 能否真实地把训练损失降下来，并保持基座权重逐字节不变。

## 本版来自哪条路线

本版承接上一轮对项目方向的判断：v1135–v1142 把“模型能力回归”做成了一条以证据查找为主、`boundary=evidence_lookup_not_model_promotion` 的治理回路，v1143–v1155 又沿 unassisted loss suffix repair 这条线做了 seed / training run / replay 等真实但极小规模的训练实验。这些都说明项目缺的不是工程纪律，而是“模型能力本身的纵深”。v1156 因此从“治理阶段”切到“真实模型能力”方向，作为该方向的第一版。它复用了既有的 `MiniGPT`、`CharTokenizer`、`dataset.get_batch` / `split_token_ids`，以及统一的可读报告产物写出器 `readability_report_artifacts.write_readability_outputs`，没有另造轮子。

## 关键新增 / 修改文件与链路角色

- `src/minigpt/lora.py`：LoRA 核心。定义 `LoRAConfig`、`LoRALinear`、`apply_lora`、`mark_only_lora_as_trainable`、`lora_parameters`、`count_parameters`、`lora_state_dict`、`merge_lora`。它是“数学契约层”，不依赖磁盘和数据集，便于单测。
- `src/minigpt/lora_finetune.py`：微调编排层。定义 `LoRAFinetuneConfig`、`estimate_loss`、`run_lora_finetune` 与内部 `_build_report`。它把“测 before → 套 LoRA → 冻结 → 只训 adapter → 测 after → 组装报告”串成一条可测的纯函数式流程，输入是内存张量，输出是符合可读报告约定的 dict。
- `scripts/run_lora_finetune_v1156.py`：真实运行入口。训练 tiny 基座、调用编排层、把报告写成 5 份产物、保存紧凑 adapter 和合并后 checkpoint。
- `tests/test_lora.py` / `tests/test_lora_finetune.py`：把数学契约和“真实学习”的断言固定下来。
- 证据：`f/1156/解释/lora-finetune-v1156/` 下的 5 份产物、`f/1156/图片/v1156-lora-finetune.png`、`f/1156/解释/说明.md`。

## 核心数据结构与字段语义

`LoRALinear` 包裹一个已有的 `nn.Linear`，把 `base.weight` / `base.bias` 的 `requires_grad` 全部置为 `False`，再新增两个可训练参数：`lora_A`（形状 `[r, in_features]`）和 `lora_B`（形状 `[out_features, r]`）。前向输出为 `base(x) + (dropout(x) @ Aᵀ @ Bᵀ) * scaling`，其中 `scaling = alpha / r`。两个关键设计：

1. `lora_A` 用 kaiming 初始化，`lora_B` 初始化为全零。于是初始时低秩更新恒等于 0，包裹层在数值上与基座线性层完全一致——这保证了“before”测量忠实反映基座，而不是被随机 adapter 污染。
2. `merge()` 把 `(B @ A) * scaling` 这块 `[out, in]` 的增量直接加进 `base.weight`，使得合并后前向无需任何额外参数和额外算子，对应真实部署路径；`unmerge()` 可逆。

`apply_lora` 遍历 `model.named_modules()`，对名字落在 `target_modules`（默认 `c_attn`、`c_proj`）且确为 `nn.Linear` 的子模块做替换，返回被替换模块的点路径列表；若一个都没匹配上会抛 `ValueError`，避免把 target 名字写错却“静默地什么都没微调”。`mark_only_lora_as_trainable` 用参数名是否包含 `lora_` 来决定 `requires_grad`，把除 adapter 以外的一切（embedding、LayerNorm、lm_head、base 权重）全部冻结。`count_parameters` 汇报 `total_parameters` / `trainable_parameters` / `trainable_ratio_percent`，这是 LoRA 价值主张的量化表达。

`run_lora_finetune` 返回的报告 dict 字段语义：`summary.trainable_ratio_percent` 是可训练占比；`before_train_loss` / `after_train_loss` / `train_loss_delta` 是主信号；`before_val_loss` / `after_val_loss` 仅作透明披露；`train_loss_improved` 为真即 `status=pass`、`decision=lora_finetune_reduced_train_loss`。`rows` 列出每个被适配模块（用于 CSV），`history` 记录微调过程中的损失采样点（用于画曲线）。

## 输入输出格式与运行流程

入口脚本默认从 `data/sample_zh.txt` 读文本，训练 `CharTokenizer`，按 9:1 切分。先用 AdamW 对全模型训练 `--base-steps` 步得到一个未完全收敛的基座；再调用 `run_lora_finetune`：它先测基座 before 损失，`apply_lora` 后只把 adapter 交给 AdamW 训练 `--lora-steps` 步，最后测 after。产物经 `write_readability_outputs` 写成 `lora_finetune_v1156.{json,csv,txt,md,html}` 五份；adapter 经 `lora_state_dict` 抽取后存成 `runs/lora_v1156/adapter.pt`（只含 `lora_` 张量，体积远小于全模型），再 `merge_lora` 后存一份 `checkpoint_merged.pt` 证明“合并即可部署”。

本版真实运行得到：`device=cuda`，`adapted_module_count=8`，`trainable_parameters=24576 / total_parameters=851584`，`trainable_ratio_percent=2.8859`，训练损失 `0.455033 → 0.416174`（`delta=-0.03886`），`status=pass`。

## 关键检查项与边界

最重要的边界是数据：bundled 语料只有 507 字符，验证集 51 字符被严重过拟合主导（val 损失约 5.3），因此 `val_loss` 不是可靠的泛化信号。本版没有掩盖这一点，而是把判定主信号从 val 改为 train——train 损失下降直接证明“adapter 确实在学”，并在报告 recommendations 中写明“语料太小、验证损失不可信、v1157 应引入更大真实数据集与 held-out 评估”。这是一次刻意的诚实取舍：把可靠的结论建立在能站得住的证据上，把数据规模这个独立问题显式留给下一版。

## 测试如何真实覆盖链路

`test_lora.py` 钉死数学契约：零初始化时包裹层输出与基座逐元素相等（`allclose`）；前向形状正确且打破零初始化后输出确实改变；`base.weight.requires_grad` 为假而 `lora_A/B` 为真；`merge()` 前后前向 `allclose`、`unmerge()` 可逆；`apply_lora` 对 2 层模型恰好替换 4 个模块、target 名写错时抛错；冻结后所有可训练参数名都含 `lora_`；`lora_state_dict` 只含 adapter 键。`test_lora_finetune.py` 用一段可记忆的重复 token 序列跑真实微调，断言三件事同时成立：训练损失确实下降（`train_loss_improved`、`after < before`）、可训练占比 < 50%、被冻结的 `base.weight` 在微调后与微调前 `torch.equal`（逐字节不变）。最后一条断言是“基座真的没被动过”的硬证据，也是 LoRA 区别于全量微调的核心。

## 一句话总结

v1156 让 MiniGPT 第一次拥有了真实可训练、可合并、可单独保存的 LoRA 微调能力——在 GPU 上只用约 2.9% 的可训练参数就把训练损失降了下来且基座逐字节冻结，把项目从“治理报告”正式推进到“真实模型能力”的起点。
