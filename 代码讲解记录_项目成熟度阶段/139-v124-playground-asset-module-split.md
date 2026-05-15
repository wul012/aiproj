# v124 playground asset module split 代码讲解

## 本版目标

v124 继续按 v110 module pressure audit 做定向收口，目标是把 `playground_assets.py` 里已经稳定的 CSS 与 JavaScript 静态资产拆成独立模块：

```text
playground_assets.py -> 旧入口 facade
playground_style.py  -> CSS、布局、响应式样式
playground_script.py -> JavaScript、page_data 注入、本地 API UI 交互
```

本版解决的问题是：`playground_assets.py` 只有 `playground_style()` 和 `playground_script()` 两个函数，但文件体量达到 711 非空行。它同时承载 CSS、JavaScript、page data 序列化、checkpoint selector、stream generation、pair generation 和 request-history UI wiring，后续修改样式或脚本时容易互相干扰。

本版明确不做：

- 不改 `render_playground_html()` 的 HTML 结构和 payload 消费方式。
- 不改 `scripts/build_playground.py` 的 CLI、默认输出文件名和 run-dir 行为。
- 不改 `/api/checkpoints`、`/api/generate-stream`、`/api/request-history`、`/api/checkpoint-compare`、`/api/generate-pair`、`/api/generate-pair-artifact` 等本地 endpoint 名称。
- 不移除 `minigpt.playground_assets.playground_style()` 和 `minigpt.playground_assets.playground_script()` 旧导出。

## 前置路线

v124 接在这条维护路线后面：

```text
v110 module pressure audit
 -> v115 playground asset split
 -> v117 server contract split
 -> v123 dashboard render split
 -> v124 playground asset module split
```

v115 先把 playground 的资产从 `playground.py` 抽到 `playground_assets.py`，v124 则继续把这个资产文件内部拆清楚。它不是扩展 playground 功能，而是把已经稳定的 UI 资产边界继续细化。

## 关键文件

```text
src/minigpt/playground_assets.py
src/minigpt/playground_style.py
src/minigpt/playground_script.py
tests/test_playground_asset_modules.py
README.md
c/124/图片
c/124/解释/说明.md
```

`src/minigpt/playground_assets.py` 现在是兼容 facade。它从两个新模块导入函数，并通过 `__all__` 明确公开：

```python
from .playground_script import playground_script
from .playground_style import playground_style

__all__ = ["playground_script", "playground_style"]
```

`src/minigpt/playground_style.py` 只负责 `playground_style()`，返回 `<style>...</style>`。这里保存 playground 的页面变量、按钮/input/textarea 样式、builder 布局、checkpoint comparison 表格、request-history detail、pair grid、artifact link、mobile media query 等 CSS 规则。

`src/minigpt/playground_script.py` 只负责 `playground_script(page_data)`，先用 `json.dumps(..., ensure_ascii=False)` 把 Python payload 注入页面，再返回 `<script>...</script>`。它承接 checkpoint 选择、command 构建、stream generate、AbortController 取消、SSE 解析、request-history 过滤/导出/详情、pair generation 和 pair artifact link 渲染。

## 核心数据结构

`playground_script(page_data)` 消费的 `page_data` 仍来自 `render_playground_html()`，关键字段包括：

- `runDir`：当前 run 目录，用于默认 checkpoint 路径和命令模板。
- `defaults`：prompt、max_new_tokens、temperature、top_k、seed。
- `commands`：静态命令参考，由 `build_playground_commands()` 生成。
- `checkpoints`：checkpoint selector 的候选项。
- `checkpointComparison`：checkpoint compare 表格数据。
- `requestHistory`：request-history 表格数据。
- `requestHistoryDetail`：单条请求详情。
- `requestHistoryFilters`：status、endpoint、checkpoint、limit 等筛选条件。
- `streamController`：页面运行时使用的 AbortController 状态。

这些字段的生产者仍在 `playground.py`。v124 只改变资产函数所在文件，不改变 payload schema。

## 核心函数

`playground_style()`
返回完整 CSS。它没有参数，不读取文件系统，也不依赖 run directory。测试主要保护 `.builder`、`.pair-grid`、`.status-pill.timeout` 和 mobile media query 这些布局契约。

`playground_script(page_data)`
返回完整 JavaScript。它把 `page_data` 序列化到 `MiniGPTPlayground` 常量，然后定义页面交互函数。这里的关键边界是：Python 侧只注入数据和静态脚本，真实 checkpoint list、request history、pair generation 等运行数据由浏览器在本地 server 存在时请求 API。

`playground_assets.playground_style/playground_script`
保留旧导出。已有测试和调用方仍可从 `minigpt.playground_assets` 导入，不需要迁移。

## 输入输出边界

v124 后的 playground 渲染流程仍然是：

```text
run directory
 -> playground.py build_playground_payload()
 -> playground.py render_playground_html()
 -> playground_style.playground_style()
 -> playground_script.playground_script(page_data)
 -> playground.py write_playground()
 -> scripts/build_playground.py
```

新模块不读写文件，不启动服务，不接触模型 checkpoint，也不改变本地 HTTP API。它们只生成静态 HTML 内嵌的 CSS 和 JavaScript。

## 测试覆盖

`tests/test_playground_asset_modules.py` 新增三类断言：

- `playground_assets` 旧模块 re-export 的函数对象就是新模块里的函数对象，保护兼容入口。
- `playground_style()` 仍返回 `<style>...</style>`，并保留核心布局选择器。
- `playground_script(page_data)` 能保留中文 prompt 序列化，并包含 streaming、request-history detail 和 pair artifact endpoint。

原有测试继续保护：

- `tests/test_playground_assets.py`：资产内容和 `render_playground_html()` 集成。
- `tests/test_playground.py`：payload 读取、链接发现、HTML escaping、控制按钮、本地 API 字符串和 `write_playground()` 输出。

这说明 v124 拆的是静态资产模块边界，不是 playground 行为契约。

## 运行证据

v124 的运行证据放在：

```text
c/124/图片
c/124/解释/说明.md
```

关键证据包括：

- 新增 playground asset module 测试、原有 playground asset 回归、原有 playground 回归、compileall 和全量 unittest。
- maintenance batching/module pressure smoke，证明 `playground_assets.py` 从 711 非空行降到 4 非空行，新的最大压力点转移到 `server.py`。
- 生成 playground HTML 并检查 CSS/JS 内容、endpoint 名称、中文 page data 序列化和 facade parity。
- Playwright 使用本机 Google Chrome 打开生成的 playground HTML 并截图。
- README、`c/README.md`、项目成熟度阶段 README 和本讲解文件的文档闭环检查。

这些截图不是临时调试文件，而是 v124 tag 的运行证明。临时 smoke 目录仍按 cleanup gate 删除。

## 一句话总结

v124 把 playground 资产从“一个大文件承载样式和交互脚本”推进到“兼容 facade + CSS 模块 + JavaScript 模块”，让 UI 资产层更容易维护，同时保持静态页面和本地推理 API 契约不变。
