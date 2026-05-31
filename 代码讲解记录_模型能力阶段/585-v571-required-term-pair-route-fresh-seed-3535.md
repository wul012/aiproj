# v571 required-term pair route fresh seed 3535

## 本版目标和边界

v571 是对 v569/v570 的反向验证。v569 和 v570 都使用 v562 中已经成功的 seed `1535`，所以它们证明的是 prompt-transfer，而不是 fresh seed 稳定。v571 用同样 objective 和训练预算，换一个新 seed `3535` 重新训练。

这一版不改 corpus，不调解码，不扩大模型。它只看路线能不能自然复现。

## 前置能力

- v568 选出 `v562-loss-balanced`。
- v569 证明 seed `1535` 在默认三 held-out prompt 上 `3/3`。
- v570 证明 seed `1535` 在七 prompt expanded suite 上 `7/7`。

v571 的问题是：

```text
fresh seed 3535 是否也能 pair-full？
```

## 运行配置

本版复用 v562 的核心配置：

```text
corpus_mode=equals_surface_no_pair_id_loss_balanced_repair
seed=3535
repeat=260
bridge_repeat=20
max_iters=1400
n_embd=64
temperature=0.8
top_k=2
```

这保证 v571 和 v562/v570 的差异主要来自 seed，而不是配置漂移。

## 关键结果

```text
pair_full_seed_count=0/1
continuation_hit_count=1
default_pair_full_variant_count=0
suppression_pair_full_variant_count=0
```

训练执行成功，checkpoint/tokenizer 都存在，但 replay 只命中一个 term，没有形成 fixed/loss pair-full。

## 证据角色

主报告：

```text
e/571/解释/model-capability-required-term-pair-route-fresh-seed-3535/model_capability_required_term_pair_colon_immediate_stability.json
```

训练产物：

```text
e/571/解释/model-capability-required-term-pair-route-fresh-seed-3535/seed-runs/seed-3535/
```

截图：

```text
e/571/图片/v571-route-fresh-seed-3535.png
```

这些证据说明 v571 是一次真实训练，不是从旧 checkpoint 派生的只读 replay。

## 测试和验证

本版复用已有 colon-immediate stability runner。该 runner 已覆盖训练命令生成、checkpoint 存在性、generation profile replay 和 summary 汇总。v571 的新增价值来自真实运行证据，而不是新增测试代码。

## 链路判断

v571 的结论很克制：v562 seed `1535` 的 prompt-transfer 证据可保留，但不能升级为 route-level seed stability。fresh seed `3535` 的失败说明下一步要诊断 missed branch 或 seed sensitivity。

## 一句话总结

v571 用 fresh seed 3535 证明当前路线仍不具备自然复现能力，项目应继续做 seed gap 诊断而不是扩大能力声明。
