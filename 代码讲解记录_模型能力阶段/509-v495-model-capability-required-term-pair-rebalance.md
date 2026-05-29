# v495 model capability required-term pair rebalance

## 本版目标和边界

v495 的目标是承接 v494 的受控负结果：v494 证明 6 个两词 pair 全部只能命中其中一个 required term，没有任何 pair 同时 full-hit。v495 不急着扩大到三词，而是先改变两词训练语料的组织方式，观察 pair-level interference 是否能被语料重平衡缓解。

本版不做模型扩容，不做真实通用语言质量声明，也不把单个指标包装成生产能力。它只检验一个窄边界：固定 v494 的 6 个 partial pair 后，加入更明确的单词隔离行和 pair 对照行，是否能从 `0/6` full-hit pair 推进到至少一个 full-hit pair。

## 前置路线

- v492：one-term isolation 首次证明部分 required term 可以被 tiny checkpoint 学到。
- v493：对成功词跨 seed 复测，得到 `fixed/loss/four/chain` 四个稳定 one-term 目标。
- v494：把四个稳定词两两组合，6 个 pair 都训练成功，但全部 partial-only。
- v495：只处理 v494 的 partial pair，不增加目标数量，先测试 rebalance 语料是否能减少两词干扰。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_rebalance.py`
  - 读取 v494 `model_capability_required_term_pair_curriculum.json`。
  - 只选择 `pair_partial_hit=True` 且 `pair_full_hit=False` 的 pair。
  - 为每个 pair 生成 rebalance corpus、训练 checkpoint、运行两个 prompt probe。
  - 计算 before/after delta、full-hit gain、probe-hit delta 和下一步建议。
- `src/minigpt/model_capability_required_term_pair_rebalance_artifacts.py`
  - 写出 JSON、CSV、text、Markdown 和 HTML。
  - CSV 聚焦 pair 级 before/after 对比；HTML 同时展示 pair comparison 和 probe rows。
- `scripts/run_model_capability_required_term_pair_rebalance.py`
  - v495 CLI 入口，支持训练参数、`--pair-limit`、`--force` 和 `--require-pass`。
- `tests/test_model_capability_required_term_pair_rebalance.py`
  - 用 `unittest` 覆盖 full-hit gain、no-gain、training failure、输入异常、语料构造、summary 和 artifact 输出。
  - 这样 GitHub coverage 的 `unittest discover` 能直接计入 v495 覆盖。
- `e/495/`
  - 保存真实 v495 运行产物、CLI 输出、Playwright snapshot 和 HTML 截图。

## 核心数据结构

输入是 v494 的 pair curriculum report。v495 主要读取：

- `summary.pair_curriculum_decision`：必须是 `pair_curriculum_partial_only`，证明这是需要 rebalance 的边界。
- `summary.probe_hit_count`：v494 总 probe 命中数，真实值为 `6`。
- `summary.pair_full_hit_count`：v494 full-hit pair 数，真实值为 `0`。
- `pairs`：提供每个 pair 的 term、prompt 和 case。
- `pair_summaries`：提供每个 pair 在 v494 的 hit/missed terms。

`select_rebalance_pairs()` 只选择 partial pair：

```text
01-fixed-loss
02-fixed-four
03-fixed-chain
04-loss-four
05-loss-chain
06-four-chain
```

每个 pair 会保留 source hit/missed 信息：

```text
source_hit_terms
source_missed_terms
source_hit_rate
source_pair_partial_hit
```

这些字段用于 v495 结束后做 before/after 对比，而不是只看新的生成结果。

## Rebalance Corpus

v494 的 pair corpus 主要是简单交替：

```text
fixed:fixed
fixed: fixed
loss:loss
loss: loss
```

v495 的 rebalance corpus 保持 prompt-leading，但加入两类额外行：

```text
fixed:fixed
fixed: fixed
fixed prompt keeps fixed
loss:loss
loss: loss
loss prompt keeps loss
pair fixed loss prompt fixed: target fixed
fixed:fixed not loss
pair fixed loss prompt loss: target loss
loss:loss not fixed
```

这样做的意图是让 tiny model 在同一个 pair checkpoint 中反复看到“prompt 自己绑定自己的 term”，同时看到另一个 term 作为干扰对象。它不是更复杂的语言任务，而是更明确的条件选择任务。

## 运行流程

1. CLI 定位 v494 pair curriculum report。
2. builder 校验 source 为 `pass` 且 `pair_curriculum_partial_only`。
3. 选择 6 个 partial pair。
4. 每个 pair 写入 `rebalance-corpora/<pair>.txt`。
5. 每个 pair 调用 `_train_micro_checkpoint` 训练一个 checkpoint。
6. 对 pair 中两个 prompt 调用 `_generation_row`。
7. `summarize_rebalance_probe_rows()` 统计 after hit/missed terms。
8. `compare_rebalance_pairs()` 计算每个 pair 的 before/after delta。
9. 写出 JSON/CSV/text/Markdown/HTML，并用 Playwright MCP 截图。

## 真实结果

```text
status=pass
decision=required_term_pair_rebalance_capacity_gain
pair_rebalance_decision=pair_rebalance_full_hit_gain
source_probe_hit_count=6
source_pair_full_hit_count=0
selected_pair_count=6
pair_run_count=6
probe_count=12
training_pass_count=6
checkpoint_exists_count=6
probe_hit_count=5
probe_hit_delta=-1
pair_full_hit_count=1
pair_full_hit_delta=1
pair_partial_hit_count=3
pair_full_success_rate=0.1667
rebalance_improved=True
model_quality_claim=pair_rebalance_capacity_signal_only
```

最重要的变化是 `fixed/loss` 从 v494 的只命中 `fixed`，变为同时命中 `fixed/loss`。这让 `pair_full_hit_count` 从 `0` 到 `1`，说明 rebalance 语料至少能打开一个 pair-level capacity 窗口。

但 `probe_hit_count` 从 `6` 降到 `5`，`loss/chain` 和 `four/chain` 退化为 zero-hit。这意味着 v495 不是全局质量提升，而是一个局部能力信号：它证明“某个 pair 可以 full-hit”，还没有证明“所有 pair 都更稳定”。

## 测试覆盖

测试不是只断言文件能写出，而是保护关键链路：

- full-hit gain：source 一个 hit，rebalance 两个 hit，必须得到 `required_term_pair_rebalance_capacity_gain`。
- no-gain：rebalance 没有超过 source，必须保持 `required_term_pair_rebalance_no_gain`。
- training failure：训练失败时状态为 `fail`，`--require-pass` 对应非零退出。
- input guard：坏 source、非 partial-only source、空 source 都不能被误判为有效能力实验。
- corpus builder：验证 prompt-leading、pair 对照和 `not <other>` 干扰行存在。
- artifact writer：JSON/CSV/text/Markdown/HTML 都能从同一 report 写出。

因为 coverage 脚本使用 `unittest discover`，测试类显式继承 `unittest.TestCase`，避免出现“pytest 通过但 CI coverage 没计入”的 v494.0.0 问题。

## 运行证据

- `e/495/解释/model-capability-required-term-pair-rebalance/model_capability_required_term_pair_rebalance.json`
- `e/495/解释/model-capability-required-term-pair-rebalance/model_capability_required_term_pair_rebalance.csv`
- `e/495/解释/model-capability-required-term-pair-rebalance/model_capability_required_term_pair_rebalance.html`
- `e/495/解释/model-capability-required-term-pair-rebalance-cli.txt`
- `e/495/解释/model-capability-required-term-pair-rebalance-snapshot.md`
- `e/495/图片/01-model-capability-required-term-pair-rebalance.png`

## 一句话总结

v495 没有把 tiny GPT 说成“整体变强”，但它把 v494 的 pair-level 干扰边界推进了一格：在固定 pair 集合下，通过语料重平衡首次观察到一个 two-term full-hit checkpoint，下一步应对该改善 pair 做跨 seed 稳定性复测。
