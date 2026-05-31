# v548 required-term pair seed config selection 代码讲解

## 本版目标和边界

v547 证明 v544 与 v546 的 union 可以覆盖三个 seed，但它仍然只是 coverage scoreboard。v548 进一步把这个 scoreboard 转成可消费的 seed config-selection policy。

本版不训练新模型，不改 tokenizer，也不重新 replay checkpoint。它只验证每个 seed 的 `winning_config_id` 是否真的在 `per_config_pair_full` 里为 true，然后输出明确的选择策略。

## 前置能力

v548 直接读取 v547 的 `model_capability_required_term_pair_seed_coverage_tradeoff.json`。

前置结论是：

- `535` 由 `v544-topk2-t080` 覆盖。
- `1535` 由 `v546-loss-calibrated-topk2-t080` 覆盖。
- `2535` 由 `v544-topk2-t080` 覆盖。

v548 的职责是把这三个事实固化为策略，并防止 selected config 与源 coverage map 不一致。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_seed_config_selection.py`
  - 定位并读取 v547 tradeoff report。
  - 校验输入结构和 per-seed selected config。
  - 生成 `selection_rows`、policy config rows 和 summary。
- `src/minigpt/model_capability_required_term_pair_seed_config_selection_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
  - HTML 同时展示 selections 和 configs。
- `scripts/run_model_capability_required_term_pair_seed_config_selection.py`
  - CLI 入口，支持输入 report 文件或输出目录。
  - `--require-pass` 在 selection 不完整时返回非零。
- `tests/test_model_capability_required_term_pair_seed_config_selection.py`
  - 覆盖 multi-config ready、selected config 不真实、artifact 输出和路径定位。

## 核心数据结构

`selection_rows` 是本版的中心：

```json
{
  "seed": 1535,
  "selected_config_id": "v546-loss-calibrated-topk2-t080",
  "selection_ready": true,
  "selected_pair_full": true,
  "covering_config_ids": ["v546-loss-calibrated-topk2-t080"]
}
```

`summary` 判断 policy 是否可用：

```json
{
  "seed_count": 3,
  "selection_ready_seed_count": 3,
  "selected_config_count": 2,
  "requires_multi_config_policy": true
}
```

当所有 seed 都 ready 且 selected config 数量大于 1，decision 为：

```text
required_term_pair_seed_config_selection_multi_config_ready
```

## 关键校验

`_selection_row()` 不只复制 `winning_config_id`，还会读取：

```python
per_config_pair_full[selected_config_id]
```

只有这个值为 true，`selection_ready` 才会成立。也就是说，如果 v547 report 被改坏，或者 winning config 指向一个没有 pair-full 的配置，v548 会 fail。

## 真实运行结果

真实 v548 运行结果：

```text
selection_ready_seed_count=3
selected_config_count=2
requires_multi_config_policy=True
```

这表示当前能力不是“单配置稳定”，而是“多配置选择策略可验证”。模型能力解释必须保持克制：它证明 fixed/loss pair 可以被已有两条配置覆盖，但还没有证明 held-out prompt 或 fresh seed 也稳定。

## 测试覆盖

单测覆盖：

- 完整 v547 tradeoff 可以生成 multi-config ready policy。
- 当 `winning_config_id` 对应的 `per_config_pair_full` 为 false 时，policy fail。
- 五种 artifact 都能生成。
- 输入目录可以被定位为默认 JSON 文件。

## 归档角色

`e/548` 保存了真实 policy 产物和 Playwright 截图。它是下一步 held-out/fresh-seed 检查的输入，而不是最终能力证明。

一句话总结：v548 把互补 coverage 升级成可验证的 seed config-selection policy，为后续验证 fallback 是否真能泛化打下入口。
