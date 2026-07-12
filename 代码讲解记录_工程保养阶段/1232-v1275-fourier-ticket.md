# v1275：Fourier lottery ticket 的预注册剪枝实验

## 一、本版目标与明确边界

v1275 要回答的不是“剪枝能不能让模型更小”这个宽泛问题，而是一个能够被当前项目直接检验的
具体问题：v1185 已经交付的 mod-97 grokking checkpoint，是否存在一张由幅值剪枝找到、并且
保留 v1188/v1191 所识别 Fourier 回路的稀疏中奖彩票。

这个问题分成两个阶段。Arm P 只读取已冻结的 checkpoint，对权重做确定性的幅值剪枝，再在
同一个 7527-pair heldout 集上复算准确率与 Fourier 指标。Arm L 原计划在 Arm P 通过后，把
幅值 mask rewind 到初始化并重新训练，同时比较 random mask 和 fresh reinit。两阶段之间有一条
先写后跑的停止门：只要 50% 稀疏已经把 heldout accuracy 降到 0.90 以下，就必须停止，不能
启动 Arm L。

本版明确不做三件事。第一，不把 toy mod-97 的结论外推到大语言模型。第二，不修改 v1185
checkpoint、v1188/v1191 artifact 或任何旧 verdict。第三，不在看到结果以后换频率、调阈值、
删对照或另造一个更容易成功的剪枝定义。最终得到的是一个诚实的阴性分支
`pruning_breaks_circuit`，不是稀疏模型 promotion，也不是“所有剪枝都不可能”的普遍命题。

## 二、前置路线与预注册为何重要

v1179 首次在本项目复现了 delayed generalization；v1183 找到 `weight_decay=1.0` 的较优 grokking
配方；v1185 把这条配方固化成可加载 checkpoint；v1188 从 number embedding 中发现 Fourier
power concentration；v1191 又用 remove/keep frequency ablation 说明五个频率
`[43, 3, 48, 26, 44]` 对行为有因果意义。v1275 并不重新发明这些能力，而是在它们上面增加
“无结构稀疏化是否保留该机制”的检验。

Lottery-ticket 实验很容易出现事后解释：如果 ticket 没成功，可以继续降低稀疏度；如果频率
没对齐，可以改用模型自己的 top-5；如果随机对照太强，可以只展示幅值 mask。为阻断这些自由度，
本版先写 `f/1275/解释/说明.md`，再把 brief、实现、阈值和 14 类测试提交为预注册 commit
`f12f8793...`，之后才跑 CPU probe。运行后相对该 commit 的代码差异只有报告字段、HTML
description 和图上“Arm L 未运行”的诚实标注，`TicketConfig` 与 `decide()` 的阈值没有变化。

预算也在运行前处理。原 brief 同时要求三档稀疏度、三种 sparse arm、三个 seed，且每 seed
最多五次训练。完整网格实际需要 `1 dense + 3 levels × 3 arms = 10` 次，约束无法同时成立。
本版没有隐去矛盾，而是先删 0.875、再删 0.75，仅在 Arm P 通过时运行 0.50；这样每 seed 是
1 次 dense 加 3 次 sparse，共 4 次。实际 Arm P 未通过，所以训练次数进一步合法地降为 0。

## 三、关键文件与各自角色

### 3.1 `src/minigpt/fourier_ticket_v1275.py`

这是本版唯一的新核心模块，最终 399 行，没有越过 400 行功能版本上限。它包含四类职责：

1. `TicketConfig` 固化所有实验自由度，包括五档 sparsity、两种 mode、五个 random seeds、三个
   train seeds、0.90 accuracy floor、0.05 alignment margin、固定频率和 checkpoint SHA-256。
2. `make_mask()`、`masked_copy()` 与 `freq_stats()` 实现精确 mask、只读候选模型和 Fourier 统计。
3. `run_arm_p()` 与 `run_arm_l()` 实现两个实验 arm；后者只有在 probe 通过时才会被调用。
4. `decide()`、`build_report()` 与 `plot_result()` 从 cache 纯函数式地产生 verdict、五格式报告和
   一张综合图，不在分析阶段训练。

### 3.2 `src/minigpt/grok_checkpoint_v1185.py`

旧的 `train_to_grok()` 训练循环没有被复制。本版为它增加两个默认关闭的参数：`init_state` 和
`masks`。默认值都是 `None`，所以 v1185 原调用路径不变；启用时，模型先加载指定初始化，mask
再同时约束初值、反向梯度和每次 optimizer step 后的权重。这使 lottery-ticket arm 能复用同一
训练器，也避免形成第二套日后会漂移的 grok harness。

### 3.3 两个 CLI

`scripts/run_fourier_ticket_v1275.py` 是 Phase A 入口。它先在 CPU 执行 Arm P，只有
`arm_p_probe_ok=True` 才把 Arm L 交给所选 device，最终写 `phase_a_cache.pt`。
`scripts/analyze_fourier_ticket_v1275.py` 是 Phase B 入口，只接受 cache，调用 `decide()` 和
readability writer。它不导入或调用训练入口，因此可以在 CPU 上快速重复复核。

### 3.4 测试与证据目录

`tests/test_fourier_ticket_v1275.py` 保护 mask 精确度、随机 mask 可复现、pruned weight 始终为
零、真实 Arm P forward、四个 verdict 分支、probe 停止、缺格 review、cache byte-stable 复算和
报告边界。最终证据位于 `f/1275/解释/fourier_ticket_v1275/`，图位于
`f/1275/图片/fourier-ticket-v1275.png`。`phase_a_cache.pt` 只有 3616 bytes，只保存数字和配置，
不复制 854 KB checkpoint，更不保存新模型。

## 四、掩码算法：到底剪了什么

`prune_targets()` 只返回三个唯一参数：tied `token_embedding.weight` 以及 MLP 的两块 matrix
weight。由于 MiniGPT 的 `lm_head.weight` 与 token embedding 是同一个 parameter，不能把它们
在 global ranking 中计算两次。attention、position embedding、LayerNorm 和 bias 均保持原样，
所以本版结论严格对应“embedding/unembed + MLP 的无结构幅值剪枝”。

`per_tensor` 和 `global` 的差异不是文字标签，而是 top-k 的作用域：

```python
if mode == "per_tensor":
    # 每个目标张量分别保留 round(numel * (1-sparsity)) 个元素
else:
    # 三个目标张量拼平后只做一次全局 top-k，再按原 shape 切回
```

实现没有用“绝对值大于阈值”这种会被 tie 数量扰动的方法，而是直接选择精确个数的 index。
随机对照复用同样的元素数量与 shape，只把 magnitude ranking 换成独立 generator 的
`randperm`。测试既检查 kept count，也检查同 seed byte-identical、异 seed 至少一个 mask 不同。

对候选模型的处理是 `deepcopy -> 参数乘 mask -> evaluate_table`。原模型从未原地变更，运行前后
checkpoint SHA-256 都是
`46F2A11A945F0BD140AF09FE298B28DD31062B4E3018EA159876C263F7DCB7DB`。这条哈希门比
“代码看起来没有写文件”更强，因为它直接检查冻结输入的字节事实。

## 五、Fourier 指标与一个关键机理

`freq_stats()` 先取 number rows `0..96`，沿 number 轴做 rFFT，跨 embedding dimension 汇总
power，去掉 DC 后归一化。它同时报告两组量：模型自己最强的 top-5，以及运行前已经固定的
五频 share。最终 gate 使用后者，避免剪枝以后重新挑一组对自己有利的频率。

未剪枝模型的 heldout accuracy 是 `0.965989`，固定五频 share 是 `0.305171`。50% per-tensor
剪枝后准确率是 `0.406536`，50% global 后是 `0.486781`，都远低于 0.90。相比之下，global
模型的固定五频 share 仍为 `0.305180`，几乎与未剪枝相同；甚至到 95% 稀疏时仍为
`0.314153`，top-5 名称也始终是原五频。

这不是矛盾。Fourier power share 只告诉我们“某些频率在 embedding 权重里的总能量仍占多少”，
并不完整描述相位、不同 embedding 维之间的成对组织、MLP 如何组合 sin/cos 分量，以及低幅值
参数是否承担协同校正。global magnitude pruning 会优先留下大幅值元素，所以频率总能量标签
可以保持；但它把实现函数所需的分布式连接打散后，网络不再能正确完成模加。换句话说，
“频率仍可见”是回路存在的必要线索，却不是回路仍可执行的充分证明。

随机 mask 让这个解释更清楚。50% global random mask 的准确率均值只有 `0.013764`，固定频率
share 均值为 `0.204559`；幅值 mask 确实比随机保留了更多结构和行为，但 0.487 仍不足以达到
预注册功能门。阴性结论不是“幅值没有价值”，而是“它没有保住一张达到既定能力标准的 ticket”。

## 六、判定链和停止逻辑

`arm_p_result()` 对每种 mode 先查 0.50 accuracy，再选择仍超过 0.90 的最高稀疏度比较固定频率
share margin。本次两个 mode 都没有任何 qualifying row，因此 `selected` 都是 `None`，
`probe_ok=False`、`p_pass=False`。

`run_phase_a()` 随即写入：

```text
skipped_reason = arm_p_probe_failed
actual_runs = 0
max_runs = 15
descoped_levels = [0.5, 0.75, 0.875]
```

`decide()` 把这种预注册停止视为“有效测量的阴性结果”，所以 `status=pass`。这里 pass 只表示
checkpoint 未变、10 个 P cell 和每 cell 5 个随机对照完整、停止逻辑与预算被遵守；它不表示
剪枝成功。实质 decision 是 `pruning_breaks_circuit`。如果把 `arm_l_complete=False` 单独拿出来
看会产生误解，因此报告还显式给出 `arm_l_skipped=True`，图中也写明 50% probe failed。

这体现了本项目一直强调的两层语义：measurement status 回答“实验是否按合同完成”，verdict
回答“科学假设得到哪一种结果”。把阴性 verdict 强行写成 status failure，会诱导执行者继续调参；
把 status pass 当成功 promotion，则会夸大结果。两者必须同时阅读。

## 七、测试、产物与链路角色

预注册前定向验证为 `22 passed`，最终定向验证扩展为 `26 passed`；其中新文件的真实 Arm P smoke 会在 p=11 小模型上实际 forward，
不是只检查字典键。name-budget gate 重新扫描 7515 条历史 baseline，新增违规是 0；核心模块 399
行，没有制造巨型文件。最终全量 pytest 为 `3773 passed in 1172.75s`；CI-style coverage 为
`90.90%`（`91072/100184`），高于不变的 `88.98%` floor。source encoding 扫描 2789 个文件无
BOM/语法错误，workflow 67/67、mypy 22 targets/0 diagnostics、ruff 与 name-budget 都没有新增债务。

五格式产物承担不同角色：JSON 是结构化复核入口；CSV 便于比较 10 个 P cell；text/Markdown
面向终端和代码评审；HTML 用于浏览器检查；PNG 把 accuracy 下坠与 Fourier margin 上升放在同一
张图上。图中看似反向的两条趋势正是本版最有信息量的结果：剪得越狠，随机对照的频率背景越低，
所以 magnitude mask 的相对 Fourier margin 反而上升；但行为准确率同步坠向 chance。

本版在整个项目中的角色是“机制证据的反例加固”：v1191 说明指定频率对完整模型有因果作用，
v1275 进一步说明只保存这些频率的统计占比还不够。若未来另开版本研究 structured Fourier pruning，
它必须是新的预注册问题，不能回头改写本版无结构 magnitude pruning 的阴性结论。

## 一句话总结

v1275 用先提交、后测量的方式证明：v1185 的 Fourier 频率痕迹能在重度幅值剪枝后继续可见，
但 50% 稀疏已经破坏模型功能，因此不存在继续启动 lottery-ticket 重训的合同依据。
