# v828：decoder-anchor distribution audit

## 本版目标和边界

v828 的目标是把 v827 的失败诊断往训练数据分布上落一层：v825 训练出来的 checkpoint 在 v826 replay 中仍然 0/5，v827 又确认 5 个 case 都是 zero-hit 和 fragment-like 输出，所以这版先审计 v824 seed/corpus 的分布。

这版不训练新 checkpoint，不修改 bounded benchmark，也不声称模型能力提升。它只判断“继续训练前是否需要先重配 decoder-anchor seed”。

## 前置链路

- v824：生成 48 条 decoder-anchor seed revision，并写出训练 corpus。
- v825：用 v824 corpus 训练真实 checkpoint。
- v826：对 v825 checkpoint 做 bounded replay 与历史对比，结果仍然是 `0/5`。
- v827：诊断失败形态，确认所有 case 都 zero-hit，下一步指向训练分布审计。

v828 接住 v827 的 `audit_decoder_anchor_training_distribution_before_more_training`，把“失败原因可能在训练分布”变成可复核指标。

## 关键文件

`src/minigpt/model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit.py`

核心 builder。它读取 seed revision、failure diagnostic 和 corpus，输出 bucket、revision type、case distribution、risk rows 和 summary。

关键字段：

- `bucket_rows`：按 `carry_forward`、`direct_answer`、`decoder_bridge`、`other` 聚合样本数量、占比和平均长度。
- `revision_rows`：按原始 `revision_type` 聚合，保留 seed 修订来源。
- `case_rows`：按 bounded case 聚合 carry/direct/bridge 样本数。
- `risk_rows`：把分布阈值和 v827 zero-hit 诊断转成具体风险。
- `distribution_audit`：记录 ready、样本数、corpus 字符数、关键占比、是否需要 rebalanced seed。
- `interpretation`：明确模型质量结论仍是 `not_improved`。

`src/minigpt/model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit_artifacts.py`

产物层。它把 audit report 写成 JSON、CSV、text、Markdown 和 HTML。CSV 是 bucket 分布表，HTML 用于 Playwright 截图和人工复核。

`scripts/audit_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution.py`

CLI 入口。它显式接收：

- `--decoder-anchor-seed`
- `--failure-diagnostic`
- `--corpus`
- `--out-dir`
- `--require-audit-ready`
- `--force`

目录输入会通过 locator 自动解析到对应 JSON 文件，避免调用者手写长文件名。

`tests/test_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit.py`

测试覆盖 ready audit、缺 seed examples 的失败路径、locator、CLI 和 artifact 输出连通。

## 核心逻辑

`_bucket()` 根据 `revision_type` 把样本分到四类：

- `unanchored_direct_answer` -> `direct_answer`
- `*_bridge` 或 `prefix_*` -> `decoder_bridge`
- `carry_forward*` -> `carry_forward`
- 其他 -> `other`

`_risks()` 采用轻量阈值：

- direct-answer share `< 0.2`：说明直接答案太稀疏。
- carry-forward share `> 0.5`：说明旧样本主导新 corpus。
- bridge share `< 0.25`：说明 forced-prefix bridge 太少。
- v827 zero-hit count 等于 case count：说明所有 replay case 都没有命中 required terms。

真实 v828 中 bridge share 是 `0.3125`，所以 bridge 不触发风险；触发的是 direct 太少、carry-forward 太多、全 case zero-hit。

## 真实运行命令

```powershell
python -B scripts\audit_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution.py `
  --decoder-anchor-seed e\824\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-seed-revision `
  --failure-diagnostic e\827\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-failure-diagnostic `
  --corpus e\824\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-seed-revision\model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_corpus.txt `
  --out-dir e\828\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-distribution-audit `
  --require-audit-ready `
  --force
```

## 真实结果

- `status=pass`
- `decision=model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_needs_rebalance`
- `example_count=48`
- `corpus_chars=3431`
- `case_count=5`
- `revision_type_count=5`
- `carry_forward_share=0.5833`
- `direct_answer_share=0.1042`
- `decoder_bridge_share=0.3125`
- `zero_hit_case_count=5`
- `risk_count=3`
- `rebalanced_seed_needed=True`
- `next_step=build_decoder_anchor_rebalanced_seed_revision`

这说明 v824 corpus 不是完全缺 bridge，而是 direct-answer 太少且旧 carry-forward 样本过重。下一步应构造 rebalanced seed revision，而不是直接把 v825 的训练步数拉长。

## 测试覆盖

focused tests：

- 构造 carry/direct/bridge 混合 seed 和 zero-hit diagnostic，确认 audit ready 且需要 rebalance。
- 删除 seed examples 后，确认 `seed_examples_present` 失败，`--require-audit-ready` 会返回非零。
- 验证 seed/diagnostic locator、CLI、JSON/CSV/text/Markdown/HTML 输出全部连通。

## 运行证据

- 审计报告：`e/828/解释/model-capability-route-promotion-bounded-real-replay-decoder-anchor-distribution-audit/`
- 截图：`e/828/图片/v828-bounded-real-replay-decoder-anchor-distribution-audit-html.png`

## 一句话总结

v828 把 decoder-anchor 路线的下一步从“继续训练试试看”收束成“先按 direct/carry-forward/zero-hit 风险重配 seed”，让后续 v829 的训练数据修复有了可复核依据。
