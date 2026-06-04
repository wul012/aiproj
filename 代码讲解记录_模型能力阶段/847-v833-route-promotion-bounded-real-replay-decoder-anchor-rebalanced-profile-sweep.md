# v833：decoder-anchor rebalanced profile sweep

## 本版目标和边界

v833 的目标是回答一个很具体的问题：v830 rebalanced checkpoint 的 `0/5` bounded replay，是不是默认解码参数导致的。v832 已经说明训练数据分布修过了，但生成仍然 zero-hit、fragment-like；所以这版在继续训练之前，先跑真实 decoder profile sweep。

这版不训练新模型，不修改 v803 benchmark，不修改 expected terms，也不把 forced prefix 或 constrained decoding 当作能力证明。它只在同一个 checkpoint 上切换 `max_new_tokens`、`temperature`、`top_k`，观察是否能自然恢复 required-term generation。

## 前置链路

- v829：修复 decoder-anchor seed 分布，降低 carry-forward，提高 direct-answer。
- v830：用 rebalanced corpus 训练出真实 checkpoint。
- v831：rebalanced checkpoint replay 仍然 `0/5`。
- v832：确认失败不是单纯数据分布未修，而是分布已修后仍然 zero-hit、fragment-like。

v833 接住 v832 的 `run_rebalanced_decoder_profile_sweep_before_more_training`。

## 关键文件

`src/minigpt/model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep.py`

核心 builder。它读取 suite review、benchmark suite、dry-run scorer、failure diagnostic 和真实 checkpoint，然后对同一套 bounded case 应用多个 decoder profile。

关键字段：

- `profiles`：本次执行的解码 profile 列表，包括 profile id、token 数、temperature 和 top-k。
- `profile_rows`：profile 级汇总，记录每个 profile 的 passed count、pass rate、zero-hit count、fragment-like count 和 any-hit count。
- `case_profile_rows`：case x profile 的明细，记录 hit/missed terms、是否 zero-hit、是否 fragment-like、continuation preview。
- `sweep`：选择 best profile，并计算是否恢复、是否 promotable、下一步。
- `summary`：README、CLI 和后续版本消费的扁平摘要。
- `interpretation`：明确本版的 `model_quality_claim`。

默认 profile 有 5 个：

- `default_bounded`：复现原 bounded replay 设置。
- `greedy_short`：近似 greedy 的短输出。
- `greedy_long`：近似 greedy 的长输出。
- `longer_low_temp`：更长但仍低温。
- `wider_rescue`：更宽 top-k 的 rescue 尝试。

`src/minigpt/model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_artifacts.py`

产物层。输出 JSON、CSV、text、Markdown 和 HTML。CSV 保存 case x profile 明细，HTML 展示 profile 表、case profile rows 和输入检查，用于运行截图。

`scripts/sweep_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profiles.py`

CLI 入口。显式接收 benchmark suite、suite review、dry-run、failure diagnostic、checkpoint 和 tokenizer。`--require-sweep-ready` 只要求输入和执行通过；`--require-recovery`、`--require-promotion` 才会把模型恢复当成退出码要求。

`tests/test_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep.py`

测试覆盖三种模型结果：无恢复、部分恢复、可推广 profile。同时用 mock 连接 CLI，避免单测加载伪 checkpoint。

## 核心运行流程

builder 首先检查 v832 diagnostic 是否真的请求 profile sweep，然后逐个 profile 复制 benchmark suite 的 case，并覆盖每个 `prompt_case` 的解码参数。

每个 profile 都复用现有 `build_model_capability_route_promotion_bounded_real_replay` 执行真实 replay。这样 v833 不重新实现 checkpoint 加载、prompt 执行和 required-term scoring，只在外层做 profile 维度的编排和汇总。

真实运行时使用缓存的 `MiniGPTGenerator`，避免同一个 checkpoint 在同一轮 sweep 里反复加载。测试时可以传入 fake `generator_runner`，所以单测能够验证 contract，而真实推理留给版本证据命令。

## 真实运行命令

```powershell
python scripts\sweep_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profiles.py `
  --benchmark-suite e\803\解释\model-capability-route-promotion-bounded-benchmark-suite `
  --suite-review e\804\解释\model-capability-route-promotion-bounded-benchmark-suite-review `
  --dry-run e\805\解释\model-capability-route-promotion-bounded-benchmark-dry-run `
  --failure-diagnostic e\832\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-failure-diagnostic `
  --checkpoint e\830\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-training-run\run\checkpoint.pt `
  --tokenizer e\830\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-training-run\run\tokenizer.json `
  --out-dir e\833\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-profile-sweep `
  --require-sweep-ready `
  --force
```

## 真实结果

- `status=pass`
- `decision=model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_no_recovery`
- `profile_count=5`
- `case_count=5`
- `best_profile_id=greedy_short`
- `best_passed_case_count=0`
- `best_any_hit_case_count=0`
- `any_profile_recovered=False`
- `promotion_ready=False`
- `next_step=route_to_objective_or_architecture_intervention`

这说明 v830 checkpoint 不是靠调长输出、降低温度、近似 greedy 或放宽 top-k 就能恢复 bounded required terms。

## 测试覆盖

focused tests：

- 无恢复路径：所有 profile 都 zero-hit，decision 为 no recovery，`--require-recovery` 会失败。
- 部分恢复路径：某个 profile 比默认多通过一个 case，但 promotion 仍为 false。
- 可推广路径：某个 profile 全部通过时，promotion gate 可以通过。
- failure diagnostic 不指向 profile sweep 时，报告 fail。
- CLI、locator、JSON/CSV/text/Markdown/HTML 输出全部连通。

## 运行证据

- sweep 报告：`e/833/解释/model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-profile-sweep/`
- 截图：`e/833/图片/v833-bounded-real-replay-decoder-anchor-rebalanced-profile-sweep-html.png`

## 一句话总结

v833 证明 decoder profile rescue 已经跑到尽头，rebalanced route 的下一步应从采样调参转向目标或模型训练结构干预。
