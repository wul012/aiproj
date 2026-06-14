# 1178 · v1166 · MiniGPT DPO-lite 偏好微调（边际升、生成退的诚实教训）

## 本版目标与不做什么

把对齐流水线推进到 [[1177-v1165-minigpt-sft-pretrain-transfer]] 之后的下一步：**偏好微调 DPO 这个损失**。在偏好三元组 (prompt, chosen, rejected) 上优化 `L = -E[log σ(β·((logp_w-logp_l)-(logp_w^ref-logp_l^ref)))]`，其中 `chosen` 是指令的正确输出、`rejected` 是**同一输入上易混 op** 的输出（`Rabc=` 的 chosen `cba` vs 排序的 `abc`），`logp` 是 completion token 对数概率之和（prompt+pad 用与 SFT 一致的掩码）。

明确不做：不把这当人类偏好/RLHF（chosen 是唯一正确答案，"偏好"=正确性）；不预设 DPO 提升能力（用三臂 + 预算扫描测量）；不靠重跑凑 pass。

## 设计先于 GPU：对抗式评审推翻讨喜叙事

开 GPU 前先跑对抗式设计评审（Workflow，3 怀疑视角 + 1 个真实 CPU 探针**先跑代码**，复用 [[1174-v1162-minigpt-rope-length-extrapolation]] 立下的范式）。探针在 8/8 个 (lr×β) 网格里证伪了三个天真假设：①「DPO 同升边际与 exact-match」假——DPO 优化**相对**边际，logp(chosen) 会跌只要 logp(rejected) 跌更快，生成回退；②「负样本压制易混错误胜过只用正样本 SFT」假——算力对齐的 SFT-on-chosen 在生成上完胜；③「参考/KL 项是稳定关键」本规模不支持（零结果）。评审把这些锁进了实验规格。

## 关键文件与链路角色

- `src/minigpt/dpo_preference_v1166.py`：核心。`logp_completion`（per-sequence 求和、复用 `train_sft` 的逐 token 掩码、logits[:, :-1] 与 labels 对齐）；`dpo_loss`（`use_reference` 开关零化 margin_ref）；`train_dpo`（ref 冻结 eval+no_grad，其 logp 常量预算一次后按批索引）；`build_confusable_preferences`（循环下一个 op 作易混负样本，丢弃并计数 chosen==rejected 退化对）；`evaluate_preference`/`evaluate_confusable`；`run_dpo_preference`（四对象：dpo_with_ref / dpo_no_ref / sft_on_chosen 控制臂 / sft_init 参照）。
- `scripts/run_dpo_preference_v1166.py`：入口，构语料→tokenizer→三元组→跑→5 格式产物，复用 v1163 `script_runtime`。
- 测试：`tests/test_dpo_preference_v1166.py`（14 例）。

## 公平性与三个隔离变量

- **算力轴 = 前向次数**（4060 真实付出的成本）：DPO 每步 2 次策略前向（chosen+rejected），故 SFT-on-chosen 在同预算下拿约 2 倍优化步——这反而对控制臂更有利，强化"SFT 胜"的结论。
- **带 ref / 无 ref**：同一基座克隆 + 同一批采样种子，唯一差别是损失是否减 margin_ref。
- **第 0 步不变量**：ref==policy 时相对边际为 0、DPO 损失恰为 log2（单元测试钉死），防止参考模型未冻结/掩码错位等"看似在训其实错"的 bug。

## 真实结果与诚实边界

GPU 运行（4L/128、SFT 基座 3000 步标定到头部区间、3 seeds）：`verdict=dpo_raises_margin_but_generation_regresses`。max 预算下——边际 14.3→**86.1**（约 6 倍），pref-acc 0.97→1.00（已近天花板），但 held-out exact-match 0.588→**0.104**，Δlogp(chosen)=**−26.7**；控制臂 SFT-on-chosen→**0.758**（完胜 DPO）；无 ref 0.141≈带 ref（参考项零结果）；网格 4 格全在基座下，严重度随 lr 与 1/β 缩放。诚实边界：pref-acc 在基座已饱和（排序比生成易），故闸门与"目标是否在动"用**边际可改善性**（稳健，不受 GPU 非确定性翻转），不用 pref-acc——这是把 v1166 第一次因 pref-acc 闸门翻转而 review 之后的方法学修正，不是凑结果。`status=pass` 只代表对比有效可测，**不代表 DPO 好**。

## 测试如何真实覆盖链路

`logp_completion` 等于同掩码下的 `-CE_sum`（对照手写循环与 reduction='sum' 交叉验证），且对批内 padding 宽度不变（因果掩码）；ref==policy 时第 0 步损失==log2、相对边际==0；`train_dpo` 后参考模型 requires_grad 全 False 且权重逐键不变；退化对（回文反转）被丢弃计数；run 报告结构 + **status==pass 当且仅当 task_learned** 不变量 + verdict 集合 + 算力轴（dpo opt_steps=budget//2、sft=budget）。全量套件通过。

## 一句话总结

v1166 实现 DPO 损失并诚实测得其本性：在训弱的 SFT 基座上 DPO 把偏好边际拉高约 6 倍，但因优化的是**相对**边际，logp(chosen) 反跌、held-out 生成从 0.59 崩到 0.10——而前向次数对齐下只做正样本 SFT 反升到 0.76，参考项本规模无可测作用。偏好准确率上升 ≠ 能力提升，这正是本实验的意义，也是对抗式评审先跑代码先证伪的价值。
