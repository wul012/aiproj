# 16 v7 测试和文档归档讲解

这一篇讲的是 v7 如何验证 model report，并把结果归档到 `a/7`。

核心流程是：

```text
新增 model_report 单元测试
 -> 训练一个小 checkpoint
 -> scripts/inspect_model.py 导出 JSON/SVG
 -> 检查 model_report.json 关键字段
 -> 截图归档到 a/7/图片
 -> 同步 README 和代码讲解记录
```

新增测试文件：

```text
tests/test_model_report.py
```

它覆盖：

```text
参数分组之和等于模型总参数量
lm_head 是否和 token_embedding 共享权重
forward 关键张量形状是否正确
sequence_length 超过 block_size 时是否报错
report 是否包含 parameter_check
model_architecture.svg 是否可以写出
```

model report smoke：

```powershell
python -B scripts/inspect_model.py --device cpu --checkpoint tmp/v7-model-report-smoke/checkpoint.pt --sequence-length 16 --out-dir tmp/v7-model-report-smoke/model_report
```

这个命令证明：

```text
checkpoint 可以被加载成 MiniGPT
脚本能导出模型配置、参数分布、每层参数、张量形状
脚本能生成可读的 SVG 架构图
```

v7 的验收重点不是模型效果，而是解释性：

```text
这个模型有多少参数
参数主要花在哪些模块
attention 的 q/k/v 形状是什么
输出 logits 的形状为什么包含 vocab_size
```

一句话总结：v7 的归档证明 MiniGPT 已经具备结构自检能力，适合继续讲解 GPT 的参数规模和计算路径。
