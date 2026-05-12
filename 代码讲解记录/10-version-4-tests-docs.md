# 10 v4 测试和文档归档讲解

这一篇讲的是 v4 如何验证 attention inspection，并把结果归档到 `a/4`。

核心流程是：

```text
新增 attention 单元测试
 -> 训练一个小 checkpoint
 -> 用 inspect_attention.py 导出 JSON/SVG
 -> 检查导出文件
 -> 截图归档到 a/4/图片
 -> 在 a/4/解释/说明.md 写清命令和意义
```

新增测试文件：

```text
tests/test_attention.py
```

它覆盖三个点：

```text
开启 capture 后每层能返回 attention map
attention map 形状符合 [batch, head, seq, seq]
未来位置权重为 0，证明 causal mask 生效
关闭 capture 后缓存会清空
```

attention smoke：

```powershell
python -B scripts/inspect_attention.py --checkpoint tmp/v4-attention-smoke/checkpoint.pt --prompt 人工智能模型 --layer 0 --head 0
```

这个命令会导出：

```text
attention.json
attention.svg
```

一句话总结：v4 的验收重点是证明注意力不是只在模型内部运行，而是能被稳定导出、检查和解释。
