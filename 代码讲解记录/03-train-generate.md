# 03 train.py 和 generate.py 讲解

这一篇讲的是 `scripts/train.py` 和 `scripts/generate.py`。它们分别是训练入口和生成入口。

训练核心流程是：

```text
读取语料
 -> 训练 CharTokenizer
 -> encode 得到 token ids
 -> 切分 train/val
 -> 创建 MiniGPT
 -> 反复 get_batch
 -> forward 计算 loss
 -> backward 反向传播
 -> AdamW 更新参数
 -> 保存 checkpoint/tokenizer/config
```

选择设备：

```python
return torch.device("cuda" if torch.cuda.is_available() else "cpu")
```

如果有 CUDA，就用 GPU；否则回落 CPU。这个项目模型很小，CPU 也能跑通学习闭环。

创建 tokenizer：

```python
tokenizer = CharTokenizer.train(text)
token_ids = tokenizer.encode(text)
```

这里的 tokenizer 是从训练文本现学出来的，所以它只认识训练语料里出现过的字符。后续生成时必须加载同一个 tokenizer，否则 token id 和字符的对应关系会变。

创建模型：

```python
config = GPTConfig(...)
model = MiniGPT(config).to(device)
```

checkpoint 里保存的 `config` 很重要。加载模型时必须用同样的层数、头数、embedding 维度和词表大小重建模型结构。

训练三步：

```python
loss.backward()
optimizer.step()
optimizer.zero_grad(set_to_none=True)
```

反向传播根据 loss 计算梯度，优化器根据梯度更新参数，然后清空梯度准备下一轮。代码里实际顺序是先清空上一轮梯度，再 backward 和 step。

评估 loss：

```python
model.eval()
...
model.train()
```

评估时切到 `eval`，让 dropout 等训练行为关闭；评估结束再切回 `train`。这个习惯对以后扩展更大的模型很重要。

保存 checkpoint：

```python
torch.save(checkpoint, args.out_dir / "checkpoint.pt")
tokenizer.save(args.out_dir / "tokenizer.json")
```

`checkpoint.pt` 保存模型参数和配置，`tokenizer.json` 保存字符表。两者要配套使用。

生成入口：

```python
checkpoint = torch.load(args.checkpoint, map_location=device, weights_only=False)
tokenizer = CharTokenizer.load(tokenizer_path)
model.load_state_dict(checkpoint["model"])
```

生成脚本先重建同结构模型，再装载训练好的参数，最后把 prompt 编码成 token id 并调用 `model.generate`。

一句话总结：`train.py` 负责让模型从文本里学习下一个 token 分布，`generate.py` 负责把学到的分布用于自回归续写。
