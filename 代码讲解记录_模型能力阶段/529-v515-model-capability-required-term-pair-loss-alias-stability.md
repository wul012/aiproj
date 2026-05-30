# v515 required-term pair loss-alias stability 代码讲解

## 本版目标与边界

v515 的目标是复验 v514 的 `loss-alias objective`。v514 在 seed `514` 上把 `loss:`、`beta:`、`theta:`、`omega:` 全部恢复为 `loss` continuation，但单 seed 结果不能直接当成稳定能力。因此本版把同一训练目标在 seed `514` 和 `515` 上重跑，汇总稳定性。

本版不添加 fixed branch，不改大模型规模，不做新数据扩展。它只回答一个问题：v514 的 loss alias 恢复是否跨 seed 稳定。

## 前置链路

前置版本：

- v513：确认 `fixed` alias 稳定，而 `loss` alias 全部缺失。
- v514：针对 `loss` alias 建立 tiny training objective，单 seed 全命中。

v515 复用 v514 builder，不复制训练逻辑。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_loss_alias_stability.py`
  - 新增 stability builder。
  - 对每个 seed 调用 v514 的 `build_model_capability_required_term_pair_loss_alias_objective()`。
  - 汇总 seed rows 和 stability summary。
- `src/minigpt/model_capability_required_term_pair_loss_alias_stability_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML。
  - CSV 以 seed 为粒度，记录 full/partial coverage。
- `scripts/run_model_capability_required_term_pair_loss_alias_stability.py`
  - CLI 支持 `--seeds`、训练参数、`--force` 和 `--require-pass`。
- `tests/test_model_capability_required_term_pair_loss_alias_stability.py`
  - 覆盖 stable full hit、seed-dependent signal、空 seed 失败、no-signal summary。

## 核心数据结构

`seed_rows` 每行记录：

- `seed`
- `status`
- `decision`
- `loss_alias_decision`
- `checkpoint_exists`
- `generation_hit_case_count`
- `source_loss_hit`
- `heldout_loss_alias_hit_case_count`
- `heldout_loss_alias_full_coverage`
- `training_status`
- `out_dir`

`summary` 聚合为：

- `seed_count`
- `pass_count`
- `checkpoint_seed_count`
- `source_loss_hit_seed_count`
- `heldout_loss_alias_partial_seed_count`
- `heldout_loss_alias_full_seed_count`
- `stable_loss_alias_full_coverage`
- `stable_loss_alias_partial_coverage`

这组字段把“所有 seed 至少部分命中”和“所有 seed 全覆盖”分开，避免结论跳得太快。

## 运行流程

`build_model_capability_required_term_pair_loss_alias_stability()` 的流程：

1. 清洗 seed 列表，去重并保持顺序。
2. 对每个 seed 调用 v514 objective builder。
3. 每个 seed 独立写入 `seed-runs/seed-<seed>`。
4. 读取每个 seed 的 summary，形成 `seed_rows`。
5. 根据 full/partial hit 分布生成 stability decision。

如果某个 seed 训练结构失败，v515 报告会进入结构失败；如果训练成功但未命中，只作为能力证据记录，不把结构状态改成 fail。

## 真实结果解释

真实结果：

- seed `514`: 4/4 case hit，3/3 held-out hit，全覆盖。
- seed `515`: 2/4 case hit，2/3 held-out hit，未全覆盖。

因此 v515 得出的判断是：

```text
required_term_pair_loss_alias_stable_partial_hit
```

这比 v514 更稳健：`loss` alias 不是完全不可学，但 full coverage 还依赖 seed。

## 测试覆盖

测试覆盖：

- 两个 seed 都 full hit 时输出 `required_term_pair_loss_alias_stable_full_hit`。
- 只有一个 seed full hit 时输出 seed-dependent 判断。
- 空 seed 列表是结构失败。
- 无命中 seed rows 会得到 no-stable-generation-signal。

测试重点保护 v515 的结论边界：稳定性报告不能把部分信号误写成 full stable signal。

## 运行证据

运行证据归档在：

```text
e/515/解释/model-capability-required-term-pair-loss-alias-stability/
e/515/图片/
```

HTML 截图：

```text
e/515/图片/01-model-capability-required-term-pair-loss-alias-stability.png
```

## 一句话总结

v515 把 v514 的单 seed 恢复信号校准为跨 seed 部分稳定信号，为下一步检查 missed rows 或重新设计 alias 语料提供了边界。
