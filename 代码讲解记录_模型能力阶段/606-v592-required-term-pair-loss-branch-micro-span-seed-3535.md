# v592 required-term pair loss-branch micro-span seed 3535

## 本版目标和边界

v592 是第三条真实 loss-branch objective 训练。它使用 `equals_surface_no_pair_id_loss_branch_micro_span_repair`，目标是检验短前缀提示是否能改善 `loss` 分支第一 token，并且不让 `fixed` 掉线。

本版不改变模型结构，也不扩大 seed 范围；它只针对 v590-v591 的 tradeoff 做一个 first-token 方向的训练样本验证。

## 输入结构

micro-span corpus 的核心行：

```text
loss=l
loss=lo
loss=los
loss=loss
fixed=f
fixed=fi
fixed=fix
fixed=fixed
```

其中 `loss` span 密度更高，用来观察模型是否能稳定走到 loss continuation。

## 运行流程

流程仍然复用 coexistence refresh：

```text
corpus -> train.py -> checkpoint/tokenizer -> generation profile replay -> report
```

这样 v590、v591、v592 的训练配置保持一致，只比较 corpus objective。

## 关键结果

```text
pair_full_observed=False
hit_terms=loss
missed_terms=fixed
```

生成预览：

```text
fixed=los=los=los=
loss=los=loss=los
```

这比 v590/v591 更明显地暴露出模型走向 `loss` span，但没有保留 fixed。

## 证据链角色

`e/592` 是第三条真实训练证据。三条 loss-branch objective 都恢复了 `loss`，但全部丢 `fixed`，这为 v593/v594 的比较和 route decision 提供了明确输入。

## 一句话总结

v592 证明 micro-span 能强化 loss continuation，却仍不能形成 fixed/loss pair-full。
