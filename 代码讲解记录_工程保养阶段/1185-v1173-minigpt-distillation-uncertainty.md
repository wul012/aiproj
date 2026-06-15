# 1185 · v1173 · MiniGPT 不确定性下的蒸馏：dark knowledge 做成真的（v1172 镜像）

## 目标与边界

v1172 证明确定性任务上 teacher 近 one-hot、dark knowledge 不存在、蒸馏=硬标签。v1173 做镜像：构造**随机**任务，每 context 映射到已知多模分布 `P_true`（Dirichlet、熵可控），teacher 输出真软，单硬样本刻画不了分布——Hinton dark knowledge 该出现处。度量精确：在唯一随机输出位置测 `KL(P_true‖P_student)`。`status==pass` 只证对比有效（teacher 软且忠实、有熵结构、基线有效、控制齐全），不等于蒸馏好。范围：单位置下一字符类别；KL 越低越好 → 所有比较经 `beats_lower`。

## 入口与核心实现（`src/minigpt/distill_v1173.py`）

- `beats_lower(a,sa,b,sb)=significant(b,sb,a,sa)`：把项目"越高越好"的 significant 反成"a 显著更低（更好）"——面板的头号阻断点（KL 是损失，直接调 significant 会反向误判）。
- `build_stochastic_task(K, seed)`：K 个 context，每个 `Dirichlet(α)`（α geomspace 扫低→高熵）抽一个 categorical，返回 `P_true(K,M)`、`H(K)`、context/output 字符。
- `student_P(model, contexts, out_ids)`：喂 `[ctx,'=']`、softmax 末位 logits、切 output 字符；返回 (renorm 条件分布, 原始 output 质量, 泄漏)。**新读出，不复用 exact-match**。
- `kl_fwd`（renorm 条件 KL，头条）、`kl_full`（用未归一化质量，**惩罚泄漏**）、`entropy`、`ols_slope_se`（熵回归斜率+标准误）、`eps_for_entropy`（二分求使平滑 one-hot 熵=目标的 ε）。
- 复用 `distill_v1172.train_student / kl_term / shuffle_residual_mass`；**对 train_student 做了向后兼容扩展**：新增可选 `teacher_probs_fn`，distill 模式下若提供则用它当软目标（v1173 的 `oracle_true_P` 注入 `P_true`），默认 None=v1172 原行为（v1172 测试 14 项仍绿）。
- `decide(...)`：纯闸门+判决。

## 数据布局（去 EOS = 单监督位）

completion=`[x]`（**去掉 `\n`**），full=`[ctx,sep,x]`、n_prompt=2 → `_build_xy` 恰好只在预测 x 的那个随机位置打标签（否则确定性 `\n` 位把 KL 稀释 50%）。teacher 软目标在该位 = `P(·|ctx)`。oracle 目标 `teacher_probs_fn` 用 `Ptrue_full[k_of_ctx[x[:,0]]]`（带 1e-6 floor 防 log0、广播到所有位，掩码外不计）。

## 6 个臂 + 三分解 + 扫描

ARM_ORDER=[scratch_hard, teacher_argmax_hard, teacher_soft, label_smooth, shuffled_teacher, oracle_true_P]，每 (arm,seed) 独立 init（`seed_base+1009*arm_idx+seed`），**每 seed 重抽学生样本**（探针固定抽样种子=测 init 方差非抽样方差）。**数据效率**=KL(scratch_hard)−KL(argmax)；**DARK KNOWLEDGE（头条）**=KL(argmax)−KL(soft)（同 teacher 同 400 预算，众数 vs 软形状）。控制：label_smooth（ε 匹配平均熵）、shuffled_teacher（毁残差身份、应变差）、oracle（上界）。`scratch_many` 样本数扫描 {1,3,10,30,100,400}=数据效率曲线（诚实证伪"魔法"）。teacher 训 ≥3 seed 报 KL 天花板均±std，distill 目标取 seed-0 teacher。

## 闸门与判决

g1 teacher 忠实（KL(true‖teacher)≤α·mean_H 且泄漏<阈）、g2 真熵结构（mean_H>floor 且 spread≥0.8）、g5 控制有限→否则 review。判决（经 beats_lower）：soft 不胜 hard→`no_distill_benefit`；soft≈argmax→`data_efficiency_not_dark_knowledge`；soft≈label_smooth→`soft_target_generic_not_specific`；扫描 n=400 不追平→`dark_knowledge_transfer_not_recoverable`；全满足→`dark_knowledge_is_data_efficiency_under_uncertainty`。熵回归在 **soft-vs-argmax** 上（soft-vs-真硬随熵涨是平凡的，netted out）。

## 测试（`tests/test_distill_v1173.py` 17 项）

beats_lower 方向（阻断 bug 守卫）、去 EOS 单监督位、KL 恒等(NLL=KL+H)、kl_full 惩罚泄漏、eps_for_entropy、ols_slope、build_stochastic_task（形状/熵谱≥0.8）、decide 五判决（表驱动，std 调到使预期显著性成立）、shuffle 软目标增大 KL-to-true、端到端 smoke。

## 运行证据（RTX 4060，5 seeds，K=32）

`status=pass`、`dark_knowledge_is_data_efficiency_under_uncertainty`、六 flag 全 True。teacher KL 0.041、熵 1.16≈真 1.13。臂 KL：oracle 0.002 / **soft 0.050** / label_smooth 1.30 / **shuffled 2.42(变差)** / argmax 3.52 / scratch_hard 4.48。**数据效率 0.96、DARK KNOWLEDGE 3.47**；dark-knowledge 随熵斜率 3.31（下界 3.05>0），数据效率混淆斜率仅 0.30；scratch_many n=400→0.047≈soft（恢复 P=不是魔法）。熵偏差：hard/argmax −1.12（塌 one-hot），soft/oracle ≈0（匹配真熵）。全量 pytest 绿。

## 一句话总结

dark knowledge = 单硬样本传达不了的分布信息：仅当 teacher 软时存在、随熵增长、足量硬数据可恢复（不确定性下的数据效率，非魔法）。与 v1172 合成完整诚实结论——蒸馏何时、为何有用；同一机器、相反结果，差别只在 teacher 的熵。
