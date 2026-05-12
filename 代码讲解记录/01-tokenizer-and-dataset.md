# 01 tokenizer 和 dataset 讲解

这一篇讲的是 `src/minigpt/tokenizer.py` 和 `src/minigpt/dataset.py`。它们负责把普通文本变成模型能训练的数字样本。

核心流程是：

```text
原始中文文本
 -> 收集出现过的字符
 -> 建立 字符 <-> id 映射
 -> encode 得到 token id
 -> 按训练集/验证集切分
 -> 从 token 序列中采样 x 和 y
```

先看 tokenizer 的角色：

```python
@dataclass
class CharTokenizer:
```

它是一个字符级 tokenizer。真实大模型通常使用 BPE、SentencePiece 或类似的子词 tokenizer；这里为了理解原理，先把每一个字符当作一个 token。

训练 tokenizer：

```python
chars = sorted(set(text))
vocab = [unk_token] + [ch for ch in chars if ch != unk_token]
```

`set(text)` 会找出训练语料里出现过的所有字符，`sorted` 让词表顺序稳定。第 0 个位置放 `<unk>`，用于处理生成或输入时遇到的未知字符。

编码：

```python
return [self.stoi.get(ch, unk_id) for ch in text]
```

`stoi` 是 string-to-index，也就是字符到整数 id 的映射。模型不能直接吃中文字符，只能吃整数 id，然后再通过 embedding 查表变成向量。

解码：

```python
pieces.append("�" if token == self.unk_token else token)
```

这一步把生成出来的 token id 还原成文本。未知 token 用替代符号显示，方便看出 prompt 中有训练词表没见过的字符。

再看数据集采样：

```python
x = torch.stack([data[i : i + block_size] for i in starts])
y = torch.stack([data[i + 1 : i + block_size + 1] for i in starts])
```

这里是语言模型训练最关键的地方。`x` 是当前上下文，`y` 是向后错开一位的目标。

比如 token 序列是：

```text
人 工 智 能 正 在
```

如果 `x = 人 工 智 能`，那么 `y = 工 智 能 正`。模型在每个位置都学习“看到当前位置以及之前内容后，下一个 token 应该是什么”。

一句话总结：tokenizer 负责把文本变成数字，dataset 负责把数字切成“前文 x / 下一个 token 目标 y”的训练样本。
