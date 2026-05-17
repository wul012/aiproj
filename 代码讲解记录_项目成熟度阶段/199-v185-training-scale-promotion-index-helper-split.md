# v185 training scale promotion index helper split

## 本版目标

v185 的目标是把 `training_scale_promotion_index.py` 中的 promotion row、name resolution、baseline selection、compare inputs、summary 和 recommendations 辅助逻辑拆到 `training_scale_promotion_index_helpers.py`。

它解决的问题是：promotion index 模块同时承担三类职责：

- 加载 promotion JSON 并构建 index report。
- 写出 JSON/CSV/Markdown/HTML 证据。
- 处理 promotion 数据归一化、可比较 run 筛选、baseline 选择和建议生成。

第三类逻辑已经偏向纯 helper。v185 把它抽出后，`training_scale_promotion_index.py` 更像稳定 public facade，helper 模块负责内部数据整理。

本版明确不做：

- 不改变 `build_training_scale_promotion_index()` 的输入输出。
- 不改变 promotion index report schema。
- 不改变 JSON/CSV/Markdown/HTML 输出文件名。
- 不改变 baseline 选择规则、compare command 结构或推荐文案。
- 不把 promotion index helper 拆分解释成真实训练能力提升。

## 前置路线

v78 引入 training scale promotion index，把多个 promotion report 汇总成可比较 run 列表，并生成后续 compare command。

v160 已经把 training scale promotion artifact writer 从 promotion decision builder 中拆出。

v180 已经把 training scale workflow artifact writer 拆出。

v185 延续训练规模链路的收口：不新增报告层，不扩展训练语义，只整理 promotion index 内部边界。

## 关键文件

### `src/minigpt/training_scale_promotion_index_helpers.py`

这是本版新增的 helper 模块。

核心函数：

- `_resolve_names()`：从用户传入的 names 或 promotion JSON 路径推导 index 名称，并检查空名和重复名。
- `_promotion_row()`：把单个 promotion report 转成 index 中的一行 promotion row。
- `_primary_variant()`：优先选择 `promotion_status == "ready"` 的 variant。
- `_artifact_map()`：从 variant artifact rows 中提取实际存在的 checkpoint、registry、maturity narrative 等路径。
- `_comparison_inputs()`：筛选 `promoted_for_comparison` 的 promotion rows，生成 training scale run paths、names、baseline 和 compare command。
- `_select_baseline()`：支持默认 baseline、数字 baseline 和名称 baseline，并拒绝 review/blocked promotion 作为 baseline。
- `_summary()`：汇总 promoted/review/blocked/missing/comparable 数量。
- `_recommendations()`：根据 comparable run 数量和 review/blocked 状态给出下一步建议。

这个模块只负责内部数据归一化和比较输入构造，不负责读写文件和 HTML/Markdown 渲染。

### `src/minigpt/training_scale_promotion_index.py`

这个模块保留 public facade：

- `load_training_scale_promotion()`
- `build_training_scale_promotion_index()`
- `write_training_scale_promotion_index_json()`
- `write_training_scale_promotion_index_csv()`
- `render_training_scale_promotion_index_markdown()`
- `render_training_scale_promotion_index_html()`
- `write_training_scale_promotion_index_outputs()`

它从 helper 模块导入内部函数，用它们构造 report，然后继续负责 artifact presentation。

### `tests/test_training_scale_promotion_index.py`

本版新增 helper smoke：

- 通过 public builder 先生成 report。
- 再用 helper 的 `_comparison_inputs()` 对 public builder 的 `promotions` 重新计算 compare inputs。
- 断言 helper 输出的 names、compare-command readiness 和 summary 与 public builder 保持一致。

这不是新增外部 API，而是保护“helper 模块已经接管核心 plumbing，且结果仍与 public builder 对齐”。

## 数据结构和输入输出

`build_training_scale_promotion_index()` 的 report schema 不变：

- `schema_version`
- `title`
- `generated_at`
- `promotion_count`
- `promotions`
- `comparison_inputs`
- `summary`
- `recommendations`

其中 `promotions` 仍然包含：

- promotion status、handoff/scale-run/batch status
- variant counts、artifact counts
- primary checkpoint/registry/maturity narrative
- missing required artifacts、blockers、review items
- `promoted_for_comparison`

`comparison_inputs` 仍然包含：

- `run_count`
- `names`
- `training_scale_run_paths`
- `baseline_name`
- `compare_command_ready`
- `compare_command`

下游 promoted training scale comparison 仍然消费这个 index JSON，不需要改调用方式。

## 运行流程

拆分后的链路是：

```text
promotion JSON paths
 -> training_scale_promotion_index.load_training_scale_promotion()
 -> training_scale_promotion_index_helpers._promotion_row()
 -> training_scale_promotion_index_helpers._comparison_inputs()
 -> training_scale_promotion_index_helpers._summary()
 -> training_scale_promotion_index report
 -> JSON/CSV/Markdown/HTML outputs
```

helper 模块不写文件，index 模块不再承载细粒度 promotion row 和 baseline 选择逻辑。

## 测试和证据

v185 的截图归档在 `c/185`。

关键验证包括：

- focused training scale promotion index tests。
- helper smoke：确认 helper 负责 compare inputs 与 summary plumbing。
- maintenance smoke：确认维护治理链路仍可跑。
- source encoding hygiene：确认新增 Python 文件没有 BOM 或语法问题。
- full unittest discovery：确认全仓主测试链路通过。
- docs check：确认 README、`c/185`、代码讲解索引、source/test 关键词对齐。

## 一句话总结

v185 把 training scale promotion index 的内部数据归一化和比较输入计算拆成 helper 模块，让 promotion index facade 更稳定，训练规模治理链路更容易继续维护。
