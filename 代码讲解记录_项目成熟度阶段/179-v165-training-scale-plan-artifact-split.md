# v165 training scale plan artifact split 代码讲解

## 本版目标

v165 的目标是把 `training_scale_plan.py` 里的 artifact 写出和报告渲染逻辑，拆到 `training_scale_plan_artifacts.py`。

这一版解决的问题不是训练能力本身，而是训练规模规划模块的职责边界：`training_scale_plan.py` 原来同时负责读取语料、评估规模、推荐 variants、生成 batch command、写 JSON/CSV/Markdown/HTML。随着训练规模链路持续增加 gate、run、comparison、decision、workflow、promotion，plan 模块如果继续承担输出层，会重新变成大文件。

本版明确不做三件事：

- 不改变 `training_scale_plan.json` schema。
- 不改变 `training_scale_variants.json` 给 batch runner 的消费格式。
- 不改变 `scripts/plan_training_scale.py`、`training_scale_run.py`、`training_scale_workflow.py` 等下游调用方式。

## 前置路线

这一版来自 v153-v164 的“大模块轻量拆分”路线：release bundle、release readiness、server、dataset card、model card、benchmark comparison 等模块已经证明，稳定的 JSON/Markdown/HTML 写出层适合先拆成 artifact 模块。

v165 把同一套方法应用到训练规模规划入口。训练规模路线仍是：

```text
source corpus
 -> training_scale_plan.py
 -> training_scale_plan_artifacts.py
 -> training_scale_variants.json
 -> training_portfolio_batch.py
 -> gate/run/comparison/decision/workflow/promotion
```

## 关键文件

- `src/minigpt/training_scale_plan.py`：继续负责构建训练规模计划，包括语料规模分层、variants 推荐、block size 安全调整、token budget 和建议文本。
- `src/minigpt/training_scale_plan_artifacts.py`：新增 artifact 模块，负责 JSON、variants JSON、CSV、Markdown、HTML 的写出和渲染。
- `tests/test_training_scale_plan.py`：保留原有计划构建、renderer escape、batch variants 兼容测试，并新增 facade identity 测试。
- `README.md`：更新当前版本、能力矩阵、版本标签、项目结构和 v165 证据说明。
- `c/165/解释/说明.md`：解释运行截图分别证明了哪条链路。
- `代码讲解记录_项目成熟度阶段/README.md`：把 v165 讲解纳入项目成熟度阶段索引。

## 核心数据结构

### scale plan report

`build_training_scale_plan()` 返回的 report 仍是本链路的核心对象：

- `schema_version`：当前为 `1`。
- `dataset`：保存数据集名称、版本前缀、字符数、行数、唯一字符比例、fingerprint、scale tier、质量状态和 warning/issue 数量。
- `sources_detail`：保存每个输入源的准备结果。
- `quality_issues`：来自数据质量报告的问题列表。
- `variants`：训练配置候选，例如 `scale-smoke`、`scale-baseline`、`scale-extended`。
- `variant_matrix`：从 variants 派生出的展示和对比表，包含 token budget、corpus pass estimate 和模型配置。
- `batch`：记录 `training_scale_variants.json` 的路径、batch 输出目录、baseline 名称和可执行 batch 命令。
- `recommendations`：给下一步训练规模执行的建议。

v165 不改变这些字段，只改变它们如何被写出成证据文件。

### variants JSON

`write_training_scale_variants_json()` 生成的 payload 仍保持：

```text
schema_version
generated_at
source
dataset
variants
```

其中 `source` 继续是 `training_scale_plan`，这是 batch runner 识别“这些 variants 来自 scale plan”的证据字段。

## 核心函数

### `build_training_scale_plan()`

这个函数仍在 `training_scale_plan.py` 中。它读取 sources，构建 prepared dataset，再用数据质量报告决定 scale tier 和 variants。它是决策层，不负责输出格式。

### `write_training_scale_plan_outputs()`

这个函数现在由 `training_scale_plan_artifacts.py` 实现，但从 `training_scale_plan.py` 重新导出。它写出：

- `training_scale_plan.json`
- `training_scale_variants.json`
- `training_scale_plan.csv`
- `training_scale_plan.md`
- `training_scale_plan.html`

返回值仍是 `{key: path}`，所以 CLI 和下游模块不需要改。

### `render_training_scale_plan_markdown()`

Markdown 渲染仍展示 scale tier、dataset、source count、quality、variant matrix、batch command、recommendations 和 quality issues。它是人工审阅证据，不是下游机器消费的主契约。

### `render_training_scale_plan_html()`

HTML 渲染仍用 card、variant table、batch handoff、recommendations、quality issues 组织浏览器可读报告。它是最终可读证据，但不驱动训练执行。

## facade 兼容

`training_scale_plan.py` 现在从 artifact 模块导入并重新导出：

```text
render_training_scale_plan_html
render_training_scale_plan_markdown
write_training_scale_plan_outputs
write_training_scale_variants_json
...
```

因此旧代码仍可继续使用：

```python
from minigpt.training_scale_plan import write_training_scale_plan_outputs
```

这点很重要，因为 `scripts/plan_training_scale.py`、`training_scale_run.py`、`training_scale_workflow.py` 和多组测试都依赖这个入口。

## 测试覆盖

本版测试分三层：

- `tests.test_training_scale_plan`：验证计划构建、variants JSON 兼容 batch runner、tiny corpus block size 调整、HTML escaping、scale tier 边界，以及 facade 函数身份。
- `tests.test_training_scale_run`：验证下游 scale run 仍能通过 plan 输出继续执行 gate 和 batch dry-run。
- `tests.test_training_scale_workflow`：验证 plan -> run -> comparison -> decision 的更长链路没有因为 artifact 拆分断开。

新增 facade identity 断言保护的是“实现可以拆走，但旧入口不能变”：

```text
training_scale_plan.write_training_scale_plan_outputs
is training_scale_plan_artifacts.write_training_scale_plan_outputs
```

## 运行证据

`c/165/图片/` 保存本版截图：

- `01-training-scale-plan-tests.png`：训练规模 plan/run/workflow 局部测试通过。
- `02-training-scale-plan-smoke.png`：CLI smoke 真实写出五类 plan artifacts。
- `03-maintenance-smoke.png`：module pressure 仍为 pass。
- `04-source-encoding-smoke.png`：源码编码和 Python 3.11 兼容检查通过。
- `05-full-unittest.png`：全量 unittest 通过。
- `06-docs-check.png`：README、讲解、`c/165` 和关键源码/测试索引对齐。

## 边界说明

`training_scale_plan_artifacts.py` 不是新的业务决策层。它只负责把 report 写成文件和页面。

训练规模是否应该执行、是否 gate pass、是否 promotion，都仍由后续模块判断。也就是说，v165 提升的是可维护性，不把报告漂亮程度误当成模型能力提升。

## 一句话总结

v165 把训练规模规划的“决策生成”和“证据发布”拆开，让 scale planner 从 541 行降到 313 行，同时保持训练规模链路的旧入口、schema 和 batch 消费契约不变。
