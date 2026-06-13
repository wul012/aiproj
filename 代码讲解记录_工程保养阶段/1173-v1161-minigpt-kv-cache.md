# 1173 · v1161 · MiniGPT KV-cache 增量生成

## 本版目标与不做什么

本版给 MiniGPT 加上 KV-cache（缓存历史 key/value 的增量生成）。现有 `generate` 每生成一个 token 都把整段序列重新前向一遍，复杂度是 O(n²)；KV-cache 把每步降到一次单 token 前向（O(n)），是现代大模型推理的标准优化。本版承接 [[1172-v1160-minigpt-rope]] 选定的“架构纵深”路线，是“RoPE + KV-cache”里的第二块。

本版要做两件事并都拿出证据：一是**正确性**——缓存路径必须与未缓存的整段前向数值等价；二是**加速**——测量生成的 tokens/sec 提升。明确不做：不改动现有 `forward` / `generate` / `sample_next` 的对外行为（必须向后兼容）、不在很小的配置上强行宣称加速、不实现超出 `block_size` 的长度外推（缓存上限设为 `block_size`，与模型训练上下文一致）。

## 关键修改文件与链路角色

- `src/minigpt/model.py`（修改，向后兼容）：
  - 新增模块级 `select_next_token(last_logits, *, temperature, top_k, blocked_token_ids)`，把“logits → 采样下一个 token”的逻辑抽成一处；`sample_next` 改为调用它，行为不变。这样未缓存与缓存两条生成路径用**同一套采样逻辑**，保证可比。
  - `CausalSelfAttention.forward_cached(x, cache, pos_offset)`：对新 token 计算 q/k/v，在 `use_rope` 时按**绝对位置** `pos_offset` 切片旋转（这是缓存正确性的关键——新 token 的 RoPE 角度必须用它的真实位置，而不是 0），把新 k/v 与缓存的 past k/v 拼接，按绝对位置构造因果掩码（query 行 `pos_offset+i` 只能看 key 列 `j ≤ pos_offset+i`），返回输出与更新后的 (k, v)。
  - `Block.forward_cached`：把缓存穿过注意力，残差与 MLP 不变。
  - `MiniGPT.forward_cached(idx, caches, pos_offset)`：只前向新 token，按 `use_rope` 决定是否加绝对位置嵌入（位置从 `pos_offset` 起），逐层穿缓存，返回新 token 的 logits 与各层更新后的缓存。
  - `MiniGPT.generate_cached(...)`：先对 prompt 做一次 prefill 建缓存，之后每步只喂上一个新 token、`pos_offset` 递增；采样契约与 `generate` 完全一致；到 `block_size` 上限即停止。
- `src/minigpt/kv_cache_eval_v1161.py`：验证 + 基准。算缓存 vs 整段前向的最大 logit 差、贪心序列是否一致，并计时两种生成的 tokens/sec（含 CUDA 同步与 warmup）。
- `scripts/run_kv_cache_eval_v1161.py`、`tests/test_kv_cache.py`、`tests/test_kv_cache_eval_v1161.py`：入口、正确性测试与基准 shape 测试。

## 缓存正确性的数学要点

因果注意力下，位置 i 的输出只依赖它和它之前的 key/value。所以“整段一次性算”与“逐 token 增量算”在数学上等价，只要满足两点：一是位置信息正确——RoPE 必须按新 token 的绝对位置旋转，绝对位置嵌入必须取 `pos_offset` 起的索引；二是因果掩码正确——增量时新 query 能看到所有缓存的 key（它们都在它之前）加它自己。dropout 在 eval 下是恒等，所以缓存路径在推理时与训练前向的非随机部分完全一致。

## 真实结果与诚实边界

GPU 运行（n_embd=512、n_layer=8、ctx=1024、生成 700 token）：`max_logit_diff=1.07e-06`、贪心序列一致、`speedup≈1.58x`、`decision=kv_cache_correct_and_faster`。

关于正确性判据，本版有一个刻意的、诚实的设计决定：**通过门槛只看 logit 数值等价（max_logit_diff < 1e-4），不看贪心序列逐 token 相等**。原因是：缓存与整段前向在 float32 下因矩阵分组不同会有约 1e-6 的微差，这在微型未训练模型上可能在 argmax 近似平局处翻转某个 token，从而让贪心序列分叉——这是 argmax 的特性，不是缓存的 bug。把门槛建立在“logits 数值等价”这个可靠判据上，才不会把一个 argmax 平局误判成缓存错误。贪心一致性仍作为信息项报告（实测多数配置为 True）。

关于加速，诚实结论是“随规模增长”：在很小配置（n_embd=128、200 token）上，单步 Python/kernel 开销主导，缓存可能持平甚至略慢（实测约 0.96x）；放大到大模型、长序列时，未缓存的 O(n²) 计算被放大，缓存的 O(n) 优势才显现（约 1.2–1.6x）。本版用较大配置归档以体现真实收益，并在报告中写明这一规模依赖，不在小配置上夸大。

## 测试如何真实覆盖链路

`test_kv_cache` 钉死正确性：对 use_rope 关/开两种模型，逐 token 走缓存收集的 logits 必须与整段前向 `allclose`（atol 1e-4）；prefill 多 token 后再 decode 一个 token，与整段前向对应位置一致；`generate` 与 `generate_cached` 在 `top_k=1`（确定性）下产生**完全相同**的 token 序列；缓存长度每步加一。`test_kv_cache_eval_v1161` 在 CPU 小配置上验证基准报告的正确性字段（`max_logit_diff < 1e-4`、`correctness_verified`、状态 pass）与报告结构，但不对计时做断言（计时本身有波动，断言会脆）。配合既有 model/generate 测试零改动通过，"加缓存但不破坏旧生成路径"的链路被真实保护。

## 一句话总结

v1161 给 MiniGPT 加上经严格数值验证（max logit diff ~1e-6、贪心一致）的 KV-cache 增量生成路径，在较大配置上把 700-token 生成加速约 1.6 倍，且不改动既有生成接口——现代推理优化的第一块正确落地，加速的规模依赖也讲得诚实。
