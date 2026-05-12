# 18 v8 测试和文档归档讲解

这一篇讲的是 v8 如何验证 dashboard，并把结果归档到 `a/8`。

核心流程是：

```text
新增 dashboard 单元测试
 -> 训练一个小 checkpoint
 -> 导出 model report / predictions / eval report / chat transcript
 -> build_dashboard.py 生成 dashboard.html
 -> 检查 HTML 是否包含关键区块
 -> 截图归档到 a/8/图片
 -> 同步 README 和代码讲解记录
```

新增测试文件：

```text
tests/test_dashboard.py
```

它覆盖：

```text
artifact 是否能识别存在/缺失
summary 是否能从 JSON 产物中读取
HTML 是否会转义不可信文本
dashboard.html 是否可以写出
非法 JSON 是否会进入 warnings
```

dashboard smoke：

```powershell
python -B scripts/build_dashboard.py --run-dir tmp/v8-dashboard-smoke
```

这个命令证明：

```text
脚本能扫描一个 run 目录
能汇总训练、评估、预测、模型结构和聊天产物
能写出可直接打开的 dashboard.html
```

v8 的验收重点是可复盘：

```text
训练是否成功
loss 是否下降
模型结构是什么
下一 token 概率是什么
一次 chat 的输入输出是什么
所有关键产物在哪里
```

一句话总结：v8 的归档证明 MiniGPT 已经有了一个静态实验报告层，方便把模型学习过程展示给别人看。
