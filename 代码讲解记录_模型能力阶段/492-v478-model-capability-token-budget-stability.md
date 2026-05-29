# v478：model capability token budget stability

## 本版目标和边界

v478 的目标是复核 v477 的单 seed 发现是否稳定。v477 已经证明在 seed `1337` 下把 `case-token-cap` 从 `4` 提到 `12` 会减少 token/shape stall，但这个结果还不能直接指导后续训练预算。本版把同一套 token-budget probe 复制到 seeds `1337` 和 `2026`，再汇总成稳定性报告。

本版不扩大模型，不新增训练数据，不改变 scorecard 规则，也不声明 MiniGPT 的语言能力已经提高。它只验证：cap 12 对评估形态阻塞的释放是否跨 seed 重复出现。

## 前置能力

本版承接 v477 的 `model_capability_token_budget_probe`：

- 每个 seed 内仍然运行 `case-token-cap=4,12`。
- 每个 token cap 仍然先跑 v474 的 tiny ladder，再走 v476 的 stall diagnostic。
- v478 只在外层增加 seed 维度汇总，不改动内部 ladder、diagnostic 和 probe 的默认语义。

这个设计让 v478 成为复核层，而不是一条新的治理链。

## 关键新增文件

- `src/minigpt/model_capability_token_budget_stability.py`
  - 核心汇总逻辑。
  - 从多个 v477 probe JSON 中提取 seed、token budget delta、persistent fail delta、score/pass delta。
  - 生成 `stability_summary`，判断 token-budget relief 是否在所有成功 seed 中重复出现。
- `src/minigpt/model_capability_token_budget_stability_artifacts.py`
  - 负责 JSON/CSV/text/Markdown/HTML 输出。
  - HTML 作为浏览器截图证据，CSV 作为 seed 级表格证据，text 作为 CLI 摘要证据。
- `scripts/run_model_capability_token_budget_stability.py`
  - CLI 入口。
  - 对每个 seed 调用 `scripts/run_model_capability_token_budget_probe.py`，读取对应的 `model_capability_token_budget_probe.json`，再写稳定性总报告。
  - 继续设置 OpenMP/BLAS 单线程环境，避免 tiny PyTorch smoke 被线程调度放大耗时。
- `tests/test_model_capability_token_budget_stability.py`
  - 覆盖 repeated relief、score/pass progress、缺字段失败、artifact 输出和 CPU 线程环境。

## 核心数据结构

最终报告是：

```text
model_capability_token_budget_stability.json
```

关键字段：

- `rows`
  - 每个 seed 一行。
  - 记录 `token_budget_or_shape_limit_delta`、`persistent_fail_count_delta`、`score_improved_count_delta`、`pass_transition_count_delta` 和源 probe 路径。
- `stability_summary`
  - `token_relief_seed_count`：多少个成功 seed 出现 token/shape stall 下降。
  - `persistent_fail_relief_seed_count`：多少个成功 seed 出现 persistent fail 下降。
  - `score_or_pass_progress_seed_count`：多少个 seed 出现 score 或 pass transition 进展。
  - `mean_token_budget_or_shape_limit_delta`：跨 seed 平均 token/shape stall delta。
  - `decision`：本版最核心的稳定性判断。
- `interpretation`
  - 继续固定 `model_quality_claim=not_claimed`。
  - 把下一步建议限定为“保留 cap 12 评估预算，并先检查数据/rubric”，而不是立刻扩模型。

## v478 真实运行结果

真实配置：

```text
seeds=1337,2026
case-token-cap=4,12
max_iters=1,4
model: n_layer=1, n_head=1, n_embd=8
device=cpu
```

结果：

```text
stability_decision=repeated_token_budget_relief_without_score_progress
token_relief_seed_count=2
persistent_fail_relief_seed_count=2
score_or_pass_progress_seed_count=0
mean_token_budget_or_shape_limit_delta=-9.0
mean_persistent_fail_count_delta=-9.0
mean_score_improved_count_delta=0.0
mean_pass_transition_count_delta=0.0
```

两个 seed 都复现了 `-9.0` 的 token/shape stall delta 和 persistent fail delta，说明 cap 12 释放评估阻塞的现象比较稳定。但 score/pass 仍然没有动，所以本版仍不支持模型能力提升声明。

## 测试覆盖

新增测试保护了四类边界：

- 两个成功 seed 都出现 token relief 时，必须输出 `repeated_token_budget_relief_without_score_progress`。
- 如果任一 seed 出现 score 或 pass transition 进展，稳定性决策必须升级到 `repeated_token_budget_relief_with_some_score_progress`。
- 少于两个 seed、probe 命令失败、seed 状态失败或关键 delta 缺失时，报告必须失败。
- JSON/CSV/text/Markdown/HTML 五类输出必须全部生成，且 HTML 中必须显示核心指标。

这些断言确保 v478 既能复核 v477，又不会把“评估预算问题被解除”误包装成“模型真实能力提高”。

## 运行证据

运行证据位于：

```text
e/478/解释/model-capability-token-budget-stability/
e/478/图片/01-model-capability-token-budget-stability.png
e/478/解释/playwright-model-capability-token-budget-stability-snapshot.md
```

每个 seed 的完整 v477 probe 也保留在：

```text
e/478/解释/model-capability-token-budget-stability/seeds/seed-1337/
e/478/解释/model-capability-token-budget-stability/seeds/seed-2026/
```

这些产物不是训练 checkpoint，也不是模型卡最终结论；它们是后续选择评估预算、检查数据和 rubric 的证据入口。

## 一句话总结

v478 证明 cap 12 对 token-budget stall 的释放在两个 seed 下稳定复现，但模型能力提升仍未出现，下一步应优先检查数据和评分信号，而不是盲目扩大模型。
