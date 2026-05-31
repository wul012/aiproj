# v551 required-term pair seed config held-out gap 代码讲解

## 本版目标和边界

v550 已经证明 selected seed/config policy 在 held-out prompt surface 上达到 `8/9` pair-full，但剩下一个 `equals + seed 1535` 缺口。v551 的目标是把这个缺口继续拆到 profile/case 级别，明确它到底缺哪个 term、在哪个 prompt surface 上缺、两个 generation profile 是否表现一致。

本版不训练新模型，不修改 v548 policy，也不改变 v550 replay 逻辑。它只消费 v550 的只读报告和 sidecar，把后续修复从“猜测 prompt 泛化问题”变成“针对 fixed-term equals surface 的证据驱动修复”。

## 前置链路

输入来自 v550：

- 主报告记录 9 个 held-out replay rows。
- `replay_reports` 保存每个 spec/config/seed 的 generation-profile replay 详情。
- 唯一失败行是 `spec_id=equals`、`seed=1535`、`selected_config_id=v546-loss-calibrated-topk2-t080`。

v551 不重新执行生成，而是读取 v550 已归档 sidecar 的 `variant_rows` 和 `case_rows`。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_seed_config_heldout_gap.py`
  - 定义 held-out gap diagnostic 的核心 builder。
  - `locate_pair_seed_config_heldout_replay()` 支持输入 JSON 或输出目录。
  - `build_model_capability_required_term_pair_seed_config_heldout_gap_diagnostic()` 读取 replay rows，定位非 pair-full 行，并关联对应 sidecar。
- `src/minigpt/model_capability_required_term_pair_seed_config_heldout_gap_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML。
  - HTML 中同时展示 gap row 和 profile evidence，便于截图复核。
- `scripts/run_model_capability_required_term_pair_seed_config_heldout_gap_diagnostic.py`
  - CLI 入口，支持 `--out-dir`、`--force`、`--require-pass`。
- `tests/test_model_capability_required_term_pair_seed_config_heldout_gap.py`
  - 覆盖 gap 分类、gap-free、输入失败和 artifact 输出。

## 核心数据结构

主报告输出字段：

- `gap_rows`
  - 只收录 `replay_pair_full != True` 的 held-out rows。
  - 每行带 `spec_id`、`seed`、`selected_config_id`、`gap_class`、`missed_terms`、`best_profile_id` 和 `profile_details`。
- `profile_details`
  - 来自 sidecar replay 的 `variant_rows` 和 `case_rows`。
  - 每个 profile 保存 `hit_terms`、`missed_terms`、`pair_full_hit`、`blocked_token_count_total` 和 `case_previews`。
- `summary`
  - 汇总 `gap_count`、`gap_rate`、`spec_gap_counts`、`seed_gap_counts`、`config_gap_counts` 和 `gap_class_counts`。

本版的 `gap_class` 是轻量分类：

```text
fixed_term_surface_gap
loss_term_surface_gap
multi_term_surface_gap
missing_replay_sidecar
pair_full_summary_gap
```

真实 v551 归档命中的是 `fixed_term_surface_gap`。

## 运行流程

CLI 执行时：

1. 将输入目录解析为 `model_capability_required_term_pair_seed_config_heldout_replay.json`。
2. 读取 v550 held-out replay JSON。
3. 建立 `(spec_id, config_id, seed) -> sidecar report` 索引。
4. 找出所有 `replay_pair_full` 不为 true 的 rows。
5. 从 sidecar 的 `variant_rows`、`case_rows` 提取 profile 级 hit/miss 和 continuation preview。
6. 输出五种报告格式。

这个流程保证诊断结论可以从 v550 证据重新推导，不依赖手写解释。

## 真实结果

真实运行结果：

```text
decision=required_term_pair_seed_config_heldout_gap_fixed_term_surface
gap_count=1
gap_class_counts=fixed_term_surface_gap:1
spec_gap_counts=equals:1
seed_gap_counts=1535:1
```

profile evidence 显示 `fixed=` prompt 下 default 与 newline-suppression profile 都没有命中 `fixed` continuation，而 `loss=` prompt 可以命中 `loss`。这把问题从“held-out 泛化不稳”进一步缩小为“equals prompt 的 fixed 分支不足”。

## 测试覆盖

测试覆盖以下边界：

- fake held-out report 中 fixed 缺失时，输出 `required_term_pair_seed_config_heldout_gap_fixed_term_surface`。
- 所有 row pair-full 时，输出 `required_term_pair_seed_config_heldout_gap_none`。
- 输入源 status 失败时，`--require-pass` 对应 exit code 为 1。
- JSON、CSV、text、Markdown、HTML 五种 artifact 都可生成。
- 输入目录定位会自动补 `model_capability_required_term_pair_seed_config_heldout_replay.json`。

## 归档角色

`e/551` 保存 v551 的诊断报告、HTML 截图和 Playwright snapshot。它不是新的治理链，而是 v550 held-out replay 的解释层和修复入口：后续若要修复 seed `1535`，应优先围绕 `fixed=` surface 做训练样本或 prompt repair。

一句话总结：v551 把 v550 的唯一 held-out 缺口定位为 `fixed=` surface 的 fixed-term miss，让下一步修复有了明确靶点。
