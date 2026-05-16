# v159 server HTTP helper split 代码讲解

## 本版目标

v159 的目标是把 `server.py` 中纯 HTTP 层的辅助逻辑拆出去，让本地推理服务的路由、模型生成、请求日志和响应写出边界更清楚。

本版解决的问题是：`server.py` 已经连续承载 playground 路由、generate/stream/pair API、request history、checkpoint selector、日志记录和响应写出。v155-v156 已经分别拆出了日志事件构造和 checkpoint/model-info payload；剩下的 JSON/text/SSE/file response helper 仍在 handler 内部，继续推高主服务文件的阅读压力。

本版明确不做这些事：

- 不新增 HTTP API。
- 不改变 `/api/generate`、`/api/generate-stream`、`/api/generate-pair`、`/api/request-history`、`/api/model-info` 等路由行为。
- 不改变 `create_handler()`、`run_server()` 或旧 `minigpt.server` facade 的外部调用方式。
- 不调整模型生成、采样、checkpoint 发现、request-history schema。

## 前置路线

这版延续的是服务层收口路线：

- v117 把 server contract 数据结构和 payload 逻辑拆出。
- v125 把 `MiniGPTGenerator` 拆出，让模型加载和生成不绑在 HTTP handler 上。
- v155 把 request-history log event 构造拆到 `server_logging.py`。
- v156 把 checkpoint discovery、health、model-info 和 checkpoint comparison payload 拆到 `server_checkpoints.py`。
- v159 继续把 response/file/body/SSE helper 拆到 `server_http.py`。

这样拆分后，`server.py` 继续负责“路由编排”，而纯函数或低状态 helper 分别落在独立模块里。

## 关键文件

- `src/minigpt/server_http.py`：新增 HTTP helper 模块，集中处理 JSON/text response、SSE headers/event、静态文件发送、request body JSON 解析和 run file 路径保护。
- `src/minigpt/server.py`：保留 `create_handler()`、`run_server()` 和各路由处理函数；内部 `_send_json()`、`_send_text()` 等方法变成薄代理，调用 `server_http.py`。
- `tests/test_server_http.py`：新增直接测试，绕开真实网络 server，用 fake handler 验证 helper 行为。
- `tests/test_server.py`、`tests/test_server_contracts.py`、`tests/test_server_logging.py`、`tests/test_server_generator.py`：继续作为兼容回归，证明旧 facade 和 server 主链路没有被拆坏。
- `README.md`、`c/159/解释/说明.md`、`c/README.md`：记录本版能力、运行证据和截图归档位置。

## 核心边界

`server_http.py` 只知道“handler-like 对象”：

- `handler.headers`
- `handler.rfile`
- `handler.wfile`
- `handler.send_response()`
- `handler.send_header()`
- `handler.end_headers()`

它不认识模型、checkpoint、request history、pair generation，也不决定任何业务状态。这是本版最重要的边界：HTTP 字节层和 MiniGPT 推理业务层分开。

`server.py` 仍然保留这些职责：

- 解析 URL 和 query。
- 选择 checkpoint。
- 调用 `MiniGPTGenerator`。
- 写 request-history 日志。
- 决定异常应该返回 `400` 还是 `500`。
- 组织 streaming 的 start/token/timeout/end/error 事件时机。

## HTTP helper 数据结构和函数

### `read_json_body(handler, max_body_bytes)`

输入是 handler 和最大 body 字节数，输出是 `dict[str, Any]`。

它做三件事：

1. 从 `Content-Length` 读取 body 大小。
2. 如果超过 `max_body_bytes`，抛出 `ValueError`。
3. 读取 UTF-8 JSON，并要求顶层必须是对象。

这个函数保护的是本地推理服务的 request body 边界，避免非对象 JSON 或超大 body 进入 generation parser。

### `send_json(handler, payload, status)`

输入是 dict payload 和 HTTP status，输出是写入 handler 的 response bytes。

它固定设置：

- `Content-Type: application/json; charset=utf-8`
- `Content-Length`
- CORS 的 `Access-Control-Allow-Origin`
- CORS 的 `Access-Control-Allow-Headers`

这让 API route 的 JSON response 保持一致。

### `send_text(handler, text, content_type, filename, status)`

它用于 CSV 等文本下载场景。`filename` 不为空时会设置 `Content-Disposition`，因此 request-history CSV export 可以继续通过浏览器下载。

### `send_sse_headers(handler)` 和 `write_sse(handler, event, data)`

这两个函数服务 `/api/generate-stream`：

- `send_sse_headers()` 打开 `text/event-stream` 响应。
- `write_sse()` 复用 `server_contracts.sse_message()`，把事件名和 JSON data 写成 SSE 格式并 flush。

注意：SSE message 的格式仍由 `server_contracts.py` 定义，v159 没有改变事件 schema。

### `send_file(handler, path)` 和 `serve_run_file(handler, root, request_path)`

`send_file()` 读取文件并根据文件名推断 content type。`serve_run_file()` 在此基础上加一层路径保护：

- 将请求路径 URL decode。
- resolve 到 run root 下。
- 用 `relative_to(root.resolve())` 阻止 `../` 路径逃逸。
- 不存在或不是文件时返回 `404 {"error":"not found"}`。

这保护了 playground 静态资源和 run artifact 文件访问边界。

## 路由兼容

`server.py` 仍保留 `_send_json()`、`_send_text()`、`_send_sse_headers()`、`_write_sse()`、`_send_file()`、`_read_json_body()` 和 `_serve_run_file()` 这些内部方法名，但方法体只委托给 `server_http.py`。

这样做的好处是：

- 不需要大规模改写 route handler。
- 旧测试和调试习惯不受影响。
- 纯 HTTP helper 已经可以独立测试。
- 后续如果要进一步把 handler 方法替换成直接函数调用，也有清晰落点。

`server.sse_message` 继续从 `server_contracts.py` 导出，保持旧 facade 合同。

## 行数变化

拆分前：

- `src/minigpt/server.py`：580 行。

拆分后：

- `src/minigpt/server.py`：541 行。
- `src/minigpt/server_http.py`：102 行。

这不是为了追求单次大幅缩水，而是把稳定的 HTTP 字节层行为移到可单测模块。对当前服务层来说，这比继续在 handler 内堆 helper 更可维护。

## 测试覆盖

`tests/test_server_http.py` 覆盖了以下边界：

- JSON body 是对象时可以解析。
- body 超过 `max_body_bytes` 时拒绝。
- 顶层 JSON 不是对象时拒绝。
- `send_json()` 设置 JSON content type 并写出 UTF-8 JSON。
- `send_text()` 设置下载文件名。
- SSE header 和 `event/data` 输出格式正确。
- `send_file()` 能发送文本文件。
- `serve_run_file()` 能发送 root 内文件，并拒绝 `../` 逃逸路径。

同时保留 server 相关测试：

- `tests.test_server`
- `tests.test_server_contracts`
- `tests.test_server_logging`
- `tests.test_server_generator`

这些测试证明 v159 没有破坏本地推理服务的既有合同。

## 运行截图和证据

本版运行证据放在 `c/159`：

- `01-server-http-tests.png`：HTTP helper 和 server 兼容测试。
- `02-server-http-smoke.png`：直接 helper smoke，验证 JSON/text/SSE/file/path guard。
- `03-maintenance-smoke.png`：维护扫描和 module pressure。
- `04-source-encoding-smoke.png`：源码编码、语法和 Python 3.11 兼容。
- `05-full-unittest.png`：全量 unittest discovery。
- `06-docs-check.png`：README、说明、源码和测试关键词对齐。

这些截图是运行证据归档，不是程序运行时消费的输入。

## 一句话总结

v159 把 MiniGPT 本地推理服务的 HTTP 字节层从 route handler 中拆出来，让 `server.py` 更专注于路由和推理编排，同时保持 API、facade 和运行证据链稳定。
