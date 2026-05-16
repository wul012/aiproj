# v168 promoted training scale seed artifact split 代码讲解

## 本版目标

v168 的目标是把 `promoted_training_scale_seed.py` 里的 artifact 写出和渲染逻辑拆到 `promoted_training_scale_seed_artifacts.py`。

这版解决的是 promoted seed builder 职责偏宽的问题。`promoted_training_scale_seed.py` 原来同时做四件事：读取 promoted baseline decision、构建 next-cycle seed report、生成 next training scale plan command、写出 JSON/CSV/Markdown/HTML 证据。前三件属于 seed 语义，第四件属于证据发布层。v168 把第四件拆出去。

本版明确不做三件事：

- 不改变 `promoted_training_scale_seed.json` 的 schema。
- 不改变 next-plan command 的参数、顺序和生成条件。
- 不改变旧入口，外部仍可从 `minigpt.promoted_training_scale_seed` import render/write 函数。

## 前置路线

本版来自 training scale workflow 的持续收口路线：

```text
training scale plan artifacts
 -> training scale promotion artifacts
 -> promoted training scale seed artifacts
 -> promoted seed handoff
```

v160 已经拆过 promotion artifact，v165 拆过 plan artifact。v168 把 promoted baseline 决策之后的 seed artifact 也纳入同一套边界：构建 report 的模块只负责 report 语义，artifact 模块负责把 report 写成证据。

## 关键文件

- `src/minigpt/promoted_training_scale_seed.py`：保留 `load_promoted_training_scale_decision()` 和 `build_promoted_training_scale_seed()`，负责读取 decision、校验 selected baseline、解析 selected run、整理 corpus source、生成 next-plan command、输出 seed status 和 recommendations。
- `src/minigpt/promoted_training_scale_seed_artifacts.py`：新增模块，负责 `write_promoted_training_scale_seed_json()`、CSV、Markdown、HTML 和 `write_promoted_training_scale_seed_outputs()`。
- `tests/test_promoted_training_scale_seed.py`：原有构建、阻断、review、输出和 HTML escaping 测试继续保留，新增 facade identity 测试证明旧模块导出的 artifact 函数与新模块是同一个对象。
- `README.md`：更新当前版本、能力矩阵、维护成熟度、版本标签、项目结构和 `c/168` 截图索引。
- `c/168/解释/说明.md`：解释本版运行证据和截图含义。

## 核心数据结构

### seed report

`build_promoted_training_scale_seed()` 返回的 report 仍包含：

- `schema_version`
- `title`
- `generated_at`
- `decision_path`
- `seed_status`
- `baseline_seed`
- `next_plan`
- `blockers`
- `summary`
- `recommendations`

v168 没有改变这些字段。artifact 模块只消费这些字段，不生成新的 seed 语义。

### baseline_seed

`baseline_seed` 描述 promoted baseline 的来源：selected name、decision status、gate status、batch status、readiness score、training scale run path、comparison path 和 selected run summary。

artifact HTML 里的 Baseline Seed 表格只是展示这个结构，不参与后续决策。

### next_plan

`next_plan` 是本版最重要的下游契约之一，包括 dataset name、version prefix、description、source rows、plan out dir、batch out root、command、command text、command available 和 execution ready。

artifact 模块会把 command 写进 Markdown/HTML，但 command 的生成仍由主模块 `_plan_command()` 控制。

## 核心函数

### `build_promoted_training_scale_seed()`

主函数仍在 `promoted_training_scale_seed.py`。它的流程是：

```text
load decision
 -> resolve selected training_scale_run.json
 -> load selected run summary
 -> inspect corpus sources
 -> collect blockers
 -> decide seed_status
 -> build next-plan command if allowed
 -> return seed report
```

v168 不改变这个流程。

### `write_promoted_training_scale_seed_outputs()`

这个函数移动到 artifact 模块，但旧模块继续 re-export。它写出四类文件：

- `promoted_training_scale_seed.json`：机器可读 seed report，是最终证据。
- `promoted_training_scale_seed.csv`：单行摘要，便于横向扫表。
- `promoted_training_scale_seed.md`：人工阅读的 seed 说明。
- `promoted_training_scale_seed.html`：带样式的本地证据页。

这些文件都是最终版本证据，不是临时中间产物。

### Markdown/HTML renderers

`render_promoted_training_scale_seed_markdown()` 和 `render_promoted_training_scale_seed_html()` 也移动到 artifact 模块。它们只负责展示：status、baseline、sources、next plan command、blockers 和 recommendations。

HTML 使用 `html_escape()`，Markdown 表格使用 `markdown_cell()`，这保证 `<Seed>` 这类标题仍会被正确转义。

## 测试覆盖

本版测试覆盖四层：

- ready seed：accepted decision + corpus source 能生成可执行 next-plan command。
- review seed：review decision 保留 command 但 `execution_ready` 为 false。
- blocked seed：缺 selected baseline 或 corpus source 时阻断 command。
- artifact 输出：JSON/CSV 文件存在，Markdown 包含 next plan command，HTML 会转义标题。
- facade identity：旧模块导出的 render/write 函数与 `promoted_training_scale_seed_artifacts.py` 中的函数是同一个对象。

最后再通过全量 unittest、source encoding 和 maintenance/module pressure smoke 验证没有破坏其他训练规模链路。

## 运行证据

`c/168/图片/` 保存六张截图：

- promoted seed 局部测试。
- artifact split smoke。
- maintenance/module pressure smoke。
- source encoding smoke。
- full unittest。
- docs check。

这些截图证明 v168 不只是移动代码，还保留了旧入口、输出契约、HTML 转义和整体测试闭环。

## 边界说明

`promoted_training_scale_seed_artifacts.py` 不是新的 seed 决策模块。它不读取 decision、不判断 blockers、不生成 command，只负责把 report 写成证据。

后续如果继续收口，`promoted_training_scale_seed_handoff.py` 会是相邻候选，但需要同样遵守低风险原则：先拆 artifact/render 或执行结果展示，不动真实 command execution。

## 一句话总结

v168 把 promoted training scale seed 的 artifact 输出层独立出来，让 `promoted_training_scale_seed.py` 从 530 行降到 319 行，同时保持 seed schema、next-plan command、脚本行为和旧 facade 导出不变。
