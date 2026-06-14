# 1181 · v1169 · MiniGPT 奖励建模 + best-of-N（RLHF 组件的诚实局限）

## 本版目标与不做什么

用户提议用 Anthropic HH-RLHF（真实人类偏好）。诚实结论：不适合从零 char 级 MiniGPT（4L/128、block_size=16）——多轮自然英语对话表示不了、生成不出连贯文本、诚实闸门必然不过、且是多版本工程。于是选了同尺度可诚实测量、又正是 RLHF 核心的方向：**奖励建模**——[[1178-v1166-minigpt-dpo-preference]]/[[1180-v1168-minigpt-dpo-sft-aux]] 的 DPO 是**无奖励模型**的，本版补上经典 RLHF 的奖励模型组件，并用 best-of-N 检验它是否真有用。

明确不做：不当人类偏好/RLHF-at-scale；不预设 RM 有用（用同分布/离分布排序 + best-of-N + oracle 对照测量）。

## 设计先于 GPU（会话限额下主线程亲跑探针）

工作流面板因会话限额未跑成（同 v1168），可行性探针我在主线程亲跑：微型探针显示 RM 同分布 0.82、离分布 0.48≈随机（纯捷径）、best-of-N 越多越差。据此设计并加入 **oracle** 基线（N 个里有任一正确）以区分"RM 不会排"与"池里没有正确答案"。这条经验值得记：评审的价值是"先跑代码证伪/校准"，谁跑次要。

## 关键文件与链路角色

- 新增 `src/minigpt/reward_model_v1169.py`：
  - `RewardModel`：`build_minigpt` 主干 + `nn.Linear(n_embd,1)` 标量头，在最后真实 token 池化（`reward(idx, last_idx)` 用新暴露的 `backbone.features`）。
  - `train_reward_model`：Bradley-Terry `-logσ(r_c-r_r)`。`rank_accuracy`：成对排序准确率。
  - `best_of_n_sweep`：每条 prompt 只生成 max(N) 个样本**一次**，再对每个 N 切片算 rerank（RM argmax）/ random（N 个的期望单样本正确率）/ oracle（任一正确）。
  - `RewardModelConfig`、`run_reward_model`：多 seed；RM 同分布 + 离分布排序；best-of-N 扫描；闸门 = RM 同分布可学（排序显著 > 0.5）；穷举 verdict。
- 顺带核心改动：`MiniGPT.forward` 重构为 `lm_head(self.features(idx))`，新增 `features()` 暴露 ln_f 后、lm_head 前的隐状态（奖励头需要表示而非 token logits）。逐值等价、既有测试零改动。
- 新增脚本 `scripts/run_reward_model_v1169.py`（构同分布易混对、离分布随机扰动对、弱基座、held-out prompts）、测试 `tests/test_reward_model_v1169.py`。

## 三个对照如何把结论钉死

- **同分布 vs 离分布排序：** 同分布（vs 易混 reject，与训练同类）测"学没学到这条边界"；离分布（vs 随机扰动 reject）测"学到的是不是通用正确性"。两者差距大 = 捷径/分布窄。
- **best-of-N 的 random 与 oracle 基线：** random（随机挑）是"无重排器"的下界，rerank 要赢它才算 RM 有用；oracle（任一正确）是上界，证明答案是否在池里。rerank 远低于 oracle 而≈random ⇒ 答案在池里但 RM 找不到。
- **闸门：** RM 同分布排序必须显著 > 0.5，否则 review；`status=pass` 只代表可测。

## 真实结果与诚实边界

GPU（3 seeds、RM 600 步、弱基座 700 步）：`verdict=reward_model_learns_best_of_n_no_clear_gain`。RM 同分布 0.815、离分布 0.640（显著 > 0.5——比探针的纯捷径 0.48 更微妙，真实尺度**部分泛化**）；但 best-of-N 的 oracle 随 N 升到 **0.54**（正确答案在池里），RM 重排却停在 0.10-0.13 且随 N 下降，与随机挑（~0.12）无显著差别。**核心洞见：RM 能通过成对排序评测、甚至泛化到随机负样本，却排不好策略自己的样本（重排 0.10 vs oracle 0.54）——因为策略样本是又一个分布（基座的似是而非错误），RM 在其上没校准。这正是 RLHF 教训：奖励模型只在训练分布上可靠，而策略优化中的生成恰离分布。** 边界：合成信号、tiny 尺度、oracle 列把 RM-blame 与 base-blame 分开。

## 测试如何真实覆盖链路

`features` 与 forward 路径逐值一致（`lm_head(features)==logits`）+ 序列超长护栏；RM 池化形状；Bradley-Terry 在平凡对上达 1.0 排序；run 报告结构 + oracle≥rerank + "status==pass 当且仅当 task_learned" + verdict/rm_verdict/best_of_n_verdict 集合。`MiniGPT.forward` 重构后既有 model 测试零改动仍绿（行为不变的证据）。全量套件通过。

## 一句话总结

v1169 建好 DPO 跳过的 Bradley-Terry 奖励模型并诚实测得其真实局限：它能在 held-out 成对排序上达 0.82、对随机负样本泛化到 0.64，却在 best-of-N 里排不出策略自己样本中的正确答案（重排 0.10≈随机，oracle 却 0.54）——HH-RLHF 在 char 级不可行，遂用合成可控设置量化了"奖励模型只在训练分布上可靠、策略生成恰离分布"这一 RLHF 核心风险。
