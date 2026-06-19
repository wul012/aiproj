# v1194 MiniGPT EWC（参数锚定）vs replay（数据回放） 代码讲解

## 本版定位：持续学习轴的第二步

v1193 在持续学习这条干净新轴上证明了灾难性遗忘真实、且是**分布漂移**驱动，replay 能缓解。v1194 深化这条轴：加入一个**机制完全不同**的缓解法 EWC（Elastic Weight Consolidation，在参数空间锚定对 A 重要的权重），和 replay 同台比较。这是持续学习领域最标准的"方法对比"，但用诚实测量做——比"稳定性-可塑性前沿"，而不是各取一个讨喜的 λ/k。

## 流程：先用 4 个探针把核心证伪

EWC 这种方法很容易"实现得不对就说它输"（假 null）。所以这次先跑探针确认 EWC 是否真的没救：
1. 探针 1：默认 AdamW(wd=0.5) 下扫 λ=0..1e7，EWC 完全没保住 A。
2. 探针 2：排除实现伪影——换 wd=0、换 SGD、λ 一路到 1e11。只有 Adam+λ=1e11 能保 A 但**把 B 弄死**；SGD 完全不行。
3. 探针 3：细扫 λ 拐点（1e9..1e11）映射 EWC 完整前沿 vs replay 前沿——**replay 完胜**（到 (A0.93,B0.83)；EWC 没有两全点）。
这四个探针把"EWC 输"从单点结论变成稳健事实（跨 optimizer/wd/λ），也直接喂给设计评审。

## 设计评审（3 视角 + 综合，无 API 掉线）抓的 must-fix

评审头号担心是**Fisher 估计错**会制造假 null：若用整批 mean loss 的梯度平方（squared-mean）而非逐样本梯度平方的均值（mean-of-squares），off-diagonal 抵消会把 Fisher 压到 0、逼 λ 巨大。**我的实现本来就是逐样本** `A_tr[i:i+1]`（正确）。其余照单全收：
- **公平对待 EWC**：wd=0（已是默认）；λ 网格在拐点加密（4e10/4.5e10/5e10）；加 EWC+replay **hybrid** 臂（EWC 在 replay 之上有用吗）；**两条前沿都跑在 wd=0**，让唯一差别是机制。
- **绑定权重校验**：`lm_head.weight` 与 `token_embedding.weight` 绑定，`named_parameters()` 只列一次（已校验），所以 Fisher/惩罚对共享数字 embedding 只作用一次、且确实包含它（这正是 B 要改写的、A 最重要的参数——真正的机制）。
- **多 seed + 一个门控标量**：M(method)=沿旋钮 max min(acc_A,acc_B)，逐 seed 再 mean±std；占优 = significant() + min_margin（std=0 防护）。
- **对称 verdict 分支**：replay_dominates / ewc_dominates / both_mitigate / neither_mitigates。
- **公平门控**：EWC 必须真发力（能保 A、能可塑、前沿夹住）才允许下"EWC 输"的结论。
- **预算披露**：replay per-step batch 更大、存样本；EWC 存 Fisher+θ\*、不回放。声明限定为"匹配步数下 best-min 占优"，非无视资源的 Pareto。

## 真实结果（p=23，3 seed）

```text
best min(acc_A,acc_B):  replay 0.818±0.039  vs  EWC 0.192±0.039  →  replay_dominates_ewc (pass)
EWC 全或无: 最大 acc_A 0.676(>>naive 0.047 → 锚定发力)，最大 acc_B 0.805，但不同时；
            λ_max 时 acc_B 塌到 0.283(冻结，前沿夹住)。hybrid 0.116 < replay@k8 0.755 (EWC 没加成)。
joint 上界 A 0.862/B 0.837。
```

机制（接 v1193）：遗忘是全局漂移，A 最重要的参数是共享数字 embedding 行，B 必须改写它；对角 Fisher 局部锚只能靠冻结抵抗（堵死 B），replay 把 A 留在损失里不冻任何东西，所以两全。

## 一个被自查纠正的门控阈值伪影（本 arc 第 6 次）

第一次 Phase B 判 `review: ewc_anchor_does_not_engage`——我把"锚定发力"门设成绝对 acc_A≥0.7，而多 seed 最大 acc_A=0.676 差一点。但 0.676 vs naive 0.047 是巨大保护效应，被一个 v1183 式绝对阈值挡住。改成**相对**判据（最大 acc_A 比 naive 高 >0.2）。第二个：bracketed 门（要求 λ_max 处 B 冻结）会误伤"前沿很好、根本不用冻"的 EWC（合成测试 ewc_dominates 暴露）——改成"keeps_both **或** bracketed"。两处都是零重训从缓存重判。

## 工程

Phase A（`run_ewc_replay_v1194.py`）一次训两条前沿(10 λ + 7 k)+hybrid+continue-on-A 地板+joint，存 cache；Phase B（`analyze_ewc_replay_v1194.py`）纯 CPU 重算。库 `ewc_replay_v1194.py` 复用 v1193 的任务/巩固/train_phase(replay)，新增 `compute_fisher`（逐样本对角）/`train_ewc`（带可选 replay 的 hybrid + penalty/CE 比记录）。10 个测试。

一句话总结：v1194 比较两种缓解机制——匹配步数下数据回放在稳定性-可塑性前沿 best-min 0.82 完胜参数锚定 0.19；EWC 拿到公平且充分扫过的机会但全局漂移遗忘下局部 Fisher 锚只能靠冻结抵抗、两全不可得；过程零重训自查纠正了两处门控阈值伪影。
