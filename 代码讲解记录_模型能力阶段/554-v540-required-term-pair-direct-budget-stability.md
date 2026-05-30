# v540 required-term pair direct-budget stability 代码讲解

## 本版目标和边界

v539 证明 isolated prompt block 会让 pair-full 退化到 `0/3`。v540 回到最直接的 `colon_immediate` corpus，并增加训练预算，验证 v536 的 `1/3` 是否只是训练不足。

本版没有新增代码模块。它是一次受控实验：固定模型结构、固定 seed 组、固定评估链路，只提高 `repeat`、`bridge_repeat` 和 `max_iters`。

## 输入和参数

v540 使用已有 stability runner：

```text
corpus_mode=colon_immediate
seeds=535,1535,2535
repeat=420
bridge_repeat=40
max_iters=2200
n_layer=1
n_head=1
n_embd=64
learning_rate=0.02
```

与 v536 相比：

```text
repeat: 260 -> 420
bridge_repeat: 20 -> 40
max_iters: 1400 -> 2200
```

## 关键产物

- `e/540/解释/model-capability-required-term-pair-colon-immediate-direct-budget-stability/`
  - 三 seed 训练、checkpoint、replay、stability JSON/CSV/HTML。
- `e/540/解释/model-capability-required-term-pair-colon-immediate-direct-budget-missed-seed-diagnostic/`
  - 对三 seed checkpoint 的 first-token 只读诊断。
- `e/540/图片/`
  - Playwright MCP 截取的 stability 与 missed-seed diagnostic HTML。

这些产物是最终运行证据，不是临时调试文件。

## 真实结果

stability：

```text
decision=required_term_pair_colon_immediate_not_stable
pair_full_seed_count=0/3
```

first-token：

```text
535  -> fixed rank=2, loss rank=1
1535 -> fixed rank=1, loss rank=2
2535 -> fixed rank=2, loss rank=1
```

这说明更高预算没有把两个分支同时推到 top-ranked。模型仍然按 seed 偏向单一分支。

## 链路角色

v540 的价值是排除“继续加训练就行”的简单方案。它把后续路线从训练预算问题转向解码边界、目标判定和数据分布结构问题。

## 验证覆盖

本版复用已经通过测试的 runner 和 diagnostic。验证重点是：

- 真实三 seed PyTorch 训练成功。
- 每个 seed 都产生 checkpoint 和 replay sidecar。
- missed-seed diagnostic 能读取 v540 stability report 并完成 first-token logits 诊断。
- Playwright MCP 能打开 HTML 并保存截图。

一句话总结：v540 证明当前 pair objective 的瓶颈不是简单训练预算不足。
