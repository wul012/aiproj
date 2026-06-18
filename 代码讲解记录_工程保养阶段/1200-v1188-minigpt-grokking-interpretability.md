# v1188 MiniGPT grokking 机理可解释性 代码讲解

## 本版目标与边界

v1188 给项目开了一条**全新的轴：机理可解释性（mechanistic interpretability）**。此前 grokking 线回答的都是“行为”问题：v1179 证明模型 grok（泛化），v1183 测了它对 weight decay 的剂量反应，v1185 把它存成标准 checkpoint，v1186 用它推理。v1188 第一次回答“权重内部到底发生了什么”：grok 后的模型**怎么算** `a + b (mod 97)`。

教科书结论（Nanda 2023，“Progress measures for grokking”）是：grok 后的模数加法网络把每个数字表示成**稀疏的傅里叶特征**——数字 token 的 embedding 看成数字索引的函数时，频谱集中在少数关键频率上，网络再用三角恒等式 `cos/sin` 相加实现模加。

本版几乎零额外训练成本（结构直接从权重读出，符合用户多次强调的省算力倾向），是一个全新能力（可解释性），且**闭合了 grokking 的故事**：v1179/v1183 在行为层面发现“wd 驱动泛化”，v1188 在权重层面给出机制——只有泛化的模型长出傅里叶结构。边界：`toy_scale_single_task_interpretability_embedding_fourier_structure_only`。

## 核心分析：embedding 频谱

核心模块 `src/minigpt/grok_interp_v1188.py`。

`number_embedding(model, p)` 取 `token_embedding.weight[0:p]`（数字 0..p-1 的 embedding 行，排除 PLUS/EQ），得到 `(p, n_embd)`。

`embedding_spectrum(E)` 是关键：对 embedding 的每一列（每个维度作为数字索引的信号）做 `torch.fft.rfft`，取功率 `|·|²` 在维度上求和，**去掉 DC**（每列均值，无信息），归一化到 1。返回每个非零频率的归一化功率。

`concentration_metrics(norm_power)` 量化“多稀疏”：`top_k_fraction`（前 5 个频率的功率占比，稀疏则高）、`spectral_entropy`（归一化谱熵，稀疏则低）、`dominant_freq`、`n_freqs_for_90pct`（覆盖 90% 功率需要几个频率）。

可证伪点很明确：纯余弦 embedding（`cos(2π·k·n/p)`）应给出单一主频、top-5 占比≈1、熵≈0；随机 embedding 应弥散（top-5≈5/48、熵≈1）。这两条都写进了测试。

## 配对三臂对照

`collect_arms` 是本版的科学设计。对每个 seed：

- **grokked**：复用 `grok_checkpoint_v1185.train_to_grok`，配置 `wds=(1.0,)`、`max_steps=40000`，早停于 grok。
- **memorized**：同一个 `train_to_grok`，但 `wds=(0.0,)`、`max_steps=5000`——wd=0 永远不 grok，于是跑满 5000 步、记住训练集但验证集停在低位，返回这个 memorize-但-没-grok 的模型。
- **random**：`make_grok_model` 未训练，作为 null。

关键是 grokked 和 memorized 用**同一 seed → 同 init、同 split**，只有 weight_decay 不同（配对设计，和 v1179 一致）。这样三臂频谱集中度的差异，干净地归因于“是否泛化”，而不是初始化或数据。这里全程复用 v1179/v1185 的原语（`train_to_grok`、`make_grok_model`），没有新写训练循环。

## decide：gate 与 verdict

`decide` 把有效性和结论分开：

- `g0_arms_behaved`：每个 grokked 臂确实 grok 了（t_gen 非空），每个 memorized 臂确实是“记住但没 grok”（t_mem 非空、t_gen 空）。否则对照无效。
- `g1_grid_complete`：三臂 seed 数相等且非空。
- `status=pass` 当且仅当 g0 且 g1。

verdict 用 `significant`（来自 experiment_utils，多 seed 的 gap-minus-combined-std 检验）比较 top-5 占比：

- `fourier_structure_explains_generalization`：grokked 显著高于 random **且** 显著高于 memorized（结构跟着泛化走）。
- `fourier_structure_from_training_not_generalization`：grokked 显著高于 random 但 ≈ memorized（训练就会长结构，与是否泛化无关）。
- `fourier_structure_not_separable`：grokked 不显著高于 random（honest null）。

## 真实结果与诚实解读

真实 GPU（3 seeds）：`verdict=fourier_structure_explains_generalization`，status=pass。

```text
                top-5 占比        谱熵      90%功率所需频率数
grokked         0.307 ± 0.004    0.914     34 / 48
memorized       0.150 ± 0.002    0.995     42 / 48
random          0.120 ± 0.001    0.999     43 / 48   (chance ≈ 0.104)
```

- **方向确认且显著**：grokked > memorized > random，顺序完全符合假设，误差棒极小。只有泛化的那个臂显著高于 memorized，所以傅里叶结构**跟着泛化走**——这是 grokking 的权重层面机制，闭合了 v1179/v1183 的行为发现。已提交的 v1185 checkpoint（seed 1337）top-5 占比 0.305、主频 43，和它的 grokked 孪生一致。
- **但幅度温和，不是极稀疏**：top-5 只占约 31% 功率，要 34 个频率才到 90%，主频还随 seed 变（43/35/32）。这**不是** Nanda 在 attention-only 模型里的“四五个频率解释一切”的极稀疏基。我们的 1 层模型带 LayerNorm + GELU MLP，所以傅里叶结构是个**显著的倾向**，不是完整干净的算法。

这正是诚实纪律：verdict 抓住真实且显著的结论，但说明/文档明确把幅度标成 partial，不为了贴合教科书而夸大成极稀疏。

## 测试

`tests/test_grok_interp_v1188.py`（8 个，CPU 快）：纯余弦 embedding 给单一主频 + top-5≈1 + 熵≈0；随机 embedding 弥散；`analyze_model` 输出形状正确；decide 三种 verdict + g0 失败落 review（用合成臂指标）；一个极小端到端 smoke（p=5）真训三臂并 decide。

## 链路角色与一句话总结

v1188 把 grokking 从“行为现象”推进到“机制解释”，并开了项目的可解释性轴。后续可做：把主频和输出 logits 的频率对齐（验证三角恒等式相加）、或用同样的频谱分析看 train_frac/wd 怎么影响结构强度。

一句话总结：v1188 用 FFT 揭示——只有 grok（泛化）的模型把数字 embedding 的能量显著集中到少数频率（top-5 占比 0.307 vs memorized 0.150 vs random 0.120，配对同 init），从权重层面解释了 grokking；同时诚实指出在带 LayerNorm/MLP 的 1 层模型里这是个显著倾向而非教科书式极稀疏傅里叶算法。
