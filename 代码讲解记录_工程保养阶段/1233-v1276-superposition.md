# v1276：20 个特征如何装进 5 个维度——superposition 实验

## 一、本版到底在问什么

v1276 开启的是一个新的模型能力轴：superposition。它不再研究 v1275 的现成 grokking
checkpoint，而是构造一个最小、透明、能够直接观察表示几何的 ReLU autoencoder。输入有 20 个
相互独立的 feature，hidden space 只有 5 维。如果 feature 每次都出现，直觉上 5 个维度只能
专门表示 5 个 feature；如果 feature 极少同时出现，模型可能让多个 feature 共用非正交方向，
依靠 ReLU 和负 bias 过滤干扰，从而在 5 维里保存超过 5 个 feature。

这个问题与 v1275 有清楚的逻辑关系。v1275 发现 Fourier circuit 在频率基底上稀疏，却在单个
weight magnitude 上是 dense 的：只看神经元或单个权重的自然基底会错过真正结构。superposition
研究的正是“feature 方向与 neuron basis 不对齐时，模型如何共享有限维度”。但本版没有因此
声称 MiniGPT 内已经存在 superposition。正式 scope 固定为 `toy autoencoder, own substrate`，
把 MiniGPT activation probe 留给未来独立版本。

## 二、预注册纪律与一次真实纠错

本版沿用 v1275 确立的 `preregister-commit-then-run`。brief、`SuperConfig`、`decide()`、四个
verdict 分支、τ grid、五 seed、收敛门、2% optimality epsilon、脚本和测试先进入 commit
`2cc520f0`，之后才运行真实 probe。这个顺序让后续审查者可以直接比较运行前后源码，而不用相信
执行者口头声称“阈值早就定好了”。

probe 也确实抓出了一个设计错误。最初的解析 baseline 把“drop feature”理解成让输出恒为 0，
于是用 `E[x²]=(1-S)/3` 计算误差。但模型方程是：

```text
x' = ReLU(W^T W x + b)
```

即使某个 feature 的 W column 为零，它仍有独立 bias。对未表示 feature，最佳常数输出不是 0，
而是 `E[x]=(1-S)/2`；最小 MSE 是方差：

```text
q = 1 - S
Var(x) = q/3 - q²/4
L_dedicated = Var(x) × sum(dropped feature importance)
```

uniform dense probe 的 loss 是 `1.25098765`，而修正后的理论值是 `15×1/12=1.25`，几乎精确
命中。这不是可以忽略的数值小差，而是 G4 的量纲错误。完整 50-cell 网格因此暂停；代码、测试和
说明在 commit `076c61e3` 中披露修正，再从未改动的 probe cache 复算。2% epsilon、G1-G5、
训练配置和 verdict 顺序全部保持不变。修正后 dense loss ratio 回到约 1，说明没有虚假地击败
dedicated optimum；sparse ratio 仍为 0.21/0.16，且没有重训。这是一次符合失败条件的 cache-only
纠错，而不是看到结果后调门。

## 三、关键文件和链路角色

### 3.1 `src/minigpt/superposition_v1276.py`

核心模块最终不到 400 行，包含 substrate、训练、cache analysis、统计判定、报告和绘图。它没有
抽象成新的通用实验 package，因为本版只需要一个特定、可审计的 TMS substrate。主要对象是：

- `SuperConfig`：冻结 n=20、m=5、五个 sparsity、两个 arm、五 seed 和所有阈值。
- `ToyAE`：只含 `W∈R^(5×20)` 与 `b∈R^20` 的 tied autoencoder。
- `train_cell/run_phase_a`：CPU 训练一个 cell，并把原始参数与 loss trajectory 写入 cache。
- `dedicated_loss`：计算最优 dedicated solution 的解析期望 loss。
- `weight_metrics/analyze`：从 cache 重建 norm、R(τ)、interference、plateau 与 loss ratio。
- `spearman_exact/decide`：执行 exact permutation 与 G1-G5 verdict ladder。
- `build_report/plot_result`：生成稳定报告模型和唯一一张 R-vs-S 综合图。

### 3.2 两个薄脚本

`run_superposition_v1276.py` 有 `probe` 与 `full` 两种模式。`full` 强制要求 `--resume`，并先调用
`probe_ready()`；如果任一 sparse arm 在 τ=0.3 没有 R>5，脚本直接拒绝完整网格。通过后，
`run_phase_a` 会复制 probe cache 的四格，只训练剩余 46 格，保证每格只训练一次。

`analyze_superposition_v1276.py` 只加载 cache，依次调用 `analyze -> decide -> build_report`。
它不会补跑缺失 cell。正式 verdict 是 review 时退出码为 1，但五格式 artifact 与 figure 仍先完整
落盘；这个退出码表达“headline 未获准”，不是脚本异常。

### 3.3 测试和证据

`tests/test_superposition_v1276.py` 不只测试字典 shape。它用 Cartesian midpoint quadrature 独立
验证解析 baseline；构造已知 W 检查 represented count 与 interference；对五点完全单调序列验证
`rho=1` 和 one-sided exact `p=1/120`；覆盖 finding、dedicated null、not optimal、mixed-τ、
non-monotone、未收敛和 G5 独立报告等路径。真实 cache 出现前 actual-cache test 明确 skip，产物
提交后则必须从 cache 两次重算出完全相同 verdict。

正式证据位于 `f/1276/解释/superposition_v1276/`，单图位于
`f/1276/图片/superposition-v1276.png`。cache 约 117 KB，包含 50 格 W、b、trajectory 和 final
loss，不保存 optimizer state，也不依赖 GPU checkpoint。

正式 cache 落盘后，定向套件为 `16 passed`，actual-cache test 会连续两次从同一 cache 重建
analysis 与 verdict，证明 Phase B 没有隐藏随机性。全仓 CI 同款验证进一步执行 3547 项测试，
总覆盖率为 90.74%，高于 88.98% floor；20 组 coverage 前置门也全部通过。HTML 不是“生成即
算完成”：Playwright MCP 实际打开页面并从 accessibility tree 读到 `review`、G2=False 和两个
失败 τ check，console 为 0 error/0 warning，full-page 截图归档为
`f/1276/图片/superposition-report-v1276.png`。因此代码、原始 cache、结构化报告和人可读页面
四层证据对同一个受限结论保持一致。

第一次远端 CI 还揭示了一个 Windows 本地环境遮住的测试入口问题：本地安装了 pytest，但仓库
正式 CI 只保证标准库 unittest，原测试文件既导入 pytest，又只提供模块级 test 函数。修复没有
增加运行依赖或删除测试，而是用 `math.isclose`、`unittest.SkipTest` 替代 pytest helper，再用
标准 `load_tests` 协议将同样 16 个函数注册成 `FunctionTestCase`。修复后 unittest 与 pytest
两个入口都执行并通过 16 项契约，因此 patch 解决的是“谁来发现测试”，没有改变“测试证明什么”。

## 四、数据、模型和训练如何工作

每个 feature 独立采样。给定 sparsity S，先以概率 S 置零；否则从 `[0,1]` 均匀采样。两个 arm
使用完全相同的输入：

- `importance`：`I_i=0.7^i`，前面的 feature 对 loss 更重要。
- `uniform`：所有 `I_i=1`，用来判断“重要 feature 优先独占维度”是否只是 setup 产物。

同一个 `(S,seed)` 的两个 arm 使用相同模型初始化 seed、训练数据 generator、trajectory eval
generator 和 final eval generator。唯一变化是 importance vector，所以 arm 差异不能归因于更好
初始化或更幸运样本。

模型先把 x 压到 5 维：`h=xW^T`，再通过 tied weight 解码：`hW+b`，最后 ReLU。训练 loss 是
每个样本 20 个 feature 的 importance-weighted squared error 之和，再对 batch 平均。每格固定
6000 steps、batch=1024、Adam lr=0.003；每 100 steps 在固定 8192 样本上记录 trajectory，最后
用独立 262144 样本估计 final loss。大 final set 尤其重要，因为 S=0.99 时每个 feature 只有约
1% 样本激活，太小的 eval set 会让 G4 margin 被 Monte Carlo 噪声左右。

最后 10% trajectory 的 max-min range 除以解析 baseline 必须不超过 0.02。所有 50 格实际都
通过，最大 drift 约 0.0039；没有 seed 被悄悄删除。

## 五、Phase B 如何识别 superposition

W 的第 i 列是 feature i 在 5 维 hidden space 中的方向。`weight_metrics()` 先计算每列 norm：

```text
R(τ) = number of i where ||W_i|| >= τ
τ ∈ {0.3, 0.5, 0.7}
```

如果 R>5，至少有多个 feature 不能互相正交，必然共享有限维度。interference 则把列单位化后，
对每个 feature 累加它与其他方向 squared cosine。它用于描述几何，不参与 headline gate；真正
判断“packing 是否有价值”的是 G4：模型必须比最佳 dedicated baseline 至少低 2%。

G3 没有调用 SciPy 黑箱。`spearman_exact()` 先做带 ties 的平均 rank，再计算 Pearson correlation；
随后枚举五个 median 的全部 120 个排列，统计 one-sided `rho_perm >= rho_observed` 的比例。这样
p 值在 tiny five-point sweep 上是可完全复算的，而不是依赖渐近近似。

## 六、结果：强信号为什么仍是 review

importance arm 的 τ=0.5 中位数随 S 变化为 `[5,8,9,10,11]`，Spearman `rho=1.0`，exact
`p=0.008333`。uniform 为 `[6,10,18,20,20]`，`rho=0.974679`，`p=0.016667`。两条曲线都
明显随 sparsity 增长。S=0.99 时，importance 的 model/dedicated loss ratio 是 `0.192564`，
uniform 是 `0.161437`；换言之，packing 不是训练偶然留下的高 loss 几何，而是大幅优于专用
5-feature 方案。importance dense 的 represented set 在 5/5 seeds 都是 `{0,1,2,3,4}`，G5
也通过。

正式 verdict 仍必须是 `review`。原因只在 G2 的“所有 τ、两个 arm”全称条件。importance 在
0.3/0.5/0.7 三个 threshold 都表现为 dense R=5、sparse R>5；uniform sparse 三个 threshold
也都是 R=20，但 uniform dense 的 R 分别约为 15、6、4。τ=0.7 将它视为 dedicated，τ=0.3
和 0.5 则把多个小 norm column 算作 represented。因此 G2 check 是：

```text
importance|0.3 pass   importance|0.5 pass   importance|0.7 pass
uniform|0.3    fail   uniform|0.5    fail   uniform|0.7    pass
```

这正是预注册所谓 mixed-τ，必须优先 route review。删掉 0.3/0.5、只展示 importance arm，或者
改用 loss 反推一个更舒服的 τ，都属于事后改门。本版保留更细的解释：**loss-optimal packing 的
证据成立，但 norm threshold 对 uniform dense 的分类不稳，所以预注册的跨-arm headline 未获准。**

## 七、产物输入输出与后续角色

Phase A 输入只有 frozen config 和可选 probe cache，输出 `phase_a_cache.pt`。Phase B 输入该
cache，输出：JSON 供结构化复算，CSV 供 50 行 cell 比较，text/Markdown 供终端与评审，HTML
供浏览器检查，PNG 用一张双面板图同时展示两个 arm 和三条 τ 曲线。artifact 都是只读证据，
不是 promotion checkpoint。

本版为后续留下两个清楚方向，但不在本版内展开。第一，外部评审可判断 uniform dense 的小 norm
columns 是 threshold 定义问题还是实质残余表示；若继续，应另写任务简报并重新预注册。第二，只有
toy substrate 的定义稳定后，未来版本才有资格研究 MiniGPT activation 是否存在类似 packing。

## 一句话总结

v1276 在 20→5 toy autoencoder 上测得收敛、单调且 loss-optimal 的 sparse packing，同时因
uniform dense 对 norm threshold 呈 mixed-τ 而诚实停在 formal review，没有把强探索信号冒充
已经通过全部预注册条件的 superposition headline。
