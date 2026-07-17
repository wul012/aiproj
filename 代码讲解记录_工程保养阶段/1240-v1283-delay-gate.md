# 1240 - v1283 delay gate：grokking 的延迟相位是宽度门控的——门在哪里？

## 这一版回答什么问题

v1282 bank 下的新现象："w=16 从未记忆却泛化到 0.96"。这一版的 P1 法证（对四份
提交缓存的 33 个含训练曲线的格子做延迟+耦合分析，纯 CPU 免费）先把问题重塑了
两次：

1. **"grokking 是 lr 假象"的强形式被证伪**：d=128 在每个稳定 lr 下都保有完整的
   延迟相位——max(train−val) gap 在 0.85–1.0（存在"已记忆未泛化"的完整平台），
   lr 把延迟从 ~11,100 步压缩到 ~700 步，但**从未消灭它**。
2. **w=16 的耦合是宽度门控而非 lr 诱导**：它在 lr=4e-3 下 max_gap 0.29–0.41，
   在 lr=1e-3 下 t_mem ≈ t_gen（None/2600/5900 对 2800/2600/6600）——w=16 在
   任何 lr 下都**从未 grok 过**：没有延迟相位，train 和 val 一起上升，它只是
   在"学习"。而 w=32 在两个 lr 下都有真实的延迟相位（1e-3 下延迟 1,400–2,600）。

于是问题锋利化：**grokking 的相位结构在 w=16（耦合）与 w=32（延迟）之间的哪里
开启？开启是陡峭还是渐变？** P1 还给了判据一件礼物：33 个格子的 max_gap 分布
双峰，[0.41, 0.79] 是空洞——阈值就冻结在洞里。

## 实验设计：三个边界宽度 + 重跑锚点

全部 α=1、lr=1e-3（经典配方，本版只动宽度）、60k 时钟。

- **边界臂（判决）**：w ∈ {20, 24, 28} × 3 seeds = 9 runs（head_dim 5/6/7 合法），
  缓存完整 train+val 曲线。
- **锚点臂**：w ∈ {16, 32} × 2 seeds = 4 runs——v1279 只存了 val 曲线，端点必须
  用曲线级 max_gap 重新确认（G0：16 两格 coupled、32 两格 delayed，否则
  anchor_mismatch → review）。
- 相位分类（阈值对 (0.5, 0.7) 为主、(0.4, 0.8) 为 G2 稳健性检查，都在 P1 空洞
  内）：failed（heldout<0.9）/ coupled（gap≤c）/ delayed（gap≥d）/ intermediate。
  宽度类 = 非 failed 格的一致类（容忍 ≤1 failed；≥2 failed → substrate_unsound）。
- 阶梯（预注册 `5146a306`）：全部 ∈ {coupled, delayed} 且随宽度单调 →
  `delayed_phase_onset_is_sharp`；含 intermediate 且单调 →
  `delayed_phase_onset_is_graded`；mixed 或非单调 → review；两个阈值对判决不一致
  → review（threshold_instability）。
- P2 探针 = w=24 seed 1337（正中格），槽位复用；唯一止损：不泛化。
- 预算 13 ≤ 16；描述性输出：延迟长度、max_train、t_gen 随宽度的走向。

## 实现要点

`src/minigpt/grok_delay_gate_v1283.py`：训练完全复用 v1280 `train_cell`（宽度经
`dataclasses.replace` 传入）；本版新增的是**度量本身**——`max_train_val_gap`
与四类相位分类器。测试 7 项：分类器单元（含 failed 与两个阈值对）、配置校验、
锚点失配 G0、全部阶梯分支（sharp/graded/非单调/混杂/substrate/阈值翻转）、
注入 trainer + 探针槽位、字节稳定契约、图像落盘。

## 结果：门在 w≈24，开启是陡峭的双峰跳变，临界点上 seed 掷硬币

P2 探针先落在 P1 空洞正中（w=24 seed 1337：max_gap 0.4766、t_mem=t_gen=1100、
heldout 0.988），预警了阈值翻转风险。全网格揭晓后图景反而更干净：**空洞守住
了**——13 个新格里没有任何一个落在 [0.5, 0.7]，分布保持双峰；但 w=24 的三个
seed 分裂在两个模式上（0.48 耦合 vs 0.71/0.72 延迟）。按预注册规则宽度类为
mixed，判决 **`review`（mixed_widths）**，G0/G1/G2 全过——而且 G2 在两个阈值对
下判决一致，P2 预警的 threshold_instability 反而没有触发（review 的原因在两对
下相同）。

宽度分类全景：16（锚）coupled 2/2 → 20 coupled 3/3 → **24 mixed（1C/2D）** →
28 delayed 3/3 → 32（锚）delayed 2/2。两个量化细节把"陡峭"钉死：coupled 格的
延迟**精确为 0**（t_mem = t_gen，同一个 eval 点双双过线），delayed 格延迟
≥300——延迟本身也是双峰的，没有"小延迟"过渡带；全部 13 格泛化成功
（heldout 0.952–0.988），无 failed。

解读：宽度从 16 扫到 32，动力学在"耦合学习"（train/val 同升、零延迟、从不
grok）与"grokking"（先记忆后泛化、正延迟）两个**离散模式**之间切换，临界宽度
≈24 处两模式共存、seed 决定归属——一级相变 + 有限尺寸涨落的图景，`graded`
（连续渐变）分支被干净排除。至此 v1277 起点之问的三层解构完整：w≥32 的快慢
差异主要是 lr 饥饿（v1281/v1282）；w≤20 根本不在 grokking（没有延迟相位，
本版）；相位边界在 w≈24，陡峭且随机。

## 诚实边界与自审

范围：own grokked substrate、toy scale、经典配方 lr=1e-3、60k 预算；"临界宽度
≈24"的分辨率受宽度网格间距 4 与 n_head=4 整除约束限制；mixed 是三 seed 的
样本性质，更多 seed 会把共存区刻画得更细（banked）；机制问题（耦合格是否
不经过记忆解直接长出傅里叶回路——与 v1191 回路足迹、v1277 容量地板的关系）
banked 给机制版。decide() 自审：预注册 `5146a306` 后判据与代码**零改动**
（图形函数亦未动，连图例都没碰）；阈值在任何新数据之前冻结于 P1 空洞内；
mixed_widths → review 是预注册路由的正式产出。GPU 13/16。
