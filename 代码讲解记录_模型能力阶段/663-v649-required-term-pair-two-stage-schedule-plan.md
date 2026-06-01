# v649 required-term pair two-stage schedule plan

## 本版目标和边界

v649 的目标是把 v648 关闭批次后提出的 `two_stage_surface_internal_schedule` 变成可执行前的计划契约。它解决的问题是：当前已经有一条路线能在自由生成里同时放出 `fixed/loss`，也有另一条路线在 forced-choice 内部评分里同时偏好 `fixed/loss`，但二者还没有出现在同一个 checkpoint 上。

本版不做真实训练，不声明模型能力提升，也不伪装成 checkpoint resume。当前训练入口没有续训参数，因此计划里明确写入 `not_checkpoint_resume`，下一步只能先做单语料的 surface-first approximation。

## 前置能力

- v630/v631：`loss-internal-joint-cycle` 在生成侧 pair-full，但内部 forced-choice 只有 partial。
- v640/v641：`joint-cycle-internal-repair` 在内部 forced-choice 达到 pair-full，但生成侧没有释放两个词。
- v648：批次收口后选择两阶段 surface/internal schedule，而不是继续堆轻量 merge。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_two_stage_schedule_plan.py`
  - 构建计划报告。
  - 复用 generation/internal alignment comparison 的 source row 作为底层事实。
  - 输出 `stage_rows`、`guardrails`、`schedule_boundary` 和 `interpretation`。
- `src/minigpt/model_capability_required_term_pair_two_stage_schedule_plan_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
  - HTML 报告显示状态、决策、stage gate 和 guardrail。
- `scripts/build_model_capability_required_term_pair_two_stage_schedule_plan.py`
  - CLI 入口。
  - 接收 `--surface-source LABEL REFRESH FORCED` 与 `--internal-source LABEL REFRESH FORCED`。
- `tests/test_model_capability_required_term_pair_two_stage_schedule_plan.py`
  - 覆盖通过计划、surface 缺 pair-full 失败、输出渲染和 CLI `--require-pass`。

## 核心数据结构

`stage_rows` 有两行：

- `surface_generation_stage`
  - `goal=preserve_generation_pair_full`
  - `gate=generation_pair_full`
  - 对应 v630/v631 的 surface 证据。
- `internal_repair_stage`
  - `goal=repair_internal_preference_without_claiming_generation_alignment`
  - `gate=internal_pair_full`
  - 对应 v640/v641 的 internal 证据。

`guardrails` 有四类保护：

- `not_checkpoint_resume`：明确这只是计划，不是续训。
- `no_aligned_route_claim`：没有 aligned pair-full 时不能宣称对齐。
- `surface_generation_pair_full_required`：第一阶段必须来自生成 pair-full。
- `internal_pair_full_required`：第二阶段必须来自内部 pair-full。

## 运行证据

产物写入：

- `e/649/解释/model-capability-required-term-pair-two-stage-schedule-plan/`
- `e/649/图片/v649-two-stage-schedule-plan.png`

关键结果：

- `status=pass`
- `decision=two_stage_surface_internal_schedule_ready`
- `stage_gate_pass_count=2`
- `guardrail_fail_count=0`
- `schedule_boundary.training_semantics=not_checkpoint_resume`

## 测试覆盖

单测覆盖了四件事：

- 合法 split evidence 可以通过计划。
- surface source 缺少 generation pair-full 时失败。
- 所有报告格式能渲染。
- CLI 在 `--require-pass` 下遇到失败计划会返回非零退出码。

这让下一版的 corpus approximation 有一个明确前置条件：只有当计划报告通过，才继续做 surface-first schedule 近似。

## 一句话总结

v649 把两条互补路线从口头判断变成可复核 schedule contract，并把“不是 checkpoint resume”的边界写进产物。
