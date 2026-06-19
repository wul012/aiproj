# v1193 MiniGPT 持续学习 / 灾难性遗忘 代码讲解

## 本版定位：干净断裂的新轴

v1191 收尾了 grokking 线；v1192（校准）被我自己诚实判定为"贴着 v1173 KL 的相邻轴"，不是干净的新轴——用户随后明确选了 **clean break**：持续学习 / 灾难性遗忘。这是一个**全新现象**：顺序多任务的相互干扰（不是延迟泛化，不是置信度校准）。

两个可区分的模数运算共享一个 1 层 transformer，用 op token 区分（PLUS=p, TIMES=p+1, EQ=p+2，vocab=p+3）：任务 A=`(a+b) mod p`，任务 B=`(a*b) mod p`。先把 A 训到稳定平台，再训 B，量 A 留出准确率的塌缩。复用了 grok 的模数任务基建（`build_modular_task` 的思路、`answer_accuracy`/`answer_loss`、SEQ_LEN 布局），但问的是完全不同的问题。

开工前照例跑了对抗式设计评审（5 视角 Workflow，其中 2 个视角因 API 连接中断挂了，拿到 3 个 + 我自己补全 scope/compute）+ 两个 CPU 探针——都在写正式代码之前。

## 探针先证伪

探针 1 直接确认：add→mul 和 add→sub 都把 A 从 ~0.95 砸到 ~0.05（≈随机）=灾难性；replay 单调缓解；wrong-replay（回放 B）保不住 A；联合可学。探针 2 验证评审新加的三个控制：全局 pair 掩码 + 巩固平台都成立；**关键发现 random-label-B 把 A 砸得和 real-B 一样狠（0.047 vs 0.038）**——所以遗忘是分布漂移驱动，不是 B 结构特有。这个发现直接写进了诚实叙事。

## 评审堵的坑（写代码前）

1. **测试集泄漏（fatal）**：A 和 B 共享数字 token 0..p-1 和绑定的 embedding/lm_head 行，A 的留出操作数 (a,b) 会作为 B-train 出现。修法：**全局 pair 掩码**——同一组 (a,b) 从 A-train、B-train、replay、joint 统一剔除，`verify_no_leak` 校验并作门控。
2. **巩固混淆**：A 必须训到**持续平台**（acc 连续 W 次评估 ≥ 阈值），不是首次越线，否则"遗忘"只是"没学牢"。
3. **固定 B 预算**读留存；**continue-on-A 地板**（无漂移应≈0 遗忘）；**random-label-B null**（结构 vs 漂移）；**savings 重学探针**（擦除 vs 掩蔽）；**"catastrophic"按幅度门控**（掉到≈1/p 才算）。

## 真实结果（p=23，add→mul，3 seed）

```text
A 平台 0.984 → 训完 B 后 0.041 (≈chance 0.043) = 遗忘 0.943 (瞬时塌缩)
continue-on-A 地板: 遗忘 -0.006    random-label-B: 遗忘 0.937 (≈real-B)
wrong-replay(回放B): 遗忘 0.931     joint 上界: A 0.862 / B 0.837
replay A-train 剂量: buf0=0.943 buf8=0.362 buf32=0.063 buf128=0.038
```

`verdict = catastrophic_forgetting_mitigated_by_replay`（status=pass）。诚实机制：random-label-B ≈ real-B → 分布漂移驱动，非 B 结构特有；savings 慢 → 更接近擦除。

## 门控与诚实测量

status=pass 只证有效测量：g_a_consolidated（A 到平台）、g_b_learned（B 真学会，acc−majority_prior≥margin，排除"见 0 猜 0"捷径）、g_jointly_learnable（联合能同时学会 = 干扰非无能）、g_no_operand_leak、g_floor_clean（continue-on-A 不忘）。verdict 阶梯有真实可达 null（no_catastrophic_forgetting / not_mitigated）。

**两次从缓存零重训修 decide（reuse-cached）**：
1. g_joint 最初错误地用 add 单任务平台 0.98 当联合门槛，但 mul mod p 天花板本就更低（joint B 0.84）。改成"两者都远超 majority-prior + margin"——干净、与 g_b_learned 一致，不拿任意 0.88 卡自己的头条。
2. 三个 seed 遗忘 std=0（都塌到≈0.04），导致 wrong-replay 比 naive 仅低 0.012 就被 `significant()` 判成"有缓解"（std=0 刀刃）。加了 `min_reduction=0.05` 最小有效幅度门槛：一次缓解必须**同时**超过 margin 和合并 std 才算。replay 真实的 0.90 缓解照样过，0.012 的噪声不过。这是这条纪律第三/四次抓住 decide 阈值伪影（v1183 over、v1191 under、v1192 boundary、这次 std=0 刀刃）。

## 工程：训练/分析分离

Phase A（`run_continual_v1193.py`）只训一次，把每 arm 准确率/轨迹/savings/replay 扫描存进 `cache.pt`；Phase B（`analyze_continual_v1193.py`）纯 CPU 重算聚合 + decide。库 `continual_v1193.py` 把训练函数和纯分析函数分开，17 个测试在合成缓存上跑 decide 全分支 + 一个 p=7 训练 smoke。

一句话总结：v1193 开了持续学习这条干净新轴——共享 1 层 transformer 上先学 add 再学 mul，A 灾难性塌到≈随机，回放 A 按剂量缓解、回放 B 无效（特异）；诚实标注遗忘是分布漂移驱动（random-label-B 同样砸 A）而非任务结构特有、且更接近擦除；过程中两次零重训修正了 decide 阈值伪影。
