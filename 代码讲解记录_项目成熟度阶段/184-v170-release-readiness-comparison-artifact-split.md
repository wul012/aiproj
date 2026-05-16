# v170 release readiness comparison artifact split 代码讲解

## 本版目标

v170 的目标是把 `release_readiness_comparison.py` 里的 artifact 写出和页面渲染逻辑拆到 `release_readiness_comparison_artifacts.py`。

它解决的是 release readiness comparison 模块职责偏宽的问题。这个模块原来同时负责读取多个 release readiness dashboard、计算 baseline delta、解释 status/panel/CI workflow 变化、生成 recommendations，并写出 JSON/CSV/delta CSV/Markdown/HTML 证据。前三类属于 comparison 语义，最后一类属于证据发布层。v170 只拆证据发布层。

本版明确不做这些事：不改变 comparison schema，不改变 baseline override，不改变 readiness status 排序，不改变 panel delta、audit score delta、CI workflow regression 判断，不改变 registry 对 release readiness comparison 输出的消费路径，也不改变旧 `minigpt.release_readiness_comparison` 的导出入口。

## 前置路线

v170 接在 v153-v170 的 artifact split 收束路线里。v154 已经拆过 release readiness dashboard 的 artifact 输出，v149-v151 又把 CI workflow hygiene 接入 readiness comparison、registry 和 maturity summary。到 v170，跨版本 release readiness comparison 本身也需要把“比较算法”和“证据写出”分开。

这版来自当前 module pressure 报告：v169 后最大模块变成 `src/minigpt/release_readiness_comparison.py`。它是成熟治理链路里的关键节点，但输出层边界稳定，所以适合低风险拆分。

## 关键文件

- `src/minigpt/release_readiness_comparison.py`：保留 comparison 主流程，继续读取 readiness reports、生成 rows、计算 deltas、summary 和 recommendations。
- `src/minigpt/release_readiness_comparison_artifacts.py`：新增 artifact 模块，负责 JSON、CSV、delta CSV、Markdown、HTML 写出和 HTML 片段渲染。
- `tests/test_release_readiness_comparison.py`：继续覆盖 improvement、regression、CI workflow regression、输出文件和 HTML escaping，并新增 facade identity 测试。
- `README.md`、`c/README.md`、`代码讲解记录_项目成熟度阶段/README.md`：登记 v170 能力、tag 和证据位置。
- `c/170/解释/说明.md`：记录本版运行截图分别证明什么。

## 核心数据结构

`build_release_readiness_comparison()` 返回的 report 仍然是本链路的中心对象。v170 没改字段，只改变谁负责把这些字段写成证据。

关键字段包括：

- `baseline_path`：基准 release readiness report 路径。如果传入 `baseline_path`，它会排到第一位。
- `readiness_paths`：参与比较的所有 readiness report 路径。
- `rows`：每个 readiness report 的扁平行，包含 `release_name`、`readiness_status`、`decision`、`gate_status`、`audit_status`、`ci_workflow_status`、`request_history_status`、panel counts 等。
- `deltas`：相对 baseline 的变化，包含 `status_delta`、`delta_status`、`audit_score_delta`、`ci_workflow_failed_check_delta`、`ci_workflow_status_changed`、`changed_panels` 和 `explanation`。
- `summary`：跨报告摘要，例如 ready/blocked/improved/regressed 数量、panel delta 数量和 CI workflow regression 数量。
- `recommendations`：根据 regression、CI workflow regression、panel changes 等状态生成的下一步建议。

这些字段仍由 comparison 主模块生成。artifact 模块只消费 report，不创造新的 comparison 语义。

## 主流程

`release_readiness_comparison.py` 的主流程仍是：

1. `build_release_readiness_comparison()` 收集输入路径，并把 baseline 放到第一位。
2. `_read_required_json()` 读取每个 `release_readiness.json`。
3. `_row_from_report()` 把 dashboard summary/panels 转成可比较行。
4. `_delta_from_baseline()` 计算每个 compared report 相对 baseline 的变化。
5. `_delta_explanation()` 生成可读解释，说明 status、panel、audit score、CI workflow 的变化。
6. `_summary()` 汇总 improved/regressed/panel delta/CI workflow regression 数量。
7. `_recommendations()` 生成发布前需要关注的建议。
8. 旧模块 re-export artifact 写出函数，保持旧入口不变。

v170 之后，主模块从 521 行降到 242 行，但比较算法没有改变。

## Artifact 模块

`release_readiness_comparison_artifacts.py` 接管这些函数：

- `write_release_readiness_comparison_json()`：写出完整 comparison report JSON。
- `write_release_readiness_comparison_csv()`：写出 readiness matrix CSV。
- `write_release_readiness_delta_csv()`：写出 baseline delta CSV，保留 changed panels 和 CI workflow delta 字段。
- `render_release_readiness_comparison_markdown()`：生成 Markdown 证据，包含 summary、readiness matrix、deltas 和 recommendations。
- `render_release_readiness_comparison_html()`：生成 HTML 证据页，展示统计卡片、readiness matrix、deltas 和 recommendations。
- `write_release_readiness_comparison_outputs()`：统一写出 JSON/CSV/delta CSV/Markdown/HTML 五类证据，并返回路径字典。

这个模块复用 `report_utils` 的 `write_json_payload()`、`csv_cell()`、`html_escape()`、`list_of_dicts()` 等 helper。HTML/CSS 和表格布局只属于证据发布层，不再挤在 comparison 算法文件里。

## 兼容性

旧调用方如果继续这样导入，仍然有效：

```python
from minigpt.release_readiness_comparison import write_release_readiness_comparison_outputs
```

原因是 v170 在 `release_readiness_comparison.py` 中 re-export 了新 artifact 模块的写出和渲染函数，并在 `__all__` 中继续登记旧名字。

`tests/test_release_readiness_comparison.py` 新增 facade identity 测试，断言旧模块导出的 render/write 函数和新 artifact 模块里的函数是同一个对象。这能防止未来旧模块重新复制一套输出实现。

## 测试覆盖

本版测试覆盖了三层：

- 定向 release readiness comparison 测试：`python -B -m unittest tests.test_release_readiness_comparison -v`，覆盖 improvement、regression、CI workflow regression、输出文件、HTML escaping 和 facade identity。
- 全量测试：`python -B -m unittest discover -s tests -v`，确认 release、registry、maturity、training-scale、server/playground 等旧能力没有被破坏。
- 维护和编码卫生：`check_maintenance_batching.py` 确认 module pressure 仍为 `pass`，`check_source_encoding.py` 确认 BOM、syntax 和 Python 3.11 compatibility 仍干净。

## 运行证据

v170 的截图归档在 `c/170`：

- `01-release-readiness-comparison-tests.png`：定向测试通过，证明 comparison 行为和 facade identity 仍成立。
- `02-release-readiness-comparison-artifact-smoke.png`：直接导入旧模块和新 artifact 模块，证明 render/write 函数对象一致，并记录主模块 242 行、artifact 模块 335 行。
- `03-maintenance-smoke.png`：维护批次和 module pressure 检查，证明本版没有制造新的大模块压力。
- `04-source-encoding-smoke.png`：源码编码卫生检查通过，避免 BOM 或 syntax hygiene 问题。
- `05-full-unittest.png`：全量 unittest 通过。
- `06-docs-check.png`：README、`c/170`、讲解索引、源码和测试关键字检查通过。

这些截图不是临时日志，而是 v170 的版本证据。临时 `tmp_v170_*` 日志会在提交前清理。

## 边界说明

`release_readiness_comparison_artifacts.py` 不是新的比较器。它不读取 readiness JSON，不决定 baseline，不计算 status delta，不判断 CI workflow regression，也不生成 recommendations。

它只消费 comparison report，并把 report 写成机器可读和人工可读的证据。后续如果要调整发布就绪比较逻辑，主要看 `release_readiness_comparison.py`；如果要调整 CSV/Markdown/HTML 展示，主要看 artifact 模块。

## 一句话总结

v170 把 release readiness comparison 的 artifact 输出层独立出来，让 `release_readiness_comparison.py` 从 521 行降到 242 行，同时保持 comparison schema、baseline override、delta 逻辑、registry 消费路径和旧 facade 导出不变。
