# v1191 MiniGPT grokking 因果频率消融 代码讲解

## 本版目标与边界

可解释性这条轴到这里有了相关性证据：v1188 发现 grok 模型的数字 embedding 在傅里叶基上频率集中（top-5 ≈ 31% 功率，显著高于 memorized/random），v1190 发现输出 logits 的加法对角频率（diagonal fraction 0.72）和 embedding 的 top-5 频率完全一致。但两版都只是相关性——命名都用 `supports`，没有做因果干预。v1191 是这条轴的**因果收尾**：直接在已提交的 v1185 checkpoint 上删/留傅里叶频率，看 held-out 准确率怎么变。

这是用户在“advise next step”时我推荐并执行的一版：相关性证据已经够强，唯一缺的高价值步骤就是因果干预，而且 CPU 几秒、不训练（符合用户多次强调的省算力）。边界：`toy_scale_single_checkpoint_causal_frequency_ablation_not_a_general_interpretability_claim`。

## 关键杠杆：绑定的 lm_head

`model.py` 里 `lm_head.weight = token_embedding.weight`（绑定）。所以过滤数字 embedding 的频率，会**同时**改输入表示和输出读出——一次干预打到加法这条频率通道的两端。这让“embedding 频率消融”成为一个强干预，而不只是改输入。

## 频率过滤怎么做

`filter_embedding(E, folded_freqs, mode, p)`：对数字 embedding `E`（`(p, n_embd)`）沿数字轴做 `torch.fft.rfft`（得到 `1..p//2` 折叠频率），按 mode 处理：`remove` 把指定频率清零，`keep` 把除 DC 外、不在指定集合里的频率全清零（DC 永远保留），再 `torch.fft.irfft(..., n=p)` 重建为实信号。`irfft` 自动处理共轭对称，不用手工折叠。

`ablated_model(model, p, folded_freqs, mode)`：深拷贝模型，把数字行 `[0:p]` 换成过滤后的 embedding（op token 行 PLUS/EQ 不动），绑定的 lm_head 自动跟着变。原模型不受影响。

`dominant_folded_freqs` 复用 v1188 的 `embedding_spectrum`+`concentration_metrics` 取 top-k 折叠频率。held-out 准确率复用 v1186 的 `evaluate_table`。

## 三个干预

`run_ablation` 对 v1185 checkpoint 做：

1. baseline（不消融）。
2. remove top-k dominant：删掉 embedding 功率最高的 k 个频率 → 测**必要性**。
3. remove k random non-dominant：删同样数量的随机非主频（多个随机 trial 取均值）→ 测**特异性**（是不是“删什么都疼”）。
4. keep only top-k：只保留 top-k（其余清零）→ 测**充分性**。

## 真实结果

```text
                                  held-out acc
baseline                            0.966
remove top-5 [43,3,48,26,44]        0.578   (掉 0.388)
remove 5 random non-dominant        0.973   (掉 -0.007)
keep ONLY top-5                     0.972
chance 1/97 ≈ 0.010
```

`verdict = dominant_frequencies_sufficient_and_specific_partial_necessity`：

- **充分**：只留 top-5、扔掉其余 43 个频率，准确率还有 0.972——加法算法基本就在这 5 个频率里。
- **特异**：删 top-5 掉 0.39，删随机频率几乎不掉。损伤特异指向 dominant 频率。
- **部分必要**：删 top-5 没塌到 chance（0.578）——模型有冗余。诚实说是部分必要，不是完全必要。

合起来把 v1188/v1190 的相关性升级成因果：dominant 傅里叶频率就是模数加法算法所在，但模型有冗余。

## 一次被自查纠正的 under-claim（和 v1183 的 over-claim 对称）

第一次跑，`decide()` 把这个结果判成 `no_causal_frequency_dependence`。原因是我把 `collapse_drop` 阈值设成 0.40，实际 drop 是 0.388（差一点），而旧 verdict 阶梯只看“是否完全崩”，于是忽略了“只留 top-5 就够（0.972）”这个强充分性信号，也忽略了特异性（0.39 对随机 0.0）。一个强而冗余的因果效应被单一阈值伪影标成“无依赖”。

这和 v1183 把内部最优误标成单调加速是对称的——上次 over-claim，这次 under-claim，都是 `decide` 阈值/阶梯没贴合数据。修法：把必要性、特异性、充分性拆成三个正交信号；verdict 阶梯先看 specific & sufficient，再用 full_collapse 区分“完全必要”和“部分必要”。这样强而冗余的因果不会被掩盖，真正的 null 也仍能落到 `no_clean_causal_frequency_dependence`。这是诚实测量纪律第二次抓住我自己 `decide` 代码里的偏差。

## 测试

`tests/test_grok_freq_ablation_v1191.py`（11 个，CPU 快）：filter remove 后主频变成次主频、filter keep-only 后只剩指定频率、ablated_model 保留 op token 行且不动原模型、decide 五种 verdict 全覆盖（含真实结果对应的 sufficient_and_specific_partial_necessity）、base 太低落 review、report 形状、以及一个 p=11 的端到端 smoke。

## 链路角色与一句话总结

grokking/可解释性这条线现在完整：reproduce(v1179) → characterize(v1183) → audit(v1180-82,84) → ship(v1185) → use(v1186) → consolidate(v1187) → explain 相关性(v1188 embedding, v1190 logit) → **explain 因果(v1191 ablation)**。这条轴可以收尾了，下一步适合换一条全新轴（continual learning / calibration 等）。

一句话总结：v1191 用频率消融把 grokking 的傅里叶机制从相关性升级为因果——只保留 top-5 频率就能保住 0.972 准确率、删它们特异地掉到 0.578（删随机不掉），是充分且特异、因冗余而部分必要；过程中自查纠正了一次阈值导致的 under-claim。
