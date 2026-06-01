# v655 required-term pair surface-first failure analysis

## 本版目标和边界

v655 的目标是把 surface-first schedule 的失败做成结构化诊断。它不是新训练，也不是新路线决策，而是把 v651-v654 的证据连接起来，判断失败类型和下一步是否值得继续。

本版不声称模型能力提升，只给出负向路线分析。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_surface_first_failure_analysis.py`
  - 读取 refresh、forced-choice、comparison、route-decision 四类输入。
  - 生成 `evidence_rows`、`summary`、`recommendations`。
- `src/minigpt/model_capability_required_term_pair_surface_first_failure_analysis_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
- `scripts/run_model_capability_required_term_pair_surface_first_failure_analysis.py`
  - CLI 入口，支持目录或 JSON 路径。
- `tests/test_model_capability_required_term_pair_surface_first_failure_analysis.py`
  - 覆盖 fixed collapse、坏输入失败和多格式输出。

## 核心数据结构

`evidence_rows` 包含四个观察：

- `generation_replay`：从 v651 refresh replay 中抽取命中 term。
- `forced_choice`：从 v652 prompt summaries 中抽取 expected-best term。
- `alignment_class`：从 v653 comparison 中读取 source row 分类。
- `route_selection`：从 v654 route decision 中确认是否被选为 generation route。

`summary.fixed_collapse_confirmed` 的条件是：

- generation hit terms 等于 `["fixed"]`。
- forced-choice expected terms 等于 `["fixed"]`。

## 运行结果

真实报告显示：

- `decision=surface_first_schedule_fixed_collapse_confirmed`
- `generation_hit_terms=["fixed"]`
- `forced_choice_expected_terms=["fixed"]`
- `alignment_class=fixed_only_aligned_partial`
- `next_objective=loss_guarded_surface_schedule_repair`

## 测试覆盖

单测保护三件事：

- 合法输入能确认 fixed collapse。
- 任一上游输入 status 失败时，本层也失败。
- JSON/CSV/TXT/Markdown/HTML 全格式可输出。

## 一句话总结

v655 把 surface-first 的失败归因到 fixed-only collapse，并把下一步限定为 loss-guarded 变体或停止分支。
