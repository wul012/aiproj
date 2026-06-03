# v827：decoder-anchor failure diagnostic

## 本版目标和边界

v827 的目标是解释 v826 的失败：为什么 v825 使用 decoder-anchor corpus 训练后，bounded replay 仍然是 0/5。

这版不继续训练，也不调整 benchmark。它只读取已经存在的真实证据，做失败形态诊断。这样可以避免在没有理解失败原因时继续堆训练版本。

## 前置链路

- v824：生成 48 条 decoder-anchor seed examples。
- v825：用这份 corpus 训练出真实 checkpoint。
- v826：用同一套 bounded replay 复核，结果仍然 0/5。

v827 接在 v826 的 next step 后面，先诊断 replay failure。

## 关键文件

`src/minigpt/model_capability_route_promotion_bounded_real_replay_decoder_anchor_failure_diagnostic.py`

核心 builder。它读取 decoder-anchor replay、三方 comparison、seed revision、training run 和 corpus，生成 case-level diagnostic 和 root causes。

关键输出：

- `case_diagnostics`：每个 replay case 的 prompt/corpus 覆盖、zero-hit、fragment-like、missed terms 和推荐动作。
- `root_causes`：本版聚合出的根因列表。
- `diagnostic`：核心统计，例如 failed/zero-hit/fragment-like/root-cause count。
- `summary`：供 README、HTML 和 text 输出消费。

`src/minigpt/model_capability_route_promotion_bounded_real_replay_decoder_anchor_failure_diagnostic_artifacts.py`

产物层。它输出 JSON、CSV、text、Markdown 和 HTML。CSV 是 case-level 诊断表，HTML 用于截图归档。

`scripts/diagnose_model_capability_route_promotion_bounded_real_replay_decoder_anchor_failure.py`

CLI 入口。它显式接收五个输入：replay、comparison、seed、training run、corpus。这样诊断报告可复现，不依赖隐式路径。

`tests/test_model_capability_route_promotion_bounded_real_replay_decoder_anchor_failure_diagnostic.py`

测试覆盖 ready 诊断、comparison 不 ready 时失败、locator/CLI/artifact 输出连通。

## 核心诊断逻辑

每个 replay row 会被转换成一条 case diagnostic：

- `prompt_in_seed`：原 prompt 是否出现在 seed example 文本中。
- `prompt_in_corpus`：原 prompt 是否出现在训练 corpus 中。
- `zero_hit`：是否完全没有命中 expected terms。
- `fragment_like_generation`：生成是否是碎片化字符输出。
- `term_seed_count` / `term_corpus_count`：required terms 在 seed/corpus 中出现次数。
- `diagnosis`：单 case 诊断类型。
- `recommended_action`：建议下一步动作。

root cause 聚合会检查：

- bridge/direct 样本存在但 replay 仍 zero-hit。
- required terms 完全没命中。
- 生成被 fragment-like 输出主导。
- loss 下降没有转化为 bounded replay。

## 真实运行命令

```powershell
python -B scripts\diagnose_model_capability_route_promotion_bounded_real_replay_decoder_anchor_failure.py `
  --decoder-anchor-replay e\826\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-checkpoint-comparison\decoder-anchor-replay `
  --comparison e\826\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-checkpoint-comparison `
  --decoder-anchor-seed e\824\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-seed-revision `
  --training-run e\825\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-training-run `
  --corpus e\824\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-seed-revision\model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_corpus.txt `
  --out-dir e\827\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-failure-diagnostic `
  --require-diagnostic-ready `
  --force
```

## 真实结果

- `status=pass`
- `failed_case_count=5`
- `zero_hit_case_count=5`
- `fragment_like_case_count=5`
- `root_cause_count=4`
- `next_step=audit_decoder_anchor_training_distribution_before_more_training`

这说明 decoder-anchor corpus 虽然存在，但模型在 bounded prompt 上仍然没有稳定解码出 required terms。

## 测试覆盖

focused tests：

- 构造包含 prompt/corpus 和 fragment-like replay 的样例，确认能生成 ready diagnostic。
- comparison 为 fail 时，diagnostic 失败并返回非零。
- CLI、locator、JSON/CSV/text/Markdown/HTML 输出全部连通。

## 运行证据

- 诊断报告：`e/827/解释/model-capability-route-promotion-bounded-real-replay-decoder-anchor-failure-diagnostic/`
- 截图：`e/827/图片/v827-bounded-real-replay-decoder-anchor-failure-diagnostic-html.png`

## 一句话总结

v827 把 decoder-anchor 训练失败从“0/5 的坏结果”细化成“5 个 zero-hit、5 个 fragment-like、4 类根因”，为下一步训练分布审计提供明确入口。
