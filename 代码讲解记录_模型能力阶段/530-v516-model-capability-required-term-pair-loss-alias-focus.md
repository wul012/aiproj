# v516 required-term pair loss-alias focus 代码讲解

## 本版目标与边界

v516 继续处理 v515 的不稳定点。v515 证明 `loss` alias 有跨 seed 部分信号，但 seed `515` 没命中 `source-loss` 和 `heldout-beta-loss`。本版新增 focused repair：从 v515 stability 报告中自动抽取 missed rows，把这些 rows 在语料中加密，再训练 seed `515`。

本版不增加模型规模，不把 fixed branch 加回来，也不继续扩大 alias 集合。它只验证一个具体假设：missed row density 是否足以修复 v515 的 partial signal。

## 前置链路

前置版本：

- v514：seed `514` 的 loss alias objective 全命中。
- v515：seed `514` 全命中，seed `515` 只部分命中。

v516 的输入是 v515 stability report，它会读取每个 seed report 中的 `case_rows`，找出 `generation_hit_count=0` 的 loss cases。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_loss_alias_focus.py`
  - 新增 focused repair builder。
  - 提取 support cases 和 focus cases。
  - 构建 base repeat + focus repeat 的 focused corpus。
  - 训练指定 seed 并回测全部 support cases。
- `src/minigpt/model_capability_required_term_pair_loss_alias_focus_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML。
  - HTML 展示 focus cases 与 seed rows。
- `scripts/run_model_capability_required_term_pair_loss_alias_focus.py`
  - CLI 支持 `--seeds`、`--base-repeat`、`--focus-repeat`、训练参数和 `--require-pass`。
- `tests/test_model_capability_required_term_pair_loss_alias_focus.py`
  - 覆盖 missed case selection、focused corpus、repair/no-repair、无 missed rows 失败。

## 核心数据结构

`support_cases` 是 v515 报告中出现过的全部 loss cases：

- `source-loss`
- `heldout-beta-loss`
- `heldout-omega-loss`
- `heldout-theta-loss`

`focus_cases` 是至少一个 seed 没命中的 cases：

- `source-loss`
- `heldout-beta-loss`

每个 focus case 会记录：

- `missed_seed_count`
- `missed_seeds`

这让报告不仅知道“要修什么”，也知道“为什么修这些”。

## 语料策略

focused corpus 分三层：

1. support rows：所有 loss aliases 都保留基础重复。
2. focus rows：missed rows 额外加密。
3. bridge rows：把所有 support prompts 串到同一个 loss alias bridge。

示例：

```text
support alias omega: means loss
focus alias beta: means loss
focused loss alias bridge loss:loss beta:loss omega:loss theta:loss
```

这个设计比 v514 更定向，但仍然保持语料形状简单，避免把 fixed branch 或新任务混进来。

## 真实结果解释

真实运行结果：

- `focus_case_count=2`
- `focus_full_seed_count=0`
- `support_full_seed_count=0`
- `decision=required_term_pair_loss_alias_focus_no_repair`

generation preview 中出现类似：

```text
los\ns\ns\ns\ns
```

这说明模型并非完全远离目标字符，而是输出形状被换行/分隔打断，严格 `loss` substring 检查无法命中。下一步应检查 normalization-aware hit 或 decoding path，而不是继续简单增加 repeat。

## 测试覆盖

测试覆盖：

- fake generation 全命中时，focused repair 报告 support full hit。
- selection 能从 v515 形状的 fixture 中选出 `source-loss` 和 `heldout-beta-loss`。
- fake generation 不命中时，结构仍 pass，但 decision 是 no repair。
- 如果 v515 没有 missed rows，报告结构失败，避免无意义训练。

## 运行证据

运行证据归档在：

```text
e/516/解释/model-capability-required-term-pair-loss-alias-focus/
e/516/图片/
```

截图：

```text
e/516/图片/01-model-capability-required-term-pair-loss-alias-focus.png
```

## 一句话总结

v516 证明 missed-row 加密本身不能稳定修复 `loss` alias，问题已经从“是否训练过”推进到“生成输出形状和命中判定是否对齐”。
