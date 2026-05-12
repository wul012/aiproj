# 15 v7 model report 讲解

这一篇讲的是 v7 新增的 `src/minigpt/model_report.py` 和 `scripts/inspect_model.py`。

v7 的目标是回答一个很基础但很重要的问题：

```text
这个 MiniGPT checkpoint 到底由哪些部分组成？
每一部分有多少参数？
一次 forward 时主要张量形状怎样流动？
```

核心流程是：

```text
加载 checkpoint
 -> 读取 GPTConfig
 -> 构建 MiniGPT
 -> load_state_dict
 -> 统计参数分组
 -> 计算每个 Transformer block 的参数
 -> 推导 token/embedding/attention/logits 张量形状
 -> 写 model_report.json
 -> 写 model_architecture.svg
```

`model_report.py` 里最重要的函数是：

```python
build_model_report(model)
```

它会输出一个结构化报告，里面包含：

```text
config：vocab_size、block_size、n_layer、n_head、n_embd 等模型配置
total_parameters：模型总参数量
owned_parameter_groups：embedding、position embedding、blocks、final LayerNorm 的参数分布
transformer_blocks：每个 block 内 attention、MLP、LayerNorm 的参数量
tensor_shapes：一次 forward 里的主要张量形状
tied_weights：lm_head.weight 是否和 token_embedding.weight 共享
```

`lm_head.weight` 和 `token_embedding.weight` 共享是 GPT 里常见的权重绑定技巧。它的意思是：

```text
输入 token embedding 表
和
输出 logits 投影矩阵
使用同一份权重
```

这样既减少参数，也让输入 token 表示和输出词表空间保持一致。

`tensor_shape_summary` 帮你看到 Transformer 内部的形状变化：

```text
token_ids:        [batch, sequence]
embeddings:       [batch, sequence, n_embd]
qkv_split:        [batch, n_head, sequence, head_size]
attention_scores: [batch, n_head, sequence, sequence]
logits:           [batch, sequence, vocab_size]
```

这能把“GPT 是矩阵运算”这件事落到具体维度上。

`inspect_model.py` 是命令行入口：

```powershell
python scripts/inspect_model.py --checkpoint runs/minigpt/checkpoint.pt
```

它会写出：

```text
model_report.json
model_architecture.svg
```

一句话总结：v7 让 MiniGPT 不只会训练和生成，还能解释自己的结构、参数量和关键张量形状。
