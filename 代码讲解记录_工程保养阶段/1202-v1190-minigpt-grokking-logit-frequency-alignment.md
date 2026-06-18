# v1190：grokking 输出 logit 频率对齐

## 本版目标和边界

v1190 是根据图片建议推进的一版机制解释版本。图片里提到，v1188 已经打开了 mechanistic interpretability 轴：只看模型“能不能做对”还不够，还要问“它到底用什么结构做对”。v1188 的结论是，grokked 模型的 number embeddings 在 Fourier basis 上出现了明显但不过度夸张的频率集中：top-5 frequency power 大约 31%，显著高于 memorized-not-grokked 和 random-init。图片还建议下一步可以把 embedding 的 dominant frequencies 和 output logits 的 frequencies 对齐，直接验证 trig-identity addition。v1190 就做这件事。

本版不重新训练模型，也不再继续扫 weight decay。用户已经明确说 `wd=1.0` 足够，不想深挖 weight decay，所以 v1190 只读取 v1185 已经 shipped 的 canonical grokking checkpoint。它回答的是一个更具体的问题：如果 number embeddings 的 Fourier 频率真是模型计算 `a+b mod 97` 的机制组成部分，那么输出 logits 在所有 `[a,+,b,=]` prompt 上形成的三维表 `L[a,b,y]`，是否也沿着加法所要求的频率结构组织？如果答案是肯定的，v1188 的 embedding 发现就不只是“权重里有一些周期性纹理”，而是和输出读出共同指向同一套 modular-addition 机制。

边界也必须说清楚。v1190 仍然是 toy-scale single checkpoint 的机制证据，不是大模型 interpretability 的普遍结论；它也不是严格因果干预实验，没有删除某个频率再证明模型失效。它证明的是：在已 grok 的 v1185 checkpoint 上，输入 number embeddings 的 dominant Fourier frequencies 和输出 logits 的 diagonal FFT frequencies 高度一致，并且 random-init 对照没有这种结构。这是“机制对齐证据”，不是最终机制证明。

## 为什么要看输出 logits

v1188 看的是 number token embedding：把数字 `0..96` 对应的 embedding rows 当成一个离散函数，对数字轴做 FFT，观察 power 是否集中在少数频率上。这一步能说明模型把数字表示成了某种周期结构，但还没有直接说明这些频率如何变成答案。因为模型真正输出答案时，读的是 prompt `[a,+,b,=]` 的最后位置 logits：每个候选输出 token `y` 都有一个 logit。也就是说，最终对象不是单独的 `embedding[a]`，而是一个三维表：

```text
L[a, b, y] = model([a, +, b, =]) 对输出 y 的 logit
```

如果模型学会的是 `y = a+b mod p`，那么对于固定的 `y`，二维 surface `L[:,:,y]` 应该像一条 ridge：在满足 `a+b=y` 的位置高，在其他位置低。这个 ridge 的频率结构非常特殊。理想 target surface `I[a,b,y]=1[a+b=y]` 对 `(a,b)` 做 2D FFT 时，非 DC 能量只落在 `k_a == k_b` 的对角频率上。直觉上，因为 `a` 和 `b` 是以同样的相位进入加法约束的；频率空间里，两个输入方向必须同步，才能表示“它们的和等于某个输出”。

因此 v1190 的核心指标不是普通准确率，而是 output-logit cube 的 diagonal FFT fraction：所有输出 token 的 2D FFT power 加总后，有多少非 DC 能量落在 `k_a == k_b` 这条对角线上。理想加法 target 的这个值是 `1.0`；random-init 模型应该接近 0；如果 grokked checkpoint 真的形成了加法频率结构，它应该显著高。

## 新增文件角色

`src/minigpt/grok_logit_freq_v1190.py` 是本版核心模块。它提供几个层次的函数。第一层是数据构造：`prompt_grid(p)` 生成所有 `[a,+,b,=]` prompt，`answer_logit_cube(model,p)` 读取模型最后位置 number-token logits 并 reshape 成 `p×p×p`。第二层是理想对照：`ideal_addition_cube(p)` 构造 one-hot target 表 `I[a,b,(a+b)%p]=1`。第三层是频率分析：`diagonal_fft_power(cube)` 对 `(a,b)` 维度做 2D FFT 并汇总输出 token power；`folded_diagonal_distribution` 把频率 `k` 和 `p-k` 合并成 canonical folded frequency；`logit_frequency_metrics` 输出 diagonal fraction、top-k diagonal fraction、dominant frequency 和 top frequencies。

`scripts/analyze_grok_logit_freq_v1190.py` 是 CLI。默认读取 v1185 shipped checkpoint，也可以通过 `--checkpoint` 指定其他 `.pt`。它支持 `--device auto/cpu/cuda`，但本版默认 CPU 就能在几秒内完成，因为只需要对 `97×97` 个 prompt 前向一次，再做 FFT。`--require-pass` 用于把机制检查接入自动化；如果 diagonal fraction 或频率对齐不达标，脚本会返回非零码。

`tests/test_grok_logit_freq_v1190.py` 是本版单测。它覆盖 prompt grid 格式、理想加法 cube 的 diagonal fraction 为 1、random cube 的 diagonal fraction 很低、folded frequency 的正负频率合并、top frequency overlap 计算，以及 `decide_alignment` 的 pass/review 两条路径。测试不依赖 GPU，也不强制加载 v1185 checkpoint，因此 CI 风险小。

## 核心算法解释

第一步，构造 prompt grid。对于 `p=97`，共有 `9409` 个 `(a,b)` 组合。每个 prompt 是四个 token：

```text
[a, PLUS, b, EQ] = [a, p, b, p+1]
```

这和 v1186 的 inference API 保持一致：模型训练时看到 `[a,+,b,=,c]`，答案 loss 作用在 `=` 位置预测 `c`；推理时只喂 `[a,+,b,=]`，读取最后位置 logits。

第二步，得到 output-logit cube。模型输出的 logits shape 是 `(p*p, 4, vocab_size)`，我们取最后位置和 number-token 部分 `:p`，reshape 成 `(p,p,p)`。这里第三个维度 `y` 是候选答案 token。这个 cube 保留了模型对每个候选答案的相对偏好，而不是只看 argmax 是否正确。相比准确率，logit cube 能暴露模型内部读出结构。

第三步，对每个 `y` 的二维 surface 做 FFT。代码中先对 `(a,b)` 方向减去每个输出 token 自己的均值，去掉 DC bias。然后：

```python
spectrum = torch.fft.fft2(centered, dim=(0, 1))
power = (spectrum.abs() ** 2).sum(dim=2)
power[0, 0] = 0.0
```

这样得到的 `power[k_a,k_b]` 表示输出 logits 在输入两个方向的频率能量。理想加法 surface 的 power 只落在 `k_a == k_b`；所以本版把 `torch.diag(power)` 的总和除以非 DC 总 power，得到 `diagonal_fraction`。

第四步，把 diagonal frequencies 折叠成 `1..p//2`。FFT 里频率 `k` 和 `p-k` 是正负频率对，实值信号通常应合并看。所以 `fold_frequency(94,97)=3`，和 `fold_frequency(3,97)=3`。v1188 的 embedding spectrum 也是 rFFT 后的非 DC folded 频率，因此 v1190 的 logit top frequencies 可以和 v1188 的 embedding top frequencies 直接比较。

## 真实结果

本版真实运行命令为：

```powershell
python scripts\analyze_grok_logit_freq_v1190.py --device cpu --out-dir f\1190\解释\grok_logit_freq_v1190 --require-pass --force
```

输出结论为：

```text
status=pass
decision=embedding_logit_frequency_alignment_supports_trig_addition
heldout_acc=0.965989
embedding_top_freqs=[43, 3, 48, 26, 44]
logit_top_freqs=[43, 3, 48, 26, 44]
embedding_logit_top_freq_overlap_count=5
embedding_logit_top_freq_overlap_fraction=1.0
logit_diagonal_fraction=0.718712
random_logit_diagonal_fraction=0.000122
ideal_logit_diagonal_fraction=1.0
logit_top_k_diagonal_fraction=0.610591
```

这些数字的含义很清楚。第一，checkpoint 仍然是可用的：heldout accuracy 为 `0.965989`。第二，模型 logits 的非 DC 频谱能量有 `71.8712%` 落在加法所预期的 diagonal frequencies 上，而 random-init 同架构模型只有 `0.0122%`。第三，logit diagonal top-5 frequencies 完全等于 embedding top-5 frequencies：`43, 3, 48, 26, 44`。这正好把 v1188 的 embedding 证据和输出读出证据接起来。

理想 target 的 diagonal fraction 是 `1.0`，这是 sanity check：算法确实识别到了 `a+b=y` ridge 的频率结构。理想 target 的 top-k diagonal fraction 不高，是因为 one-hot target 把 power 比较均匀地分散在所有 diagonal frequencies 上；而 trained model 的 top-k diagonal fraction 达到 `0.610591`，说明它不是平均使用所有频率，而是把输出读出集中在少数和 embedding 一致的 dominant frequencies 上。

## 检查与判定

`decide_alignment` 用七条检查来判定：

- checkpoint heldout accuracy 至少 `0.90`；
- ideal addition 的 diagonal fraction 至少 `0.999`；
- shipped logits 的 diagonal fraction 至少 `0.50`；
- random logits 的 diagonal fraction 至多 `0.05`；
- shipped-random 的 diagonal gap 至少 `0.25`；
- embedding/logit top frequency overlap 至少 4 个；
- dominant frequency 必须一致。

真实结果全部通过，因此 decision 是 `embedding_logit_frequency_alignment_supports_trig_addition`。这个命名刻意使用 `supports` 而不是 `proves`：它支持 trig-identity 机制解释，但不是因果干预证明。后续如果要更进一步，可以做 frequency ablation：在 embedding 或 output readout 中削弱 top frequencies，看 heldout accuracy 是否下降。但那属于新的干预版本，不属于 v1190。

## 和 v1188 的关系

v1188 的核心事实是：generalizing 模型的 number embeddings 有 Fourier concentration，而 memorized-not-grokked 和 random-init 没有同样强的集中。v1190 不重复训练那组 paired arms，而是读取 shipped checkpoint，沿着“输出读出”方向做更直接的机制对齐。两版连起来形成这样的解释链：

```text
v1179: weight decay 让模型先记忆后泛化
v1183: wd=1.0 是这个设置下足够且最快的内部最优
v1185: 把 wd=1.0 recipe 固化成可加载 checkpoint
v1186: checkpoint 能真实预测 a+b mod 97
v1188: checkpoint 的 number embeddings 出现 Fourier dominant frequencies
v1190: 输出 logits 的加法 ridge 也集中在同一组 frequencies
```

因此 v1190 的价值不是又堆一份报告，而是把“表示层的 Fourier 结构”接到“输出层的答案读出结构”。这更贴近图片里说的“verify the trig-identity addition directly”。

## 输出和归档

本版输出：

- `f/1190/解释/grok_logit_freq_v1190/grok_logit_freq_v1190.json`
- `f/1190/解释/grok_logit_freq_v1190/grok_logit_freq_v1190.csv`
- `f/1190/解释/grok_logit_freq_v1190/grok_logit_freq_v1190.txt`
- `f/1190/解释/grok_logit_freq_v1190/grok_logit_freq_v1190.md`
- `f/1190/解释/grok_logit_freq_v1190/grok_logit_freq_v1190.html`
- `f/1190/图片/grok-logit-frequency-alignment-v1190.png`

JSON 是机器证据，Markdown/HTML 是人工阅读入口，截图证明报告可渲染且关键字段可见。README、`f/README.md` 和工程保养阶段讲解 README 都更新到 v1190。

一句话总结：v1190 把 v1188 的 embedding Fourier 发现推进到 output logits，证明 shipped grokking checkpoint 的答案读出也集中在 modular-addition 所预期的对角频率上，并且 dominant frequencies 与 embedding 完全对齐。
