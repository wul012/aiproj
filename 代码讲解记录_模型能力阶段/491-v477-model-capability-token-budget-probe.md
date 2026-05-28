# v477：model capability token budget probe

## 本版目标和边界

v477 的目标是验证 v476 的下一步假设：如果 prompt-level stall 主要来自短输出和 task shape，那么把 `case-token-cap` 从 `4` 提高到 `12`，应该能减少 token/shape 相关阻塞。

本版不做大模型训练，不增加模型层数，不引入外部数据，也不宣称模型能力已经提升。它只比较两个 token budget 下的 tiny capability ladder 和 stall diagnostic，判断评估阻塞是否被释放。

## 前置能力

本版复用三条前置链路：

- v474 的 `model_capability_ladder`
  - 负责跑同 seed 的 `max_iters=1,4` tiny ladder。
- v476 的 `model_capability_stall_diagnostic`
  - 负责把每个 ladder 首尾 rung 拆到 prompt 级失败原因。
- v475 的 CPU 单线程 runner 经验
  - token budget probe 调用 ladder 时继续设置 OpenMP/BLAS 单线程环境，避免 tiny PyTorch smoke 被线程调度拖慢。

## 关键新增文件

- `src/minigpt/model_capability_token_budget_probe.py`
  - 核心比较逻辑。
  - 解析 token cap，读取多个 stall diagnostic，计算 token stall、persistent fail、score improved、pass transition 等 delta。
- `src/minigpt/model_capability_token_budget_probe_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
  - HTML 用于 Playwright 截图，CSV 用于表格化比较。
- `scripts/run_model_capability_token_budget_probe.py`
  - CLI 入口。
  - 对每个 token cap 调用 `scripts/run_model_capability_ladder.py`，再生成 single-seed stability sidecar 和 stall diagnostic，最后写总 probe 报告。
- `tests/test_model_capability_token_budget_probe.py`
  - 覆盖 token relief、still blocked、persistent fail relief、输入校验和 artifact 输出。

## 核心数据结构

最终报告是：

```text
model_capability_token_budget_probe.json
```

关键字段：

- `rows`
  - 每个 token cap 一行。
  - 记录 `case_token_cap`、`token_budget_or_shape_limit_count`、`persistent_fail_count`、`score_improved_count`、`pass_transition_count` 和 `summary_decision`。
- `summary`
  - 比较最小 token cap 和最大 token cap。
  - `token_budget_or_shape_limit_delta` 表示 token/shape stall 是否减少。
  - `persistent_fail_count_delta` 表示持续 fail case 是否减少。
  - `score_improved_count_delta` 和 `pass_transition_count_delta` 用于避免把“评估形态释放”误说成“能力分提升”。
- `interpretation`
  - 继续固定 `model_quality_claim=not_claimed`。
  - 给出下一步建议：先跨 seed 复核长 token probe，再考虑更大训练预算。

## v477 真实运行结果

真实命令使用：

```text
seed=1337
max_iters=1,4
case-token-cap=4,12
model: n_layer=1, n_head=1, n_embd=8
device=cpu
```

结果：

```text
token_budget_or_shape_limit_delta=-9.0
persistent_fail_count_delta=-9.0
score_improved_count_delta=0.0
pass_transition_count_delta=0.0
avg_score_delta_change=0.0
```

这说明 cap 12 明显释放了短输出造成的评估形态阻塞：token/shape stall 从 10 降到 1，persistent fail 从 10 降到 1。但首尾 ladder 的 rubric 分数仍没有提升，所以这不是模型能力提升证据。

## 测试覆盖

新增测试覆盖：

- token stall 减少时，summary 决策必须是 `longer_token_budget_reduces_eval_stall`。
- token stall 不变时，summary 决策必须是 `longer_token_budget_still_blocked`。
- 即使 token stall 不变，只要 persistent fail 显著减少，也应视为评估阻塞释放。
- token caps 必须非空、正数、唯一，并按升序比较。
- JSON/CSV/text/Markdown/HTML 五类输出必须全部生成。

## 运行证据

运行证据位于：

```text
e/477/解释/model-capability-token-budget-probe/
e/477/图片/01-model-capability-token-budget-probe.png
e/477/解释/playwright-model-capability-token-budget-probe-snapshot.md
```

每个 token cap 下保留完整 ladder 和 stall diagnostic，方便向下追溯具体 prompt 的变化。

## 一句话总结

v477 把 v476 的“短输出可能卡住评估”变成了真实对比证据：长 token budget 确实减少阻塞，但模型能力是否提升仍需跨 seed 和更强训练信号继续验证。
