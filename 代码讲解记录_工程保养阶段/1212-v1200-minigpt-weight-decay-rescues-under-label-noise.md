# v1200 MiniGPT 权重衰减在标签噪声下"救回"泛化 代码讲解

## 本版定位：v1199 的显式正则化补集（里程碑 v1200）

v1199（双下降在 toy 尺度缺席）发现：带标签噪声、过参数化、wd=0 的 MiniGPT 插值带噪训练集、泛化差，**过参数化反而有害**，唯一杠杆是早停。v1200 问下一步：**权重衰减能救回吗？机制是真正的"拒绝噪声"还是仅仅等价早停？** 结论是诚实的 `wd_equals_early_stopping`——wd 大幅改善**收敛**泛化、机制是**真选择性拒绝噪声**，但在 5 seed 下没显著越过 wd=0 的早停最优。

## 用 Workflow 跑了 5 视角对抗设计评审（ultracode），它大幅硬化了设计

建模前用 Workflow 起 6 个 agent。它逼出的 must-fix（远超我的初稿）：
- **机制必须用翻转掩码"解离"度量**：缓存真实翻转索引，拆成 `acc_clean_subset`（非翻转行 vs 真标签，真拒绝→高）和 `fit_to_noise`（翻转行预测=翻转目标，真拒绝→低）。聚合 train_acc→1−η 对"真拒绝"和"均匀欠拟合"**完全一样**，不能用。
- **要求解离 + 欠拟合阳性对照**：只有"fit_to_noise 崩塌 WHILE acc_clean 守住"才算拒绝；加一个故意强 wd 的欠拟合对照（acc_clean 也崩）证明指标能检出欠拟合。
- **差中差归因**：v1199 证明宽模型连干净数据也过拟合，所以在 eta=0 与 0.2 都扫 wd，只有多出来的带噪改善（DiD）才算噪声特异。
- **打败强早停基线**：救回必须越过 wd=0 轨迹最小值，否则退化成"wd≈早停"。
- **固定步预算**（不训到插值，因为成功拒绝时永不到 train=1）；**seed 内配对**（同初始化扫 wd，复用 v1183）；**有效衰减 lr·wd** 作 x 轴；**logit 缩放对照**（vocab=2 tied head；不过 argmax 对均匀缩放不变，所以解离指标本身免疫，logit_norm 作辅助）。

## CPU 探针确认前提（gate GPU）

单 seed 探针扫 wd∈{0..3}：wd=3.0 给出 train_acc 0.76（≈1−η，拒绝噪声）、test_err 0.047（≈干净 Bayes）！前提强确认。但探针也暴露**非单调**（wd=1.0 比 0.3 和 3.0 都差）和"近乎完美"的 wd=3.0——提示要把网格上端拉宽（加 wd=10.0 bracket 上端）并提防 logit-缩放/优化态。

## 真实多 seed 结果（verdict=`wd_equals_early_stopping`，status=pass）

```text
剂量响应（eta=0.2，收敛 test_err）：wd0 0.368 -> wd3 0.176（内部最优）-> wd10 0.345（欠拟合）
救回：best wd=3.0 收敛 0.176 vs wd=0 早停 0.255（gap 0.079）-> rescue=False（5 seed 不显著）
机制：acc_clean 0.90 而 fit_noise 0.32（解离=True）；DiD vs eta=0 = 0.239；内部最优=True
```

**诚实的故事**：wd 大幅改善收敛泛化（0.368→0.176）、机制是**真选择性拒绝噪声**（fit_to_noise 1.0→0.32 而 acc_clean 守 0.90；最强 wd=10 处 acc_clean 崩到 0.66=欠拟合对照），DiD=0.239 说明噪声特异。**但**没显著越过早停最优（0.255）→ `wd_equals_early_stopping`：wd 达到早停**平手**（一个不需早停 oracle 的替代），不是超越早停的新机制。

## 多 seed 把单 seed 探针打回原形

单 seed wd=3.0 给 0.047；5 seed 平均 0.176（方差大）。0.047 是幸运 seed。多 seed 让"救回"统计上不显著越过早停——与 v1199（单 seed signal-before-noise 没扛过多 seed）同一教训。

## 在真实 Phase-A 数据上自抓自修的 3 个 decide() 阈值伪影（本弧第 9–11 个）

1. **substrate_unsound 误触发**：基底判据原查 eta=0 在**最宽**宽度**收敛**干净误差≤0.12——但宽模型连干净也过拟合。改用**最佳可达**（早停）干净泛化（最佳 0.04 ≤0.12）。
2. **budget_unconverged 误触发**：收敛原用末段**极差**，但测试误差天然抖动；改用相邻十分位**均值之差**（drift 非抖动），且只在 verdict 直接比较的 NOISE 臂点（wd=0+best_wd）设闸（震荡的 eta=0 对照与 wd=10 端只刻画形状）。
3. **dissociation knife-edge**：原用 acc_clean≥0.90 绝对阈，实测 0.899 差 0.001 误判 False；改用**控制相对**判据（拒绝噪声 + 选择性差≥0.30 + 明显高于最强 wd 欠拟合对照）稳健给 True。

每个都是原则性校准修正（基底=最佳可达、收敛=drift、解离=控制相对），不是为讨喜调阈。verdict 在这些修正下仍是诚实的 `wd_equals_early_stopping`（救回不显著越过早停这一结论不变）。

## 工程

Phase A（`run_wd_noise_v1200.py`）每 seed 一份 (teacher,数据,翻转掩码,初始化)，seed 内配对扫 wd（两个 eta），固定步预算、记录完整轨迹 + 末态翻转掩码指标 + logit_norm + 翻转索引。Phase B（`analyze_wd_noise_v1200.py`）纯 CPU 重判救回/解离/DiD/内部最优 + wd 网格稳健（丢极端点），零重训。这些 toy 模型 GPU 上 launch-bound，60 臂×8000 步偏慢。10 个测试（合成缓存跑 decide 阶梯全分支 + 微型真实 Phase-A 烟测）。

一句话总结：v1200 在 v1199 基底加权重衰减——剂量响应显示 wd 大幅改善带噪收敛泛化（0.368→0.176，wd=3.0 内部最优）且机制是真选择性拒绝噪声（fit_to_noise 1.0→0.32 而 acc_clean 守 0.90、DiD 0.239 噪声特异、最强 wd 欠拟合对照证明指标有效），但 5 seed 下没显著越过 wd=0 早停最优 → 诚实 `wd_equals_early_stopping`（早停平手、不需 oracle 的替代）；5 视角 Workflow 评审硬化了翻转掩码解离/DiD/打败早停基线/固定预算等设计，多 seed 把单 seed 探针 0.047 打回 0.176，真实数据上自抓自修 3 个 decide 阈值伪影。**不是**大模型断言。
