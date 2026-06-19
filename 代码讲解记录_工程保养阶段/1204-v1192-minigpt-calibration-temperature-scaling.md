# v1192 MiniGPT 校准 + 温度缩放 代码讲解

## 本版定位：开新轴

grokking/可解释性这条线在 v1191 已经因果收尾。v1192 是一条**全新的能力轴：校准（calibration）**。此前所有版本量的都是*准确率*或*分布保真度*（v1173 的 `KL(P_true||P_model)`），从没量过校准——**模型给出的置信度可信吗？** 我复用 v1173 的随机 Dirichlet 任务（`build_stochastic_task`：K=32 个上下文，每个有已知类别分布 `P_true`，熵被扫开），所以校准能对着一个**精确的 oracle** 来量，而不是只对采样。

开工前先跑了对抗式设计评审（5 个独立批评视角 + 综合），再用一个 CPU 探针验证 regime——这俩都在写正式代码之前完成，沿用本项目"先证伪/标定，再花算力"的纪律。

## 设计评审抓到的关键问题（写代码前就改掉）

1. **采样 ECE 有 Jensen 正偏**：经验准确率是二项比例，完美校准的模型在有限采样上 ECE 也 >0，拿它跟 0 地板比会**凭空造出过自信**（v1183 单阈值伪影那一类）。解法：因为我们*构造*了 `P_true`，就**解析地**算 ECE/NLL/Brier/KL；oracle 的解析 ECE 恰好是 0（每上下文 confidence ≡ true accuracy）。采样 ECE 只留作旁证，正好量出 oracle 采样地板 0.003 > 0，反证为何要用解析。
2. **NLL 就是 KL 换皮**：期望 NLL = 熵 + KL。所以真正与 v1173 不同的轴是 **ECE**（top-1 可靠性），而不是 NLL。诚实定位：本版不主张 ECE/KL 解离（实测它俩同向移动），校准多给的是**方向**（KL 方向盲）和可操作的单标量修复。
3. **假的 held-out 划分**：此底座每个上下文是独一无二的符号、各自抽 `P_true`，按上下文切 train/test 不是 i.i.d.。解法：把温度 T 诚实地当作**全局**重标定（在全部上下文上按 NLL 拟合）。
4. **配对检验**：温度前后的 ECE 共享同一模型与同一上下文，必须用**配对**逐 seed 差（`mean(Δ)-std(Δ)>0`），不能用独立两臂的方差平方和（会用错方差、埋掉真效应，v1191 那类 under-claim）。

## CPU 探针抓到的 regime 陷阱

探针先试了 n=1：模型把每上下文那 1 个采样标签背得死死的（loss 0.001），confidence 全是 0.999、毫无展开、KL=4.85 **比 uniform 还差**（g0 都过不了）——病态记忆，不是校准。于是扫 samples/ctx，锁定 **n=10**：第一个 KL（0.266）显著低于 uniform 地板（0.483）= 真学到了，同时清楚地过自信（gap +0.118、T=1.86 在 [0.5,5] 内部）、有置信度展开。

## 真实结果（n=10，3 seed，对着已知 P_true）

```text
hard_ce: conf 0.559 >> acc 0.442 (gap +0.118)  解析 ECE 0.124±0.031 >> oracle 地板 0.000
  全局温度 T=1.82±0.10:  ECE 0.124 -> 0.065   配对 ΔECE 0.059±0.029   |   KL 0.257 -> 0.161
sweep T:  n=3:4.45  n=10:1.82  n=30:1.24  n=100:1.14  n=300:1.08
```

`verdict = overconfidence_specifically_corrected_by_temperature`（status=pass）。

- **过自信**：gap +0.118、ECE 0.124 显著 >0、T 显著 >1。
- **修复**：配对 ΔECE 显著 >0。
- **特异**（不是"随便压平都行"）：ECE 关于 T 是 U 形、最低点就在拟合 T；错的 T=4.53 反而更差（0.141 vs 0.065）；把这个 T 套到本就校准好的模型上有害（0.040→0.082）。
- **不是魔法**：T 随 n 增大趋向 1——少样本 MLE 产物（v1173 的镜像）。
- **边界（null）**：低熵任务（H 0.31）只极轻微过自信（+0.013）且温度修不动（0.045→0.046，`correctable=False`）。

## 门控与诚实测量纪律

status=pass 只证明**有效测量**：g0 模型胜过 uniform KL 地板、g1 真实熵展开（复用 v1173）、g2 温度可辨识（内部最优在 [0.5,5]）、g3 置信度展开非退化。verdict 阶梯有真实可达的 null 分支（`already_calibrated_no_overconfidence`、`overconfidence_not_correctable_by_temperature`、`ece_reduction_binning_fragile`、`any_flattening_helps_not_temperature_specific`）。头条要同时满足 ECE>地板 + 方向 + T>1 + 配对修复 + 三个特异性证伪 + 分箱稳健（跨 10/15/20 + 等质量分箱），没有单一阈值能造或埋发现。

一个被自查纠正的点：边界 arm 的"null"我最初定义成"统计上不过自信"，但本版讲的是温度**修复**，正确定义应是"温度修不动"。已据此改正——纯逻辑改动，从 `cache.pt` 重新派生，**未重训**。

## 工程：训练/分析分离（reuse-cached）

Phase A（`run_calibration_v1192.py`）只训练一次，把每 arm 逐上下文 logits 存进 `output/calibration-v1192/cache.pt`（~33KB）；Phase B（`analyze_calibration_v1192.py`）纯 CPU 不训练，加载 logits 做温度拟合 + 全部指标 + decide()。反复改阈值/verdict **零重训**（镜像 v1185 训练 → v1186/88/91 分析）。库函数（`src/minigpt/calibration_v1192.py`）全是 `(P_true, logits)` 的纯函数，测试在合成 logits 上跑（oracle z=logP → ECE 恰 0；放大 k 倍 → 已知最优 T=k），17 个测试 CPU 秒级。

一句话总结：v1192 开了校准这条新轴——少样本 transformer 系统性过自信（ECE 0.124 ≫ 精确 oracle 地板 0），全局温度 T=1.82 显著且特异地修到 0.065；诚实标注这是少样本 MLE 产物、且 ECE 与 KL 同向（校准多给的是"方向"与可操作修复，而非与 v1173 解离）。
