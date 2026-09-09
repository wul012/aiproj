# 第一讲：aiproj 的模型主线

## 先记住项目定位

`aiproj` 是一个独立的 MiniGPT 研究实验室。它不是 Java 订单平台的 AI 子模块，也不是
一个调用外部大模型 API 的聊天网站。项目主要包含三层：第一层是模型层，包括 tokenizer、
Embedding、Transformer、训练和生成；第二层是实验层，用小模型研究 grokking、Fourier
circuits、superposition 等现象；第三层是工程层，用配置、checkpoint、实验记录和检查门
保证结果能被复查。模型结果默认只适用于 toy scale、own substrate，不能直接外推成通用
LLM 能力或生产模型质量。

## 面试问：输入一段文字后，模型怎样得到预测？

参考回答：文字先经过 tokenizer 变成 token ID。训练脚本从连续 ID 中截取长度为
`block_size` 的输入，并把目标整体向后移动一位。ID 查 Embedding 表得到向量，加入位置
信息后进入多个 Transformer Block。每个 Block 通过因果自注意力和 MLP 更新表示，最后
用 LayerNorm 和线性输出层得到每个位置对整个词表的 logits。训练用交叉熵比较 logits
和目标，反向传播计算梯度，再由 AdamW 更新参数。

源码入口是 `D:\aiproj\scripts\train.py`、`D:\aiproj\src\minigpt\core\dataset.py`、
`D:\aiproj\src\minigpt\core\model.py` 和 `D:\aiproj\src\minigpt\core\layers.py`。

## 为什么输入和目标必须错一位？

假设文本被分成“我、爱、学、习、。”，训练样本是：

```text
x = 我 爱 学 习
y = 爱 学 习 。
```

每个位置分别学习“下一个 token”。如果 x 和 y 完全相同，模型只需复制当前位置，损失
可以下降，却没有真正学习续写。`get_batch` 的两次切片正是这个错位关系：

```python
x = data[i : i + block_size]
y = data[i + 1 : i + block_size + 1]
```

这属于自监督学习，因为标签来自原始文本本身，不需要人工逐条标注；但它仍然有明确的
目标和损失，不能说成“模型自己随便学习”。

## 为什么训练可以并行，生成必须逐步进行？

训练时整段真实文本已经存在。因果 mask 会限制每个位置只能读取自己和前文，但所有位置
仍可以组成矩阵运算，一次完成同一层的计算。生成时，下一个 token 尚未确定，必须先得到
第一个新 token，把它追加进上下文，才能预测第二个新 token。因此“并行计算”与“不能看
未来”并不矛盾：前者是计算组织方式，后者是信息访问规则。不同 Transformer 层仍然按
顺序依赖前一层输出。

## Embedding 到底是什么？

token ID 是整数索引，不是语义分数。编号 37 并不意味着它和编号 38 更相似。Embedding
是一张可训练的表，每一行对应一个 token，每一行是 `n_embd` 维浮点向量。训练过程中，
这些向量会和其它模型参数一样被更新。输入 ID 的形状是 `[B, T]`，经过 Embedding 后是
`[B, T, C]`：`B` 是批大小，`T` 是序列长度，`C` 是隐藏维度。

项目中的 `MiniGPT` 创建了 `token_embedding` 和 `position_embedding`。默认位置表示是
按序号查表后与 token 表示相加；开启 RoPE 时，位置信息改为在注意力的 Q、K 上旋转，不能
把两套位置机制混为一谈。模型最后输出 `[B, T, V]` 的 logits，`V` 是词表大小；每个
位置都有一组对整个词表的分数。

## 训练循环的四个动作

训练核心可以压缩为：

```python
_, loss = model(x, y)
optimizer.zero_grad(set_to_none=True)
loss.backward()
optimizer.step()
```

第一行计算预测和误差；第二行清理上一步留下的梯度，不会清空模型参数；第三行沿计算图
反向计算每个参数的梯度；第四行由 AdamW 按梯度更新参数。交叉熵内部会完成稳定的
log-softmax 相关计算，调用者不必先把 logits 手动转成概率。

正常且足够长的数据会切分为训练集和验证集。训练损失用于观察优化是否进行，验证损失用于观察模型
在未参与参数更新的文本上的表现。验证损失不是模型通用能力证明，尤其在字符级小数据
上，低损失可能只反映记忆或数据分布简单。当前 `split_token_ids` 在验证集不足两个 token
时会回退到训练集；这种极小输入不能当独立验证证据，实际使用还必须满足 `get_batch` 的长度要求。

## 生成和 checkpoint

生成阶段不更新参数，而是从已有上下文得到最后位置 logits，再按照 temperature、top-k
和可选禁止 token 规则选出一个 token，拼接后继续预测。普通 `generate` 会反复重算上下文；
项目还提供 KV Cache 路径，后面单独讲它为什么能减少重复计算。

训练脚本的 checkpoint 不只是模型权重，还保存 optimizer、模型配置、训练步数、tokenizer
类型、数据来源和实验记录路径。恢复时必须先找到同目录的 tokenizer，再核对词表大小和
checkpoint 配置，避免用不匹配的词表解释权重。下一版工程优化会继续补充随机状态，使中途
恢复不仅“能继续跑”，还可以和不间断训练对齐。

## 面试压缩答案

> 这是一个独立的 PyTorch MiniGPT 实验室。它把文本变成 token ID，用错位的输入和目标
> 做下一 token 预测；ID 经过 Embedding、位置处理和 Transformer 得到词表 logits，因果
> mask 防止读取未来。训练阶段交叉熵提供误差，反向传播和 AdamW 更新参数；生成阶段只
> 使用已训练参数逐步采样。项目同时保存 checkpoint 和实验记录，但模型效果仍按 toy-scale
> 范围解释。

## 自测问题

1. 如果把 `y` 改成和 `x` 完全相同，模型可能学成什么？
2. 为什么训练和验证损失都下降，仍然不能直接证明模型泛化到真实任务？
