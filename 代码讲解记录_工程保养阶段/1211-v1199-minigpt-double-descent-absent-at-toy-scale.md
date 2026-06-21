# v1199 MiniGPT 双下降（玩具尺度下不出现）代码讲解

## 本版定位：归纳轴收口后的新轴——双下降（一个诚实的零结果 + 反直觉发现）

归纳机制三连（v1196 行为"需要深度"→v1197 机制 QK→v1198 机制 OV）收口后，开一条**新轴**：双下降（Belkin 2019；Nakkiran "Deep Double Descent" 2019）——测试误差随容量**非单调**：先降、在**插值阈值**冲高、再在过参数化区**第二次下降**。在小 MiniGPT 上诚实检验，结论：**这个尺度下双下降不出现**，模型是**单下降**过拟合，且**过参数化反而单调变差**。

## 用 Workflow 跑了一个 5 视角对抗设计评审（ultracode）

建模前用 Workflow 起了 6 个 agent（5 个独立批判视角 + 1 个综合）。它逼出的 must-fix：(1) **别用 a+b mod p**——取模是 grokking 基底，width 曲线会被"哪个宽度在预算内 grok 了"主导（时间轴伪装成容量轴）；(2) **先跑 CPU 探针、用它 gate 所有 GPU 花费**；(3) 训到插值要按**训练**准确率早停（不按测试，否则混进 epoch-wise）；(4) **经验地**定插值阈值（不用 #参数≈#样本 公式）；(5) 主臂 wd=0/dropout=0/不早停（一切正则都压制峰）；(6) 标签噪声每 seed 冻结、测试集干净不相交；(7) 显著性 + 多 seed + co-location 闸。其中一个视角**自己跑了探针**，发现 **parity 永不插值带噪标签**——直接救我换基底。

## 4 个 CPU 探针把方向钉死（每个都 gate 了 GPU）

1. **parity model-size**（评审视角跑的）：不插值、无峰 → parity 是死基底。
2. **halfspace model-size 小预算**（3500 步）：边缘信号但欠训练污染（峰在没插值的宽度上）。
3. **halfspace sample-wise**（固定宽扫 N）：单调、无峰；且发现噪声插值阈值远比"#参数"估计的小。
4. **halfspace model-size 大预算 + 3 seed**：模型确实插值了，但**没有阈值处的峰、没有第二次下降**，大宽度反而泛化更差，seed 间不一致。
5. **epoch-wise 轨迹**（w16/w32，30k 步）：插值后测试误差**上升**（先学信号 best 0.23 再记噪声），但**没有回落**（recovery≈0）= 单纯过拟合。

结论：双下降三种形态（model-size / sample-wise / epoch-wise）在此尺度都不出现。这正中评审 risk #1（"现象在 toy 尺度可能根本不存在"）。

## 任务与容量轴

固定随机半空间教师（L=21 bit，标签 sign(w·(2bit−1))），训练集固定、eta 比例标签翻错、测试集干净不相交。容量轴 = `eff_params`（去掉 tied lm_head/嵌入后的**非嵌入**参数，因为 tied lm_head 不加自由参数）。两条臂：model-size（扫 width，训到插值）、epoch-wise（固定宽扫步）。

## 真实结果（5 seed，verdict=`no_double_descent_monotone`，status=pass）

```text
有效性：eta=0 对照可学（最佳 0.041≪0.12 且插值）；带噪确实插值 w_interp=16；5 seed；tau 网格 100%。
MODEL-SIZE（eta=0.2 test_err）：w3 0.247(tr.84) ... w16 0.338 ... w32 0.389 ——越过插值后**单调变差**，
   最佳在欠参数化端 -> 过参数化 HURTS，无第二次下降。eta=0 对照也随宽度变差（0.04->0.25）。
EPOCH-WISE（w32）：插值前最好 0.314 -> 平台 0.389（升 0.075），但 eta=0 也升 0.051 -> 只**部分**归因噪声；
   recovery 0.009 -> 无回落 -> epoch_dd=False，单下降过拟合，早停最优。
```

## 一个被多 seed 诚实修正的现象

单 seed 探针里 epoch-wise 有漂亮的"先学信号(0.23)再记噪声"下凹；但 5 seed 下 best_pre 涨到 0.31、干净对照也在时间上过拟合，所以 `signal_before_noise` **没**跨 seed 稳健成立 → 保守落在 `no_double_descent_monotone`，不升格。多 seed 修正掉单 seed 的脆弱漂亮现象——和 v1196 把单 seed 大宽度 drop 诚实归因为优化、v1183/v1191 自查 decide 阈值伪影一脉相承。

## 一个在 Phase A 真实数据上抓到的 decide() bug

Phase A 出来后发现：eta=0 对照在**最宽**宽度的干净测试误差是 0.246（>substrate_err 0.12），因为宽模型连干净数据都过拟合。我的 `ctrl_ok` 闸原本查**最宽**宽度 → 会误判 `substrate_unsound`。修正为查**最佳**宽度（任一宽度同时插值且泛化 <0.12 即算基底成立——w4 给 0.041）。这是"基底可学"该有的判据。

## 诚实零结果的定位

`status==pass` 只认**有效**测量：对照可学、带噪**确实插值**（在测插值后区间、不是够不到阈值）、≥4 seed、tau 稳健。在这些前提下诚实报告"无双下降"。与蒸馏 v1172（无收益）、PTQ v1175（逐通道是单 seed 伪影）同源——零结果是被珍视的、可发布的结果。

## 工程

Phase A（`run_double_descent_v1199.py`）一次训完两条臂、缓存每条 (arm,eta,width,seed) 结果 + 完整轨迹 + 插值标志；Phase B（`analyze_double_descent_v1199.py`）纯 CPU 重判 + 插值-tau 稳健，零重训。这些 toy 模型在 GPU 上是 launch-bound（与 v1196 同病），epoch 臂 240k 步因此偏慢。9 个测试（合成缓存跑 decide 阶梯全分支：no-DD-monotone / signal-before-noise / model-size-DD / epoch-DD / substrate-unsound / threshold-unreachable / too-few-seeds + 报告形状 + 微型真实 Phase-A 烟测）。

一句话总结：v1199 在小 MiniGPT 上诚实检验双下降——半空间带标签噪声任务，model-size（扫宽度训到插值）与 epoch-wise（固定宽扫步）两条臂都无第二次下降，过参数化反而单调变差、最佳泛化在欠参数化端，epoch-wise 插值后只升不回（早停最优）；5 视角 Workflow 评审 + 4 CPU 探针钉死了基底（parity 死→半空间）与方向，多 seed 把单 seed 的 signal-before-noise 漂亮现象诚实修正回保守的 `no_double_descent_monotone`，Phase A 真数据上自抓自修了一个 ctrl_ok 闸的 bug；status=pass 只认有效测量。**不是**断言双下降在大模型里不存在（在大模型里有充分记录）。
