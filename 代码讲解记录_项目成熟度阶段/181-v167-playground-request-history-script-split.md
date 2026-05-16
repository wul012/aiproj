# v167 playground request history script split 代码讲解

## 本版目标

v167 的目标是把 `playground_script.py` 里负责 request-history UI 的 JavaScript 片段拆到 `playground_request_history_script.py`。

这版解决的是 playground 浏览器端脚本继续膨胀的问题。`playground_script.py` 在 v124 之后已经成为独立 JS asset，但内部仍同时承担 checkpoint 选择、命令生成、stream generate、pair generate 和 request-history 表格渲染。request-history 这块已经有稳定的服务端契约：v113 抽出了核心日志读取与过滤，v164 抽出了 HTTP endpoint，v167 顺着这条线把浏览器端消费逻辑也拆成专用片段。

本版明确不做三件事：

- 不改 `/api/request-history`、`/api/request-history-detail`、CSV 导出和 JSON 下载 URL。
- 不改 `playground_script(page_data)` 的公开入口，调用方仍只拿完整 `<script>...</script>`。
- 不改 streaming generation、pair generation、checkpoint comparison 等其他 playground 行为。

## 前置路线

本版来自本地推理与 UI 的持续拆分路线：

```text
request_history.py
 -> server_request_history.py
 -> playground_request_history_script.py
 -> playground_script(page_data)
 -> render_playground_html(...)
```

v164 让服务端 request-history endpoint 从 `server.py` 里独立出来；v167 则让前端 request-history 表格、过滤、导出和详情展示从主 playground script 里独立出来。这样服务端和浏览器端的 request-history 边界都能被单独测试。

## 关键文件

- `src/minigpt/playground_request_history_script.py`：新增模块，返回 request-history JavaScript fragment。它不是完整 HTML asset，不包含 `<script>` 标签，只负责浏览器端 request-history 函数集合。
- `src/minigpt/playground_script.py`：继续负责组装完整 `<script>`，并通过 `playground_request_history_script()` 注入新片段。它仍承担公共 helper、checkpoint、stream generate、pair generate 和 DOMContentLoaded 绑定。
- `tests/test_playground_request_history_script.py`：新增直接测试，保护 request-history endpoint 字符串、detail URL、JSON 下载名和单花括号 JS 形态。
- `tests/test_playground_asset_modules.py`：新增断言，确认完整 playground script 仍包含拆出的 fragment。
- `README.md`、`c/167/解释/说明.md`、`代码讲解记录_项目成熟度阶段/README.md`：登记版本目标、证据位置和讲解索引。

## 核心函数和数据语义

### `playground_request_history_script()`

这个函数返回纯 JavaScript 片段。它依赖 `playground_script.py` 里仍然保留的公共 helper：

- `formatValue()`：把空值、布尔值和普通值转为展示文本。
- `formatSeconds()`：格式化 stream elapsed seconds。
- `formatTimestamp()`：把 ISO 时间转换成本地显示。
- `buildQuery()`：把筛选条件转为 query string。
- `appendCell()`：向表格行追加普通单元格。

因为这些 helper 是 playground 全局脚本的公共基础，v167 没把它们复制到新模块，避免形成两套格式化逻辑。

### request-history fragment

片段里保留的主要函数是：

- `requestCheckpointLabel(item)`：从单次生成、pair 生成或 fallback 字段中取 checkpoint label。
- `requestOutputChars(item)`：展示单次输出字符数，或 pair 左右输出字符数。
- `requestStreamSummary(item)`：只对 `/api/generate-stream` 展示 chunk、timeout、cancelled 摘要。
- `requestHistoryFilters()`：读取 status、endpoint、checkpoint、limit 四个过滤控件。
- `requestHistoryQuery(format)`：生成 `/api/request-history?...` 查询 URL，`format='csv'` 时用于导出链接。
- `requestHistoryDetailUrl(logIndex)`：生成 `/api/request-history-detail?log_index=...`。
- `renderRequestHistory()`：把 `MiniGPTPlayground.requestHistory` 渲染为表格行。
- `showRequestHistoryDetail(logIndex)`：加载单条 JSON 详情并显示在 detail panel。
- `loadRequestHistory()`：调用历史接口、更新 summary 文案并触发表格渲染。

这些函数消费的是服务端返回的 request-history JSON：`requests`、`filters`、`summary`、`record_count`。最终证据仍是服务端 JSON/CSV/detail 响应和渲染后的 playground 页面，fragment 本身是可复用的浏览器端逻辑，不是最终运行报告。

## f-string 边界

`playground_script.py` 返回的是 Python f-string，所以原文件里的 JavaScript 花括号必须写成 `{{` 和 `}}`。但 `playground_request_history_script.py` 返回的是普通字符串片段，里面必须是单花括号的真实 JavaScript。

这就是 v167 测试中特意断言 fragment 不包含 `{{` / `}}` 的原因：如果把 f-string 转义残留带进新模块，最终 HTML 会出现双花括号，浏览器端 JavaScript 就会损坏。

## 测试覆盖

本版测试覆盖四层：

- `tests.test_playground_request_history_script` 直接检查 request-history fragment 的 endpoint、detail URL、JSON 下载名、渲染函数和花括号形态。
- `tests.test_playground_asset_modules` 检查完整 `playground_script(page_data)` 仍包含新 fragment。
- `tests.test_playground_assets` 和 `tests.test_playground` 检查渲染后的 playground HTML 仍有 request-history UI、CSV 导出、detail panel、stream generate 和 pair generate 合同。
- 全量 unittest、source encoding hygiene 和 maintenance/module pressure smoke 继续证明拆分没有破坏其他治理链路。

## 运行证据

`c/167/图片/` 保存本版六张证据截图：

- 局部 playground/request-history 测试。
- fragment 注入和单花括号 smoke。
- maintenance/module pressure smoke。
- source encoding smoke。
- 全量 unittest。
- 文档和索引对齐检查。

这些截图不是临时日志，而是 v167 的版本证据；临时 `tmp_v167_*` 日志会在提交前清理。

## 边界说明

`playground_request_history_script.py` 不是新的前端框架，也不是新的 API 层。它只是把稳定的 request-history 浏览器端函数从主脚本中移出来，让 `playground_script.py` 不再同时承担所有 UI 细节。

后续如果继续拆 playground，更合理的候选是 pair generation 或 checkpoint comparison 的片段；但每次都应保持 `playground_script(page_data)` 入口和渲染后的 HTML 合同稳定。

## 一句话总结

v167 把 playground request-history 浏览器端逻辑从主脚本里独立出来，让 `playground_script.py` 从 532 行降到 389 行，同时保持 request-history 查询、详情、CSV 导出和 playground 入口完全不变。
