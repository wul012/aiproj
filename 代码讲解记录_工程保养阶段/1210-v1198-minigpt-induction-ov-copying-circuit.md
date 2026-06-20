# v1198 MiniGPT 归纳头 OV 拷贝电路 代码讲解

## 本版定位：归纳机制的另一半（OV），与 v1197 的 QK 合成二段式机制

v1197 因果验证了归纳机制的 **QK / 前缀匹配半边**（归纳头**注意到**后继位置）。v1198 验证**另一半边**——**OV（value→output）电路是一个"拷贝"电路**：把被注意到的 token 拷贝进输出 logit。两者合起来 = 教科书的二段式归纳头机制（Elhage 2021；Olsson 2022）。这刻意镜像 grokking 弧的进路——那条弧有权重级版本（FFT v1188）和因果版本（消融 v1191）；这里是 v1197 的因果 QK + v1198 的 OV 拷贝。

## 两条证据（**都**满足才正向；不一致→review）

**Prong 1 —— 权重级 OV 拷贝。** OV 映射 `M = W_E @ W_V^T @ W_O^T @ W_E^T`（忽略 LayerNorm，Elhage 2021）对归纳头应当**对角占优**：注意到 token t 抬高 logit t。逐 head 打分：`copy_z`（逐行 (M_ii − 行均值)/行标准差 的平均；随机≈0，正=拷贝、负=反拷贝）和 `diag_is_max`（对角是该行 argmax 的比例；随机≈1/V）。

**Prong 2 —— 激活级 Direct Logit Attribution（LN 诚实真值）。** head 对残差流的贡献 `c_h =（它的拼接 head 切片）@ W_O_h^T`，过**真实 ln_f 缩放** + tied unembed，量它在 inductable 位置对**正确答案** token 的 logit 加成 `DLA_gap = logit(正确) − 平均 logit(错误)`。归纳头应 ≫0，prev/对照≈0。DLA 用真实注意力 + 真实 value，补上权重级丢掉的 LayerNorm 和 layer-0 value 输入。

## 设计评审逼出的关键决定（建模前，靠 CPU 探针）

- **lens-1：tied-embedding 的 Gram 混淆（致命）**。模型把 unembed 与 embedding 绑定，`M` 两边同一个 `W_E`，而**裸 Gram `W_E @ W_E^T` 本身就强对角**（探针测得 copy_z +3.83）。所以 verdict **必须成对/相对**：归纳头要比"非归纳 L1 对照头"和"prev 头"拷贝得显著多——这些对照**共享同一个 `W_E`、只在 `W_V/W_O` 上不同**。若对角是 Gram 继承的，对照也该拷贝；探针证明它们不（对照 −0.31、−1.66，甚至反拷贝）。
- **第二条证据用激活级 DLA**：权重级是 LayerNorm-free 的理想化；DLA 用真实激活折叠真实 ln_f 缩放，是"它在激活里真这么干"的真值。两条必须一致（镜像 v1197 的 mean/zero 一致）。
- **正号要求 + 绝对底**：copy 不只要 beat 对照，还要 `copy_z ≥ 0.5`、`diag_is_max ≥ 0.30`（排除"反拷贝但 beat 更反对照"的假阳）。DLA 要 `gap ≥ 0.05`。
- **逐 seed base 闸 + 可分类闸**：没学会归纳的 seed 没有电路可解剖（排除）；要有 ≥1 归纳头 AND ≥1 非归纳 L1 对照头才可分类。
- **τ 稳健性扫描**：verdict 在 tau_ind 网格上不变才算数。

## 4 个 CPU 探针 + 它们各自暴露的真实问题

1. **探针 v1/v2 用 n_head=8（沿用 v1197）训练失败**：base 0.40→0.50，2500 步都没越过归纳相变，**没有归纳头形成**。诊断 = head size 8 太小、训练不可靠（不是机制问题）。归纳是经典**相变**能力，head size 小会把相变推出预算外。
2. **改 n_head=4（head size 16，v1196 的可靠基底）→ 探针 v3 完美**：base 600 步 0.997、1500 步 1.000；电路教科书式干净（1 个主导 prev head L0.3=0.96，3 个冗余归纳头 L1.{3,0,1}=0.88/0.87/0.68，1 个天然对照 L1.2=0.07）。**于是 v1198 用 n_head=4**，并诚实记录这点。
3. **探针 v3 崩在一个 Unicode 打印**（`ᵀ` 上标 Windows GBK 编不了）——与机制无关，改 ASCII。
4. **探针 v4 标定 DLA**：归纳头 DLA_gap +0.88/+0.42，prev −0.013、对照 −0.054 ≈0；据此把 `dla_margin=0.10`、`dla_floor=0.05` 标定好。

## 真实结果（K=20，T=64，n_head=4，8 seed 全部学会归纳，verdict=`induction_ov_is_copying_circuit`，status=pass）

```text
base 0.9995（unigram 0.142，chance 0.050）；classifiable 7/8；τ 网格一致 100%

PRONG 1 权重级 OV copy_z（成对）：
  induction  +2.52   diag_is_max 0.89   <- 拷贝
  L1 对照    -1.66   （同一个 W_E！）  -> 反拷贝
  prev-token -0.45
  raw Gram   +3.83   （tied-embed 基，lens-1）
  -> copy_ok = True
PRONG 2 激活级 DLA_gap：
  induction  +0.566  L1 对照 -0.043  prev -0.006
  -> dla_ok = True
```

**诚实的细节**：归纳 OV 的对角占优是 `W_V/W_O` **学**出来去**利用**那个拷贝友好的 tied-embedding 基（+2.52，但**小于**裸 Gram +3.83——OV 不是完美恒等），而同基的对照头反而**破坏**它（−1.66）。所以拷贝是 OV 变换、不是 Gram 白捡。seed 1343 四个 L1 头全被分成归纳头 → 没对照 → 不可分类（7/8 仍过）。归纳头是**冗余**的（每 seed 2–4 个都拷贝），呼应 v1197 的冗余发现。

## 工程

Phase A（`run_induction_ov_v1198.py`）每 seed 训一个 2 层 n_head=4 模型（复用 v1197 的 `train_model`），缓存逐 head 的 prev/induction 分数、权重级 OV 拷贝分（copy_z、diag_is_max）、激活级 DLA gap、Gram 基线。Phase B（`analyze_induction_ov_v1198.py`）纯 CPU 重判两条证据 + τ 扫描，零重训。DLA 用 c_proj 的 forward-pre-hook 抓拼接 head 输出、ln_f 的 forward-pre-hook 抓归一化前残差，按真实 ln_f 缩放折叠。一个 GPU-only 的 bug：`copying_scores` 里 `torch.arange(V)` 默认 CPU 而 `M` 在 cuda——CPU 探针没碰到，Phase A 在 GPU 第一次跑就炸，改 `device=M.device`。11 个测试（合成缓存跑 decide 阶梯 + OV 数学单测 + 微型真实 Phase-A 烟测）。

一句话总结：v1198 在自己的 2 层模型上证明归纳头的 OV 电路是拷贝电路——权重级 OV 对角占优（copy_z +2.52 vs 同-`W_E` 对照 −1.66，diag_is_max 0.89）且激活级 DLA 特异地抬高正确答案（+0.566 vs 对照≈0），两条证据一致；成对对照钉死了 tied-embedding 的 Gram 混淆（对照同基却不拷贝），逐 seed base 闸 + 可分类闸 + 两证一致闸 + 正号要求 + τ 稳健保证 status=pass 只认有效测量；4 个 CPU 探针发现并改正了 n_head=8 训练不可靠（→n_head=4）、标定了 DLA 阈值，建模时一个 GPU-only 的 arange 设备 bug 在 Phase A 即被抓修。与 v1197（QK）合成二段式归纳头机制。
