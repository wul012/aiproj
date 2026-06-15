# 1184 · v1172 · MiniGPT 知识蒸馏：label transfer 而非 dark knowledge

## 目标与边界

新轴=能力迁移。teacher（4L/64）经逐 token KL 把"知识"蒸到更小 student，与从零硬标签 SFT 在同参数同步数下对比。`status==pass` 只证明对比**有效**（teacher 可学、scratch 离地板、有余量、对照齐全），绝不等于蒸馏好。范围：B=1、teacher-forced 金路径 logit KL、char 级确定性任务（dark knowledge 按定义不存在）。

## 入口与核心实现（`src/minigpt/distill_v1172.py`）

- `kl_term(student_logits, teacher_probs, mask, tau)`：Hinton KD 的逐 token KL，带 `tau²` 梯度匹配修正，仅在 completion 掩码位平均；student==teacher 时为 0。抽成独立函数便于测试。
- `shuffle_residual_mass(probs, perm)`：**shuffled_teacher 对照**的核心——每 token 保住 argmax 槽与其概率（→ argmax 索引、max-prob、熵都不变），把**非 argmax 残差质量**按固定置换 `perm` 重排（破坏"哪个错误类别拿多少残差"的身份）。向量化：`noncol = arange(V)!=argmax`，`probs[noncol].view(B,T,V-1)[...,perm]` 再 scatter 回。
- `train_student(...)`：一个训练函数覆盖所有臂。`loss_mode="ce"` = 硬标签 SFT（`label_smoothing` 可选，=0 时等价 train_sft）；`loss_mode="distill"` = `hw*CE + (1-hw)*kl_term(...)`，teacher 在 no_grad 下给 `p_T=softmax(zT/tau)`（shuffled 臂再过 `shuffle_residual_mass`）。
- `teacher_logit_stats(...)`：completion 位 softmax 的 mean max-prob 与熵（nats）——dark-knowledge 测量（近 one-hot ⇒ 无）。**注意把 X/Y 移到 teacher 所在 device**（首版 GPU 跑因 X 在 CPU、teacher 在 cuda 而崩，已修）。
- `decide(cell, teacher_em, teacher_maxprob, headroom)`：纯函数闸门+判决，便于测试。

## 8 个臂 + 独立 init（杀掉共享 init 混淆）

ARM_ORDER = [scratch_hard, label_smooth, shuffled_teacher, distill_tau1_hw0, distill_tau1_hw05, distill_tau2_hw0, distill_tau2_hw05, scratch_long]。每个 (arm, seed) 用 `torch.manual_seed(seed_base + 1009*arm_index + seed)` **独立 init**——使项目无配对的 `significant`（gap−combined_std）检验成立（探针的共享 init 是被点名的混淆，不带入 GPU）。能干尺寸 2L/32 跑全部 8 臂；其余 4 个尺寸只跑曲线子集 {scratch_hard, label_smooth, distill_tau1_hw0} 画 Δ-vs-gap 曲线。teacher 全程训练一次复用。

- `label_smooth`（对照）：`F.cross_entropy(label_smoothing=eps)`，`eps=(1-teacher_maxprob)/(1-1/V)` 把正确类概率匹配到 teacher 置信度 → 减掉**通用软标签正则**。
- `shuffled_teacher`（对照）：KL 到保熵保 argmax、打乱残差身份的 teacher → 隔离**类别身份/dark knowledge**。
- `scratch_long`（同算力对照）：步数 `round(700*(1+teacher_params/(3*student_params)))`，把 teacher 前向算力折给 scratch。

## 闸门与判决

能干 2L/32 处：`status=pass` IFF (G1) teacher_em≥0.5 且 (G2) scratch 显著>chance（离地板）且 (G3) teacher−scratch≥0.05（有余量）且 (G4) 两对照跑出有限 EM；否则 review（no_valid_distillation_headroom / controls_missing）。判决（确定性函数）：`no_distill_benefit`（distill τ1 未显著>scratch）| `distillation_helps_via_logit_matching_not_dark_knowledge`（同时显著胜 scratch+label_smooth+shuffled 且近 one-hot）| `gain_is_generic_soft_target_regularization`（胜 scratch 但打平某对照）| `distill_gain_is_faster_convergence_not_better_asymptote`（胜 scratch 但 scratch_long 追平）。预注册主对比只有 distill_tau1_hw0，避免 grid 上 argmax 选择偏差；hw=0.5 等为次要、不可凭其判 pass。

## 设计先于 GPU + 测试

对抗式面板把探针的 +0.058 判定为不可证伪假象，要求独立 init/5 seeds/两对照/同算力对照——全部落实。新增 `tests/test_distill_v1172.py` 14 测：KL 自蒸=0、tau² 缩放、掩码、shuffled 不变量（保 argmax/max-prob/熵、变身份）、独立 init 契约、`decide` 的各判决（含 no-headroom→review、logit_matching、generic、no_benefit）、端到端 smoke。

## 运行证据（RTX 4060，5 seeds，独立 init）

`status=pass`、`verdict=no_distill_benefit`、teacher EM 0.858 近 one-hot（max-prob 0.989、熵 0.037）。2L/32：scratch 0.773±0.111、**distill τ1 0.757±0.101（Δ−0.016，未>0）**、label_smooth 0.783≈scratch、shuffled 0.761≈scratch；**τ2 0.803 > τ1 0.757（τ 序较探针反转）**；**scratch_long(2485 步) 0.949 远超全部**。容量曲线 Δ(distill−scratch) 全程为负（−0.006…−0.084），"中等容量峰值"预测被证伪；最小 1L/16 训练集 EM 仅 0.05=优化地板（非容量上限）。全量 pytest 绿。

## 一句话总结

确定性任务上 teacher 近 one-hot、dark knowledge 按定义不存在；探针看似的 +0.058 在 5 seeds 独立 init 下蒸发并反号，两对照打平基线（既无 teacher 专属信号也无显著通用正则），而**同算力下让学生多训（scratch_long 0.949）完胜任何蒸馏**——`no_distill_benefit` 是诚实结论，设计面板+多种子+对照+同算力联手识破了讨好性的单种子结果。
