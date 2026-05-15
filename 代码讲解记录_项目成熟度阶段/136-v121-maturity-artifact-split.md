# v121 maturity artifact split 代码讲解

## 本版目标

v121 继续执行 v110 的 module pressure audit 路线，目标是把 `maturity.py` 里已经稳定的成熟度报告输出层拆到独立模块：

```text
maturity.py           -> 成熟度规则、版本/归档发现、上下文汇总、推荐项、兼容导出
maturity_artifacts.py -> JSON/CSV/Markdown/HTML 写入与展示 helper
```

本版解决的问题是：`maturity.py` 同时承担成熟度矩阵计算、registry/request-history/release-readiness 上下文读取、推荐项生成、CSV 展开、Markdown 组装、HTML 页面渲染和 artifact 写入。它已经不是业务逻辑单一的模块。v121 把 artifact 边界拆出后，`maturity.py` 从 697 非空行降到 374 非空行，同时保留旧调用方式。

本版明确不做：

- 不改变 maturity summary 的 JSON schema。
- 不改变 `scripts/build_maturity_summary.py` 的 CLI 参数和输出文件名。
- 不改变 capability specs、成熟度评分、阶段时间线、registry context、request history context、release readiness context 和 recommendations 的计算。
- 不改变 Markdown/HTML 的可见结构和字段语义。
- 不移除 `minigpt.maturity` 里原有的 artifact 函数导出。

## 前置路线

v121 接在这条维护收口路线后面：

```text
v110 module pressure audit
 -> v119 maintenance policy artifact split
 -> v120 benchmark scorecard scoring split
 -> v121 maturity artifact split
```

这说明当前不是继续新增一层治理报告，而是回到已有核心模块，把“成熟度判断”和“证据发布格式”拆开。成熟度模块仍然回答“项目到什么程度了”；artifact 模块只回答“这个结果如何写成 JSON/CSV/Markdown/HTML”。

## 关键文件

```text
src/minigpt/maturity_artifacts.py
src/minigpt/maturity.py
tests/test_maturity_artifacts.py
README.md
代码讲解记录_项目成熟度阶段/README.md
c/121/图片
c/121/解释/说明.md
```

`src/minigpt/maturity_artifacts.py` 是本版新增的 artifact 层。它负责：

- 写入 `maturity_summary.json`。
- 写入 `maturity_capabilities.csv`。
- 渲染和写入 `maturity_summary.md`。
- 渲染和写入 `maturity_summary.html`。
- 把 capability、phase timeline、registry context、release readiness context、request history context 和 recommendations 转成展示段落。

`src/minigpt/maturity.py` 仍然是成熟度主模块。它负责：

- 维护 `CapabilitySpec` 和 `CAPABILITY_SPECS`。
- 发现版本、截图归档、代码讲解记录和测试文件。
- 读取 registry、request history summary 和 release readiness comparison。
- 生成 `build_maturity_summary()` 的 summary 对象。
- 生成 maturity recommendations。
- 从 `maturity_artifacts.py` 重新导出旧 artifact 函数，保持历史调用兼容。

`tests/test_maturity_artifacts.py` 是本版新增测试。它既直接调用新 artifact 模块，也检查旧的 `minigpt.maturity` 导出是否仍然指向新实现。

## 核心数据结构

artifact 层消费的是 `build_maturity_summary()` 生成的 summary dict。关键字段包括：

- `summary`：当前版本、平均成熟度、整体状态、通过/警告/缺失数量。
- `capabilities`：每个能力项的成熟度等级、目标等级、证据、下一步和覆盖版本。
- `phase_timeline`：项目阶段覆盖情况。
- `registry_context`：registry 是否可用、run 数、leaderboard 数、release bundle 数、quality 统计。
- `release_readiness_context`：发布就绪趋势、pass/warn/fail 统计、improved/regressed/stable 数量。
- `request_history_context`：请求历史可用性、总请求、错误率、筛选记录、导出记录和审计状态。
- `recommendations`：面向下一步开发的成熟度建议。

这些字段仍然由 `maturity.py` 计算。`maturity_artifacts.py` 只读取它们，不重新解释成熟度规则。

## 核心函数

`write_maturity_summary_json(summary, path)`
把 summary 原样写成格式化 JSON，是后续脚本和人工检查最稳定的机器可读证据。

`write_maturity_summary_csv(summary, path)`
把 `capabilities` 展平为 CSV。列表和字典字段通过稳定 JSON 字符串保存，避免 CSV 丢失结构信息。

`render_maturity_summary_markdown(summary)`
生成 Markdown 汇总，覆盖 summary、capability matrix、phase timeline、registry context、release readiness context、request history context 和 recommendations。

`render_maturity_summary_html(summary)`
生成自包含 HTML 页面。HTML 会对标题、路径、字段值和列表项做 escaping，避免报告标题或证据文本中出现 `<`、`&` 时破坏页面结构。

`write_maturity_summary_outputs(summary, out_dir)`
统一写出 JSON、CSV、Markdown 和 HTML，并返回输出路径映射。旧 CLI 仍然通过这个函数获得同名产物。

## 输入输出边界

v121 后的运行流程是：

```text
project root
 -> maturity.py 发现版本、截图、讲解、测试和上下文 JSON
 -> maturity.py 生成 maturity summary dict
 -> maturity_artifacts.py 写 JSON/CSV/Markdown/HTML
 -> scripts/build_maturity_summary.py 保持原 CLI 和输出路径
```

artifact 模块不扫描项目、不读取 registry 文件、不计算成熟度等级。它只接收已经组装好的 summary dict 并写出证据文件。这样后续如果要调整页面样式、CSV 字段或 Markdown 表格，不需要碰成熟度规则；如果要调整成熟度规则，也不需要碰页面渲染。

## 测试覆盖

`tests/test_maturity_artifacts.py` 新增两类断言：

- 直接调用 `maturity_artifacts.write_maturity_summary_outputs()`，确认 JSON/CSV/Markdown/HTML 都能写出，CSV 包含 capability 行，Markdown 包含 release readiness 和 request history 区块，HTML 对标题做 escaping。
- 检查 `minigpt.maturity.write_maturity_summary_outputs`、`render_maturity_summary_html`、`render_maturity_summary_markdown` 和 `write_maturity_summary_csv` 仍然是 artifact 模块里的同一组函数，保护旧入口不被拆分破坏。

原有 `tests/test_maturity.py` 继续覆盖：

- 成熟度 summary 的核心字段。
- registry、release readiness 和 request history context。
- recommendations。
- CLI 输出闭环。

这组测试说明 v121 拆的是 artifact 边界，不是成熟度判断本身。

## 运行证据

v121 的运行证据放在：

```text
c/121/图片
c/121/解释/说明.md
```

关键证据包括：

- 单测、compileall 和全量 unittest 回归。
- maturity summary CLI smoke。
- maintenance batching/module pressure smoke。
- artifact 输出结构检查。
- Playwright 使用已安装 Google Chrome 打开生成的 maturity HTML 页面。
- README、c/README、代码讲解索引和本讲解文件的文档闭环检查。

这些截图不是临时调试文件，而是 v121 tag 的运行证明。临时输出目录仍按 cleanup gate 删除。

## 一句话总结

v121 把 maturity summary 从“一个模块既算成熟度又发布证据”推进到“成熟度计算和 artifact 发布分层”，让项目治理链本身也更容易维护。
