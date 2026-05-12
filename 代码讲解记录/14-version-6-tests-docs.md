# 14 v6 测试和文档归档讲解

这一篇讲的是 v6 如何验证 chat wrapper，并把结果归档到 `a/6`。

核心流程是：

```text
新增 chat 单元测试
 -> 训练一个小 checkpoint
 -> scripts/chat.py 运行 one-shot chat smoke
 -> 写出 transcript.json
 -> 截图归档到 a/6/图片
 -> 在 README 和代码讲解记录里同步 v6
```

新增测试文件：

```text
tests/test_chat.py
```

它覆盖：

```text
ChatTurn role 校验
chat prompt 是否包含 system/user/assistant 标签
生成文本是否能去掉上下文
遇到下一轮角色标记是否停止
prompt 超过 block_size 时是否截断
turns 是否能稳定转成 JSON 字典
```

chat smoke：

```powershell
python -B scripts/chat.py --device cpu --checkpoint tmp/v6-chat-smoke/checkpoint.pt --message "解释 token 是什么" --max-new-tokens 30 --out tmp/v6-chat-smoke/transcript.json
```

这个命令证明：

```text
checkpoint 可以通过 chat prompt 入口生成 assistant 回复
脚本能输出上下文 token 数量和是否截断
对话过程可以保存成 transcript.json
```

v6 的重点是工程边界：

```text
model.py 仍然只负责 next-token prediction
chat.py 负责把多轮消息变成 prompt
scripts/chat.py 负责加载 checkpoint、采样和保存 transcript
```

一句话总结：v6 的验收重点是证明 MiniGPT 已经具备一个最小聊天应用入口，同时没有把聊天产品逻辑混进模型核心代码。
