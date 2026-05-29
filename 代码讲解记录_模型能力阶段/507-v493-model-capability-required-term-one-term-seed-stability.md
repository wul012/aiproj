# v493 model capability required-term one-term seed stability

## 本版目标和边界

v493 的目标是复核 v492 的 one-term 正向信号是否稳定。v492 里 `fixed/text/loss/four/chain` 这 5 个词在单独训练 checkpoint 时出现 continuation hit，但单次 seed 不能说明这种能力可靠。

本版只做 seed stability，不做多 term curriculum，也不扩大模型规模。它的边界是：如果稳定，也只能说明 tiny GPT 在单目标训练条件下有可复现的 prompt-to-term 记忆能力；不能说明多目标条件选择或 held-out 泛化已经成立。

## 前置路线

这条链路来自 v489-v492：

- v489 修正 prompt-leading corpus。
- v490/v491 证明多 term prompt-leading/direct prompt training 仍是 `0/9`。
- v492 每个 term 单独训练 checkpoint，首次观察到 `5/9` 单目标命中。
- v493 只取 v492 的成功 term，在多个 seed 下重新训练，确认命中是否稳定。

## 关键文件

- `src/minigpt/model_capability_required_term_one_term_seed_stability.py`
  - 读取 v492 one-term isolation report。
  - 默认只选择 v492 已命中的 term。
  - 对每个 term 和每个 seed 重新生成 corpus、训练 checkpoint、运行短 continuation。
  - 汇总 term-seed 命中率、稳定 term 数、部分稳定 term 数和下一步建议。
- `src/minigpt/model_capability_required_term_one_term_seed_stability_artifacts.py`
  - 写出 JSON、CSV、text、Markdown 和 HTML。
  - HTML 分成 term stability 和 seed runs 两张表，方便人工复核。
- `scripts/run_model_capability_required_term_one_term_seed_stability.py`
  - CLI 入口，支持 `--seeds`、`--include-all-terms`、训练参数、`--force` 和 `--require-pass`。
- `tests/test_model_capability_required_term_one_term_seed_stability.py`
  - 覆盖稳定/部分稳定、默认只选 v492 hit term、无复现但结构通过、坏 source、产物写出和 source 定位。
- `e/493/`
  - 保存真实 15 次训练 run、报告、CLI 输出、Playwright snapshot 和截图。

## 核心数据结构

输入是 v492 的 `model_capability_required_term_one_term_isolation.json`，核心读取：

- `summary.single_term_capacity_observed`：必须为 `True`，否则没有 seed stability 的前提。
- `summary.term_with_continuation_hit_count`：v492 的成功 term 数，真实值为 `5`。
- `isolation_rows`：逐 term 记录 `term`、`scaffold_prompt`、`continuation_hit_count`、`checkpoint_path` 和 preview。

`select_seed_stability_terms()` 默认只保留 `continuation_hit_count > 0` 的行，因此 v493 真实选择的是：

```text
fixed, text, loss, four, chain
```

每个 `seed_row` 表示一次独立训练和生成：

- `one_term_seed_run_id`：例如 `01-fixed-seed-493`。
- `seed`：训练和生成共用的 seed。
- `one_term_seed_corpus_path`：当前 term 当前 seed 的训练语料。
- `training_status`、`checkpoint_exists`：证明该 seed run 的 checkpoint 是否可用。
- `generated`、`continuation`、`continuation_hit_count`：当前 seed 的短续写结果。

`term_seed_summaries` 再按 term 聚合：

- `hit_seed_count`：当前 term 命中的 seed 数。
- `hit_seeds` / `missed_seeds`：方便定位哪个 seed 不稳定。
- `stable_across_seeds`：只有全部配置 seed 命中才为 `True`。

## 运行流程

1. CLI 定位 v492 one-term isolation report。
2. builder 选择 v492 中已命中的 5 个 term。
3. 对每个 term 和 seed 生成独立 corpus。
4. 调用 `_train_micro_checkpoint` 训练 15 个 tiny checkpoint。
5. 调用 `_generation_row` 做短 continuation probe。
6. 汇总 `term_seed_hit_count`、`stable_term_count`、`partial_stable_term_count`。
7. 写出 JSON/CSV/text/Markdown/HTML，并用 Playwright MCP 截图归档。

## 真实结果

```text
status=pass
decision=required_term_one_term_seed_stability_observed
one_term_seed_stability_decision=some_successful_terms_seed_stable
selected_term_count=5
seed_count=3
seed_run_count=15
training_pass_count=15
checkpoint_exists_count=15
term_seed_hit_count=14
term_seed_success_rate=0.9333
stable_term_count=4
partial_stable_term_count=1
```

稳定 term 是 `fixed`、`loss`、`four`、`chain`。`text` 是部分稳定：seed `493` 和 `2493` 命中，seed `1493` 未命中。

这个结果比 v492 更强：v492 只能说单目标训练出现了正向信号，v493 进一步说明大部分成功词不是单一 seed 的偶然输出。

## 测试覆盖

测试覆盖了几个关键风险：

- fake generation 全 seed 命中时，必须输出稳定能力信号。
- 同时存在稳定 term 和部分稳定 term 时，汇总不能误判为全稳定。
- 默认选择逻辑必须只选 v492 命中过的 term，避免把 v492 失败词混进稳定性复测。
- 所有 seed 都不命中时，结构仍然 `pass`，但能力结论必须是 not reproduced。
- v492 source 异常时，报告必须 fail，`--require-pass` 场景可返回非零。
- JSON/CSV/text/Markdown/HTML 必须全部写出。

这些测试保护的是证据边界：训练成功不等于稳定能力，单次命中也不等于跨 seed 可复现。

## 证据角色

- JSON 是后续 small-group curriculum 可以消费的主证据。
- CSV 用于查看 15 个 seed run 的逐行结果。
- HTML 和截图用于人工复核 term-level 稳定性。
- `one-term-seed-corpora/` 保存每次训练输入。
- `one-term-seed-runs/` 保存 15 个 checkpoint/tokenizer/metrics/config。

## 一句话总结

v493 把 required-term 路线从“单目标偶发命中”推进为“部分单目标词跨 seed 稳定命中”，为下一步 small-group 多目标干扰测试提供了更可靠的起点。
