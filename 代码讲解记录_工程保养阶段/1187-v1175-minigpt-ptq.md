# 1187 · v1175 · MiniGPT 训练后权重量化（PTQ）：质量代价，诚实测量

## 目标与边界

承接推理效率线（v1161 KV-cache、v1170 投机解码）。训练好的 MiniGPT 权重**伪量化**（`W→dequantize(quantize(W))`、fp32 推理、无整数 kernel），测"质量-比特"退化曲线。这测**质量代价**（架构无关），**不是**显存/速度收益（玩具尺度无意义、无整数 kernel，同 v1170 墙钟诚实）。主指标 = held-out completion-token **CE**（连续；EM 粗糙会错置悬崖）。`status==pass` 只证测量有效（往返正确、基线可学不饱和、退化可分辨、网格完整），非"量化好"。范围：仅权重 RTN；激活量化/QAT/GPTQ/AWQ 校准不在范围。

## 入口与核心实现（`src/minigpt/ptq_v1175.py`）

- `quantize_tensor(W, bits, *, granularity, scheme)`：2D 权重伪量化。粒度 per_tensor / per_channel_row / per_channel_col / group32（统一走 `_to_groups`→`_quantize_groups`→`_from_groups`，把 W 重排成 (G, group) 逐行量化再还原）。方案 absmax_sym（基线）/ percentile_clip（99.9 分位裁剪）/ mse_clip（每行网格搜裁剪比最小化 MSE）/ affine_asym（min/max+zero-point）。
- `component_param_names(model, component)`：用 `named_parameters`（**去重绑定**）选 2D 权重；组件 embedding / c_attn / c_proj / mlp / attention(=c_attn+c_proj) / all；排除 position_embedding（RoPE 下未用）与 1D（LayerNorm/bias 保持 fp32）。
- `quantized_model(base, bits, component, *, granularity, scheme)`：deepcopy 后**按参数身份**就地量化 `p.data`（`named_parameters` 去重，绑定的 token_embedding=lm_head 只量化一次、不会被 state_dict 往返"最后写入"悄悄还原——探针的"embedding 无损"正可能是这个还原假象；本版有测试守卫）。
- `effective_bits_per_weight(...)`：`b + 16*n_scales/numel`，按矩阵规模加权——per-channel 每行一个 fp16 scale 是真实元数据开销，让"省 1 bit"按**有效比特**公平计费。
- 指标：`ce_and_kl`（held-out 完成位 CE 主 + KL(fp32‖quant) logit 扰动）、`weight_rel_error`（每组件 ‖W−Wq‖/‖W‖）、EM（次）。
- `beats_lower(a,sa,b,sb)=significant(b,sb,a,sa)`（CE 越低越好，反转项目越高越好的 significant，同 v1173）。
- `decide(...)`：纯闸门+判决。

## 三组扫描 + 闸门 + 判决

S1 质量-比特曲线（all，absmax_sym，per_tensor/per_channel_row/group32，b∈{8,6,4,3,2}）；S2 分组件敏感度（embedding/c_attn/c_proj/mlp/attention/all，b∈{4,3}，两粒度）；S3 注意力轴×方案稳健性（c_attn，4 方案×3 粒度）。5 seed，每 seed 训一个 fp32 基线、所有臂量化它（**唯一方差源是训练 seed**，单 seed std 是谎）。闸门：g0 往返正确（dequant 误差 ≤ s/2）、g1 基线可学不饱和（EM∈带）、g2 退化可分辨（per_tensor 2b 显著差于 fp32）、g3 网格完整。判决（CE，经 beats_lower）：`per_channel_holds_3b_per_tensor_collapses`（per-channel 3b 严格胜 per_tensor 4b）| **`per_channel_advantage_not_separable`**（延展名义悬崖但有效比特下平局——本结果）| `attention_most_sensitive_per_row_absmax` / `..._outlier_sensitive_clipping_helps` / `..._axis_artifact`（S2 显著且 S3 稳健/被裁剪修复/翻轴）| `embedding_least_sensitive_per_row` | `component_sensitivity_not_separable`。注意力放大仅当**低权重误差但高 logit-KL**才成立，否则是"输入误差大"的平凡解。

## 设计先于 GPU + 修复一个潜在不可达判决

面板把探针三个讨好结论（省 1 bit、注意力最敏感、embedding 无损）判为单 seed 未验证假象，要求 5 seed/CE/拆 attention/有效比特/绑定按身份。首版 GPU 跑出 `component_sensitivity_not_separable`（真但欠精确，且 `per_channel_advantage_not_separable` 在判决梯里**不可达**——一个 latent bug）；补上"per-channel 是否延展名义悬崖"分支后重跑，得到更精确的 `per_channel_advantage_not_separable`。

## 测试（`tests/test_ptq_v1175.py` 19 项）

往返误差界、per-channel 误差<per-tensor（离群行）、更多比特更低误差、裁剪在离群上不更差、group32 形状保持；**绑定守卫**（量化 embedding 真的改变 lm_head 输出、不被还原；component_names 去重绑定、排除 position_embedding/lm_head）；有效比特 per-channel>per-tensor；自 KL=0；高比特 rel-error≈0；beats_lower 方向；decide 各判决（含新增 per_channel_advantage_not_separable、基线饱和→review）；端到端 smoke。

## 运行证据（RTX 4060，5 seeds，4L/64）

`status=pass`、`verdict=per_channel_advantage_not_separable`、fp32 CE 0.081/EM 0.883。S1 CE：per_tensor 8b 0.081→4b 0.097→**3b 0.540（崩）**→2b 5.04；per_channel 3b 0.168（守）；group32 3b 0.145（守）。悬崖：per_tensor 4b，per-channel/group 3b。但 per_channel 3b（3.19 eff，CE 0.168）相对 per_tensor 4b（4.0 eff，CE 0.097）按有效比特是平局（`per_channel_buys_bit=False`、`per_channel_extends_cliff=True`）。S2 4b per-channel ΔCE 全 ≈0（emb +0.006、c_attn +0.006、c_proj +0.0006、mlp +0.0002，均 < fp32 seed std 0.027）→ `attn_most_sensitive=False`；c_attn rel-err 0.106 ≈ emb 0.108、KL 0.004（无放大）。全量 pytest 绿。

## 一句话总结

量化悬崖真而尖锐（≥6b 无损、3-4b 可用、2b 崩），per-channel/group 延展名义悬崖但按有效比特只是平局，分组件敏感度本尺度不可分离——探针的"省 1 bit/注意力最敏感/embedding 无损"在 5 seed+CE+按身份量化下全部溶解，是本会话第四次多 seed 严格性杀死单 seed 讨好结果。
