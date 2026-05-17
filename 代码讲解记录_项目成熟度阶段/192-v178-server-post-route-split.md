# v178 server POST route split 代码讲解

## 本版目标

v178 的目标是把 `server.py` 中的 POST route handling 拆到 `server_post_routes.py`，让本地推理 server 的 HTTP handler 继续向“装配入口”和“路由执行逻辑”分离。v171 已经把 GET route dispatch 拆到 `server_routes.py`，但 POST 侧的 `/api/generate`、`/api/generate-stream`、`/api/generate-pair` 和 `/api/generate-pair-artifact` 仍留在 `server.py` 内部，导致 handler 同时负责普通生成、SSE 流式生成、pair 生成、pair artifact 写入、错误映射和日志触发。

本版明确不做这些事：不改变四条 POST API 的请求和返回 schema，不改变 HTTP 状态码，不改变 checkpoint selector 和 checkpoint existence 检查，不改变 SSE `start/token/timeout/end/error` 事件语义，不改变 timeout/cancel 日志字段，不改变 pair artifact 的 JSON/HTML 写出位置和 schema，不改变 `create_handler()`、`run_server()` 和旧的 `minigpt.server` facade 导出。

## 前置路线

v178 接在 server 拆分路线后面。v117 把请求契约、payload、SSE helper 和 checkpoint 元数据抽到 `server_contracts.py`；v125 把 PyTorch checkpoint/tokenizer 加载和 token 生成抽到 `server_generator.py`；v155 把 request log event 构造抽到 `server_logging.py`；v156 把 checkpoint/model-info/health payload 抽到 `server_checkpoints.py`；v159 把 JSON/text/SSE/file response helper 抽到 `server_http.py`；v164 把 request-history endpoint handling 抽到 `server_request_history.py`；v171 把 GET route dispatch 抽到 `server_routes.py`。

因此 v178 不是新增推理能力，而是补齐 server 的另一半路由边界：GET 已经外移，POST 也应由专门模块承接。这样后续继续维护本地推理时，可以清楚区分 Handler 装配、GET 查询路由、POST 生成路由、HTTP response helper、日志事件和模型生成器。

## 关键文件

- `src/minigpt/server_post_routes.py`：新增 POST route helper 模块。它负责解析 request path、分发四条 POST route，并执行普通生成、流式生成和 pair 生成流程。
- `src/minigpt/server.py`：保留 `create_handler()`、`run_server()`、GET 委托、OPTIONS、日志 wrapper、HTTP helper wrapper 和旧导出。`do_POST()` 只调用 `handle_post_request()`。
- `tests/test_server_post_routes.py`：新增分割测试，覆盖 facade identity、普通 `/api/generate` helper flow 和 `/api/generate-pair-artifact` helper flow。
- `README.md`、`c/178/解释/说明.md`、`代码讲解记录_项目成熟度阶段/README.md`：记录本版能力、证据目录和讲解索引。

## POST route 模块

`handle_post_request()` 是新模块的入口。它接收 handler、request path、run root、默认 checkpoint、安全配置、checkpoint options 和 `generator_for()`。它不自己创建 HTTP server，也不持有全局状态，而是消费 `create_handler()` 已经准备好的闭包资源。

它的分发规则保持旧行为：

```text
/api/generate-pair-artifact -> handle_generate_pair_request(save_artifact=True)
/api/generate               -> handle_generate_request()
/api/generate-stream        -> handle_generate_stream_request()
/api/generate-pair          -> handle_generate_pair_request()
其他 POST path              -> 404 JSON
```

这样的设计让 `server.py` 的 `do_POST()` 只表达“POST 请求交给 POST route layer”，而具体 route 语义集中在一个可单测的新模块里。

## 普通生成流程

`handle_generate_request()` 保留旧流程：读取 JSON body，调用 `parse_generation_request()` 应用 `InferenceSafetyProfile`，用 `resolve_checkpoint_option()` 找 checkpoint，检查 `option.exists`，然后通过 `generator_for(option).generate(request)` 得到 `GenerationResponse`。

错误映射也保持不变：

- `ValueError`：记录 `bad_request` 日志并返回 HTTP 400。
- 其他异常：记录 `error` 日志并返回 HTTP 500。
- 成功：记录 `ok` 日志，把 response 转成 dict，并补上 `checkpoint_id`。

这个函数不直接写 JSONL 文件，而是调用 handler 的 `_log_generation()`。这样日志事件构造仍由 `server_logging.py` 负责，实际 append 仍在 `server.py` 的 handler wrapper 内完成。

## 流式生成流程

`handle_generate_stream_request()` 保留旧的 SSE 编排：先发送 `start`，随后对 `generator_for(option).stream(request)` 的 chunk 逐个写出 `token`。如果耗时达到 `safety.max_stream_seconds`，就发送 `timeout`，并用 `stream_timeout_payload()` 保留 partial response。

函数内部继续记录这些关键状态：

- `chunk_count`：已发送 token chunk 数。
- `stream_open`：是否已经发出 SSE headers，决定错误用 SSE `error` 还是 JSON response。
- `timed_out`：是否触发 timeout。
- `cancelled`：客户端断开时记录 cancel 状态。
- `elapsed_seconds`：日志和 timeout payload 使用的耗时。
- `generated`、`continuation`、`tokenizer`、`checkpoint_path`：用于 timeout/cancel partial response。

取消分支继续捕获 `BrokenPipeError`、`ConnectionAbortedError` 和 `ConnectionResetError`，并记录 `cancelled` 日志。普通异常在 stream 已打开时写 SSE `error`，未打开时返回 HTTP 500 JSON。这个边界没有改变前端 playground 的 streaming/cancel/timeout 行为。

## Pair 生成和 artifact 流程

`handle_generate_pair_request()` 同时服务 `/api/generate-pair` 和 `/api/generate-pair-artifact`。它先解析 `GenerationPairRequest`，分别解析 left/right checkpoint，检查两个 checkpoint 是否存在，然后分别生成 left/right response。

成功后通过 `pair_generation_payload()` 构造响应。如果 `save_artifact=True`，则调用 `write_pair_generation_artifacts(root, payload)` 写出 pair generation 的 JSON 和 HTML，再把 `artifact` 字段放回响应。日志依旧通过 handler 的 `_log_pair_generation()` 进入 `server_logging.py` 和 `append_inference_log()`。

这里的关键边界是：pair artifact 的实际写出实现仍在 `pair_artifacts.py`，POST route 只决定什么时候调用它。因此 v178 没有改变 artifact 格式，只改变调用位置。

## 兼容性

旧调用方式仍然有效：

```python
from minigpt.server import create_handler, run_server, handle_post_request
from minigpt.server import parse_generation_request, pair_generation_payload
```

`server.py` 继续导入并暴露历史上常用的 contract、checkpoint、HTTP、logging 和 pair artifact 符号。v178 没有把旧 facade 导出改成强制用户迁移，因为这个项目的本地 server 已经被 playground、tests 和脚本长期消费，兼容性比“导入表更干净”更重要。

## 测试覆盖

v178 的测试覆盖四层：

- `tests.test_server_post_routes`：直接覆盖新 POST route helper 的 facade identity、普通生成成功响应、pair artifact 写出和 pair 日志 artifact 引用。
- server 相关测试组：覆盖真实 HTTP `/api/generate`、`/api/generate-stream`、timeout、pair routes、request history、GET route、HTTP helper、logging、checkpoint 和 contract facade。
- full unittest discovery：确认 POST 拆分没有破坏训练、评估、dashboard、release、registry、maintenance 和 training-scale 链路。
- source encoding hygiene 和 maintenance batching：确认新源码无 BOM/语法/兼容性问题，module pressure 继续为 `pass`。

新增测试中的 `FakeHandler` 不是新的生产 handler。它只模拟 `_read_json_body()`、`_send_json()`、`_log_generation()` 和 `_log_pair_generation()`，用于验证 `server_post_routes.py` 不依赖 `ThreadingHTTPServer` 也能独立执行 route helper 逻辑。

## 运行证据

v178 的运行截图归档在 `c/178`：

- `01-server-post-route-tests.png`：server 相关 41 个测试通过。
- `02-server-post-route-smoke.png`：`server.py` 行数降到 240，新模块 344 行，旧 facade 指向新 helper，四条 POST route 被列出。
- `03-maintenance-smoke.png`：module pressure 为 `pass`，最大模块转为 `maturity_narrative.py`。
- `04-source-encoding-smoke.png`：编码、语法和 Python 3.11 兼容检查通过。
- `05-full-unittest.png`：全量 402 个测试通过。
- `06-docs-check.png`：README、`c/178`、讲解索引、source/test 关键词对齐。

临时 `tmp_v178_*` 日志和 `runs/*v178*` 输出会在提交前按 AGENTS 清理门禁删除，`c/178` 是保留的正式证据。

## 边界说明

`server_post_routes.py` 不是新的模型生成器，也不是新的 HTTP response 库。模型加载和 token sampling 仍在 `server_generator.py`，HTTP response 仍在 `server_http.py`，request/response schema 仍在 `server_contracts.py`，checkpoint metadata 仍在 `server_checkpoints.py`，日志事件构造仍在 `server_logging.py`。POST route 模块只负责“哪条 POST route 调用哪段生成流程，以及如何把成功/错误映射到 handler 输出”。

## 一句话总结

v178 把 MiniGPT 本地推理 server 的 `/api/generate`、`/api/generate-stream`、`/api/generate-pair` 和 `/api/generate-pair-artifact` 从 `server.py` 抽到 `server_post_routes.py`，让 server 主入口继续收束，同时保持推理 API、SSE、pair artifact、日志和旧 facade 契约不变。
