# 07 v3 BPE tokenizer 讲解

这一篇讲的是 v3 新增的 `BPETokenizer`、`load_tokenizer` 和 `scripts/inspect_tokenizer.py`。

v3 的目标是让项目从“每个字符都是 token”迈向“常见片段可以合并成 token”。这更接近真实 GPT 使用的子词 tokenizer 思路，但实现仍然保持教学版、无第三方依赖。

核心流程是：

```text
训练文本
 -> 先拆成字符
 -> 统计相邻 token pair
 -> 找出现次数最多的 pair
 -> 合并成一个新 token
 -> 重复直到达到 vocab_size 或低于 min_frequency
 -> 保存 itos + merges
```

先看 BPE 类：

```python
@dataclass
class BPETokenizer:
```

它和 `CharTokenizer` 一样提供 `encode`、`decode`、`save`、`load` 和 `vocab_size`。这样训练脚本不需要知道底层到底是字符级还是 BPE，只要调用同一套接口。

训练入口：

```python
BPETokenizer.train(text, vocab_size=256, min_frequency=2)
```

`vocab_size` 控制最终词表上限，`min_frequency` 控制只有出现次数足够高的 pair 才会被合并。这样可以避免把只出现一次的偶然片段塞进词表。

统计 pair：

```python
pair_counts.update(zip(sequence, sequence[1:]))
```

这行会把相邻 token 组成 pair。比如：

```text
人 工 智 能 人 工 智 能
```

会统计 `(人, 工)`、`(工, 智)`、`(智, 能)`、`(能, 人)` 等 pair。出现频率高的 pair 会优先被合并。

合并 pair：

```python
tokens = _merge_pair(tokens, (left, right), left + right)
```

如果训练时学到了 `(人, 工) -> 人工`，编码时也会按相同顺序应用这个规则。BPE 的关键不是只知道词表，而是必须保存 merge 顺序。

自动加载：

```python
def load_tokenizer(path):
```

v3 不再让生成脚本固定调用 `CharTokenizer.load`。`load_tokenizer` 会读取 `tokenizer.json` 里的 `type` 或 `merges` 字段，自动选择 `CharTokenizer` 或 `BPETokenizer`。这保证 v1/v2 的旧字符级 tokenizer 仍然能加载。

检查工具：

```powershell
python scripts/inspect_tokenizer.py --tokenizer bpe --text "人工智能"
```

这个脚本会输出 tokenizer 类型、词表大小、输入文本对应的 token ids、decode 结果，以及前几条 BPE merge 规则。它适合用来理解“为什么 BPE 后 token 数变少了”。

一句话总结：v3 的 BPE tokenizer 让 MiniGPT 开始接近真实 GPT 的文本处理方式，同时保留字符级 tokenizer 的简单学习路径。
