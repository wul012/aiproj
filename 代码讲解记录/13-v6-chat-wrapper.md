# 13 v6 chat wrapper 讲解

这一篇讲的是 v6 新增的 `src/minigpt/chat.py` 和 `scripts/chat.py`。

v6 的目标不是把 MiniGPT 变成真正强大的助手，而是拆开 GPT 产品外层最常见的一层工程包装：

```text
多轮消息
 -> chat prompt 模板
 -> tokenizer.encode
 -> MiniGPT.generate
 -> tokenizer.decode
 -> 截断停止标记
 -> assistant reply
 -> transcript.json
```

`chat.py` 里的核心数据结构是：

```python
ChatTurn(role, content)
PreparedChatPrompt(text, decoded_context, token_ids, original_token_count, trimmed)
```

`ChatTurn` 只允许三类角色：

```text
system
user
assistant
```

这对应真实聊天模型里常见的系统指令、用户消息和助手回复。

`build_chat_prompt` 会把结构化消息拼成模型能接收的普通文本：

```text
系统：你是一个简洁的中文学习助手。

用户：解释 token 是什么

助手：
```

注意：MiniGPT 仍然只是“根据前文预测下一个 token”的基础语言模型。所谓 chat 能力，本质上是把对话历史整理成上下文，让同一个自回归生成接口继续往后写。

`prepare_chat_prompt` 做两件事：

```text
把 prompt 编码成 token ids
如果超过 block_size，只保留最后 block_size 个 token
```

这对应 Transformer 的上下文窗口限制：模型一次只能看到有限长度的历史。

`assistant_reply_from_generation` 做生成后的清洗：

```text
去掉 prompt 本身
遇到“用户：/系统：/助手：”这类新角色标记时停止
```

这不是训练得到的能力，而是推理阶段的工程规则。它能帮助我们理解：真实 GPT 产品不只是模型权重，还包括 prompt 模板、采样参数、停止条件、历史管理和输出解析。

一句话总结：v6 把 MiniGPT 从“文本续写脚本”推进到“简易对话包装”，让你能看到 GPT 类应用最薄的一层产品形态是怎么搭起来的。
