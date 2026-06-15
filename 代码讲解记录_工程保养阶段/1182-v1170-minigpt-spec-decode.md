# 1182 · v1170 · MiniGPT 投机解码（speculative decoding）：可证明等价、FLOPs 诚实

## 目标与边界

承接 v1161 KV-cache 的**推理效率线**（非对齐线，对齐线在 v1169 奖励模型脆弱处暂停）。投机解码：小而快的 draft 自回归提议 `K` 个 token，大 target 用一次 `(K+1)` 宽前向并行验证，接受/拒绝规则保证输出与"只用 target 解码"同分布。范围限定 **B=1**（贪心+采样）；批量 ragged-accept 不做。`status==pass` 只证明"实现正确、效率数字可信"，绝不等于"它快"。

## 入口与核心实现（`src/minigpt/spec_decode_v1170.py`）

- `greedy_token(logits)`：**最低索引 argmax**，plain 与 spec 两条路径共用同一选择规则，使唯一残差仅是 ~1e-7 的 logit 漂移。`is_tie`（top-2 间隔<1e-5）供并列检测。
- `slice_caches(caches, n)`：回滚时把每层 (k,v) 截到长度 n 并 `.contiguous()`，防止切片视图累积到 `(K+1)` 宽的大分配上（面板 B8）。
- `speculative_generate_greedy / _sample`：一次一块。块首把上一块的锚点 token 重新喂入验证前向（`(K+1)` 宽），`td[i]` 预测绝对位置 `L+i`；贪心按"argmax 一致"接受、首个不一致处用 target 自己的 token 纠正；采样按 `min(1,q/p)` 接受、拒绝处从 `(q-p)_+` 重采、全接受时从 q 取 bonus。**两条缓存在拒绝处回滚到已提交前缀**；全接受时 draft 还差一个 token，补一次前向再截。块产出会超过 `max_new_tokens` ≤K，**末尾截到精确长度**（探针发现的 overshoot bug）。
- `SpecStats` 记 `accepted/tested/blocks/target_forwards/draft_forwards/target_positions`。`tested = n_accept + (0 if 全接受 else 1)`——只数**真正做过的接受测试**，使 α 是**逐位置条件接受概率**。
- `plain_generate_greedy / plain_sample`：KV-cache 基线（**唯一**合法对照，绝不用 O(n²) 的 `generate`）。
- 正确性仪器：`chunked_forward_logit_diff`（把已提交序列按 `K+1` 宽分块缓存前向 vs 全量前向，取最大差 = v1161 不变量在验证块宽上的版本）；`classify_greedy_diff`（EOS 截断比较，首处分歧若落在 logit 并列则判 `tie_artifact` 否则 `genuine_diff`）。
- 计时：`_time` 跑 R 次、弃 ≥1 预热、CUDA 同步前后，报 median±IQR；方向用保守 `significant` 判定后才命名（面板 B5，绝不复用 v1161 的单次 `_time`）。

## 闸门与判决（`run_spec_decode`）

`correctness_verified` = 四条且：(1) 验证 logit 差 <1e-4；(2) 贪心无 `genuine_diff`（并列伪差放行）；(3) 采样 TV ≤ 地板 `mean+2σ`（固定 N、多 seed）；(4) 每块产出 `(accepted+blocks)/blocks` ≈ 几何 `(1-α^(K+1))/(1-α)`，残差<0.5。`task_learned := correctness_verified`。判决：`spec_decode_correctness_failed`(review) | `..._but_alpha_near_ceiling_task_deterministic` | `..._fewer_forwards_no_wallclock_win`(本结果) | `..._and_faster_wallclock`（计时显著更快才取）。

**主效率指标是 FLOPs 诚实的** `target_positions_processed`（Σ 验证块宽+prefill）：`(K+1)` 宽验证**无论接受与否都付 K+1 个位置**；`tokens_per_target_forward` 是**讨好性计数指标**（把宽验证记成一次），降级为次要；`total_forwards_per_token`（draft+target）证伪"小草稿免费"。α_greedy 与 α_sample **分开**报。

## 设计先于 GPU（两个阻断点被提前抓住）

对抗式面板（4 视角+综合）抓出 **B1**：贪心逐字节相同是**不健全**的闸门（v1161 早已因近似并列把它移出闸门）→ 改键为 logit 不变量+采样 TV+接受一致性。**B3**：探针在平凡玩具上 α 恒为 1，主轴未验证 → 上 GPU 前在真实语料用欠训练检查点草稿亲跑探针，确认 α∈(0.24,0.63)，主轴成立。首版 GPU 跑出 `review`：自投机 K=4 的一致性残差恰为 8/3——因旧指标把 prefill 计入分母、用截断长度做分子；改为"每块产出 vs 几何公式 + 条件 α"后通过（残差 0.22）。

## 测试覆盖（`tests/test_spec_decode_v1170.py`，迁移自已删除的 `output/spec_decode_probe/*`）

logit 不变量（RoPE 开关 × K∈{1,2,4,8} × 多块）；随机/训练模型贪心等价；并列伪差分类；自投机锚点（α=1、达 K+1 上限）；EOS-overshoot 截断等价；block_size 边界不抛异常；回滚连续性；接受规则一致性；采样分布等价（TV 在地板内）；`run_spec_decode` 报告形状 + `status iff task_learned` + 判决集合。

## 运行证据（RTX 4060，3 seeds）

`status=pass`、target EM 0.867、logit 差 1.96e-05、贪心 3600/3600 相同、采样 TV 0.00202≤地板、一致性残差 0.221。α（条件）随草稿质量 0.58→0.88→1.0。**主指标 target 位置比 plain 多 1.28×（FLOPs 亏损）**，墙钟 **0.55×（更慢）**——char 玩具尺度的预期诚实结果：两模型远未喂饱 GPU，宽/窄前向耗时相近、Python 开销主导，draft 的 K 次前向纯属额外开销；只有 target 前向真正主导时才会出现加速。

## 一句话总结

投机解码**可证明等价**（logit/采样/接受规则四闸全过、贪心 3600/3600 相同），但"更少 target 调用"不等于"更便宜"——主指标显示它处理**更多** target 位置、墙钟**更慢**，是 char 玩具尺度上诚实的"正确但不快"。
