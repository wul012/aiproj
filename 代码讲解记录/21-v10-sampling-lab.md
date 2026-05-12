# 21 v10 sampling lab 讲解

这一篇讲的是 v10 新增的 `src/minigpt/sampling.py` 和 `scripts/sample_lab.py`。

v10 的目标是观察同一个 checkpoint 在不同采样参数下会生成什么：

```text
同一个 prompt
同一个 checkpoint
 -> conservative: temperature=0.6, top_k=10
 -> balanced:     temperature=0.8, top_k=30
 -> creative:     temperature=1.1, top_k=None
 -> 生成多组 continuation
 -> 写 sample_lab.json
 -> 写 sample_lab.csv
 -> 写 sample_lab.svg
```

`SamplingCase` 描述一次采样配置：

```text
name
temperature
top_k
seed
```

`temperature` 控制概率分布的尖锐程度：

```text
temperature 较低：更偏向高概率 token，输出更保守
temperature 较高：低概率 token 更容易被选中，输出更发散
```

`top_k` 控制候选 token 范围：

```text
top_k=10：只从概率最高的 10 个 token 里采样
top_k=None：不限制候选范围
```

`seed` 用来让 smoke 和演示更容易复现。注意，真实大模型产品里也常常会暴露类似 seed 或 temperature 的控制项。

`sample_lab.py` 的命令格式是：

```powershell
python scripts/sample_lab.py --checkpoint runs/minigpt/checkpoint.pt --prompt token --max-new-tokens 60
```

也可以自定义 case：

```powershell
python scripts/sample_lab.py --case low:0.5:10:1 --case high:1.2:0:2
```

这里 `top_k=0` 表示不做 top-k 限制。

一句话总结：v10 用同一模型、同一 prompt 的多组采样结果，帮助理解 GPT 输出并不是固定答案，而是概率分布加采样策略共同决定的。
