# v837：bounded objective seed

## 本版目标和边界

v837 的目标是把 v836 的 bounded objective contract 转成训练可用的 direct seed corpus。v836 只是定义了契约和 seed blueprint；v837 才真正输出 seed examples、JSONL 和 corpus TXT。

本版不训练、不跑 replay、不声明模型能力提升。它只做一件事：生成干净的、直接的、无 carry-forward 污染的 objective seed。

## 前置链路

输入来自 v836：

- `bounded_objective_contract_ready=True`
- `contract_id=bounded_fixed_loss_direct_completion_contract`
- `target_terms=fixed/loss`
- `contract_case_count=3`
- `planned_seed_example_count=18`
- `proposed_next_artifact=model_capability_route_promotion_bounded_objective_seed`

这保证 v837 的 seed 数量、来源 case 和下一步训练路线都来自 contract，而不是临时发挥。

## 关键文件

- `src/minigpt/model_capability_route_promotion_bounded_objective_seed.py`
  - 读取 v836 contract，生成 seed examples、corpus text、summary 和校验结果。
- `src/minigpt/model_capability_route_promotion_bounded_objective_seed_artifacts.py`
  - 输出 JSON、CSV、JSONL、corpus TXT、TXT、Markdown 和 HTML。
- `scripts/build_model_capability_route_promotion_bounded_objective_seed.py`
  - CLI 入口，支持目录输入、`--require-seed-ready` 和 `--force`。
- `tests/test_model_capability_route_promotion_bounded_objective_seed.py`
  - 覆盖正常 seed、next artifact 漂移、blueprint count 漂移、输出和 CLI。
- `e/837/解释/model-capability-route-promotion-bounded-objective-seed/`
  - 保存真实 seed/corpus 产物。
- `e/837/图片/v837-bounded-objective-seed-html.png`
  - Playwright MCP 截图。

## 核心结构

`seed_examples` 是本版核心输出。每条样本包含：

```text
example_id
case_id
example_mode
prompt
completion
text
required_terms
direct_completion=True
guardrail=bounded_objective_contract_direct_seed
```

生成规则很保守：

- 3 个 contract cases。
- 每个 case 6 条。
- 总计 18 条。
- completion 全部是 `fixed loss`。
- 所有文本都包含 `fixed` 和 `loss`。
- `carry_forward_example_count=0`。

`corpus_text` 是训练脚本最可能消费的产物，它由 18 条 `text` 用空行连接而成，并单独输出到：

```text
model_capability_route_promotion_bounded_objective_seed_corpus.txt
```

## 校验逻辑

builder 会检查：

- v836 contract 必须 pass。
- `bounded_objective_contract_ready` 必须为 True。
- next artifact 必须指向 objective seed。
- target terms 必须仍是 `fixed/loss`。
- contract case count 必须和 summary 一致。
- seed examples 数量必须等于 blueprint 的 18。
- 所有 examples 都是 direct completion。
- example mode 里不能出现 carry。
- 每条 text 都必须包含 `fixed/loss`。

这些检查保护了本版最重要的边界：seed 是直接目标样本，不是之前失败路线里的 carry-forward 或 forced-prefix 变体。

## 测试覆盖

聚焦测试覆盖：

- ready contract 生成 18 条 direct examples。
- contract 指向别的 next artifact 时失败。
- blueprint planned count 被改掉时失败。
- artifact writer 和 CLI 能输出全部格式，包括 JSONL 和 corpus TXT。

本版聚焦测试结果是 `4 passed`。

## 运行证据

真实命令：

```text
python scripts/build_model_capability_route_promotion_bounded_objective_seed.py --objective-contract e/836/解释/model-capability-route-promotion-bounded-objective-contract --out-dir e/837/解释/model-capability-route-promotion-bounded-objective-seed --require-seed-ready --force
```

关键输出：

```text
status=pass
example_count=18
direct_example_count=18
carry_forward_example_count=0
model_quality_claim=seed_only
```

HTML 截图保存到 `e/837/图片/v837-bounded-objective-seed-html.png`。

## 一句话总结

v837 把 bounded objective contract 落成了干净的 direct-only training corpus，为 v838 的 controlled training 提供了可复核输入。
