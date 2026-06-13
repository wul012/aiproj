# 1172 · v1160 · MiniGPT RoPE 旋转位置编码

## 本版目标与不做什么

本版给 MiniGPT 加上现代位置编码 RoPE（Rotary Position Embedding），作为现有“可学习绝对位置嵌入”的替代方案，并用 [[1169-v1157-minigpt-lora-heldout-eval]] 建立的 held-out 评估工具做一次诚实对照。RoPE 是当下主流大模型（如 Llama 系列）普遍采用的位置编码，理解并正确实现它，是从“玩具 GPT”走向“现代架构”的关键一步。

本版明确不做：不删除或破坏现有的可学习位置嵌入路径（必须保持完全向后兼容）、不在本版强行证明“RoPE 更强”、不实现长度外推评估（那是 RoPE 招牌优势，留给后续专门版本）。本版的交付是“正确实现 + 向后兼容接入 + 诚实对照测量”。

## 本版来自哪条路线

用户在 v1159 之后选择了“RoPE + KV-cache”这条架构纵深路线。本版先做 RoPE（v1160），KV-cache 作为自然的下一版（v1161）。它复用 v1157 的 `templated_corpus` 语料与 held-out 切分、`heldout_eval` 指标，以及 v1159 刚抽出的共享训练循环 `train_lm`——这正是 v1159 去重的收益：本版的两个模型训练直接调用同一个 `train_lm`，没有再复制循环。

## RoPE 原理与实现

RoPE 不往输入加位置向量，而是在注意力里按位置**旋转** query 和 key 向量。对一个偶数维的 head（维度 `hs`），把相邻维两两看成复平面上的点，位置 `t` 处旋转角度为 `t · theta^(-2i/hs)`。旋转是保范变换，因此不会破坏注意力分数的尺度；两个 token 的 query/key 点积只依赖它们的**相对**位置差，这就是 RoPE 把相对位置信息注入注意力的方式。

实现拆成可测试的小原语，放在 `src/minigpt/rope.py`：

- `rotate_half(x)`：把最后一维前后两半 `[x1, x2]` 映射为 `[-x2, x1]`，对应复数乘 i 的实数化写法。
- `build_rope_cache(seq_len, head_size, base)`：预计算 `cos`、`sin`，形状 `(seq_len, head_size)`；用 `theta = base^(-arange(0,hs,2)/hs)`、`freqs = outer(pos, theta)`、再把 `freqs` 自拼接成 `hs` 维。要求 `head_size` 为偶数，否则报错。
- `apply_rope(x, cos, sin)`：对 `(B, n_head, T, head_size)` 的 `x` 施加 `x * cos + rotate_half(x) * sin`，`cos/sin` 按 `(1,1,T,hs)` 广播。

## 关键修改文件与链路角色

- `src/minigpt/rope.py`（新增）：RoPE 原语。
- `src/minigpt/model.py`（修改，严格向后兼容）：`GPTConfig` 新增 `use_rope=False` 与 `rope_base=10000.0` 两个带默认值的字段；`CausalSelfAttention` 在 `use_rope` 时校验 head 维为偶、用 `register_buffer(..., persistent=False)` 注册 `rope_cos/rope_sin`（派生量，不进 checkpoint），并在 reshape 出 q、k 后对二者施加 RoPE；`MiniGPT.forward` 在 `use_rope` 时跳过可学习位置嵌入的相加。默认 `use_rope=False` 时不注册任何新 buffer、forward 路径与改动前逐字节一致。
- `src/minigpt/rope_eval_v1160.py`（新增）：对照编排。用同一语料、同一 `train_lm` 从零训练 `use_rope=False` 与 `use_rope=True` 两个模型，各自在 held-out 上评估，组装对照报告。
- `scripts/run_rope_eval_v1160.py`（新增）：真实运行入口。
- `tests/test_rope.py`、`tests/test_rope_eval_v1160.py`（新增）：覆盖原语与对照。

## 向后兼容如何保证

这是改动 `model.py` 这种核心文件时最该讲清楚的事。三条保证：一是新增 config 字段都带默认值且默认关闭，老 checkpoint 的 config dict 不含这两个键，`GPTConfig(**cfg)` 会用默认值补上 `use_rope=False`，行为不变；二是 `use_rope=False` 时不注册 `rope_cos/rope_sin`，且即便注册也用 `persistent=False`，state_dict 对既有模型完全不变；三是 forward 在 `use_rope=False` 时仍走“token 嵌入 + 可学习位置嵌入”的原路径。证据是既有 3173 条测试**一行未改**全部通过，全量到 `3183 passed`（净增 10 条正是本版 RoPE 新测试）。

## 真实结果与诚实边界

GPU 对照：可学习绝对位置 held-out loss 0.898（acc 0.681），RoPE 1.017（acc 0.679），差值 RoPE−learned 为 loss +0.119、acc −0.002。`verdict=learned_positions_lower_heldout_loss`。

诚实地说，在这个**短的、定长**语料上可学习绝对位置略优，这完全符合预期：RoPE 的真正价值在相对位置与长度外推（在比训练更长的上下文上仍可用），而定长短序列不触发这些优势，反而让可学习绝对位置“恰好拟合固定位置”。所以本版不把结果包装成“RoPE 更强”，而是把它定位为“一个被正确实现、可用、可对照的现代位置编码选项”，并把 RoPE 招牌优势——长度外推——明确留给后续版本：在 block_size 之外评估时，可学习绝对位置根本无法处理（位置表越界），而 RoPE 可以，这才是它该赢的擂台。另需记一笔小债：当前 RoPE 模型仍为 state_dict 简洁而保留了一份未被使用的 `position_embedding`，未来清理可去掉以兑现 RoPE 的省参优势。

## 测试如何真实覆盖链路

`test_rope` 钉死原语正确性：`rotate_half` 的精确映射、cache 形状与奇数维报错、RoPE 的保范性（旋转前后向量范数 `allclose`）、位置 0 处为恒等（角度为 0）；并验证 `use_rope=True` 模型能前向、注册 rope buffer、rope buffer 不进 state_dict、奇数 head 维被拒、默认 config 不开 RoPE。`test_rope_eval_v1160` 验证两种位置方案都能训练到真实（非退化）held-out 损失、报告结构正确、verdict 落在三档之一。配合既有 model 测试零改动通过，整条“加 RoPE 但不破坏旧路径”的链路被真实保护。

## 一句话总结

v1160 以一个默认关闭、严格向后兼容的开关，给 MiniGPT 加上正确实现且保范的 RoPE，并用 held-out 工具诚实测出“定长短语料上可学习绝对位置略优”——把现代位置编码能力落地、把 RoPE 真正的长度外推优势留给专门版本，结论不浮夸。
