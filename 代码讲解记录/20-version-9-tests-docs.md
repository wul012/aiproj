# 20 v9 测试和文档归档讲解

这一篇讲的是 v9 如何验证 run comparison，并把结果归档到 `a/9`。

核心流程是：

```text
新增 comparison 单元测试
 -> 训练两个小 run
 -> 分别导出 model_report / eval_report / dashboard
 -> compare_runs.py 横向比较
 -> 检查 comparison.json/csv/svg
 -> 截图归档到 a/9/图片
 -> 同步 README 和代码讲解记录
```

新增测试文件：

```text
tests/test_comparison.py
```

它覆盖：

```text
summarize_run 是否能读取 run 指标
build_comparison_report 是否能选出 best run
--name 数量不匹配时是否报错
comparison.csv 是否能写出
comparison.svg 是否能写出
write_comparison_outputs 是否能一次性写出 JSON/CSV/SVG
```

comparison smoke：

```powershell
python -B scripts/compare_runs.py tmp/v9-comparison-smoke/tiny tmp/v9-comparison-smoke/wide --name tiny --name wide --out-dir tmp/v9-comparison-smoke/comparison
```

这个命令证明：

```text
脚本能读取多个真实 run 目录
能汇总 loss/perplexity/参数量
能写出 comparison.json、comparison.csv、comparison.svg
```

v9 的验收重点是实验管理：

```text
多个 run 是否能统一比较
最好的一组指标来自哪个 run
参数量和 loss 是否能放在一张图里看
比较结果是否能保存成机器可读和人可读格式
```

一句话总结：v9 的归档证明 MiniGPT 已经能从单次实验走向多实验对比。
