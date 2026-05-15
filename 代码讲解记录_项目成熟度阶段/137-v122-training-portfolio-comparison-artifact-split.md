# v122 training portfolio comparison artifact split 代码讲解

## 本版目标

v122 继续执行 v110 的 module pressure audit 路线，目标是把 `training_portfolio_comparison.py` 里已经稳定的训练组合比较输出层拆到独立模块：

```text
training_portfolio_comparison.py           -> portfolio 读取、artifact 发现、baseline 选择、delta 计算、summary、recommendations、兼容导出
training_portfolio_comparison_artifacts.py -> JSON/CSV/Markdown/HTML 写入与展示 helper
```

本版解决的问题是：`training_portfolio_comparison.py` 同时承担组合证据读取、artifact 路径解析、score/loss/artifact/dataset/maturity delta 计算、CSV 展开、Markdown 组装、HTML 页面渲染和 artifact 写入。v122 把 artifact 边界拆出后，主模块从 635 非空行降到 373 非空行，同时保留旧调用方式。

本版明确不做：

- 不改变 `build_training_portfolio_comparison()` 的 schema version 1 输出结构。
- 不改变 baseline 选择、score relation、loss relation、artifact coverage、dataset warning 和 maturity status delta 的计算。
- 不改变 `scripts/compare_training_portfolios.py` 的 CLI 参数和输出文件名。
- 不改变 `training_portfolio_batch.py` 调用 comparison 的方式。
- 不移除 `minigpt.training_portfolio_comparison` 里原有的 artifact 函数导出。

## 前置路线

v122 接在这条维护收口路线后面：

```text
v110 module pressure audit
 -> v118 benchmark scorecard comparison artifact split
 -> v119 maintenance policy artifact split
 -> v121 maturity artifact split
 -> v122 training portfolio comparison artifact split
```

这说明本版不是重新设计训练规模治理，而是回到 v68 已经稳定的 training portfolio comparison，把“如何比较多个 portfolio”和“如何发布比较证据”拆开。

## 关键文件

```text
src/minigpt/training_portfolio_comparison_artifacts.py
src/minigpt/training_portfolio_comparison.py
tests/test_training_portfolio_comparison_artifacts.py
README.md
代码讲解记录_项目成熟度阶段/README.md
c/122/图片
c/122/解释/说明.md
```

`src/minigpt/training_portfolio_comparison_artifacts.py` 是本版新增的 artifact 层。它负责：

- 写入 `training_portfolio_comparison.json`。
- 写入 `training_portfolio_comparison.csv`。
- 渲染和写入 `training_portfolio_comparison.md`。
- 渲染和写入 `training_portfolio_comparison.html`。
- 把 portfolio delta、core artifact coverage 和 recommendations 转成可读报告。

`src/minigpt/training_portfolio_comparison.py` 仍然是训练组合比较主模块。它负责：

- 读取 `training_portfolio.json`。
- 解析 portfolio 名称和 baseline。
- 解析 run manifest、eval suite、generation quality、benchmark scorecard、dataset card、registry、maturity summary 和 maturity narrative。
- 生成每个 portfolio 的摘要。
- 计算 baseline delta、best by score、best by loss 和 recommendations。
- 从 artifact 模块重新导出旧函数，保持 CLI、batch 和旧测试兼容。

## 核心数据结构

comparison report 的关键字段包括：

- `schema_version`：仍为 `1`。
- `baseline`：被选中的基准 portfolio 摘要。
- `portfolios`：每个 portfolio 的 score、loss、artifact coverage、dataset status 和 maturity status。
- `baseline_deltas`：每个 portfolio 相对 baseline 的 score/loss/artifact/dataset/maturity 变化。
- `summary`：completed/failed/planned、score improvement/regression、artifact regression、dataset warning 和 maturity review 统计。
- `best_by_overall_score` / `best_by_rubric_avg_score` / `best_by_artifact_coverage` / `best_by_final_val_loss`：不同维度下的最佳组合。
- `recommendations`：基于失败、计划中、artifact regression、score/loss regression 和 dataset warning 给出的下一步建议。

这些字段仍然由主模块计算。artifact 模块只消费这个 report，不重新解释比较规则。

## 核心函数

`write_training_portfolio_comparison_json(report, path)`
把 comparison report 原样写为 JSON，是机器可读的最终证据。

`write_training_portfolio_comparison_csv(report, path)`
把 `portfolios` 和 `baseline_deltas` 合并为一张表，保留 score、loss、artifact coverage、dataset warning、maturity status 和 explanation。

`render_training_portfolio_comparison_markdown(report)`
生成 Markdown 汇总，包含 Summary、Portfolios、Artifact Coverage 和 Recommendations。

`render_training_portfolio_comparison_html(report)`
生成自包含 HTML 页面，并对标题、portfolio 名称、路径和 explanation 做 HTML escaping。

`write_training_portfolio_comparison_outputs(report, out_dir)`
统一写出 JSON、CSV、Markdown 和 HTML，并返回输出路径映射。旧 CLI 和 batch runner 继续通过这个函数获得同名产物。

## 输入输出边界

v122 后的运行流程是：

```text
training_portfolio.json x N
 -> training_portfolio_comparison.py 读取证据、选择 baseline、计算 deltas 和 summary
 -> training_portfolio_comparison_artifacts.py 写 JSON/CSV/Markdown/HTML
 -> scripts/compare_training_portfolios.py 保持原 CLI 和输出路径
 -> training_portfolio_batch.py 继续复用旧 facade
```

artifact 模块不读取 portfolio 文件、不解析 run artifact、不选择 baseline。这样后续如果只改 HTML/CSV 展示，不需要碰训练规模比较规则；如果只改比较计算，也不需要碰证据发布格式。

## 测试覆盖

`tests/test_training_portfolio_comparison_artifacts.py` 新增两类断言：

- 直接调用 artifact 模块写出 JSON/CSV/Markdown/HTML，确认 CSV 包含 delta 字段，Markdown 包含 Artifact Coverage，HTML 正确转义 `<comparison>`。
- 检查 `minigpt.training_portfolio_comparison` 里的旧 artifact 导出仍然指向 artifact 模块，保护 CLI、batch runner 和历史调用方式。

原有 `tests/test_training_portfolio_comparison.py` 继续覆盖：

- 目录形式加载 portfolio。
- baseline delta、score/loss relation、artifact regression 和 recommendations。
- 相对 artifact 路径解析。
- 原 public writer/render 函数的输出和 HTML escaping。
- name 数量不匹配时的错误。

`tests/test_training_portfolio_batch.py` 继续覆盖 batch runner 通过旧 comparison facade 生成 `comparison/training_portfolio_comparison.*`。

## 运行证据

v122 的运行证据放在：

```text
c/122/图片
c/122/解释/说明.md
```

关键证据包括：

- 单测、compileall 和全量 unittest 回归。
- CLI comparison smoke，真实写出 `training_portfolio_comparison.json/csv/md/html`。
- maintenance batching/module pressure smoke，证明拆分后最大压力点已转移到 `dashboard.py`。
- output check，证明 HTML escaping、portfolio delta、artifact coverage 和 facade parity 稳定。
- Playwright 使用已安装 Google Chrome 打开生成的 comparison HTML 页面。
- README、c/README、代码讲解索引和本讲解文件的文档闭环检查。

这些截图不是临时调试文件，而是 v122 tag 的运行证明。临时输出目录仍按 cleanup gate 删除。

## 一句话总结

v122 把 training portfolio comparison 从“一个模块既算比较又发布证据”推进到“比较计算和 artifact 发布分层”，让训练规模治理链也更容易维护。
