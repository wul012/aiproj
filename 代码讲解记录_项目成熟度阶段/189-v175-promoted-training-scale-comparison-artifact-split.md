# v175 promoted training scale comparison artifact split 代码讲解

## 本版目标

v175 的目标是把 `promoted_training_scale_comparison.py` 中的 artifact 输出层拆到 `promoted_training_scale_comparison_artifacts.py`，让 promoted training scale comparison 继续向“比较语义”和“证据发布”分离。原模块同时负责 promotion index 读取、promoted-run 筛选、comparison input 解析、baseline 处理、调用训练规模 run comparison、summary/blockers/recommendations、JSON/CSV/Markdown/HTML 写出和 HTML 渲染。前半部分是比较链路语义，后半部分是发布和展示层。把输出层拿出来，可以避免后续调整页面、CSV 字段或 Markdown 样式时挤占 promoted-run 比较逻辑。

本版明确不做这些事：不改变 promotion index schema，不改变 promoted_for_comparison 的筛选规则，不改变 baseline fallback 和非法 baseline blocked 行为，不改变 `build_training_scale_run_comparison()` 的复用方式，不改变 blockers/recommendations 文案，不改变 `scripts/compare_promoted_training_scale_runs.py` 用法，也不改变旧的 `minigpt.promoted_training_scale_comparison` writer/render 导出入口。

## 前置路线

v175 接在训练规模链路和 artifact split 收束路线后面。v70-v82 建立了 plan、gate、run、comparison、decision、workflow、promotion、promoted comparison 和 promoted baseline decision 的主链路。v95 曾经把 promoted comparison 迁移到 `report_utils`，让表格、HTML escape 和 JSON 写出更统一。后面 v160、v165、v168-v169、v173-v174 都在把训练规模链路里的证据产物写出从主语义模块拆出来。

从维护角度看，v175 之前最大的模块是 `promoted_training_scale_comparison.py`，它还没超过红线，但已经同时包含核心比较和多格式输出。这个拆分属于轻量、定向的质量优化，不是架构级重构。

## 关键文件

- `src/minigpt/promoted_training_scale_comparison.py`：保留 promoted comparison 主语义。它继续负责加载 promotion index、解析 promotions、筛选 compare-ready promoted runs、处理 baseline、调用 `build_training_scale_run_comparison()`、合并 comparison rows、生成 summary、blockers 和 recommendations。
- `src/minigpt/promoted_training_scale_comparison_artifacts.py`：新增 artifact 模块。它只消费已经构造好的 promoted comparison report，把它写成 JSON、CSV、Markdown 和 HTML。
- `tests/test_promoted_training_scale_comparison.py`：原有测试继续覆盖 promoted-only comparison、promoted input 不足 blocked、非法 baseline blocked、HTML escaping 和 output writing，新增 facade identity 测试。
- `README.md`、`c/175/解释/说明.md`、`代码讲解记录_项目成熟度阶段/README.md`：记录本版能力、证据目录和讲解索引。

## Comparison 主逻辑

`load_training_scale_promotion_index()` 是入口读取函数。它接受 promotion index 文件或目录，通过 `_resolve_index_path()` 找到 `training_scale_promotion_index.json`，使用 `utf-8-sig` 读取以兼容历史 BOM 文件，并把真实来源路径写入 `_source_path`。这个路径后续用于解析相对的 `training_scale_run_path`。

`build_promoted_training_scale_comparison()` 是主构建函数。它先读取 promotion index，再用 `_promotion_rows()` 把每条 promotion 标准化成包含 `name`、`promotion_status`、`promoted_for_comparison`、`training_scale_run_path`、`training_scale_run_exists`、gate/batch/readiness 字段的行。只有 `promoted_for_comparison` 为真的行会进入 comparison inputs。

`_comparison_inputs()` 负责把 promoted rows 变成 comparison 所需的 names 和 resolved paths，并保留 missing paths 与 baseline name。它的边界是“准备 comparison 输入”，不负责实际比较。

当 promoted run 少于两个，或存在 missing paths，主函数会把 `comparison_status` 保持为 `blocked`。否则它调用 `build_training_scale_run_comparison()` 生成真实 comparison report，再用 `_merge_comparison_rows()` 把 run comparison 的 status、allowed、gate、batch 和 readiness score 回填到 promotions。最后 `_summary()`、`_blockers()`、`_recommendations()` 生成 promoted comparison 的总览和后续动作建议。

## Artifact 模块

`promoted_training_scale_comparison_artifacts.py` 接管了这些函数：

- `write_promoted_training_scale_comparison_json()`：写出完整 promoted comparison report，这是机器可消费的主证据。
- `write_promoted_training_scale_comparison_csv()`：把 promotions 和 baseline deltas 合并成 CSV 行，便于检查每个 promoted run 的状态、readiness delta 和 relation explanation。
- `render_promoted_training_scale_comparison_markdown()`：生成人可读 Markdown，展示 promoted inputs、comparison summary、baseline relation、blockers 和 recommendations。
- `render_promoted_training_scale_comparison_html()`：生成浏览器可读 HTML，展示状态 card、promoted inputs table、comparison table、blockers 和 recommendations。
- `write_promoted_training_scale_comparison_outputs()`：统一写出 JSON、CSV、Markdown 和 HTML，并返回路径字典。

这个 artifact 模块不读取 promotion index，不筛 promoted run，不选择 baseline，也不决定 comparison 是否 blocked。它的边界是“发布已有 report”，不参与 promoted-run 比较语义。

## 兼容性

旧调用方式仍然有效：

```python
from minigpt.promoted_training_scale_comparison import write_promoted_training_scale_comparison_outputs
```

原因是 `promoted_training_scale_comparison.py` 从 `promoted_training_scale_comparison_artifacts.py` 重新导入并导出了 writer/render 函数。这保证 `scripts/compare_promoted_training_scale_runs.py`、promoted decision tests 和其他旧消费方不需要同步改路径。

`tests/test_promoted_training_scale_comparison.py` 新增的 identity 断言保护这个兼容层：

```python
self.assertIs(
    promoted_training_scale_comparison.write_promoted_training_scale_comparison_outputs,
    promoted_training_scale_comparison_artifacts.write_promoted_training_scale_comparison_outputs,
)
self.assertIs(
    promoted_training_scale_comparison.render_promoted_training_scale_comparison_html,
    promoted_training_scale_comparison_artifacts.render_promoted_training_scale_comparison_html,
)
```

它保护的是函数对象一致，防止未来旧模块里重新复制一份 writer 实现，造成新旧入口行为分叉。

## 测试覆盖

v175 的测试覆盖四层：

- `tests.test_promoted_training_scale_comparison`：覆盖 promoted-only comparison、promoted input 不足 blocked、非法 baseline blocked、HTML escaping、output writing 和 facade identity。
- 全量 unittest discovery：确认 promoted decision、promoted seed、training-scale workflow 等下游链路没有因为 re-export 受影响。
- source encoding hygiene：确认新模块没有 BOM、语法错误或 Python 3.11 兼容问题。
- maintenance batching：确认 module pressure 继续为 `pass`，没有新 warn/critical 模块。

## 运行证据

v175 的运行截图归档在 `c/175`：

- `01-promoted-training-scale-comparison-tests.png`：定向 promoted comparison 测试通过。
- `02-promoted-training-scale-comparison-artifact-smoke.png`：旧 facade 和新 artifact 函数对象一致，且主模块从 499 行降到 236 行。
- `03-maintenance-smoke.png`：module pressure 为 `pass`。
- `04-source-encoding-smoke.png`：编码、语法和目标 Python 兼容检查通过。
- `05-full-unittest.png`：全量 397 个测试通过。
- `06-docs-check.png`：README、`c/175`、讲解索引、source/test 关键词对齐。

临时 `tmp_v175_*` 日志和 `runs/*v175*` 输出会在提交前按 AGENTS 清理门禁删除，`c/175` 是保留的正式证据。

## 边界说明

`promoted_training_scale_comparison_artifacts.py` 不是新的 promoted comparison 构建器。它不决定哪些 run 能比较，不处理 baseline fallback，不调用训练规模 run comparison，也不生成 blockers。它只把主模块交给它的 report 发布成文件。因此后续修改时，promotion index、baseline、blocked 语义找 `promoted_training_scale_comparison.py`，输出格式和页面样式找 `promoted_training_scale_comparison_artifacts.py`。

## 一句话总结

v175 把 promoted training scale comparison 的 JSON/CSV/Markdown/HTML 输出层独立成 `promoted_training_scale_comparison_artifacts.py`，让 `promoted_training_scale_comparison.py` 从 499 行降到 236 行，同时保持 promoted-run 筛选、baseline 处理、comparison 调用、CLI 和旧 facade 导出不变。
