# v1179 MiniGPT grokking（延迟泛化）代码讲解

## 本版目标与边界

v1179 是一次有意的“换轴”。从 v1161 开始，MiniGPT 有一条很长的 inference-efficiency 线：KV-cache、speculative decoding，再到 v1175–v1178 的 post-training quantization 四连（量化测量、completion-mask 去重、候选选择器、policy 敏感性）。这条线已经做得很完整，而且本会话反复出现同一个 meta 结论：玩具规模会把很多效应冲淡，单 seed 的 probe 经常过度声称，要靠多 seed + 配对 + 同成本对照才能识破（这一会话被识破了 4 次 honest null）。

v1179 转向训练动力学里的 grokking（延迟泛化）。这个选择是经过考虑的：grokking 恰恰是在小 transformer + 算法数据集上被发现的现象（Power 2022；Nanda 2023），玩具规模是它的天然栖息地，而不是它的敌人。也就是说，本版要回答的不是“某个工程技巧有没有用”，而是“一个著名的、可证伪的泛化相变，能不能在我们自己的 MiniGPT 上被诚实地复现，并定位它的 driver”。

边界写得很克制：`toy_scale_single_task_modular_addition_grokking_not_a_scaling_claim`。本版是单任务、玩具规模的现象复现，不外推成对大模型的 scaling 结论。

## 任务设计：模数加法

核心模块 `src/minigpt/grok_v1179.py`。任务是模数加法 `a + b = c (mod p)`，默认 `p=97`。`build_modular_task` 枚举全部 `p^2` 个有序对，把每个 `(a,b)` 变成 token 序列 `[a, PLUS, b, EQ, c]`：数字 `0..p-1` 各占一个 token，`p` 是 `+`，`p+1` 是 `=`，所以 vocab=`p+2`，block_size=5。这是 Nanda 那一类 grokking 实验的标准 token 方案。

损失只算在答案 token 上：模型在 `=` 位置（索引 3）的 logits 预测 c（索引 4）。`answer_loss`/`answer_accuracy` 都只读这一个位置。这一点很关键——如果对整条序列算 CE，会引入“从空预测 a、从 a+ 预测 b”这类与 grokking 无关的噪声。

`split_indices` 用一个独立的 `torch.Generator(seed)` 做确定性、不相交的 train/val 划分，并刻意不去扰动全局 RNG（模型初始化单独 seed），保证“划分随机性”和“初始化随机性”互不污染。

## 为什么 train_frac=0.2

grokking 是否出现、延迟有多大，主要由 train_frac 决定：数据越少，泛化越难，记忆和泛化之间的延迟越大；数据足够多时模型直接泛化、没有延迟。1-seed 的 probe 一开始用了 train_frac=0.4，结果两条 arm 都在 200 步内同时把 train 和 val 拉到 ~1.0——这是“同步收敛”，根本不是 grokking。本版的 `delay_real` gate 当场把它判为“不是 grokking”，没有把它伪装成正向结果。

随后做了一次 train_frac sweep（单 seed、wd=1.0）来定位区间：`0.35 -> 延迟 200`、`0.30 -> 800`、`0.25 -> 2100`、`0.20 -> ~11300`。延迟随比例单调拉大，正是 Power 等人记录的现象。最终把 `GrokConfig.train_frac` 校准为 0.2：延迟最戏剧、validation 在记忆期仍接近 chance，而且低比例让两条 weight-decay arm 分得最开。

## 配对消融与多种子

`run_grok` 的结构体现了诚实测量合同。对每个 seed：先 `seed_everything(seed)`，构造一份 init（克隆 state_dict）和一份划分，然后让 wd=1.0 和 wd=0.0 两条 arm 从**同一份 init、同一份划分**出发，只有 weight_decay 不同。这是配对设计，把“权重衰减”这一个变量隔离出来；跨 5 个 seed 再取多种子统计。这样既有配对的因果隔离，又有跨种子的方差。

`train_arm` 全 batch AdamW 训练，每 `eval_every` 步评估 train/val 答案准确率，记录 `t_mem`（train 首次 ≥0.99）、`t_gen`（val 首次 ≥0.90）、`val_at_mem`（记忆那一刻的 val）。一旦确认 grok（val 稳定越过 0.95）就早停，省掉后面的预算；没 grok 的 arm 跑满 max_steps，被诚实地“截断”在预算处，而不是被当成 grok。

## decide()：gate 与 verdict 阶梯

`decide` 把“是否有效测量”和“是否发生 grokking”分开：

- gate（只管有效性）：`g0_task_correct`（任务构造正确）、`g1_memorization`（wd>0 的 arm 至少每个 seed 都能记忆，证明训练本身能跑通）、`g2_grid_complete`（seed×arm 网格跑全）。`status==pass` 当且仅当这三个 gate 成立——**不**取决于有没有 grok。一个干净的“预算内没 grok”同样是 pass，只是 verdict 不同。
- `delay_real`：要求 `grok_gap > eval_every` 且 `val_at_mem < 0.5`，排除“train/val 一起涨”的假 grok。
- verdict 阶梯：`no_memorization_training_broken` / `memorized_no_grok_within_budget` / `grokking_reproduced_wd_driven`（wd>0 grok、wd=0 基本不 grok）/ `grokking_reproduced_wd_accelerates`（都 grok 但 wd>0 显著更早，用 `beats_lower` 显著性判断）/ `grokking_reproduced_wd_not_separable`。

`arm_aggregate` 在截断面前很小心：rate 类指标在全部 seed 上算，而 grok 步数只在“真的 grok 了的 seed”上平均，并单独报告 grok_rate，绝不把没 grok 的 seed 偷偷丢掉或当成 0。

## 测试

`tests/test_grok_v1179.py` 共 16 个，全部 CPU 且快：任务正确性（全枚举、答案满足模等式、`verify_task` 能识破被篡改的答案）、划分确定性与不相交、答案 token 的 loss/acc 索引（用 stub model 精确验证读的是 `=` 位置和 c）、`arm_aggregate` 的截断式平均、`decide` 五个 verdict 全部可达、`delay_real` 把“同步收敛”判为非 grok、grid 不全/无法记忆时落到 review，以及一个极小的端到端 smoke（p=5）验证流水线确定性可复现并能记忆小训练集。

## 真实结果（RTX 4060，5 seeds）

`verdict=grokking_reproduced_wd_driven`，status=pass。wd=1.0：5/5 都 grok，约 100 步记忆、约 14880±5971 步泛化，val@mem≈0.147（记忆期接近 chance，确认是真延迟），final_val≈0.960。wd=0.0：5/5 同样记忆，却在 40000 步内 0/5 泛化，final_val≈0.159 停在记忆期水平。逐 seed 看，配对结构很干净：同一 seed 的两条 arm 在记忆时 val 几乎相同（如 0.111 vs 0.110），之后只有带权重衰减那条爬升上去。t_gen 标准差很大（约 40%），符合 grok 步数高方差的文献说法，本版如实报告。

这是本会话第一个“正向”结果，而不是又一个 honest null——但它仍然守住同样的纪律：多 seed、配对消融、延迟真实性 gate、截断感知的聚合。

## 链路角色与一句话总结

v1179 给项目开了一条新轴：训练动力学 / 泛化，而不是推理效率。后续可顺势做：activation/QAT 之外的方向，比如不同 p 或不同运算（乘法、减法）下的 grok 区间、weight_decay 强度对 grok 步数的定量影响、或 grokking 的进度度量。

一句话总结：v1179 在自家 MiniGPT 上诚实复现了 grokking——记忆远早于泛化、延迟随数据比例下降而拉大、并由权重衰减驱动，是本会话从 honest null 转向 honest positive 的一版。
