# v1197 MiniGPT 归纳电路因果解剖 代码讲解

## 本版定位：归纳轴的机制 capstone（行为 → 机制，沿用 grokking 弧的进路）

v1196 在行为上证明了"上下文归纳需要深度"（堵住捷径后 1 层失败、2 层成功）。v1197 打开这个 2 层模型，问 **哪些 head 实现归纳、怎么实现** —— 经典的 **prev-token-head → induction-head 电路**（Elhage/Olsson 2022），在我们自己的模型上复现并**因果验证**。这正是 transformer 可解释性最著名的结果。

## 复用 v1196 的干净任务 + 训练的 2 层模型

任务沿用 v1196 干净归纳（随机高多样性序列，目标 = 当前 token 最近一次出现后跟的那个 token，首次出现掩掉）。模型 2 层、宽 64、**n_head=8**（比 v1196 的 4 更多 head → 才可能做"数量匹配"的非电路对照）。

## 用 head 注意力模式给 head 分类

- prev-token 分 = head 在位置 i 放在 i−1 上的平均注意力质量（layer 0）。
- induction 分 = 可归纳查询 i 放在 j+1（j=x[i] 最近一次更早出现）上的质量，减去均匀基线（layer 1）。
- prev-token heads = L0 中 prev>τ_prev；induction heads = L1 中 ind>τ_ind。

## 3 视角对抗设计评审逼出的关键 must-fix（建模前）

- **M2 用 MEAN-ablation 做主干**（不是 zero）：把一个 head 的 c_proj 前输出**替换成它的数据均值**（去掉输入相关的计算、保住残差/LayerNorm 工作点）。zero-ablation 把 OOD 的 0 注入 LayerNorm、且共享 c_proj.bias 不可按 head 分解 —— v1197 探针里 zero 把准确率打到**低于 unigram 底**正是这种 OOD 冲击的信号。**两种 ablation 都跑、结论须一致**才算数。
- **M1 数量匹配的特异性对照**：在 n_head=4 下根本凑不出（电路占了 6/8 个 head）。改用 n_head=8，并比较"消融 top-k prev head"vs"消融同层 bottom-k（最不像 prev 的）head"，同数量。
- **M3 组合性需要非-prev-L0 对照**：消融 prev head 会塌掉 induction head 的注意力——但任何大的 L0 扰动 + LayerNorm 重归一化也可能如此。加对照：消融同数量的非-prev L0 head，看 induction 注意力是否**不**塌（排除"泛化扰动"，对应 v1193 的批评）。
- **M4 去循环**：head 由注意力分选出，组合性用**另一批数据**重测，并加"非-induction L1 head 不塌"对照。
- **M5 必要性两段式判据**：消融后准确率 ≤ max(unigram, chance)+margin（绝对底）**且**跌幅 ≥ 0.5·(base−unigram)（相对）；消融后**低于** unigram 则标记为 OOD 冲击。
- **M6/M7 退化分类 + std==0 守卫 + τ 稳健性扫描**：每个 significant() 带固定 margin；Phase B 在 τ 网格上重判，要求 verdict 不变。

## 真实结果（K=20，T=64，8 seed，verdict=`circuit_necessary_specific_composed_concentrated`，status=pass）

```text
7/8 seed 学会归纳（1340 优化失败，排除）；base 0.998，unigram 底 0.142
必要性: 消融全部 prev head -> 0.162，消融全部 induction head -> 0.109（都塌向 unigram）
        zero-ablation 一致（0.161/0.108）-> necessity=True（非 OOD 伪影）
特异性: 同数量对照 prev 0.972 / ind 0.980（vs 类消融 0.16/0.11）-> True
组合性: 消融 prev head 使 induction 注意力跌 0.710，而同数量非-prev 对照只跌 0.026 -> True
冗余(诚实的不对称): induction head 冗余（单 head 最大跌 0.086 ≪ 类跌 0.89）；
                    prev-token head 集中（单 head 最大跌 0.52）-> 常有一个主导 prev head
τ 网格 verdict 不变 1.0
```

**诚实的细节**：归纳电路是 prev-token → induction 的组合，必要、特异、组合性都成立；但**冗余是不对称的**——induction head 是冗余的（多份拷贝，消一个被补偿），prev-token head 更**集中**（常有一个主导 head，单独消融就掉 0.52）。这比"电路是冗余的"这种笼统说法更准确。

## 几个被探针 + 评审 + 建模逐一暴露并诚实处理的真实问题

1. **探针发现单 head 消融被补偿**（n_head=4 时消一个 prev head 只掉 0.04）→ 改为**按 head 类**消融。
2. **zero-ablation 把准确率打到低于 unigram** → 是 OOD/LayerNorm 冲击 → 改 MEAN-ablation 主干，zero 做一致性校验。
3. **n_head=8 偶发优化失败**（1/8 seed base 0.45 没学会）→ 加**逐 seed base 闸**排除未训练的 seed（没学会就没有电路可解剖）。
4. **prev-token 实现因 seed 而异**：多数 seed 用 2 个尖锐的 prev head（~0.95），有的把它**弥散**到 6 个 ~0.30 的弱 head——τ_prev=0.40 会漏掉弥散 seed。据此把 τ_prev 钉在网格下界 0.30（"≥30% 注意力在前一个 token 即算 prev head"），并报告 verdict 在 0.30–0.50 网格上不变。
5. **head 数量因 seed 而异**（prev 1–5 个）→ 冗余只是**刻画**不是 validity 闸；只在 ≥半数训练 seed 有 ≥2 head 时评估，单 head seed 走"redundancy_unassessed"分支。

## 工程

Phase A（`run_induction_circuit_v1197.py`）每 seed 训一个 2 层模型，缓存逐 head 分数 + top-k/bottom-k/单 head 的 mean & zero 消融准确率（让 Phase B 的 τ 扫描零重训）+ 组合性注意力（prev 消融 vs 非-prev 对照，用**另一批**数据）。Phase B（`analyze_induction_circuit_v1197.py`）纯 CPU 重判必要/特异/组合/冗余 + τ 稳健扫描。消融用 c_proj 的 forward-pre-hook（可逆，保住共享 bias）。9 个测试。

一句话总结：v1197 在自己的 2 层模型上因果解剖归纳电路——MEAN-ablation（zero 一致校验）下，消融 prev-token head 或 induction head 都使归纳塌向 unigram（必要），同数量对照不塌（特异），消融 prev head 特异地塌掉 induction head 的注意力（组合，beat 非-prev 对照 0.71 vs 0.03）；诚实的不对称冗余——induction head 冗余、prev-token head 集中；3 视角评审钉死了 mean-ablation/数量匹配对照/两段式必要性判据/去循环/τ 稳健性，建模中逐 seed base 闸排除未训练 seed、并据"弥散 prev 实现"把 τ 定在 0.30，verdict 在 τ 网格上不变。
