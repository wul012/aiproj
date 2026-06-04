# v846：bounded objective unassisted repair seed

## 本版目标和边界

v846 的目标是把 v845 的 unassisted repair plan 变成实际 seed/corpus。

边界：

- 不训练模型。
- 不运行 replay。
- 不使用 decoder anchor。
- 不宣称模型能力提升。

这版只负责把“下一步要训练什么”落成可复核数据。

## 前置链路

输入来自两处：

- v845 unassisted repair plan：确认 assisted anchor path 已关闭，下一步是 seed。
- v836 objective contract：提供目标 terms 和 contract cases。

v846 同时校验：

```text
bounded_objective_unassisted_repair_plan_ready=True
proposed_next_artifact=model_capability_route_promotion_bounded_objective_unassisted_repair_seed
bounded_objective_contract_ready=True
target_terms=["fixed", "loss"]
```

## 关键新增文件

- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_seed.py`
  - 构造 seed examples、corpus text、checks、summary 和 interpretation。
- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_seed_artifacts.py`
  - 输出 JSON、CSV、JSONL、corpus TXT、TXT、Markdown、HTML。
- `scripts/build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed.py`
  - CLI 入口，支持 repair plan、objective contract 和 `--require-seed-ready`。
- `tests/test_model_capability_route_promotion_bounded_objective_unassisted_repair_seed.py`
  - 覆盖 neutral prompt、无 decoder anchors、计划指向错误时失败、输出和 CLI。
- `e/846/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed/`
  - 保存真实 seed 产物。
- `e/846/图片/v846-bounded-objective-unassisted-repair-seed-html.png`
  - Playwright MCP 截图。

## Seed 设计

每个 contract case 生成 8 条样本：

- 4 条 `contract_prompt_unassisted_completion`
- 4 条 `neutral_prompt_unassisted_completion`

其中 neutral prompt 不包含 `fixed/loss`，只在 completion 中出现目标答案。这是 v846 和 v837 direct seed 的关键差别。

每条 example 包含：

```text
example_id
case_id
example_mode
prompt
completion
text
required_terms
prompt_contains_target_terms
decoder_anchor_used
direct_completion
guardrail
```

`decoder_anchor_used` 固定为 `False`。

## 真实结果

```text
status=pass
decision=model_capability_route_promotion_bounded_objective_unassisted_repair_seed_ready
bounded_objective_unassisted_repair_seed_ready=True
example_count=24
neutral_prompt_example_count=12
decoder_anchor_example_count=0
corpus_char_count=1778
model_quality_claim=seed_only
next_action=train_bounded_objective_unassisted_repair_seed
```

## 测试覆盖

测试覆盖：

- 生成 neutral prompts 和 0 decoder anchors。
- plan 指向错误时失败。
- artifact writer 和 CLI 输出完整。

focused pytest：

```text
3 passed
```

## 运行证据

真实命令：

```text
python scripts/build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed.py --repair-plan e/845/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-plan --objective-contract e/836/解释/model-capability-route-promotion-bounded-objective-contract --out-dir e/846/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed --require-seed-ready --force
```

HTML 截图：

```text
e/846/图片/v846-bounded-objective-unassisted-repair-seed-html.png
```

## 一句话总结

v846 把无锚点修复路线落成 24 条可训练样本，其中 12 条 neutral prompt 不暴露目标词，为下一版真实训练提供数据基础。
