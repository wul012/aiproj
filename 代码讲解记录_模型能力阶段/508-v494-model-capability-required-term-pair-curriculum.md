# v494 model capability required-term pair curriculum

## 本版目标和边界

v494 的目标是测试 v493 的稳定 one-term 信号能不能进入两词小组训练。v493 证明 `fixed/loss/four/chain` 在单目标条件下跨 3 个 seed 稳定命中；v494 把这 4 个词两两组合，观察同一个 checkpoint 是否能同时保住两个 required term。

本版不做三词 curriculum，不做模型扩容，也不声称真实泛化。它只检验 multi-target interference：当两个已稳定的单目标词进入同一训练语料后，是否还能按 prompt 选择正确目标。

## 前置路线

- v491：多 term direct prompt training 仍为 `0/9`。
- v492：one-term isolation 出现 `5/9` 单目标命中。
- v493：对 v492 成功词跨 seed 复测，`fixed/loss/four/chain` 四个词稳定。
- v494：用这 4 个稳定词组成 6 个 pair，测试两目标是否互相干扰。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_curriculum.py`
  - 读取 v493 seed-stability report。
  - 默认只选择 `stable_across_seeds=True` 的 term。
  - 生成两两 pair、pair corpus、pair checkpoint 和逐 term probe。
  - 汇总 full-hit pair、partial pair、probe hit rate 和下一步建议。
- `src/minigpt/model_capability_required_term_pair_curriculum_artifacts.py`
  - 写出 JSON、CSV、text、Markdown 和 HTML。
  - HTML 分成 pair summary 和 probe rows，突出每对词的命中/遗漏情况。
- `scripts/run_model_capability_required_term_pair_curriculum.py`
  - CLI 入口，支持 `--include-partial-terms`、`--term-limit`、`--pair-limit`、训练参数、`--force` 和 `--require-pass`。
- `tests/test_model_capability_required_term_pair_curriculum.py`
  - 覆盖 full/partial pair、默认只选稳定词、无 uptake、坏 source、pair corpus 平衡性、产物写出和 source 定位。
- `e/494/`
  - 保存真实 6 个 pair run、报告、CLI 输出、Playwright snapshot 和截图。

## 核心数据结构

输入是 v493 的 `model_capability_required_term_one_term_seed_stability.json`，主要读取：

- `summary.single_term_capacity_stable`：必须为 `True`，否则没有 pair curriculum 的前提。
- `summary.stable_term_count`：v493 的稳定单目标词数，真实值为 `4`。
- `term_seed_summaries`：按 term 记录 `stable_across_seeds`、hit seeds 和 missed seeds。
- `term_rows`：提供每个 term 的 `case` 和 `scaffold_prompt`。

`selected_terms` 默认只保留稳定 term：

```text
fixed, loss, four, chain
```

`pairs` 是两两组合：

```text
fixed+loss
fixed+four
fixed+chain
loss+four
loss+chain
four+chain
```

每个 `pair_row` 记录一次训练：

- `pair_id`：例如 `01-fixed-loss`。
- `pair_corpus_path`：当前两词的训练语料。
- `training_status`、`checkpoint_exists`：证明训练产物可用。
- `checkpoint_path`、`tokenizer_path`、`metrics_path`、`train_config_path`：后续复核入口。

每个 `probe_row` 记录一个 prompt 的生成结果：

- `pair_id`：属于哪个 pair checkpoint。
- `term`、`scaffold_prompt`：当前 probe 的目标。
- `continuation_hit_count`：短 continuation 是否包含目标词。
- `continuation_preview`：人工复核生成片段。

## 运行流程

1. CLI 定位 v493 seed-stability report。
2. builder 选择 4 个稳定 term。
3. 用 `combinations(terms, 2)` 生成 6 个 pair。
4. 每个 pair 生成 balanced corpus：

```text
fixed:fixed
fixed: fixed
loss:loss
loss: loss
```

5. 每个 pair 调用 `_train_micro_checkpoint` 训练一个 tiny checkpoint。
6. 对 pair 中两个 prompt 分别调用 `_generation_row`。
7. 聚合 `pair_full_hit_count`、`pair_partial_hit_count`、`probe_hit_count`。
8. 写出 JSON/CSV/text/Markdown/HTML，并用 Playwright MCP 截图。

## 真实结果

```text
status=pass
decision=required_term_pair_curriculum_partial
pair_curriculum_decision=pair_curriculum_partial_only
source_stable_term_count=4
selected_term_count=4
pair_count=6
pair_run_count=6
probe_count=12
training_pass_count=6
checkpoint_exists_count=6
probe_hit_count=6
pair_full_hit_count=0
pair_partial_hit_count=6
multi_target_pair_capacity_observed=False
```

6 个 pair 都是 partial：每个 pair 命中一个词、漏掉另一个词，没有一个 pair 同时保住两个 required term。

这说明 v493 的稳定 one-term 能力是真实的，但仍然没有跨过 pair-level multi-target interference。当前 tiny GPT 更像是在同一 pair 里偏向一个目标，而不是可靠地按 prompt 分流。

## 测试覆盖

测试保护了几个关键边界：

- full pair 和 partial pair 同时存在时，汇总必须区分 full/partial。
- 默认只选 v493 稳定词，除非显式 `include_partial_terms`。
- pair corpus 必须平衡包含两个目标，不能混入未选 term。
- 没有任何 probe 命中时，结构仍然 `pass`，但能力结论必须是 not reproduced。
- source 失败时，报告必须 fail。
- JSON/CSV/text/Markdown/HTML 必须全部写出。

这些测试避免把“训练完成”误写成“pair 能力成立”，也避免把单目标稳定证据直接外推到多目标能力。

## 证据角色

- JSON 是后续 pair rebalance 或 three-term curriculum 的主证据。
- CSV 用于逐 probe 查看命中、遗漏和生成预览。
- HTML 和截图用于人工检查 6 个 pair 的 full/partial 状态。
- `pair-corpora/` 保存每个 pair 的训练输入。
- `pair-runs/` 保存 6 个 checkpoint/tokenizer/metrics/config。

## 一句话总结

v494 证明当前 tiny GPT 的 required-term 路线已经有稳定单目标记忆，但进入两目标同训后仍只保留部分目标，pair-level 条件选择尚未成立。
