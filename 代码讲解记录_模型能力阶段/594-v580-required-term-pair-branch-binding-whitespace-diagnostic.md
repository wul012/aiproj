# v580 required-term pair branch-binding whitespace diagnostic

## 本版目标和边界

v580 诊断 v579 的负结果。v579 新增了 branch-binding corpus，但 seed `3535` 仍然没有 pair-full。v580 的问题是：失败来自 fixed/loss 分支竞争，还是更早的 token 边界漂移。

本版不改代码、不训练、不改变模型能力结论。它只复用已有 missed-seed diagnostic 读取 v579 产物。

## 输入输出

输入：

```text
e/579/解释/model-capability-required-term-pair-branch-binding-seed-3535/
```

输出：

```text
e/580/解释/model-capability-required-term-pair-branch-binding-seed-3535-diagnostic/
```

## 核心字段

诊断 CSV 中最重要的字段是：

```text
fixed_expected_rank=3
loss_expected_rank=2
fixed_top_token=<space>
loss_top_token=<space>
observed_continuation_hit_count=0
```

`fixed_top_token` 和 `loss_top_token` 都是空格，说明模型在 `fixed=`、`loss=` 之后首先倾向输出 whitespace，而不是 `f` 或 `l`。

## 证据解释

v579 的语料写了：

```text
branch fixed prompt fixed= answer fixed
branch loss prompt loss= answer loss
```

这类自然语言 binding 可能让模型学习到 `fixed=` 后接空格再接解释文本，而不是直接接目标 term。v580 因此把下一步方向从“继续加 binding 句”改成“控制 equals 后的 whitespace 边界”。

## 测试与验证

本版验证方式：

- `--require-pass` 保证诊断报告结构通过。
- Playwright MCP 截图证明 HTML 报告可见。
- 后续 v581 应以此为输入，做 whitespace-bound branch-binding corpus，而不是盲目 seed sweep。

## 链路角色

v580 是 branch-binding 路线的第一道分诊。它避免我们误以为 v579 只是 loss branch 不够强，实际问题更靠前：equals 后第一 token 先被 whitespace 吃掉。

## 一句话总结

v580 将 v579 的 branch-binding 失败定位为 whitespace first-token gap，为 v581 的 whitespace-bound objective 提供了直接证据。
