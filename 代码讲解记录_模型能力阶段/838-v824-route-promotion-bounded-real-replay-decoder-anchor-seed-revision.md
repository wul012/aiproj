# v824：decoder-anchor seed revision

## 本版目标和边界

v824 的目标是把 v821-v823 发现的 decoder-anchor 局部信号落回训练语料，而不是继续扩大手工 policy。前面 v823 已经证明 `objective-answer-check` 在 `fixed ` anchor 下能补出 `loss`，但这仍然是 anchor-assisted signal，不是 unassisted 模型能力。

所以本版只做一件事：读取 v817 prompt-aligned seed、v819 prompt-aligned replay、v823 policy replay，构造一份新的 seed revision。它明确不训练、不比较 checkpoint、不放开 promotion。

## 前置链路

- v817：构造 prompt-aligned seed，把 benchmark prompt 放进训练语料。
- v818：用 v817 语料训练出 prompt-aligned checkpoint。
- v819：发现 prompt-aligned checkpoint 在 bounded replay 上 0/5。
- v820：诊断失败不是语料缺 prompt，而是生成仍然碎片化、required term 零命中。
- v821：用 decoder-anchor probe 发现局部 forced-prefix 信号。
- v822：把局部信号收敛成 guarded policy。
- v823：真实 replay guarded policy，确认只有 1 个 case 的局部信号可复现，promotion 继续阻断。

v824 接在这里，把这个局部信号转成可训练数据，为 v825 的真实训练准备输入。

## 关键文件

`src/minigpt/model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision.py`

核心 builder。它负责定位三个输入报告，读取 JSON，校验上游状态，并生成统一 report。关键输出包括：

- `seed_examples`：最终训练样本列表。
- `check_rows`：输入契约检查。
- `decoder_anchor_seed_revision`：本版核心统计。
- `summary`：供 CLI、README、HTML 报告读取的摘要。
- `interpretation`：明确这只是 training data revision。

`src/minigpt/model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_artifacts.py`

产物层。它把同一份 report 写成 JSON、CSV、JSONL、corpus text、plain text、Markdown 和 HTML。JSON/JSONL/corpus 是后续训练消费入口，HTML 和 Markdown 是人工审阅证据。

`scripts/build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision.py`

CLI 入口。它接收三个上游目录或 JSON 文件：

```powershell
python -B scripts\build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision.py `
  --prompt-aligned-seed e\817\解释\model-capability-route-promotion-bounded-real-replay-prompt-aligned-seed-revision `
  --prompt-aligned-replay e\819\解释\model-capability-route-promotion-bounded-real-replay-prompt-aligned-checkpoint-replay\prompt-aligned-replay `
  --policy-replay e\823\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-policy-replay `
  --out-dir e\824\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-seed-revision `
  --require-seed-ready `
  --force
```

`tests/test_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision.py`

单测覆盖 ready 构造、policy replay signal 缺失时阻断，以及 CLI/locator/artifact 输出是否连通。

## 核心数据结构

每条新增样本都保持统一字段：

- `example_id`：可追踪样本来源和类型。
- `case_id`：对应 bounded replay case。
- `revision_type`：样本角色，例如 `unanchored_direct_answer`、`prefix_f_bridge`。
- `prompt`：训练 prompt。
- `completion`：期望补全。
- `text`：最终写入 corpus 的 prompt+completion。
- `required_terms`：本轮仍然锁定 `fixed/loss`。
- `guardrail`：说明这条样本为什么存在，防止后续误读。

v824 对每个 replay case 新增 4 条样本：

- 原 prompt 直接补 `fixed loss`。
- 原 prompt 加 `f` 后补 `ixed loss`。
- 原 prompt 加 `fixed ` 后补 `loss`。
- 原 prompt 加 `fixed l` 后补 `oss`。

真实运行时，v817 的 28 条样本被 carry forward，v819 的 5 个 case 每个新增 4 条，所以总数是 `28 + 20 = 48`。

## 检查逻辑

builder 的 `_checks` 会确认：

- prompt-aligned seed revision 是 `pass`。
- prompt-aligned replay 是 `pass`。
- policy replay 是 `pass`。
- v823 的 `policy_replay_success=True`，说明确实存在可复现局部 anchor signal。
- replay rows 非空。
- 所有 seed example 都有 `text`。

任一失败时，`status=fail`，`--require-seed-ready` 会让 CLI 返回非零退出码。

## 运行证据

真实 v824 输出：

- `status=pass`
- `decision=model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_ready`
- `example_count=48`
- `added_example_count=20`
- `bridge_example_count=15`
- `unanchored_direct_example_count=5`
- `next_step=train_decoder_anchor_seed_revision`

截图位于：

- `e/824/图片/v824-bounded-real-replay-decoder-anchor-seed-revision-html.png`

解释归档位于：

- `e/824/解释/说明.md`

## 测试覆盖

focused test 覆盖了三类风险：

- ready 路径会生成 1 条 carry-forward 样本和每个 replay case 的 4 条 anchor/direct 样本。
- 当 v823 policy replay 没有 `policy_replay_success=True` 时，v824 不会误生成 ready seed。
- locator、CLI、JSONL/corpus/HTML/Markdown 输出都能连通，且 corpus 中能看到 `fixed loss` 与 `ixed loss` 这类桥接补全。

## 一句话总结

v824 把 decoder-anchor 诊断信号从“人工 replay policy”推进成“下一轮真实训练可消费的 seed revision”，但模型能力结论仍然留给 v825 的训练和复核。
