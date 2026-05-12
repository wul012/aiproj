# 11 v5 prediction 和 evaluation 讲解

这一篇讲的是 v5 新增的 `src/minigpt/prediction.py`、`scripts/inspect_predictions.py` 和 `scripts/evaluate.py`。

v5 的目标是把 GPT 的“下一个 token 预测”直接展示出来。前面我们能训练、生成、看 attention；现在可以看到模型在某个 prompt 后面给每个候选 token 的概率。

核心流程是：

```text
加载 checkpoint + tokenizer
 -> encode prompt
 -> MiniGPT.forward
 -> 取最后一个位置 logits
 -> softmax 变成概率
 -> top-k 排序
 -> 写 predictions.json
 -> 写 predictions.svg
```

`prediction.py` 里的核心函数是：

```python
top_k_predictions(logits, tokens, k, temperature)
```

`logits` 是模型输出的原始分数，还不是概率。脚本会先按 `temperature` 缩放，再用 softmax 转成概率。

温度的意义：

```text
temperature 小：概率更集中，输出更保守
temperature 大：概率更平，输出更随机
```

`inspect_predictions.py` 输出两个文件：

```text
predictions.json
predictions.svg
```

JSON 适合程序读取，SVG 适合人看。SVG 中条形越长，说明该 token 被模型认为越可能是下一个 token。

`evaluate.py` 做的是另一个角度的检查：

```text
checkpoint + data
 -> 采样 batch
 -> 计算平均 cross entropy loss
 -> loss 转 perplexity
 -> 写 eval_report.json
```

perplexity 可以粗略理解为“模型平均在多少个候选之间困惑”。它越低，一般说明模型对数据分布越熟悉。

一句话总结：v5 让 MiniGPT 的 next-token prediction 从黑盒输出变成了可检查的概率表和评估报告。
