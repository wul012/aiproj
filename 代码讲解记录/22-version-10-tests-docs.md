# 22 v10 测试和文档归档讲解

这一篇讲的是 v10 如何验证 sampling lab，并把结果归档到 `a/10`。

核心流程是：

```text
新增 sampling 单元测试
 -> 训练一个小 checkpoint
 -> sample_lab.py 运行多组采样
 -> 检查 sample_lab.json/csv/svg
 -> 截图归档到 a/10/图片
 -> 同步 README 和代码讲解记录
```

新增测试文件：

```text
tests/test_sampling.py
```

它覆盖：

```text
sampling case 解析
top_k=0 转成 None
temperature 参数校验
continuation 截取和字符统计
空结果不能生成 report
默认采样配置
CSV/SVG 输出
JSON/CSV/SVG 一次性输出
```

sampling smoke：

```powershell
python -B scripts/sample_lab.py --device cpu --checkpoint tmp/v10-sampling-smoke/checkpoint.pt --prompt token --max-new-tokens 18 --out-dir tmp/v10-sampling-smoke/sample_lab
```

这个命令证明：

```text
脚本能加载 checkpoint
能按多组 temperature/top_k/seed 生成文本
能导出 sample_lab.json、sample_lab.csv、sample_lab.svg
```

v10 的验收重点是采样行为：

```text
同一个模型是否能在不同采样参数下产生不同 continuation
采样配置是否可复现
采样结果是否能保存为机器可读和人可读格式
```

一句话总结：v10 的归档证明 MiniGPT 不只会生成文本，还能系统观察采样参数如何影响生成结果。
