# v836：bounded objective contract

## 本版目标和边界

v836 的目标是把 v835 的 objective intervention plan 进一步压实成一个 contract artifact。v835 只是计划“下一步要先定义目标契约”，v836 则把这个契约写成后续模块可以直接读取的 JSON、CSV、Markdown 和 HTML。

本版不训练、不生成 checkpoint，也不说模型能力提升。它只定义一个 bounded direct-completion objective，并明确哪些训练样本和评估面不能被当作 promotion 证据。

## 前置链路

输入来自 v835：

- `objective_intervention_plan_ready=True`
- `contract_id=bounded_fixed_loss_direct_completion_contract`
- `target_terms=fixed/loss`
- `canonical_completion=fixed loss`
- `unchanged_suite_check_required=True`
- `proposed_next_artifact=model_capability_route_promotion_bounded_objective_contract`

这保证 v836 不是另起炉灶，而是严格接住 v835 计划指定的下一步。

## 关键文件

- `src/minigpt/model_capability_route_promotion_bounded_objective_contract.py`
  - 负责读取 v835 plan、校验契约字段、生成 contract cases、seed blueprint 和 holdout rule。
- `src/minigpt/model_capability_route_promotion_bounded_objective_contract_artifacts.py`
  - 负责渲染 JSON、CSV、TXT、Markdown、HTML。
- `scripts/build_model_capability_route_promotion_bounded_objective_contract.py`
  - CLI 入口，支持目录输入、`--require-contract-ready` 和 `--force`。
- `tests/test_model_capability_route_promotion_bounded_objective_contract.py`
  - 覆盖 ready contract、错误 next artifact、篡改 completion、输出和 CLI 接线。
- `e/836/解释/model-capability-route-promotion-bounded-objective-contract/`
  - 保存真实 v836 contract 产物。
- `e/836/图片/v836-bounded-objective-contract-html.png`
  - Playwright MCP 截取的浏览器证据。

## 核心结构

`objective_contract` 规范化后包含：

```text
contract_id=bounded_fixed_loss_direct_completion_contract
target_terms=fixed, loss
canonical_prompt=Answer with exactly two tokens: fixed loss\nanswer:
canonical_completion=fixed loss
required_exact_completion=fixed loss
expected_token_count=2
promotion_claim_allowed=False
```

这里有两个关键约束：

1. `canonical_completion` 必须仍是 `fixed loss`。如果源 plan 被改成 `fixed`，测试会失败。
2. `promotion_claim_allowed=False`。契约只定义训练目标，不证明模型变强。

`contract_cases` 有 3 个：

- `canonical_direct_completion`
- `minimal_direct_completion`
- `completion_label_surface`

这些 case 不是最终 benchmark，而是给 v837 seed builder 的直接目标面。

`seed_blueprint` 固定下一版计划生成 18 条样本：

```text
source_contract_case_count=3
examples_per_case=6
planned_example_count=18
next_artifact=model_capability_route_promotion_bounded_objective_seed
```

这让 v837 不再随意扩样本，而是按 contract 生成一个小而干净的 direct objective seed。

## 校验逻辑

builder 会检查：

- v835 plan 必须是 pass。
- `objective_intervention_plan_ready` 必须为 True。
- next artifact 必须指向 objective contract。
- contract id 必须匹配。
- target terms 必须精确等于 `fixed/loss`。
- canonical completion 必须精确等于 `fixed loss`。
- canonical surface 必须允许。
- forced-prefix 和 more-epoch rescue surface 必须被阻断。
- unchanged v803 holdout 必须保留。
- plan 中必须包含 `direct_seed_corpus` 和 `dual_replay` 工作项。

这些检查把“先定义契约，再做 seed，再训练，再 dual replay”的顺序固定下来。

## 测试覆盖

聚焦测试覆盖四个风险：

- ready plan 可以生成 contract，且 `planned_seed_example_count=18`。
- 如果 plan 指向别的 next artifact，contract 失败。
- 如果 canonical completion 被篡改，contract 失败。
- artifact writer 和 CLI 都能输出 JSON、CSV、TXT、Markdown、HTML。

本版聚焦测试结果是 `4 passed`。

## 运行证据

真实命令：

```text
python scripts/build_model_capability_route_promotion_bounded_objective_contract.py --objective-intervention-plan e/835/解释/model-capability-route-promotion-bounded-objective-intervention-plan --out-dir e/836/解释/model-capability-route-promotion-bounded-objective-contract --require-contract-ready --force
```

关键输出：

```text
status=pass
decision=model_capability_route_promotion_bounded_objective_contract_ready
contract_case_count=3
planned_seed_example_count=18
model_quality_claim=contract_only
```

Playwright MCP 截图保存到 `e/836/图片/v836-bounded-objective-contract-html.png`。

## 一句话总结

v836 把 v835 的计划变成了可消费的 bounded objective contract，为 v837 生成干净 direct seed 做好边界约束。
