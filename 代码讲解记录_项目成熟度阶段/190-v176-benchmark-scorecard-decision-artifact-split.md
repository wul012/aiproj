# v176 benchmark scorecard decision artifact split 代码讲解

## 本版目标

v176 的目标是把 `benchmark_scorecard_decision.py` 中的 artifact 输出层拆到 `benchmark_scorecard_decision_artifacts.py`，让 benchmark scorecard promotion decision 继续向“候选决策”和“证据发布”分离。原模块同时负责 scorecard comparison 读取、case delta 统计、candidate evaluation、baseline 排除、rubric threshold 检查、generation-quality review item、selected-run ranking、decision status、recommendations、JSON/CSV/Markdown/HTML 写出和 HTML 渲染。前半部分是决策语义，后半部分是发布和展示层。

本版明确不做这些事：不改变 comparison schema，不改变 baseline run 不能作为 promotion candidate 的规则，不改变 rubric threshold、overall/rubric regression blocker、generation-quality review item 和 case regression review item，不改变 candidate 排序逻辑，不改变 `scripts/build_benchmark_scorecard_decision.py` 用法，也不改变旧的 `minigpt.benchmark_scorecard_decision` writer/render 导出入口。

## 前置路线

v176 接在 benchmark scorecard 与 artifact split 收束路线后面。v34-v47 建立固定 prompt eval、benchmark scorecard 和比较能力；v137-v141 把 generation-quality flag taxonomy、scorecard promotion decision 和 maturity narrative 串起来；v163 又把 scorecard comparison 的 delta 层拆出。v176 继续沿用同一个节奏：不扩展新的报告种类，而是把已有决策模块里的输出层剥离出来。

从维护角度看，v175 之后最大的模块是 `benchmark_scorecard_decision.py`。它没有超过阈值，但 494 行里有很大一段是 CSV、Markdown、HTML 和 CSS。这个拆分属于轻量、定向的质量优化，不是架构级重构。

## 关键文件

- `src/minigpt/benchmark_scorecard_decision.py`：保留 scorecard promotion decision 主语义。它继续负责加载 comparison、统计 case deltas、评估候选、排除 baseline、选择候选、生成 summary 和 recommendations。
- `src/minigpt/benchmark_scorecard_decision_artifacts.py`：新增 artifact 模块。它只消费已经构造好的 decision report，把它写成 JSON、CSV、Markdown 和 HTML。
- `tests/test_benchmark_scorecard_decision.py`：原有测试继续覆盖 blocked candidate、clean candidate promotion、directory loading、output writing、HTML escaping 和 empty comparison rejection，新增 facade identity 测试。
- `README.md`、`c/176/解释/说明.md`、`代码讲解记录_项目成熟度阶段/README.md`：记录本版能力、证据目录和讲解索引。

## Decision 主逻辑

`load_benchmark_scorecard_comparison()` 是入口读取函数。它接受 comparison 文件或目录，通过 `_resolve_comparison_path()` 找到 `benchmark_scorecard_comparison.json`，使用 `utf-8-sig` 读取以兼容历史 BOM 文件，并把真实来源路径写入 `_source_path`。

`build_benchmark_scorecard_decision()` 是主构建函数。它读取 comparison 后，先取出 `runs`、`baseline_deltas` 和 `case_deltas`。如果 comparison 没有 run，会直接抛出 `ValueError`，因为没有候选就无法构造 promotion decision。

`_evaluate_run()` 是候选评估核心。它会把 baseline run 标记为 blocker，因为 baseline 只是参考对象，不是 promotion candidate。它还会检查 `rubric_avg_score` 是否缺失或低于阈值、rubric/overall 是否相对 baseline regression、rubric fail count 是否增加、generation-quality flags 是否增加、dominant/worst flag 是否变化，以及 case delta 中是否出现 regression。输出行包含 `decision_relation`、score、delta、flag、case、blockers 和 review_items。

`_select_candidate()` 在可用候选中选择最佳 run，排序依据是 rubric average score、overall score、generation-quality total flags 越少越好以及 name 稳定排序。`_decision_status()` 根据 selected run 是否存在、是否有 review item，给出 `blocked`、`review` 或 `promote`。最后 `_summary()` 和 `_recommendations()` 给出汇总和后续动作。

## Artifact 模块

`benchmark_scorecard_decision_artifacts.py` 接管了这些函数：

- `write_benchmark_scorecard_decision_json()`：写出完整 decision report，这是机器可消费的主证据。
- `write_benchmark_scorecard_decision_csv()`：把 candidate evaluations 写成 CSV 行，包含 relation、score、delta、blockers 和 review_items。
- `render_benchmark_scorecard_decision_markdown()`：生成人可读 Markdown，展示 decision、action、baseline、selected run、candidate table 和 recommendations。
- `render_benchmark_scorecard_decision_html()`：生成浏览器可读 HTML，展示状态 card、candidate evaluations table 和 recommendations。
- `write_benchmark_scorecard_decision_outputs()`：统一写出 JSON、CSV、Markdown 和 HTML，并返回路径字典。

这个 artifact 模块不读取 comparison，不评估候选，不选择 selected run，也不生成 recommendations。它的边界是“发布已有 report”，不参与 promotion decision 语义。

## 兼容性

旧调用方式仍然有效：

```python
from minigpt.benchmark_scorecard_decision import write_benchmark_scorecard_decision_outputs
```

原因是 `benchmark_scorecard_decision.py` 从 `benchmark_scorecard_decision_artifacts.py` 重新导入并导出了 writer/render 函数。这保证 `scripts/build_benchmark_scorecard_decision.py`、maturity narrative 消费方和其他旧消费方不需要同步改路径。

`tests/test_benchmark_scorecard_decision.py` 新增的 identity 断言保护这个兼容层：

```python
self.assertIs(
    benchmark_scorecard_decision.write_benchmark_scorecard_decision_outputs,
    benchmark_scorecard_decision_artifacts.write_benchmark_scorecard_decision_outputs,
)
self.assertIs(
    benchmark_scorecard_decision.render_benchmark_scorecard_decision_html,
    benchmark_scorecard_decision_artifacts.render_benchmark_scorecard_decision_html,
)
```

它保护的是函数对象一致，防止未来旧模块里重新复制一份 writer 实现，造成新旧入口行为分叉。

## 测试覆盖

v176 的测试覆盖四层：

- `tests.test_benchmark_scorecard_decision`：覆盖 regressed candidate blocked、clean candidate promotion、directory loading、output writing、HTML escaping、empty comparison rejection 和 facade identity。
- 全量 unittest discovery：确认 maturity narrative、benchmark scorecard comparison、generation quality 等下游链路没有因为 re-export 受影响。
- source encoding hygiene：确认新模块没有 BOM、语法错误或 Python 3.11 兼容问题。
- maintenance batching：确认 module pressure 继续为 `pass`，没有新 warn/critical 模块。

## 运行证据

v176 的运行截图归档在 `c/176`：

- `01-benchmark-scorecard-decision-tests.png`：定向 scorecard decision 测试通过。
- `02-benchmark-scorecard-decision-artifact-smoke.png`：旧 facade 和新 artifact 函数对象一致，且主模块从 494 行降到 263 行。
- `03-maintenance-smoke.png`：module pressure 为 `pass`。
- `04-source-encoding-smoke.png`：编码、语法和目标 Python 兼容检查通过。
- `05-full-unittest.png`：全量 398 个测试通过。
- `06-docs-check.png`：README、`c/176`、讲解索引、source/test 关键词对齐。

临时 `tmp_v176_*` 日志和 `runs/*v176*` 输出会在提交前按 AGENTS 清理门禁删除，`c/176` 是保留的正式证据。

## 边界说明

`benchmark_scorecard_decision_artifacts.py` 不是新的 promotion decision 构建器。它不决定谁能 promote，不处理 rubric/generation-quality/case regression，也不生成 recommendations。它只把主模块交给它的 report 发布成文件。因此后续修改时，候选评估和 selected-run 逻辑找 `benchmark_scorecard_decision.py`，输出格式和页面样式找 `benchmark_scorecard_decision_artifacts.py`。

## 一句话总结

v176 把 benchmark scorecard decision 的 JSON/CSV/Markdown/HTML 输出层独立成 `benchmark_scorecard_decision_artifacts.py`，让 `benchmark_scorecard_decision.py` 从 494 行降到 263 行，同时保持 candidate evaluation、selected-run ranking、decision status、CLI 和旧 facade 导出不变。
