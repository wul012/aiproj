# v612 required-term pair delimiter-span seed 3535

## 本版目标和边界

v612 跑 v610 的第二条 route：`equals_surface_no_pair_id_fixed_retention_delimiter_span_repair`。它用分号、句点和 `end` 训练目标 term 的边界，尝试减少 repeated term loop。

本版只做真实训练与归档，不新增代码。

## 前置链路

```text
v609: 首 token 冲突诊断
v610: 新增 delimiter-span corpus
v611: contrast-free 仍 cross-branch
v612: 验证 delimiter-span 是否更稳
```

## 关键产物

```text
e/612/解释/model-capability-required-term-pair-delimiter-span-seed-3535/
e/612/图片/v612-delimiter-span-seed-3535.png
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
fixed= -> fixed=lossss
loss=  -> fixed=fixed=
```

这说明 delimiter-span route 能把 fixed prompt 拉回来，但 loss prompt 仍被 fixed 分支覆盖。

## 证据边界

这是 fixed-only tradeoff，不是能力提升。它说明“停止循环”有一点帮助，但没有解决 branch selection 的双目标问题。

## 一句话总结

v612 证明 delimiter-span route 只恢复 fixed，仍不能达成 fixed/loss pair-full。
