# v123 dashboard render split 代码讲解

## 本版目标

v123 继续执行 v110 的 module pressure audit 路线，目标是把 `dashboard.py` 里已经稳定的 HTML/CSS 渲染层拆到独立模块：

```text
dashboard.py        -> artifact 发现、JSON/TXT 读取、summary payload 组装、write_dashboard、兼容导出
dashboard_render.py -> HTML/CSS、section builders、formatting、escaping、image/link helper
```

本版解决的问题是：`dashboard.py` 同时承担运行目录证据发现、summary payload 组装、静态 HTML 页面渲染、CSS 样式、各区块表格/图片/link 生成和 HTML escaping。v123 把渲染边界拆出后，主模块从 644 非空行降到 222 非空行，同时保留旧调用方式。

本版明确不做：

- 不改变 `build_dashboard_payload()` 的 payload 结构。
- 不改变 `collect_artifacts()` 的 artifact key、title、path、kind、description、href 语义。
- 不改变 `scripts/build_dashboard.py` 的 CLI 参数、默认输出路径和输出文件名。
- 不改变 `write_dashboard()` 的返回 payload。
- 不移除 `minigpt.dashboard.render_dashboard_html` 的旧 public 导出。

## 前置路线

v123 接在这条维护收口路线后面：

```text
v110 module pressure audit
 -> v115 playground asset split
 -> v116 registry data/render split
 -> v121 maturity artifact split
 -> v122 training portfolio comparison artifact split
 -> v123 dashboard render split
```

这说明本版不是重新设计 dashboard，也不是扩充 UI 功能，而是把已经稳定的“运行证据页面发布”从“运行证据 payload 组装”里拆出来。

## 关键文件

```text
src/minigpt/dashboard_render.py
src/minigpt/dashboard.py
tests/test_dashboard_render.py
README.md
代码讲解记录_项目成熟度阶段/README.md
c/123/图片
c/123/解释/说明.md
```

`src/minigpt/dashboard_render.py` 是本版新增的 render 层。它负责：

- 渲染完整 dashboard HTML。
- 管理 dashboard CSS。
- 渲染 stats、artifacts、manifest、dataset、model、training、eval suite、pair batch、prediction、attention、chat、text 和 warning 区块。
- 渲染图片链接、artifact anchors、数字格式化、文本截断和 HTML escaping。

`src/minigpt/dashboard.py` 仍然是 dashboard 主模块。它负责：

- 发现 run 目录下的 checkpoint、tokenizer、metrics、manifest、dataset、eval suite、pair batch、model report、prediction、attention、chat、experiment card 等 artifact。
- 读取 JSON/TXT 文件并记录 warning。
- 从各类 artifact 组装 `summary` 和完整 payload。
- 写出 dashboard HTML。
- 从 `dashboard_render.py` 重新导出 `render_dashboard_html()`，保持历史调用兼容。

## 核心数据结构

dashboard payload 的关键字段包括：

- `title`：dashboard 页面标题。
- `run_dir`：被展示的 run 目录。
- `output_path`：输出 dashboard HTML 的路径。
- `summary`：artifact 数量、metrics 行数、tokenizer、loss、perplexity、eval suite、pair batch、dataset、git commit 和参数量等摘要。
- `artifacts`：每个 artifact 的 key、title、path、kind、description、exists、size_bytes 和 href。
- `train_config`、`history_summary`、`eval_report`、`eval_suite`、`pair_batch`、`pair_trend`、`run_manifest`、`dataset_report`、`dataset_quality`、`dataset_version`、`model_report`、`predictions`、`attention`、`transcript`：各类原始证据。
- `sample_text`、`generated_text`、`warnings`：文本展示和读取警告。

这些字段仍然由 `dashboard.py` 计算。`dashboard_render.py` 只消费 payload，不扫描文件系统，不读取 run 目录。

## 核心函数

`render_dashboard_html(payload)`
生成完整自包含 HTML 页面。它是旧 public 入口，现在由 `dashboard_render.py` 实现，并由 `dashboard.py` 重新导出。

`_style()`
集中保存 dashboard CSS，包括页面、卡片、artifact、panel、表格、图片和 warning 样式。

`_stats_grid()` / `_artifact_grid()`
渲染页面顶部统计卡片和 artifact 列表，负责 artifact 链接、文件大小和 missing 状态。

`_manifest_section()` / `_dataset_section()` / `_model_section()` / `_training_section()` / `_eval_suite_section()` / `_pair_batch_section()`
把 payload 里的结构化证据转成展示区块。

`_prediction_section()` / `_attention_section()` / `_chat_section()` / `_text_section()` / `_warning_section()`
渲染模型检查、注意力、聊天记录、文本样本和 warning。

`_e()`
统一 HTML escaping，继续保护标题、sample、warning、路径和用户可见文本。

## 输入输出边界

v123 后的运行流程是：

```text
run directory
 -> dashboard.py collect_artifacts()
 -> dashboard.py build_dashboard_payload()
 -> dashboard_render.py render_dashboard_html()
 -> dashboard.py write_dashboard()
 -> scripts/build_dashboard.py 保持原 CLI 和输出路径
```

render 模块不读文件、不知道 run 目录结构，也不计算 summary。它只把 payload 渲染为 HTML。这样后续如果只调整 dashboard 页面样式或区块布局，不需要碰 artifact 发现和 payload 组装；如果只调整 payload 读取，也不需要碰 HTML/CSS。

## 测试覆盖

`tests/test_dashboard_render.py` 新增三类断言：

- 直接调用 `dashboard_render.render_dashboard_html()`，确认标题、sample、warning 都正确 HTML escaping，并且 artifact 链接保留。
- 检查 `dashboard.render_dashboard_html is dashboard_render.render_dashboard_html`，保护旧导出兼容。
- 通过 `dashboard.write_dashboard()` 写出 HTML，确认写文件路径和 render 模块集成正常。

原有 `tests/test_dashboard.py` 继续覆盖：

- artifact 发现和 href 生成。
- payload summary 读取 train config、history、eval、manifest、dataset、pair batch 和 pair trend。
- dashboard 中 pair batch/trend 链接。
- HTML escaping。
- invalid JSON warning。

这说明 v123 拆的是 HTML 渲染边界，不是 dashboard payload 或 artifact 发现规则。

## 运行证据

v123 的运行证据放在：

```text
c/123/图片
c/123/解释/说明.md
```

关键证据包括：

- dashboard render 单测、dashboard 回归、compileall 和全量 unittest。
- dashboard CLI smoke，真实写出 `dashboard.html`。
- maintenance batching/module pressure smoke，证明拆分后最大压力点已转移到 `playground_assets.py`。
- output check，证明 HTML escaping、artifact link、pair batch section 和旧 facade 导出稳定。
- Playwright 使用已安装 Google Chrome 打开生成的 dashboard HTML 页面。
- README、c/README、代码讲解索引和本讲解文件的文档闭环检查。

这些截图不是临时调试文件，而是 v123 tag 的运行证明。临时输出目录仍按 cleanup gate 删除。

## 一句话总结

v123 把 dashboard 从“一个模块既组装 payload 又渲染页面”推进到“payload 组装和 HTML 发布分层”，让运行证据页面也更容易维护。
