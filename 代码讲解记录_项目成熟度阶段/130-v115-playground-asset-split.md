# 第一百一十五版代码讲解：Playground Asset Split

## 本版目标

v115 的目标是继续落实 v110 的 `module pressure audit`，把 `playground.py` 里已经稳定的 HTML CSS/JavaScript 资产抽成独立模块 `playground_assets.py`。这版不是新增 playground 功能，也不是修改本地推理 API，而是把“页面资产”和“payload/链接/HTML 组装”分开维护，让 `playground.py` 不再同时承载数据读取、链接发现、页面片段和 700 多行静态脚本。

本版明确不做：
- 不修改 `scripts/build_playground.py` 和 `scripts/serve_playground.py` 的 CLI 契约。
- 不修改 `/api/checkpoints`、`/api/generate-stream`、`/api/request-history`、`/api/checkpoint-compare`、`/api/generate-pair` 或 `/api/generate-pair-artifact`。
- 不改变 `build_playground_payload()`、`render_playground_html()`、`write_playground()` 的公开调用方式。
- 不合并处理 `registry.py`，它仍作为下一轮候选压力点。

## 路线来源

本版来自 v110-v114 的厚模块治理路线：

```text
v110 module pressure audit
 -> v111 registry asset split
 -> v112 pair artifact split
 -> v113 request history core split
 -> v114 benchmark scorecard artifact split
 -> v115 playground asset split
```

外部质量反馈指出 `playground.py` 和 `registry.py` 仍是剩余大文件，同时提醒 v112-v114 的版本虽然细，但每版都有明确边界。v115 接受这个判断：先处理 `playground.py` 的静态资产边界，保留 `registry.py` 给后续版本，避免同一版改动面过宽。

## 关键文件

- `src/minigpt/playground_assets.py`
  - 新增模块。
  - 提供 `playground_style()` 和 `playground_script(page_data)`。
  - 承接 playground 页面 `<style>` 和 `<script>`，包括布局、checkpoint selector、streaming generation、request history、checkpoint comparison 和 pair generation 的前端逻辑。

- `src/minigpt/playground.py`
  - 保留 playground 的 Python 侧核心职责。
  - 继续负责 `build_playground_payload()`、run artifact 链接发现、HTML section 组装、sampling table、warning section 和 `write_playground()`。
  - `_style()` 和 `_script()` 变为薄包装，委托到 `playground_assets.py`。

- `tests/test_playground_assets.py`
  - 新增资产层测试。
  - 锁住 CSS 布局关键 class、JS 交互入口、API endpoint 字符串和 render 集成。

- `tests/test_playground.py`
  - 原有 playground 回归测试继续存在，证明 payload、链接发现、HTML 控件和文件写出契约没有因为拆分改变。

- `README.md`、`c/115`、本讲解文件
  - 记录 v115 的版本目标、运行证据、截图归档和下一步候选压力点。

## 核心数据结构

`playground_script(page_data)` 的输入仍是 `render_playground_html()` 组装出的页面状态：

```json
{
  "runDir": "runs/minigpt",
  "defaults": {
    "prompt": "人工智能",
    "max_new_tokens": 80,
    "temperature": 0.8,
    "top_k": 30,
    "seed": 42
  },
  "commands": {},
  "checkpoints": [],
  "checkpointComparison": [],
  "requestHistory": [],
  "requestHistoryDetail": null,
  "requestHistoryFilters": {
    "status": "",
    "endpoint": "",
    "checkpoint": "",
    "limit": 12
  },
  "streamController": null
}
```

v115 不改变这个对象的字段，只改变它被序列化进页面的位置：以前在 `playground.py` 的 `_script()` 里，现在在 `playground_assets.py` 的 `playground_script()` 里。

## 核心函数

`playground_style()`

返回完整 `<style>...</style>`。它包含：
- 页面主色、边框、面板、按钮、表格和响应式布局。
- `.builder`、`.controls`、`.pair-grid`、`.status-pill`、`.detail-panel` 等 playground 关键 class。
- 移动端 `@media (max-width: 760px)` 布局。

这部分是最终 HTML 证据的一部分，不是临时样式，也不是测试专用 fixture。

`playground_script(page_data)`

返回完整 `<script>...</script>`。它包含：
- `MiniGPTPlayground` 初始状态。
- checkpoint selector 和 command builder。
- `/api/generate-stream` 流式生成、`AbortController` 取消和 SSE 解析。
- `/api/request-history` 筛选、CSV 导出和详情查询。
- `/api/checkpoint-compare` 对比表。
- `/api/generate-pair` 与 `/api/generate-pair-artifact` 双 checkpoint 生成。

它仍是静态 HTML 的内嵌脚本；只有在用户启动 `scripts/serve_playground.py` 后，页面才会连接本地 API。

`_style()` / `_script()`

`playground.py` 保留这两个薄包装：

```python
def _style() -> str:
    return playground_style()

def _script(page_data: dict[str, Any]) -> str:
    return playground_script(page_data)
```

这样 `render_playground_html()` 的调用顺序不变，旧测试和旧导入路径也不需要改。

## 运行流程

本版后的页面生成流程是：

```text
scripts/build_playground.py
 -> write_playground()
 -> build_playground_payload()
 -> render_playground_html()
 -> _style() -> playground_assets.playground_style()
 -> _script(page_data) -> playground_assets.playground_script(page_data)
 -> playground.html
```

本地服务流程保持不变：

```text
scripts/serve_playground.py
 -> serves playground.html
 -> browser fetches /api/checkpoints, /api/generate-stream, /api/request-history, ...
 -> request history and pair artifacts continue through server-side modules
```

## 为什么这是合理的轻量优化

`playground.py` 原本约 1157 行，其中大部分体量来自稳定的 CSS 和 JavaScript 字符串。v115 后：
- `playground.py` 降到约 454 行。
- `playground_assets.py` 承接约 718 行静态资产。
- 页面 payload、链接发现、HTML section、公开函数和本地 API 字符串保持不变。

这比继续新增 report-only 功能更有维护价值，因为后续修改 UI 交互或样式时可以集中看 `playground_assets.py`，而修改 run artifact 链接和 payload 时仍看 `playground.py`。

## 测试覆盖

`tests/test_playground_assets.py` 保护：
- `playground_style()` 以 `<style>` 包裹，并包含 `.builder`、`.pair-grid`、`.status-pill.timeout` 和移动端媒体查询。
- `playground_script()` 以 `<script>` 包裹，并包含 `/api/checkpoints`、`/api/generate-stream`、`AbortController`、`requestHistoryQuery`、`/api/request-history-detail`、`/api/checkpoint-compare` 和 `/api/generate-pair-artifact`。
- `render_playground_html()` 会嵌入抽出的资产，并保留 `MiniGPTPlayground`、`runs/demo` 和 `Stream Generate`。

`tests/test_playground.py` 继续保护：
- sampling report 读取。
- pair batch/trend 链接发现。
- HTML escaping。
- 控件、请求历史、checkpoint comparison、pair generation 等页面契约。
- `write_playground()` 文件写出。

## 证据闭环

v115 证据放在 `c/115`：
- `01-unit-tests.png`: playground asset tests、playground regression、compileall 和全量 unittest。
- `02-playground-asset-smoke.png`: 行数下降、资产导出和 maintenance/module-pressure smoke。
- `03-playground-asset-structure-check.png`: 新模块、测试、README、讲解和 c/115 归档结构检查。
- `04-playground-output-check.png`: 生成 HTML 的 CSS/JS 嵌入、关键 API 字符串和 wrapper parity 检查。
- `05-playwright-playground-html.png`: 真实 Google Chrome 打开 playground HTML 的渲染截图。
- `06-docs-check.png`: README、c/README 和项目成熟度阶段索引已指向 v115。

这些截图和说明是最终证据；临时生成的 run 目录、测试缓存和 `__pycache__` 会在提交前清理。

## 一句话总结

v115 把 playground 的静态页面资产从 UI 组装核心里拆出，让本地推理 playground 在不改变页面和 API 契约的前提下变得更容易维护。
