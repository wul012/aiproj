# MiniGPT 代码讲解记录

本目录用于永久记录对 `MiniGPT From Scratch` 项目的分层代码讲解。

讲解风格参考项目根目录下的 `解释代码格式说明`：

```text
先说明文件或类的角色
再给核心流程
然后逐段解释关键代码
最后做一句话总结
```

## 讲解目录

```text
01-tokenizer-and-dataset.md
 -> tokenizer.py / dataset.py：文本如何变成训练样本

02-model-core.md
 -> model.py：GPTConfig、CausalSelfAttention、Block、MiniGPT 和自回归生成

03-train-generate.md
 -> scripts/train.py / scripts/generate.py：训练循环、checkpoint 保存和文本生成入口

04-tests-docs.md
 -> tests、README、a/1 归档：如何证明项目能跑、能讲清楚、能继续迭代

05-v2-training-artifacts.md
 -> history.py、plot_history.py、train.py v2：训练历史、loss 曲线、样例输出和 resume

06-version-2-tests-docs.md
 -> v2 测试、README、a/2 归档和版本说明更新

07-v3-bpe-tokenizer.md
 -> BPETokenizer、load_tokenizer、inspect_tokenizer.py：从字符级走向子词合并

08-version-3-tests-docs.md
 -> v3 BPE smoke、README、a/3 归档和 tag 说明

09-v4-attention-inspection.md
 -> model.py attention capture、inspect_attention.py：导出 causal attention JSON/SVG

10-version-4-tests-docs.md
 -> v4 attention smoke、README、a/4 归档和 tag 说明
```

## 项目整体理解

`MiniGPT From Scratch` 是一个 PyTorch 编写的字符级 GPT 学习项目。

它的核心链路是：

```text
中文文本
 -> CharTokenizer 或 BPETokenizer encode
 -> token id 序列
 -> get_batch 采样 x/y
 -> MiniGPT.forward
 -> attention capture 可选记录每层注意力矩阵
 -> logits
 -> cross entropy loss
 -> AdamW 更新参数
 -> metrics.jsonl / loss_curve.svg / sample.txt
 -> generate 自回归采样新 token
 -> tokenizer.decode
 -> 生成文本
```

一句话理解：这个项目用最小的工程结构复现 GPT 的核心训练目标，也就是“根据前文预测下一个 token”。
