# 1176 · v1164 · MiniGPT SFT 指令微调（completion-only 损失）

## 本版目标与不做什么

本版开一条新能力线：**SFT（监督微调）/ 指令微调**——把基础语言模型训练成"会听指令"的模型，这是现代 chat 模型诞生的根本步骤。任务：给 op 标记（`C` 复制 / `R` 反转 / `S` 排序）+ 输入串，模型要在**未见输入**上生成正确输出。核心技术是 SFT 的关键机制：**只在 completion（回答）token 上计算损失**，prompt 与 padding 用 `ignore_index=-100` 掩掉。

明确不做：不在另行预训练的基座上微调（本版从零在指令数据上训练，隔离 SFT 的"监督机制"本身，这是该规模下的恰当范围）；不预设掩码一定有用（用消融 + step 扫描测量）。

## 为什么是 SFT（一次诚实的转向）

上一轮我尝试的"RoPE base × 召回距离"探针命中了可行性评审预言的 Risk 1：微型从零模型在那个 trigger-匹配任务上的拷贝信号太稀疏，连最短距离都学不到 chance 以上——学习性闸门如实拦下，报 `task_not_learned`，没有把 chance 级结果粉饰成"无 base 效应"。两次诚实失败后，按用户选择转向 SFT。这条线更可学、对"成为 AI 开发者"更有迁移价值，事实也证明它给出了干净的正面结果。

## 关键文件与链路角色

- `src/minigpt/sft_corpus.py`：合成指令数据。每条样本 `op + 输入 + '=' + 输出 + '\n'`，op 决定确定性变换；**留出输入按 op 与训练不相交**，所以留出 exact-match 衡量"把 op 应用到新输入"的泛化而非记忆。
- `src/minigpt/sft_training.py`：可复用的 `train_sft`，实现 SFT 的定义性机制——把每条 `prompt+completion` 预先 padding 成定长，构造**只在 completion token 上有效**的目标（prompt/padding 置 -100），用 `F.cross_entropy(ignore_index=-100)` 训练。`mask_prompt=False` 退化为朴素全序列损失（消融基线）。与 [[1171-v1159-minigpt-train-lm-dedup]] 的 `train_lm` 互补。
- `src/minigpt/sft_instruction_v1164.py`：`evaluate_instructions` 用贪心生成对留出 prompt 逐 op 算 exact-match；`run_sft_instruction` 跑两臂（completion_only / full_loss）× **step 扫描**（150/400/800/1500）× 多 seed，产出 accuracy-vs-steps 曲线与数据驱动的结论。
- `scripts/run_sft_instruction_v1164.py`：入口，复用 v1163 的 `script_runtime`（`choose_device`/`seed_everything`，吃了自己的狗粮）。
- 测试：`test_sft_corpus`、`test_sft_training`、`test_sft_instruction_v1164`（含"pass 当且仅当学会"不变量）。

## 为什么必须做 step 扫描（本版最关键的诚实决定）

最初只跑单个 step 数，结论会自相矛盾：600 步看"掩码明显有用"（0.60 vs 0.37），1500 步看"掩码无差异"（0.88 vs 0.72，方差重叠）。任取其一都会误导读者。于是改成 step 扫描，把"单点会翻转"这件事本身变成真正的发现：**completion-only 掩码是低算力加速器**——训练少时巨大领先，训练足够久两臂趋同。这是经过控制、可复现、诚实的结论，比任何单点都更有价值。

## 真实结果与诚实边界

GPU 运行（n_layer=4、n_embd=128、3 seeds、留出 453 条）：能力上，1500 步时对未见输入的指令遵循 exact-match=0.795（逐 op C=0.75/R=0.80/S=0.83，随机约 0.0016）。机制上，掩码优势 150 步 +0.238（0.266 vs 0.029，约 9 倍）、800 步 +0.199、1500 步 +0.019——清晰递减。`verdict=completion_only_helps_early_benefit_shrinks_with_training`。诚实边界：从零训练而非微调基座（范围声明）；full-loss 在中段方差大，恰好印证"无掩码学习更不稳定"；学习性闸门（copy@max ≥0.5）通过才报 pass。

## 测试如何真实覆盖链路

`test_sft_corpus` 钉死样本格式、op 正确性与留出输入不相交；`test_sft_training` 验证 completion-only 训练降损、两种掩码模式都能跑、block_size 过小报错；`test_sft_instruction_v1164` 验证 `evaluate_instructions` 准确率在 [0,1]、step 扫描报告形状（arm×steps 行、曲线、逐 op@max）、以及关键不变量 **status==pass 当且仅当 task_learned**——闸门逻辑被真实保护。全量套件通过。

## 一句话总结

v1164 用 SFT 让 MiniGPT 学会在未见输入上遵循 copy/reverse/sort 指令（exact-match 0.79），并用 step 扫描诚实揭示 SFT 的核心机制：completion-only 损失掩码是低算力加速器，早期把指令遵循从 0.03 抬到 0.27，训练足够久后优势收敛——现代指令微调的第一块，测得干净也讲得诚实。
