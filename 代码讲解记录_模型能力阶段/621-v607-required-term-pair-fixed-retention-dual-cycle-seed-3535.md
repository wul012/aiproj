# v607 required-term pair fixed-retention dual-cycle seed 3535

## 本版目标和边界

v607 验证 v605 的第二条语料路线 `equals_surface_no_pair_id_fixed_retention_dual_cycle_repair`。它把 fixed/loss 目标交替放入语料，试图减少 v606 那种 loss-only 覆盖。

本版不修改训练脚本、不改模型结构、不扩大模型质量结论；它只给 dual-cycle route 留下真实训练证据。

## 前置链路

```text
v604: 选出 v601 first-token fixed recovery evidence
v605: 新增 loss-rebalance 与 dual-cycle corpus modes
v606: loss-rebalance route 变成 loss-only
v607: dual-cycle route 检查是否能同时保住 fixed/loss
```

v607 的价值在于给 v606 做对照：如果 v606 太偏 loss，dual-cycle 是否能通过交替行恢复平衡。

## 关键产物

```text
e/607/解释/model-capability-required-term-pair-fixed-retention-dual-cycle-seed-3535/
e/607/图片/v607-fixed-retention-dual-cycle-seed-3535.png
e/607/解释/说明.md
```

其中 JSON 是后续 closeout 可以消费的源证据；HTML/Markdown/text 是可读报告；截图证明报告能在浏览器里打开。

## 输入输出

输入命令使用固定训练预算：

```text
--seed 3535
--corpus-mode equals_surface_no_pair_id_fixed_retention_dual_cycle_repair
--repeat 260
--bridge-repeat 20
--max-iters 1800
--n-embd 64
--temperature 0.2
--top-k 1
```

输出判定：

```text
status=pass
decision=required_term_pair_coexistence_refresh_no_pair_full
pair_full_observed=False
```

Replay rows：

```text
fixed= -> fixed=fixed=
loss=  -> fixed=los=fi
```

因此 dual-cycle route 是 fixed-only tradeoff，不是 pair-full repair。

## 测试和证据覆盖

本版使用同一套 coexistence refresh runner：

- 真实训练并生成 checkpoint/tokenizer。
- 对 default 和 newline-suppression profiles 做 replay。
- 用 `--require-pass` 确认流程没有失败。
- Playwright MCP 截 HTML 报告，保证归档证据可浏览。

## 一句话总结

v607 证明 dual-cycle route 可以恢复 fixed，但仍会丢失 loss，pair-full 问题没有解决。
