# v851：bounded objective unassisted repair seed revision

## 本版目标和边界

v851 的目标是把 v850 curriculum revision 变成新的 seed/corpus。

边界：

- 不训练模型。
- 不运行 replay。
- 不使用 decoder anchor。
- 不改变 v836 objective contract。

这版只产出下一轮训练的数据。

## 前置链路

输入：

```text
e/850/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-curriculum-revision/
e/836/解释/model-capability-route-promotion-bounded-objective-contract/
```

v850 指向：

```text
proposed_next_artifact=model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision
decoder_anchor_allowed=False
```

## 关键新增文件

- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision.py`
  - 读取 curriculum revision 和 objective contract，生成 seed examples、corpus、checks 和 summary。
- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_artifacts.py`
  - 输出 JSON、CSV、JSONL、corpus TXT、TXT、Markdown、HTML。
- `scripts/build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision.py`
  - CLI 入口。
- `tests/test_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision.py`
  - 覆盖正常 seed revision、anchor 允许时失败、writer/CLI。
- `e/851/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed-revision/`
  - 保存真实 revised seed。
- `e/851/图片/v851-bounded-objective-unassisted-repair-seed-revision-html.png`
  - Playwright MCP 截图。

## Seed Revision 设计

每个 contract case 生成 8 条样本：

```text
output_position_anchor_examples
neutral_prompt_exact_completion_repetition
fragment_contrast_examples
short_completion_repetition
```

其中 fragment contrast 会把 v849 观察到的 `los/wixed` 当成不完整片段，再要求输出完整 `fixed loss`。这不是 decoder anchor，因为它只存在训练文本中，不在生成阶段强制 prefix。

每条样本保留：

```text
decoder_anchor_used=False
direct_completion=True
guardrail=bounded_objective_unassisted_repair_seed_revision
```

## 真实结果

```text
status=pass
decision=model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_ready
example_count=24
neutral_prompt_example_count=18
decoder_anchor_example_count=0
corpus_char_count=2028
model_quality_claim=seed_revision_only
next_action=train_bounded_objective_unassisted_repair_seed_revision
```

## 测试覆盖

focused pytest 覆盖：

- 生成 revised seed 且无 decoder anchors。
- curriculum 允许 anchor 时失败。
- artifact writer 和 CLI 输出完整。

focused pytest：

```text
3 passed
```

全量回归：

```text
1731 passed
```

source encoding hygiene：

```text
status=pass
source_count=1264
syntax_error_count=0
```

## 运行证据

真实命令：

```text
python scripts/build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision.py --curriculum-revision e/850/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-curriculum-revision --objective-contract e/836/解释/model-capability-route-promotion-bounded-objective-contract --out-dir e/851/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed-revision --require-seed-ready --force
```

HTML 截图：

```text
e/851/图片/v851-bounded-objective-unassisted-repair-seed-revision-html.png
```

## 一句话总结

v851 把无锚点课程修订落成 revised corpus，为下一版真实训练提供新的数据基础。
