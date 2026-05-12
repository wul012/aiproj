# 02 model.py 讲解

这一篇讲的是 `src/minigpt/model.py`。它是项目的核心，负责定义一个最小 GPT。

核心流程是：

```text
token id
 -> token embedding + position embedding
 -> 多层 Transformer Block
 -> LayerNorm
 -> lm_head 输出每个位置的下一个 token 概率
 -> 训练时计算 cross entropy loss
 -> 生成时循环采样新 token
```

先看配置类：

```python
@dataclass
class GPTConfig:
```

这里集中保存模型结构参数。`vocab_size` 决定输出类别数量，`block_size` 决定上下文窗口长度，`n_layer` 是 Transformer block 层数，`n_head` 是多头注意力头数，`n_embd` 是隐藏向量维度。

注意力层：

```python
q, k, v = self.c_attn(x).split(embd_size, dim=2)
```

GPT 的 self-attention 会把同一份输入投影成 Q、K、V 三组向量。Q 表示当前位置想找什么，K 表示每个位置能提供什么，V 是最终被加权汇总的信息。

因果 mask：

```python
mask = torch.tril(torch.ones(config.block_size, config.block_size))
```

`torch.tril` 生成下三角矩阵。它保证第 t 个位置只能看见自己和前面的 token，不能偷看未来答案。这就是 GPT 做自回归生成的关键约束。

注意力权重：

```python
att = (q @ k.transpose(-2, -1)) * (self.head_size**-0.5)
att = att.masked_fill(self.causal_mask[:, :, :seq_len, :seq_len] == 0, float("-inf"))
att = F.softmax(att, dim=-1)
```

第一行计算 token 之间的相关性，第二行屏蔽未来位置，第三行把相关性变成概率分布。概率越大，说明当前位置越关注那个历史位置。

Transformer block：

```python
x = x + self.attn(self.ln_1(x))
x = x + self.mlp(self.ln_2(x))
```

每个 block 包含注意力和前馈网络。残差连接 `x + ...` 让深层网络更容易训练；LayerNorm 让激活分布更稳定。

输出层：

```python
logits = self.lm_head(x)
```

`logits` 的形状是 `[batch, seq_len, vocab_size]`。它不是最终文字，而是每个位置对词表里每个 token 的打分。

训练损失：

```python
loss = F.cross_entropy(logits.reshape(-1, logits.size(-1)), targets.reshape(-1))
```

交叉熵会比较模型预测的 logits 和真实目标 token。预测越接近真实下一个 token，loss 越小。

生成函数：

```python
idx_cond = idx[:, -self.config.block_size :]
logits, _ = self(idx_cond)
logits = logits[:, -1, :] / temperature
```

生成时只关心最后一个位置的 logits，因为它代表“下一个 token”的分布。`temperature` 越高，采样越随机；越低，输出越保守。

一句话总结：`model.py` 用因果 self-attention 搭出一个迷你 GPT，让模型只能根据历史 token 预测下一个 token。
