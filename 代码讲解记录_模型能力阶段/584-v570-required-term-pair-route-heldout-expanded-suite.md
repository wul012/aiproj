# v570 required-term pair route held-out expanded suite

## 本版目标和边界

v570 的目标是把 v569 的三 prompt held-out replay 扩大成七 prompt suite。v569 已经说明 seed `1535` 不是只会源 prompt；v570 要进一步排除“只碰巧适配三种常见格式”的可能。

这一版不训练模型，不新增 corpus mode。它只增强 CLI 的 prompt spec 输入能力，并用真实 v562 checkpoint 跑更大的 held-out suite。

## 关键改动

- `scripts/run_model_capability_required_term_pair_route_heldout_replay.py`
  - 增加 `--prompt-spec SPEC_ID FIXED_PROMPT LOSS_PROMPT`。
  - 可以重复传入多组 prompt spec。
  - 如果不传，继续使用默认三 spec，保持 v569 行为不变。
- `tests/test_model_capability_required_term_pair_route_heldout_replay.py`
  - 增加 `_prompt_specs` 测试，保护 CLI 参数解析。

## 扩展 prompt suite

本版实际运行七种 prompt surface：

```text
colon-spaced:  fixed:      / loss:
equals:        fixed=      / loss=
arrow:         fixed ->    / loss ->
colon-tight:   fixed:      / loss:
equals-spaced: fixed =     / loss =
value-label:   fixed value:/ loss value:
item-label:    fixed item: / loss item:
```

这些 spec 仍然要求 continuation 里出现 `fixed` / `loss`，不会因为 prompt 本身含有 label 就自动通过。

## 运行流程

CLI 解析 prompt specs 后，把它们传给 v569 新增的 builder：

1. 读取 v568 route decision。
2. 找到 selected route：`v562-loss-balanced`。
3. 读取 v562 稳定性报告。
4. 取 pair-full seed `1535` 的 checkpoint。
5. 对七种 prompt surface 分别调用 generation profile replay。
6. 汇总 `heldout_pair_full_count`。

## 真实结果

```text
heldout_pair_full_count=7
row_count=7
heldout_all_pair_full=True
```

这比 v569 的 `3/3` 更强，说明 v562 seed `1535` 的 fixed/loss pair-full 信号可以跨多种 prompt surface 重放。

## 测试覆盖

测试覆盖点：

- 默认 prompt spec 行为保持不变。
- 自定义 prompt spec 可以被解析为 builder 接受的结构。
- v569 的 ready/not-ready 和 sidecar 输出测试继续覆盖主链路。

## 边界说明

v570 仍然只是 targeted route held-out evidence。它没有解决 v562 中 seed `535` 与 `2535` 的不稳定问题，也没有证明 fresh seed 能复现。后续应继续做 seed-transfer 或 fresh-seed 复核。

## 一句话总结

v570 把 v562 seed `1535` 的 held-out 证据从 `3/3` 扩展到 `7/7`，但仍把结论限制在单 seed targeted 能力层。
