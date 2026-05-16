# v172 eval suite artifact split 代码讲解

## 本版目标

v172 的目标是把 `eval_suite.py` 中的 artifact 输出层拆到 `eval_suite_artifacts.py`，让固定 prompt benchmark 模块继续向“语义构建”和“证据发布”分离。

它解决的问题是：`eval_suite.py` 原来同时负责 prompt case、prompt suite、prompt result、eval report schema、JSON/CSV/SVG/HTML 写出和 HTML 页面渲染。前半部分是 benchmark 语义，后半部分是证据输出。随着项目后续 benchmark scorecard、generation quality、registry 和 dashboard 都消费 eval suite 产物，这个模块适合把输出层拿出去，避免早期核心文件继续膨胀。

本版明确不做这些事：不改变默认 prompt 内容，不改变 suite JSON 加载格式，不改变 `PromptCase`、`PromptSuite`、`PromptResult` 字段，不改变 `build_eval_suite_report()` 返回 schema，不改变 `scripts/eval_suite.py` 命令，也不改变旧的 `minigpt.eval_suite` 导出入口。

## 前置路线

v172 接在项目长期 artifact split 和 benchmark 治理路线后面。早期 v16-v35 建立了固定 prompt eval suite 和 benchmark metadata，后续 generation quality、benchmark scorecard、registry、experiment card、project audit、training portfolio 都把 `eval_suite/eval_suite.json` 当作固定评估证据来消费。

这意味着 eval suite 是真实能力链路的上游，不只是一个展示报告。把 artifact writer 拆出来以后，后续如果要调整 HTML/SVG 展示，不会挤在 prompt/report schema 文件里；如果要调整 prompt suite 语义，也不会误碰输出渲染。

## 关键文件

- `src/minigpt/eval_suite.py`：保留 prompt case 校验、prompt suite 加载、prompt result 统计和 eval report schema 构建。
- `src/minigpt/eval_suite_artifacts.py`：新增 artifact 模块，负责 JSON、CSV、SVG、HTML 写出和 HTML 页面渲染。
- `tests/test_eval_suite.py`：保留原有输出测试，并新增 facade identity 测试。
- `README.md`、`c/172/解释/说明.md`、`代码讲解记录_项目成熟度阶段/README.md`：记录版本能力、证据位置和讲解索引。

## 核心数据结构

`PromptCase` 仍然描述单条固定 prompt：

- `name`：case 标识，用于结果行和报告展示。
- `prompt`：输入文本。
- `max_new_tokens`、`temperature`、`top_k`、`seed`：生成参数。
- `task_type`：任务类型，例如 continuation、qa、summary、structured、factual-consistency。
- `difficulty`：难度标签。
- `expected_behavior`：期望行为说明，用于后续人工判断和 benchmark scorecard 解释。
- `tags`：补充标签，支持字符串或列表输入，最终规范成 tuple。

`PromptSuite` 仍然是 suite 层元数据，包含 `name`、`version`、`description`、`language` 和 `cases`。

`PromptResult` 仍然是模型输出后的结果对象，记录 prompt、生成文本、continuation、字符数和 unique char 数。`build_prompt_result()` 继续用“generated 是否以 prompt 开头”来切出 continuation。

`build_eval_suite_report()` 返回的 report schema 不变，关键字段包括：

- `schema_version`
- `checkpoint`
- `tokenizer`
- `suite`
- `benchmark`
- `case_count`
- `avg_continuation_chars`
- `avg_unique_chars`
- `task_type_counts`
- `difficulty_counts`
- `results`

这些字段仍然由 `eval_suite.py` 生成；v172 只改变谁负责把 report 写成文件。

## Artifact 模块

`eval_suite_artifacts.py` 接管这些函数：

- `write_eval_suite_json()`：写出完整 eval suite JSON。
- `write_eval_suite_csv()`：把每个 result 扁平化成 CSV 行。
- `write_eval_suite_svg()`：生成 unique char bar chart。
- `render_eval_suite_html()`：生成浏览器可读 HTML 报告。
- `write_eval_suite_html()`：写出 HTML。
- `write_eval_suite_outputs()`：统一写出 JSON、CSV、SVG、HTML，并返回路径字典。

这个模块只消费 report，不构造 prompt case，不计算 prompt result，也不决定 benchmark schema。它是证据输出层。

## 兼容性

旧调用方式仍然有效：

```python
from minigpt.eval_suite import write_eval_suite_outputs
```

原因是 `eval_suite.py` 从 `eval_suite_artifacts.py` re-export 了 writer 和 renderer。`scripts/eval_suite.py` 也继续从 `minigpt.eval_suite` 导入 `write_eval_suite_outputs`，所以 CLI 使用方式不变。

`tests/test_eval_suite.py` 新增断言：

```python
self.assertIs(eval_suite.write_eval_suite_outputs, eval_suite_artifacts.write_eval_suite_outputs)
self.assertIs(eval_suite.render_eval_suite_html, eval_suite_artifacts.render_eval_suite_html)
```

这能防止未来旧模块重新复制一份 writer 实现，造成新旧入口行为分叉。

## 测试覆盖

本版测试覆盖四层：

- `tests.test_eval_suite`：覆盖默认 prompt suite、suite JSON 加载、legacy list payload、prompt result 统计、report summary、artifact 输出和 facade identity。
- 全量 unittest：确认 registry、dashboard、benchmark scorecard、generation quality、training portfolio 等 eval suite 消费方不受影响。
- source encoding hygiene：确认无 BOM、无 syntax error、Python 3.11 compatibility 干净。
- maintenance batching：确认 module pressure 为 `pass`，没有产生新的 warn/critical 模块。

## 运行证据

v172 的截图归档在 `c/172`：

- `01-eval-suite-tests.png`：定向 eval suite 测试通过。
- `02-eval-suite-artifact-smoke.png`：旧模块和新 artifact 模块 writer/render 函数对象一致，并记录主模块 322 行、artifact 模块 220 行。
- `03-maintenance-smoke.png`：module pressure 为 `pass`。
- `04-source-encoding-smoke.png`：源码编码和语法卫生通过。
- `05-full-unittest.png`：全量 394 个测试通过。
- `06-docs-check.png`：README、归档、讲解索引、源码和测试关键词一致。

这些截图是版本证据，临时 `tmp_v172_*` 日志和 `runs/*v172*` 输出会在提交前清理。

## 边界说明

`eval_suite_artifacts.py` 不负责加载 suite，不负责调用模型，不负责生成 prompt result，也不负责分析 generation quality。它只把已经构造好的 eval suite report 写成机器可读和人可读产物。

如果后续要新增 prompt 类型或修改 benchmark schema，主要看 `eval_suite.py`；如果要调整 CSV 字段、SVG chart 或 HTML 布局，主要看 `eval_suite_artifacts.py`。

## 一句话总结

v172 把 eval suite 的 JSON/CSV/SVG/HTML 输出层独立成 `eval_suite_artifacts.py`，让 `eval_suite.py` 从 517 行降到 322 行，同时保持固定 prompt benchmark schema、CLI 调用和旧 facade 导出不变。
