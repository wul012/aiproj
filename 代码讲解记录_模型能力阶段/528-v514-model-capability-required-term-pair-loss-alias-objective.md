# v514 required-term pair loss-alias objective 代码讲解

## 本版目标与边界

v514 的目标是处理 v513 暴露出的最清楚能力缺口：`fixed` alias 已经能泛化，但 `loss` 在 source prompt 和 held-out alias prompt 上都没有命中。为避免继续堆只读报告，本版新增一个轻量训练目标，把 `loss:`、`beta:`、`theta:`、`omega:` 明确写成 alias-to-term 语料，训练一个 tiny checkpoint，再回测这些 prompts。

本版不扩大模型规模，不引入外部语料，不宣称通用模型能力提升。它验证的是一个更窄的问题：在当前 tiny GPT 设置下，显式 loss alias 语料是否能恢复 v513 缺失的 `loss` continuation。

## 前置链路

前置版本：

- v511：双 seed continuation-span 训练，证明 prefix gain 可复现。
- v512：held-out probe 发现 `alpha:` 能触发 `fixed`，`beta:` 不能触发 `loss`。
- v513：alias matrix 扩展后确认 `fixed` 三个 held-out alias 全命中，`loss` 三个 held-out alias 全未命中。

v514 直接读取 v513 的 `case_rows`，只选择 `expected_term=loss` 的 source 和 held-out cases。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_loss_alias_objective.py`
  - 新增 v514 的核心 builder。
  - 读取 v513 heldout alias matrix，选择 loss alias cases。
  - 生成 `required_term_pair_loss_alias_objective_corpus.txt`。
  - 调用已有 tiny training helper 训练 checkpoint。
  - 对 source/heldout loss prompts 做 generation 回测并输出 summary。
- `src/minigpt/model_capability_required_term_pair_loss_alias_objective_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML。
  - CSV 以 case 为粒度，保留 v513 source hit 和 v514 candidate hit 对照。
- `scripts/run_model_capability_required_term_pair_loss_alias_objective.py`
  - 提供 CLI 入口，支持训练参数、`--force` 和 `--require-pass`。
- `tests/test_model_capability_required_term_pair_loss_alias_objective.py`
  - 用 fake train/generate 覆盖 full-hit、no-gain、缺少 case_rows、语料选择四类情况。

## 核心数据结构

`select_loss_alias_objective_cases()` 从 v513 报告中提取：

- `source-loss`: `loss:` -> `loss`
- `heldout-beta-loss`: `beta:` -> `loss`
- `heldout-theta-loss`: `theta:` -> `loss`
- `heldout-omega-loss`: `omega:` -> `loss`

每个 case 保留：

- `case_id`
- `case_type`
- `alias_group`
- `prompt`
- `expected_term`
- `source_run_count`
- `source_hit_count`
- `source_hit_rate`

这些字段让 v514 报告能直接比较“v513 原始命中情况”和“v514 新 checkpoint 回测命中情况”。

## 语料与训练流程

`build_loss_alias_objective_corpus()` 为每个 alias 写入几种短行：

```text
beta:loss
beta: loss
alias beta: means loss
continue loss alias beta:loss
```

同时加入 `loss alias bridge` 行，把多个 loss alias 串到同一小语境里。这个语料只为训练 alias-to-loss continuation，不包含 fixed branch，也不试图解决更广泛的 pair conditioning。

训练复用已有 `_train_micro_checkpoint()`，默认参数为：

- `repeat=220`
- `bridge_repeat=4`
- `max_iters=900`
- `block_size=16`
- `n_embd=64`
- `seed=514`

训练完成后，builder 立刻用同一批 loss cases 做 generation probe。

## 输出字段

`summary` 的关键字段：

- `loss_alias_decision`
- `generation_hit_case_count`
- `source_loss_hit`
- `heldout_loss_alias_hit_case_count`
- `heldout_loss_alias_full_coverage`
- `all_loss_alias_full_coverage`
- `checkpoint_exists`

`decision` 分四层：

- `required_term_pair_loss_alias_continuation_full_hit`
- `required_term_pair_loss_alias_continuation_partial_hit`
- `required_term_pair_loss_alias_source_only`
- `required_term_pair_loss_alias_no_gain`

本版真实运行落在第一层，但解释里仍保留边界：单 seed 成功需要下一版 seed stability 复验。

## 测试覆盖

测试覆盖四个关键点：

- fake full-hit generation 时，报告进入 `required_term_pair_loss_alias_continuation_full_hit`。
- fake no-gain generation 时，结构仍为 `pass`，因为训练成功但能力未恢复不是结构错误。
- 缺少 loss alias cases 时，报告失败并让 `--require-pass` 返回 1。
- 语料选择稳定包含 `loss:loss`、`beta:loss`、`omega:loss` 和 bridge 行。

这组测试保护的是 v514 的 contract：它是训练目标，不是 release gate；结构失败才失败，能力结果按证据如实记录。

## 运行证据

运行证据归档在：

```text
e/514/解释/model-capability-required-term-pair-loss-alias-objective/
e/514/图片/
```

真实结果：

- `generation_hit_case_count=4`
- `heldout_loss_alias_hit_case_count=3`
- `heldout_loss_alias_full_coverage=True`
- `checkpoint_exists=True`

HTML 截图保存在：

```text
e/514/图片/01-model-capability-required-term-pair-loss-alias-objective.png
```

## 一句话总结

v514 把 `loss` alias 从 v513 的“全部缺失”推进到单 seed tiny 训练“全部命中”，但稳定性仍需下一版复验。
