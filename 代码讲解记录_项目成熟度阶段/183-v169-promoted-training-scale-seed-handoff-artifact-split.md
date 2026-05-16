# v169 promoted training scale seed handoff artifact split 代码讲解

## 本版目标

v169 的目标是把 `promoted_training_scale_seed_handoff.py` 里的 artifact 写出和页面渲染逻辑拆到 `promoted_training_scale_seed_handoff_artifacts.py`。

它解决的是 seed handoff 模块职责继续变宽的问题。这个模块原来同时负责读取 v81/v168 产生的 promoted seed、判断是否允许 handoff、可选执行 next plan command、读取 plan artifact、生成 summary/recommendations，并写出 JSON/CSV/Markdown/HTML 证据。前半段属于执行 handoff 语义，后半段属于证据发布层。v169 只拆后半段。

本版明确不做这些事：不改变 handoff schema，不改变命令执行逻辑，不改变 timeout 行为，不改变 plan artifact 检测规则，不改变旧 `minigpt.promoted_training_scale_seed_handoff` 的导出入口。

## 前置路线

这版接在 v168 后面。v168 已经把 promoted seed builder 的 artifact 输出层拆到 `promoted_training_scale_seed_artifacts.py`，但 seed 之后的 handoff 模块仍然是训练规模链路里的大模块之一。

v169 顺着同一条训练规模治理路线推进：

```text
promoted baseline decision -> promoted seed -> promoted seed handoff -> next training scale plan artifacts
```

v169 让 `promoted_training_scale_seed_handoff.py` 更专注于 handoff 决策和执行，artifact 模块专注于把 report 写成可归档证据。

## 关键文件

- `src/minigpt/promoted_training_scale_seed_handoff.py`：保留 handoff 主流程，继续读取 seed、判断 blocker、执行或跳过 plan command、加载 plan report、生成 artifact rows、summary 和 recommendations。
- `src/minigpt/promoted_training_scale_seed_handoff_artifacts.py`：新增 artifact 模块，负责 JSON、CSV、Markdown、HTML 写出和 HTML 片段渲染。
- `tests/test_promoted_training_scale_seed_handoff.py`：继续覆盖 planned、blocked、execute、failed、HTML escaping，并新增 facade identity 测试。
- `README.md`、`c/README.md`、`代码讲解记录_项目成熟度阶段/README.md`：登记 v169 能力、tag 和证据位置。
- `c/169/解释/说明.md`：记录本版运行截图分别证明什么。

## 核心数据结构

`build_promoted_training_scale_seed_handoff()` 返回的 report 仍然是本链路的中心对象。v169 没改它的字段，只改变谁负责写出这些字段。

关键字段包括：

- `seed_path`：被消费的 promoted seed 文件路径，用来追溯上游决策来源。
- `seed_status`：seed 自身状态，影响是否允许继续 handoff。
- `command` / `command_text`：下一轮 `scripts/plan_training_scale.py` 命令的结构化列表和可读字符串。
- `execution`：执行结果，包含 `status`、`returncode`、`elapsed_seconds`、`stdout_tail`、`stderr_tail` 和 `blocked_reason`。
- `plan_report` / `plan_report_path`：如果 next plan 已生成，则读取训练规模计划报告，供后续 batch command 继续消费。
- `artifact_rows`：由 plan 输出路径生成的 artifact 存在性清单，记录哪些 JSON/CSV/Markdown/HTML 证据已经落盘。
- `summary`：面向 gate 或 README 的短摘要，例如 `handoff_status`、`available_artifact_count`、`plan_status`、`next_batch_command_available`。
- `recommendations`：根据 handoff 状态、plan artifact 和 execution 结果生成的下一步建议。

这些字段仍由 handoff 主模块生成。artifact 模块只读取 report，不创建新的 handoff 语义。

## 主流程

`promoted_training_scale_seed_handoff.py` 的主流程仍是：

1. `load_promoted_training_scale_seed()` 读取 seed JSON，并保留 `_source_path`。
2. `build_promoted_training_scale_seed_handoff()` 从 seed 中拿到 `next_plan` 和 command。
3. `_handoff_allowed()` 判断 ready/review/blocked 状态和命令是否可用。
4. `_execution_result()` 根据 `execute` 和 `allowed` 决定是 report-only、blocked、completed、failed 还是 timeout。
5. `_load_plan_report()` 和 `_artifact_rows()` 读取 next plan 产物状态。
6. `_summary()` 和 `_recommendations()` 给下游报告、README 和发布证据使用。
7. 旧模块 re-export artifact 写出函数，保持旧入口不变。

v169 之后，主模块从 530 行降到 301 行，但这条流程没有改变。

## Artifact 模块

`promoted_training_scale_seed_handoff_artifacts.py` 接管这些函数：

- `write_promoted_training_scale_seed_handoff_json()`：写出完整 report JSON。
- `write_promoted_training_scale_seed_handoff_csv()`：写出一行摘要 CSV，字段覆盖 handoff status、seed status、return code、artifact count、plan status 等。
- `render_promoted_training_scale_seed_handoff_markdown()`：生成 Markdown 证据，包含 command、execution、plan artifacts、next batch command 和 recommendations。
- `render_promoted_training_scale_seed_handoff_html()`：生成 HTML 证据页，展示状态卡片、命令、执行结果、plan artifact 表格和 plan report 摘要。
- `write_promoted_training_scale_seed_handoff_outputs()`：统一写出 JSON/CSV/Markdown/HTML 四类证据，并返回路径字典。

这个模块复用 `report_utils` 的 `write_json_payload()`、`write_csv_row()`、`html_escape()`、`markdown_cell()`、`string_list()` 等公共 helper。这样输出层继续走已有报告基础设施，而不是恢复私有写出逻辑。

## 兼容性

旧调用方如果继续这样导入，仍然有效：

```python
from minigpt.promoted_training_scale_seed_handoff import write_promoted_training_scale_seed_handoff_outputs
```

原因是 v169 在 `promoted_training_scale_seed_handoff.py` 中 re-export 了新 artifact 模块的写出和渲染函数，并在 `__all__` 中继续登记旧名字。

`tests/test_promoted_training_scale_seed_handoff.py` 新增 facade identity 测试，断言旧模块导出的函数和新模块里的函数是同一个对象。这比只测试“能调用”更强，因为它能防止以后旧模块又悄悄复制一份输出逻辑。

## 测试覆盖

本版测试覆盖了三层：

- 定向 handoff 测试：`python -B -m unittest tests.test_promoted_training_scale_seed_handoff -v`，覆盖 planned、blocked、execute success、execute failure、HTML escaping 和 facade identity。
- 全量测试：`python -B -m unittest discover -s tests -v`，确认训练规模链、报告链、server/playground、release/maturity 等旧能力没有被破坏。
- 维护和编码卫生：`check_maintenance_batching.py` 确认 module pressure 仍为 `pass`，`check_source_encoding.py` 确认 BOM、syntax 和 Python 3.11 compatibility 仍干净。

## 运行证据

v169 的截图归档在 `c/169`：

- `01-promoted-seed-handoff-tests.png`：定向测试通过，证明 handoff 行为和 facade identity 仍成立。
- `02-promoted-seed-handoff-artifact-smoke.png`：直接导入旧模块和新 artifact 模块，证明 render/write 函数对象一致，并记录主模块 301 行、artifact 模块 277 行。
- `03-maintenance-smoke.png`：维护批次和 module pressure 检查，证明本版没有制造新的大模块压力。
- `04-source-encoding-smoke.png`：源码编码卫生检查通过，避免再次出现 BOM 或 syntax hygiene 问题。
- `05-full-unittest.png`：全量 unittest 通过。
- `06-docs-check.png`：README、`c/169`、讲解索引、源码和测试关键字检查通过。

这些截图不是临时日志，而是 v169 的版本证据。临时 `tmp_v169_*` 日志会在提交前清理。

## 边界说明

`promoted_training_scale_seed_handoff_artifacts.py` 不是新的执行器。它不运行 command，不判断 allow_review，不读取 seed，不判断 timeout，也不决定 next batch command 是否可用。

它只消费 handoff report，并把 report 写成机器可读和人工可读的证据。这个边界能让后续如果要改 execution 或 timeout，主要看 handoff 主模块；如果要改 HTML/Markdown 展示，主要看 artifact 模块。

## 一句话总结

v169 把 promoted training scale seed handoff 的 artifact 输出层独立出来，让 `promoted_training_scale_seed_handoff.py` 从 530 行降到 301 行，同时保持 handoff schema、真实命令执行、timeout、plan artifact 检测和旧 facade 导出不变。
