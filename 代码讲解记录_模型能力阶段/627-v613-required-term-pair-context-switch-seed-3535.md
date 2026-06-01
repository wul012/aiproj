# v613 required-term pair context-switch seed 3535

## 本版目标和边界

v613 跑 v610 的第三条 route：`equals_surface_no_pair_id_fixed_retention_context_switch_repair`。它用 `[fixed-context]` / `[loss-context]` 分离局部语料上下文，但 replay prompt 仍保持 `fixed=` / `loss=`。

本版只做真实训练和证据归档，不新增代码。

## 前置链路

```text
v609: first-token preference conflict
v610: context-switch corpus mode
v611: contrast-free cross-branch negative
v612: delimiter-span fixed-only
v613: context-switch fixed-only
```

## 关键产物

```text
e/613/解释/model-capability-required-term-pair-context-switch-seed-3535/
e/613/图片/v613-context-switch-seed-3535.png
```

## 运行结果

```text
status=pass
decision=required_term_pair_coexistence_refresh_no_pair_full
training_status=pass
checkpoint_exists=True
pair_full_observed=False
```

Replay rows：

```text
fixed= -> fixed=fixed=
loss=  -> fixeded=fixe
```

这说明 context-switch 可以保住 fixed，但 loss 仍被 fixed 起始覆盖。

## 证据边界

本版结果不是 pair-full，也不是 broad model improvement。它只说明 context-switch 语料在 seed `3535` 下仍然形成 fixed-only tradeoff。

## 一句话总结

v613 证明 context-switch route 仍然没有解决 loss branch 被 fixed 覆盖的问题。
