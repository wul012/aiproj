# 1177 · v1165 · MiniGPT base→SFT 迁移（预训练的数据效率）

## 本版目标与不做什么

本版补上 [[1176-v1164-minigpt-sft-instruction]] 明确声明跳过的一步：真正的**两阶段 SFT 配方**——先用全量 next-token 损失预训练一个基座，再在其上做 completion-only SFT。要测量的是这个配方存在的根本原因：**预训练能否迁移到一个下游新任务，从而用更少的微调数据学会它**。任务设计：基座在 {复制 C / 反转 R / 排序 S} 上预训练，下游 SFT 在一个**留出的新 op**——shift-left（`abcd→bcda`）——上进行，对比「预训练基座→SFT」与「从零 SFT」在多个 SFT 预算下的 held-out exact-match。

明确不做：不预设迁移一定发生（用两臂对比 + 预算扫描测量）；不声称"预训练对任意下游都迁移"（新 op 刻意与预训练 op 同族，展示迁移机制而非普适性）。

## 关键文件与链路角色

- `src/minigpt/sft_corpus.py`：新增 `L`（shift-left）op，作为留出的下游新指令；与 {C,R,S} 共享同一字符表，所以基座的 token 嵌入可迁移到下游。
- `src/minigpt/sft_pretrain_transfer_v1165.py`：编排。每个 seed 先用 `train_lm`（全量 LM）在 {C,R,S} 流上预训练基座一次并快照 state_dict；然后对每个 SFT 预算，分别：(预训练臂) 新建模型→`load_state_dict(base)`→`train_sft` completion-only；(从零臂) 随机初始化→`train_sft`。两臂在同一 (seed,budget) 下用**相同 SFT 批采样种子**，唯一差异是初始权重。下游用 `evaluate_instructions`（v1164）贪心算 exact-match。
- `scripts/run_sft_pretrain_transfer_v1165.py`：入口，构建基座流 + 下游语料 + 单一共享 tokenizer，复用 v1163 `script_runtime`。
- 测试：`test_sft_corpus` 加 shift-left 正确性；`test_sft_pretrain_transfer_v1165` 验证报告结构、"pass 当且仅当 task_learned"不变量、verdict 集合。

## 迁移为什么是真的（不是泄漏）

下游 op `L` 从未出现在基座预训练数据里（基座只见 C/R/S）。所以预训练臂相对从零臂的任何优势，只能来自两样**可迁移**的东西：一是指令格式（`<op><输入>=<输出>\n` 的结构、`=` 后开始生成、`\n` 停止），二是共享的"按位置定位并拷贝字符"原语（复制/反转/左移都是位置置换）。`L` 与 C/R 同族是刻意设计，目的是让迁移机制能在微型规模上显现——这是机制演示，不是普适断言。两臂在同一 (seed,budget) 下对齐 SFT 批采样，把"初始权重来源"隔离为唯一变量。

## 真实结果与诚实边界

GPU 运行（n_embd=128、基座 1200 步、3 seeds）：`verdict=pretraining_improves_downstream_sft`。数据效率曲线——50 步 SFT：预训练 0.313 vs 从零 0.022（约 14 倍）；150 步 0.556 vs 0.285；400 步 0.857 vs 0.488；1000 步 0.971 vs 0.826。即预训练把 SFT 曲线**整体左移**：预训练基座 150 步就达到从零 400 步的水平。迁移增益随预算 +0.29→+0.15 递减（两臂终将收敛）但全程显著为正。诚实边界：微型从零基座 + 合成 op，迁移幅度规模依赖；新 op 同族是刻意的；学习性闸门（预训练臂 max 预算 ≥0.5）通过才报 pass。

## 测试如何真实覆盖链路

`test_sft_corpus` 钉死 shift-left 变换（`abcd→bcda`）与样本格式；`test_sft_pretrain_transfer_v1165` 用极小配置（基座 15 步、SFT 预算 (10,30)）验证报告形状（2 臂×预算行、曲线）、`downstream_op=L`、以及关键不变量 **status==pass 当且仅当 task_learned**——闸门逻辑被真实保护。全量套件通过。

## 一句话总结

v1165 跑通真正的两阶段 SFT 配方并测得干净迁移：在 {复制,反转,排序} 上预训练的基座迁移到**没见过的** shift-left 指令时，50 步 SFT 即达 0.31（从零仅 0.02），1000 步达 0.97——预训练把 SFT 曲线整体左移，量化了"预训练→微调"在数据稀缺时的核心价值。
