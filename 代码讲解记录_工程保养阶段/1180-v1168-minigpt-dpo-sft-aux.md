# 1180 · v1168 · MiniGPT DPO+SFT 辅助项（NLL 正则化 DPO 的诚实印证）

## 本版目标与不做什么

[[1178-v1166-minigpt-dpo-preference]] 测得原始 DPO 优化相对边际、会压垮 logp(chosen) 让生成回退，而纯 SFT-on-chosen 更好；v1166 的探针点名了"上行"修法：给 DPO 加 chosen-NLL（SFT）辅助项 `L = L_DPO + λ·SFT_CE_mean(chosen)`（即 NLL 正则化 DPO / DPO+SFT / RPO）。本版沿 λ 扫描测量：某个 λ>0 能否救回生成？救回后偏好项是否比纯 SFT 多做了什么？

明确不做：不当人类偏好/RLHF（合成确定性正确性信号）；不预设辅助项有上行收益（用 λ 扫描 + 两个端点锚测量）；不靠重跑凑结果。

## 设计先于 GPU（会话限额下仍守纪律）

按 [[1174-v1162-minigpt-rope-length-extrapolation]] 立的范式先开对抗式评审。本次评审中途触发会话限额，仅 Lens B（损失正确性）跑完。但**关键的可行性探针我在主线程亲自跑**（Lens B 失败前已写好探针脚本），拿到经验数据后自行综合锁定设计，没有空等限额。这本身是一条经验：评审的价值在"先跑代码证伪/校准"，谁来跑代码次要——主线程能跑就主线程跑。

## 关键文件与链路角色

- 新增 `src/minigpt/dpo_sft_aux_v1168.py`：
  - `chosen_logp_and_ce(model, examples, pad_id, *, device)`：**一次** chosen 前向同时产出 (a) 求和 completion logp（DPO 项，与 `logp_completion` 逐值一致）和 (b) 逐 token 平均交叉熵（SFT 辅助项，与 `train_sft` 同 reduction/同掩码）。这是 Lens B 的核心要求——λ→∞ 才会收敛到 SFT-on-chosen、λ=0 才复现原始 DPO。
  - `train_dpo_sft(..., sft_aux_lambda)`：`L = dpo_loss(...) + λ·ce_aux`；λ=0 即原始 DPO。复用 v1166 的 `dpo_loss`/`logp_completion`、冻结参考。
  - `run_dpo_sft_aux(...)`：臂 = sft_init / dpo_aux_l{λ}（含 λ=0 原始 DPO）/ sft_on_chosen；所有臂共用同一基座克隆 + 同一批采样种子，唯一差别是损失。复用 `experiment_utils`（含本版从 v1166 提升来的 `significant`）、`evaluate_preference`/`evaluate_confusable`（v1166）、`evaluate_instructions`（v1164）。
- 新增脚本 `scripts/run_dpo_sft_aux_v1168.py`、测试 `tests/test_dpo_sft_aux_v1168.py`。
- 顺带保养：`significant`（gap-减-合并标准差判定）在 v1167 被刻意留在 v1166 本地（单用户）；本版成为第二个使用方，遂提升进 `minigpt.experiment_utils` 并迁移 v1166——这正是 v1167 "出现第二个使用方再抽取" 的约定兑现。

## 公平性与正确性的三个锚

- **算力轴 = 前向次数：** DPO+aux 每步 2 次策略前向（chosen 融合 + rejected），故 SFT-on-chosen 在同预算下拿约 2 倍优化步——对控制臂更有利，强化"SFT 不输"。
- **λ=0 ≡ 原始 DPO：** 单元测试用同 seed/同批、逐参数 `allclose` 钉死（λ=0 时辅助项 ×0 不产生梯度，更新与 v1166 `train_dpo` 完全一致）。
- **闸门复用 v1166：** 基座 em 在 [0.40,0.85]、λ=0 的 DPO 损失在下降、边际可改善（用 λ=0 臂判定）；`status=pass` 只代表对比有效可测。

## 真实结果与诚实边界

GPU（3 seeds、基座 3000 步标定到 em≈0.51）：`verdict=dpo_sft_aux_recovers_generation_matches_plain_sft`。λ=0 把 em 砸到 0.142（Δlogp(chosen)=−23）；λ≥0.25 救回到 0.62-0.68，最佳 λ=1.0 达 0.684（Δlogp(chosen) 愈合到 −0.1）——**辅助项确实救回生成（框架 A 成立）**。但最佳 λ 的 0.684 与 SFT-on-chosen 0.739 在合并标准差内**无法区分**（`matches_sft=True`、`beats_sft=False`）；探针里 DPO+aux 把易混错误压到 0、SFT 留在 0.073 的优势，在真实规模因基座 conf 本就只有 0.023 而消失（`suppresses_confusable_vs_sft=False`）。诚实结论：**NLL 辅助项修好了 DPO 的破坏性，但偏好项相对纯 SFT 没有可测的额外能力**；DPO+aux 保留了更高边际（λ=1：49 vs SFT 24）却不转化为能力——"边际≠能力"的延续。规模依赖、合成信号等边界同 v1166。

## 测试如何真实覆盖链路

`chosen_logp_and_ce` 的求和 logp 与 `logp_completion` 逐值一致、mean-CE 与同掩码 `F.cross_entropy` 一致；**λ=0 逐参数复现 v1166 `train_dpo`**（Lens B 的硬锚）；λ>0 确实改变更新；run 报告结构 + "status==pass 当且仅当 task_learned" 不变量 + verdict 集合 + `vanilla_dpo_verdict`。v1166 既有测试在 `significant` 迁移后零改动仍绿。全量套件通过。

## 一句话总结

v1168 给 DPO 加 chosen-NLL 辅助项并诚实测得：辅助项把原始 DPO 砸坏的生成救回（0.14→0.68，Δlogp(chosen) −23→0），但只追平、未超过算力对齐的纯 SFT（0.74），探针中的易混压制优势在真实规模因基座少犯而消失——修好了破坏性，偏好项却没带来超过 SFT 的能力，是对 "边际≠能力" 的又一次诚实印证；过程上还在会话限额下靠主线程亲跑探针守住了"先跑代码"的评审纪律。
