# 12 v5 测试和文档归档讲解

这一篇讲的是 v5 如何验证 prediction/evaluation，并把结果归档到 `a/5`。

核心流程是：

```text
新增 prediction 单元测试
 -> 训练一个小 checkpoint
 -> inspect_predictions.py 导出 predictions.json/svg
 -> evaluate.py 导出 eval_report.json
 -> 截图归档到 a/5/图片
 -> 在 a/5/解释/说明.md 写清命令和意义
```

新增测试文件：

```text
tests/test_prediction.py
```

它覆盖：

```text
top-k 结果按概率排序
temperature 参数校验
loss 到 perplexity 的转换
predictions.svg 可以写出
```

prediction smoke：

```powershell
python -B scripts/inspect_predictions.py --checkpoint tmp/v5-prediction-smoke/checkpoint.pt --prompt 人工智能 --top-k 6
```

这个命令证明 logits 可以被转成可读概率表，并生成 JSON/SVG。

evaluation smoke：

```powershell
python -B scripts/evaluate.py --checkpoint tmp/v5-prediction-smoke/checkpoint.pt --eval-iters 2
```

这个命令证明 checkpoint 可以被独立评估，并输出 loss/perplexity。

一句话总结：v5 的验收重点是证明模型输出的概率分布和整体评估指标都可以被稳定导出。
