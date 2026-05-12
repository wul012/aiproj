# 09 v4 attention inspection 讲解

这一篇讲的是 v4 新增的 attention 捕获能力和 `scripts/inspect_attention.py`。

v4 的目标是把 GPT 里最核心的 self-attention 变成可观察产物。训练脚本告诉你 loss，生成脚本告诉你输出，而 attention 检查器告诉你：某个 token 在某一层、某个 head 里到底关注了哪些历史 token。

核心流程是：

```text
加载 checkpoint + tokenizer
 -> encode prompt
 -> model.set_attention_capture(True)
 -> 前向推理一次
 -> 读取每层 attention map
 -> 选择 layer/head
 -> 写出 attention.json
 -> 写出 attention.svg 热力图
```

模型侧新增：

```python
self.capture_attention = False
self.last_attention = None
```

默认不捕获 attention，避免训练时额外保存矩阵。只有脚本显式调用：

```python
model.set_attention_capture(True)
```

时，注意力层才会把 softmax 后、dropout 前的 attention 矩阵保存下来。

为什么保存 dropout 前？

```text
softmax 后的矩阵代表模型原始注意力分布
dropout 后的矩阵是训练正则化产物
```

我们做解释和可视化时，更关心原始注意力分布。

注意力矩阵形状：

```text
[batch, n_head, seq_len, seq_len]
```

其中行表示“当前 token”，列表示“它关注的 token”。由于 GPT 使用 causal mask，矩阵右上角的未来 token 权重应为 0。

脚本输出：

```text
attention.json
attention.svg
```

`attention.json` 适合程序读取，包含 token id、token 文本、矩阵和最后一个 token 的 top attention links。`attention.svg` 适合人看，是一个热力图。

一句话总结：v4 让 MiniGPT 的 self-attention 从代码里的矩阵乘法变成了可检查、可归档、可解释的学习材料。
