# v164 server request history endpoint split 代码讲解

## 本版目标

v164 的目标是把 `server.py` 里的 `/api/request-history` 和 `/api/request-history-detail` HTTP endpoint 处理拆到 `server_request_history.py`。

它解决的问题是：request-history 的数据读取、过滤、detail payload 和 CSV 导出已经在 `request_history.py` 中独立，但 `server.py` 仍直接承担 query 解析、JSON/CSV 分支、400/404 错误映射和响应发送。本版把这些 endpoint glue logic 抽出来，让 `server.py` 的 GET 路由更像调度层。

本版明确不做：

- 不改 request-history payload schema。
- 不改 `/api/request-history` 的 JSON 或 CSV 输出格式。
- 不改 `/api/request-history-detail` 的 detail payload。
- 不改生成、stream、pair generation 或 checkpoint 逻辑。
- 不改变 `minigpt.server` 继续导出 request-history helper 的兼容行为。

## 前置路线

这版承接 server 模块的持续收口：

- v155 把 request log event 构造拆到 `server_logging.py`。
- v156 把 checkpoint/model-info payload 构造拆到 `server_checkpoints.py`。
- v159 把 JSON/text/SSE/file response helper 拆到 `server_http.py`。
- v164 继续把 request-history endpoint glue logic 拆出来，但不碰真实模型生成。

这个顺序是刻意保守的：先拆纯响应 helper，再拆稳定的请求历史 endpoint，避免在没有必要时改动 stream/generate 主流程。

## 关键文件

- `src/minigpt/server.py`：保留 `create_handler()`、`run_server()`、generate、stream、pair、model-info 和 checkpoint 路由；request-history 分支现在只调用 helper。
- `src/minigpt/server_request_history.py`：新增 endpoint helper 模块，负责 `/api/request-history` 和 `/api/request-history-detail` 的 query 解析、payload 构造、CSV 分支和错误状态映射。
- `tests/test_server_request_history.py`：新增 fake handler 单测，直接验证 helper 的 JSON、CSV、BAD_REQUEST、NOT_FOUND 行为。
- `tests/test_server.py`：继续覆盖真实 HTTP server 上的 request-history JSON、CSV、detail、400 和 404 路由。
- `tests/test_request_history.py`：继续覆盖 request-history 数据层。
- `tests/test_server_http.py`：继续覆盖底层响应 helper。

## 核心函数

`handle_request_history_endpoint(handler, request_log, query)`：

- 读取 `limit`、`status`、`endpoint`、`checkpoint` 等 query 参数。
- 调用 `build_request_history_payload()` 生成结构化 JSON。
- 如果 `format=csv`，调用 `request_history_to_csv()` 并通过 `_send_text()` 返回 CSV。
- 参数非法时返回 HTTP 400 JSON error。

`handle_request_history_detail_endpoint(handler, request_log, query)`：

- 读取 `log_index`。
- 调用 `build_request_history_detail_payload()` 返回原始 record 和 normalized record。
- `log_index` 缺失或非法时返回 HTTP 400。
- 指定记录不存在或是无效记录时返回 HTTP 404。

这两个函数都使用 handler 的 `_send_json()` / `_send_text()`，所以它们仍然依赖 server handler 的响应接口，但不再把 endpoint 分支散落在 `do_GET()` 中。

## 输入输出边界

输入：

- request log 路径。
- URL query string。
- 具备 `_send_json()` 和 `_send_text()` 的 handler。

输出：

- JSON response。
- CSV text response。
- BAD_REQUEST / NOT_FOUND error response。

新模块不读取请求 body、不启动 server、不访问模型 checkpoint，也不写 request log。它只是 GET endpoint 的响应编排层。

## 测试覆盖

本版测试分四层：

- `tests.test_server_request_history`：直接验证 helper 的 JSON、CSV、400、404。
- `tests.test_server`：通过真实 `ThreadingHTTPServer` 验证路由行为仍兼容。
- `tests.test_request_history`：验证 request-history payload、filters、detail 和 CSV 数据层。
- `tests.test_server_http`：验证 `_send_text()`、`_send_json()` 等响应 helper。

全量 `unittest discover` 作为回归网，防止 server 拆分影响其他 MiniGPT 训练、评估、registry、release 和 maturity 链路。

## 产物和证据

`c/164/图片/` 保存本版运行截图：

- `01-server-request-history-tests.png`：server/request-history 局部测试。
- `02-server-request-history-smoke.png`：endpoint helper 直接 smoke。
- `03-maintenance-smoke.png`：维护批处理与 module pressure 检查。
- `04-source-encoding-smoke.png`：源码编码和 Python 3.11 语法兼容检查。
- `05-full-unittest.png`：全量单测。
- `06-docs-check.png`：README、归档、讲解、源码和测试关键词一致性检查。

这些截图是最终证据，临时日志和临时 run 输出完成后按 AGENTS 清理。

## 行数变化

- `src/minigpt/server.py`：从 541 行降到 519 行。
- `src/minigpt/server_request_history.py`：52 行，集中承载 request-history GET endpoint glue logic。

这个变化的价值不在于一次减少很多行，而在于 server handler 的职责继续变窄，为后续拆 GET routing 或 stream/pair 边界降低风险。

## 一句话总结

v164 把 request-history 的 HTTP endpoint 编排从 `server.py` 中拆出，让本地推理服务的请求历史链路更独立，同时保持 JSON、CSV、detail 和错误状态契约稳定。
