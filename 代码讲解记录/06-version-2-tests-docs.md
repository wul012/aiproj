# 06 v2 测试和文档归档讲解

这一篇讲的是 v2 如何验证训练产物功能，并把验证过程归档到 `a/2`。

核心流程是：

```text
新增 history 单元测试
 -> 跑全量 unittest
 -> 跑真实训练 smoke
 -> 用 --resume 跑恢复训练 smoke
 -> 用 plot_history.py 重建 loss_curve.svg
 -> 用 generate.py --out 写生成文本文件
 -> 截图归档到 a/2/图片
 -> 在 a/2/解释/说明.md 写清命令、结果和意义
```

新增测试文件：

```text
tests/test_history.py
```

它覆盖两件事：第一，`metrics.jsonl` 能写、能读、能汇总；第二，loss 曲线 SVG 能生成并包含预期标题。

训练 smoke：

```powershell
python -B scripts/train.py --device cpu --out-dir tmp/v2-smoke --max-iters 2 ...
```

这个命令不会追求生成质量，只证明训练链路能写出 v2 产物：

```text
checkpoint.pt
tokenizer.json
metrics.jsonl
history_summary.json
loss_curve.svg
sample.txt
```

恢复训练 smoke：

```powershell
python -B scripts/train.py --device cpu --out-dir tmp/v2-smoke --resume tmp/v2-smoke/checkpoint.pt --max-iters 4 ...
```

这个命令证明 checkpoint 里的模型和 optimizer 可以恢复，并从已有 step 继续推进。

独立产物脚本：

```powershell
python -B scripts/plot_history.py --history tmp/v2-smoke/metrics.jsonl
python -B scripts/generate.py --checkpoint tmp/v2-smoke/checkpoint.pt --out tmp/v2-smoke/generated.txt
```

这说明产物不是只能由训练脚本内部使用，外部脚本也能读取和复用。

一句话总结：v2 的验收重点不是生成文本有多聪明，而是训练过程开始有可追踪、可恢复、可展示的工程闭环。
