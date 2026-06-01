# v611 required-term pair contrast-free seed 3535

## 本版目标和边界

v611 跑 v610 的第一条新 objective：`equals_surface_no_pair_id_fixed_retention_contrast_free_repair`。它尝试让 fixed rows 不提 loss、loss rows 不提 fixed，减少对侧 term 泄漏。

本版不新增代码逻辑，只做真实 seed 训练和证据归档。

## 前置链路

```text
v609: first-token preference tradeoff confirmed
v610: 新增 contrast-free / delimiter-span / context-switch 三条路线
v611: 先跑 contrast-free route
```

## 关键产物

```text
e/611/解释/model-capability-required-term-pair-contrast-free-seed-3535/
e/611/图片/v611-contrast-free-seed-3535.png
```

JSON 报告记录训练状态、checkpoint、replay rows 和 pair-full 判定；HTML/截图用于人工审查。

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
fixed= -> lossssssss
loss=  -> fixed=fixed=
```

这不是 fixed-only 或 loss-only，而是两个 prompt 都出现 cross-branch 起始，说明 row separation 自身不足以稳定选择 branch。

## 测试与证据

本版复用 `run_model_capability_required_term_pair_coexistence_refresh.py`：

- 真实训练 checkpoint/tokenizer。
- default 与 newline-suppression profiles 都 replay。
- `--require-pass` 保证流程失败会退出，但不把 pair-full 作为通过条件。
- Playwright MCP 截取 HTML 报告。

## 一句话总结

v611 证明 contrast-free row separation 仍不能解决 fixed/loss 的首 token 冲突。
