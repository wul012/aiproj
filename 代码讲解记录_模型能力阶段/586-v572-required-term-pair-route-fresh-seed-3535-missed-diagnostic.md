# v572 required-term pair route fresh seed 3535 missed diagnostic

## 本版目标和边界

v572 解释 v571 的 fresh seed 失败。v571 证明 seed `3535` 训练执行成功但没有 pair-full；v572 不再训练，而是读取 v571 的稳定性报告和 checkpoint，对 missed seed 做 first-token 诊断。

这一版不改变模型、不改变数据、不改变 decode。它只定位失败层级。

## 前置能力

- v571：fresh seed `3535` 的 `pair_full_seed_count=0/1`。
- 既有 missed-seed diagnostic：可以读取 colon-immediate stability 报告，检查 expected first token 的 top-rank 情况。

## 输入输出

输入：

```text
e/571/解释/model-capability-required-term-pair-route-fresh-seed-3535/model_capability_required_term_pair_colon_immediate_stability.json
```

输出：

```text
e/572/解释/model-capability-required-term-pair-route-fresh-seed-3535-missed-diagnostic/
```

## 核心字段

- `missed_seed_count=1`
  - v571 的唯一 fresh seed 未 pair-full。
- `missed_expected_top_count=0`
  - 没有 seed 同时让两个 expected first token 排第一。
- `missed_first_token_gap_count=1`
  - fresh seed 失败发生在 first-token preference 层。
- `fixed_expected_rank=1`
  - `fixed=` 已经能把 `f` 排第一。
- `loss_expected_rank=3`
  - `loss=` 的期望首 token 没有排第一。
- `loss_top_token=f`
  - `loss=` 仍被拉回 fixed-like 路径。

## 诊断含义

v572 把 v571 的失败从“没有 pair-full”进一步解释为：

```text
loss branch first-token preference gap
```

这和前面多个版本看到的 fixed/loss 互相迁移问题一致。模型不是完全没学到任务，而是在 `loss=` 入口处仍容易选择 fixed 分支。

## 测试和验证

本版复用现有 missed-seed diagnostic 代码路径。验证重点是：

- CLI 读取 v571 归档目录成功。
- 输出 `status=pass`。
- CSV 明确给出 fixed/loss 的 expected rank 和 top token。
- Playwright 截图证明 HTML 报告可读。

## 链路角色

v572 是 v571 的解释层。它阻止我们误判“需要更多 held-out prompt”或“需要更长 continuation”，因为问题已经定位到 first-token preference。

## 一句话总结

v572 把 fresh seed 3535 的失败定位为 `loss=` 首 token 排名落后，下一步应围绕 first-token preference 做更有针对性的修复。
