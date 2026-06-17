# v1183 MiniGPT grokking 权重衰减剂量-反应 代码讲解

## 本版目标与边界

v1179 在 `a + b = c (mod 97)` 上复现了 grokking，并给出二元因果结论：weight_decay=1.0 时 5/5 seed 都 grok，weight_decay=0.0 时 0/5。随后 v1180/v1181/v1182 都是对 v1179 这一份 artifact 的离线审计（证据复核、曲线阶段、成对反事实），没有跑新训练。v1183 推进的是科学本身：把“weight decay 驱动 grokking”从一个二元开关，变成一条剂量-反应曲线——扫描权重衰减强度，测量泛化步 `t_gen` 如何随它变化。

本版刻意复用 v1179 的逐臂训练原语 `grok_v1179.train_arm`（v1174 式的“共享原语”纪律），所以每条 arm 的训练动力学和 v1179 逐字节一致；新的只是权重衰减网格和跨臂趋势分析。配对结构保持：同一个 seed 下所有 wd arm 共享同一份 init 和 split，只改 weight_decay，因此剂量-反应不被初始化/划分混淆。

边界：`toy_scale_single_task_modular_addition_grokking_dose_response_not_a_scaling_claim`——单任务玩具规模的训练动力学现象，不是 scaling 结论。

## 模块结构

核心模块 `src/minigpt/grok_wd_law_v1183.py`：

- `WdLawConfig`：扫描超参（默认 `wds=(0.0, 0.1, 0.3, 1.0, 3.0)`，train_frac=0.2，1 层/128，max_steps=40000）。`grok_config()` 派生出一个 `GrokConfig` 承载逐臂训练超参，交给 `train_arm`。
- `run_wd_law`：逐 seed、逐 wd 做配对训练，收集 `results_by_wd`、`seed_rows`、`curves`，再交给 `assemble_report`。
- `assemble_report`：从训练结果（不再训练）做 decide、组装报告。把它从 `run_wd_law` 拆出来，是为了让 verdict/报告能在不重训的前提下从缓存结果重新推导——训练是确定性的，所以重新组装和重跑得到完全一致的报告。
- `decide_wd_law`：有效性门 + 剂量-反应分类。

每个 wd 用 v1179 的 `arm_aggregate` 做截断感知聚合：rate 类指标在全部 seed 上算，`t_gen` 只在真的 grok 了的 seed 上平均。

## 真实结果：不是单调加速，而是内部最优

真实 GPU（RTX 4060，5 seeds，40k step budget）的剂量-反应表：

```text
 wd    grok_rate  mem_rate  t_gen_mean ± std    final_val
 0.0     0/5        5/5      —  (never)          0.159
 0.1     1/5        5/5      38000 (单seed)       0.721
 0.3     5/5        5/5      26560 ± 5684        0.960
 1.0     5/5        5/5      14920 ± 5944        0.960  ← 最快
 3.0     0/5        5/5      —  (never)          0.195
```

结论 `verdict=wd_dose_response_interior_optimum`：grokking 在权重衰减上是**非单调、有内部最优**的。它在 wd≈1.0 处 grok 最快；在 0.3→1.0 区间里 `t_gen` 随 wd 单调下降（且 wd=1.0 显著早于 wd=0.3，用 `beats_lower` 判定）；但**两端都失败**——wd≤0.1 太弱（0.1 只有 1/5 且很晚，0.0 从不），wd=3.0 太强（虽然仍然 5/5 记忆，却 0/5 grok）。可靠 grok 只出现在 [0.3, 1.0] 这条带里。

关键区分：wd=3.0 的 `mem_rate=5/5`、`too_much_wd_breaks_memorization=False`——它不是“衰减太大导致训练崩了/记不住”，而是“能记住却在预算内不泛化”。为确认这不是 40k 预算的假象，本版补了一个延长预算探针：wd=3.0、2 seeds、**100000 step**，结果仍然 0/2 grok（final_val ~0.17-0.21）。所以高端失败是真实的过度正则化效应，不是被截断。

## 一个被自查纠正的过度声称

本版第一次跑出来时，`decide_wd_law` 给的是 `wd_dose_response_monotone_acceleration`。但那是错的：当时的判定只看了“会 grok 的 wd”（grok_rate≥0.6 的 [0.3, 1.0]），在这条子区间里确实单调，于是误判成“衰减越大 grok 越快”。它漏掉了**被测的最强 wd=3.0 根本不 grok** 这一事实——把一个内部最优误报成了单调加速。这正是项目纪律要拦截的那种讨好式结论。

修复方式：在 `decide_wd_law` 里加入 `high_end_grok_censored`（最强 wd 记忆但 grok_rate<0.6）和 `interior_optimum`（存在 grok 区间但最强 wd 不 grok）。verdict 阶梯里把 `interior_optimum` 排在 `monotone_acceleration` 之前，所以只要最强 wd 不 grok，就不会再声称单调加速。修复后 verdict 正确变为 `wd_dose_response_interior_optimum`。

## 测试

`tests/test_grok_wd_law_v1183.py` 共 10 个，全部 CPU 且快。decide 的 verdict 阶梯用合成的逐臂指标全覆盖：monotone_acceleration（含最强 wd 也 grok 的情形）、**interior_optimum（最强 wd 记忆但不 grok）**、nonmonotone_but_accelerates、threshold_without_trend、insufficient_grok_range、no_memorization、grid 不全落 review、too_much_wd_breaks_memorization 标志。外加一个极小的端到端 smoke（p=5），验证流水线确定性可复现、每个 wd 一行剂量-反应行。

## CLI 与产物

脚本 `scripts/run_grok_wd_law_v1183.py`（`--wds` 可改网格）。产物：

```text
f/1183/解释/grok_wd_law_v1183/grok_wd_law_v1183.{json,csv,txt,md,html}
f/1183/图片/grok-wd-law-v1183.png   （t_gen vs wd 双轴图：左轴 t_gen 误差棒，右轴 grok_rate 柱，两端标注 censored）
```

## 链路角色与一句话总结

v1179 建立 grokking 正结果，v1180-82 审计它，v1183 第一次在这条线上跑新训练、把二元因果推进成一条带有内部最优的剂量-反应曲线。后续可做：train_frac × wd 的二维相图、不同 p 或运算下的最优 wd、或 grok 步数对 wd 的定量律拟合。

一句话总结：v1183 把“weight decay 驱动 grokking”从开关变成剂量-反应，并诚实地发现它是**非单调的内部最优**——grok 最快在 wd≈1.0，太弱（≤0.1）或太强（3.0，连 100k step 都不 grok）都不行；过程中还自查纠正了一次把内部最优误报成单调加速的过度声称。
