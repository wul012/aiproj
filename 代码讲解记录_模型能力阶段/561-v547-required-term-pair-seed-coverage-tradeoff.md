# v547 required-term pair seed coverage tradeoff 代码讲解

## 本版目标和边界

v546 证明 `colon_immediate_loss_calibrated` 可以恢复 seed `1535`，但会丢掉 v544 已恢复的 `535` 和 `2535`。v547 不继续训练，也不修改模型结构，而是在两个已归档 stability report 之间增加一层只读 scoreboard。

本版解决的问题是：把“v544 覆盖两个 seed、v546 覆盖另一个 seed”的人工判断，变成可测试、可归档、可被后续脚本消费的 coverage tradeoff report。

## 前置链路

v547 直接消费两份前置产物：

- v544 `top_k=2, temperature=0.8` stability：pair-full `2/3`，覆盖 `535`、`2535`。
- v546 `loss_calibrated + top_k=2, temperature=0.8` stability：pair-full `1/3`，覆盖 `1535`。

这两份报告都是 `model_capability_required_term_pair_colon_immediate_stability.json`，因此 v547 可以只读重算 coverage，不需要重新训练。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_seed_coverage_tradeoff.py`
  - 读取多份 colon-immediate stability report。
  - 抽取每个配置的 `pair_full_seeds`。
  - 计算 per-seed union coverage、best single config、exclusive seed map 和 tradeoff 状态。
- `src/minigpt/model_capability_required_term_pair_seed_coverage_tradeoff_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML。
  - HTML 同时展示 config 表和 seed 表，让审阅者能看到哪个配置覆盖哪个 seed。
- `scripts/run_model_capability_required_term_pair_seed_coverage_tradeoff.py`
  - CLI 入口，支持传入多个 report 文件或输出目录。
  - `--label` 给每个输入配置一个稳定名称。
  - `--require-pass` 只在输入结构失败时返回非零；partial coverage 本身不是脚本失败。
- `tests/test_model_capability_required_term_pair_seed_coverage_tradeoff.py`
  - 覆盖 full union、partial coverage、非法输入、artifact 渲染和路径定位。

## 核心数据结构

`config_rows` 表示每个来源配置：

```json
{
  "config_id": "v544-topk2-t080",
  "pair_full_seed_count": 2,
  "seed_count": 3,
  "pair_full_seeds": [535, 2535]
}
```

`seed_rows` 表示每个 seed 的覆盖情况：

```json
{
  "seed": 1535,
  "covered_by_union": true,
  "winning_config_id": "v546-loss-calibrated-topk2-t080",
  "covering_config_ids": ["v546-loss-calibrated-topk2-t080"]
}
```

`summary` 是本版的判断中心：

```json
{
  "union_pair_full_seed_count": 3,
  "best_single_pair_full_seed_count": 2,
  "tradeoff_detected": true,
  "all_seed_covered_by_union": true
}
```

当 union 大于 best single，说明多个配置确实互补；当 union 达到全部 seed，decision 进入 `required_term_pair_seed_coverage_tradeoff_complementary_full_union`。

## 运行流程

1. CLI 把输入路径规范化为 `model_capability_required_term_pair_colon_immediate_stability.json`。
2. builder 校验每份 report 的 `status=pass` 且存在 `seed_rows`。
3. 每份 report 生成一个 config row。
4. 所有 seed 合并成 seed rows，计算每个 seed 被哪些配置覆盖。
5. summary 对比 union coverage 与 best single config。
6. artifact writer 写出五种格式，HTML 用于截图归档和人工审阅。

## 真实结果解释

v547 的真实运行结果：

```text
union_pair_full_seed_count=3
best_single_config_id=v544-topk2-t080
best_single_pair_full_seed_count=2
tradeoff_detected=True
```

这不是“模型能力已经稳定”的结论。更准确的结论是：同一 tiny GPT 训练目标在不同 corpus/seed 配置下出现互补覆盖，后续最有价值的是测试显式 fallback 或 config-selection policy，而不是继续单点改 corpus。

## 测试覆盖

单测保护了四个关键边界：

- 两个互补 report 可以产生 full union decision。
- 两个重复覆盖同一 seed 的 report 不会误报 tradeoff。
- 输入 report 结构失败时 `--require-pass` 语义对应非零退出。
- JSON/CSV/text/Markdown/HTML 都能被生成。

额外修正：真实 JSON 检查时发现 `contributing_config_ids` 曾误写为 seed 列表，本版已改为 config id，并用单测钉住。

## 归档角色

`e/547` 保存运行说明、HTML 报告、Playwright snapshot 和截图。它是模型能力阶段的一个决策节点：告诉后续版本先做 fallback/config-selection，而不是继续把每个 corpus 变体当成孤立实验。

一句话总结：v547 把 v544/v546 的 seed-level tradeoff 固化成可复核证据，让下一步模型能力实验从“继续试参数”转向“验证配置选择策略”。
