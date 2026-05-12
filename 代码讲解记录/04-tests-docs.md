# 04 tests 和文档归档讲解

这一篇讲的是项目的测试、README 和 `a/1` 归档。它们对应 `mini-kv` 里的测试验证和阶段记录习惯。

核心流程是：

```text
写最小单元测试
 -> 运行真实命令
 -> 保存关键输出截图
 -> 在 a/1/解释/说明.md 记录每张图对应的命令和意义
 -> README 链接到这些验收材料
```

测试目录：

```text
tests/test_tokenizer.py
tests/test_dataset.py
tests/test_model.py
```

这些测试覆盖三个基础层次：

```text
tokenizer 能否 encode/decode
dataset 能否构造错位一格的 x/y
model 能否 forward、计算 loss、generate
```

为什么测试不是越多越好？

这个项目的第一阶段目标是“理解 GPT 核心闭环”，所以测试也围绕闭环最小集合展开。后续如果加入 BPE、LoRA、Web UI 或训练恢复，就应该继续扩展对应测试。

`a/1` 归档：

```text
a/1/图片
a/1/解释/说明.md
```

`图片` 保存关键命令输出截图，`解释` 说明每张截图对应的命令、结果和意义。这样以后回头看项目时，不需要猜“当时到底有没有跑过”。

一句话总结：测试证明代码行为，截图证明真实运行，讲解记录证明你理解了每一层为什么这样写。
