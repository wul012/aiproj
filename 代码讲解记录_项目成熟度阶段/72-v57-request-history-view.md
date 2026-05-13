# 第五十七版代码讲解：request history view

## 本版目标、来源和边界

v55 把 MiniGPT 本地推理从一次性 JSON 响应推进到 `/api/generate-stream` 的 SSE token 流；v56 给这条流式链路补上 `max_stream_seconds`、`timeout` 事件、浏览器 `Stop` 取消和 `cancelled` 日志。到这里，服务端已经会把普通生成、流式生成、超时、取消和 pair generation 写进 `inference_requests.jsonl`。

v57 的目标不是继续扩大模型能力，而是把这份已有日志变成可查询、可展示、可复查的本地推理请求历史。它新增 `/api/request-history`，读取 `inference_requests.jsonl`，归一化最近请求记录，并在 playground 中加入 Request History 表格。

本版不做用户账号、不做远程审计、不做数据库、不做日志清洗后台任务，也不改变训练、采样和模型结构。它仍然是本地学习项目里的轻量可追溯层，重点是让已经写下来的推理证据能被人快速看到。

## 所在链路

```text
/api/generate 或 /api/generate-stream 或 /api/generate-pair
 -> append_inference_log(...)
 -> inference_requests.jsonl
 -> build_request_history_payload(...)
 -> GET /api/request-history?limit=12
 -> playground Request History table
```

这条链路回答的问题是：一次本地 playground 推理结束后，能不能不用手动打开 JSONL，也能看到最近请求去了哪个端点、用哪个 checkpoint、状态是什么、生成了多少字符、流式请求是否超时或取消。

## 关键文件

- `src/minigpt/server.py`：新增请求历史 payload 构造函数、日志读取函数、limit 解析、记录归一化和 HTTP GET 路由。
- `src/minigpt/playground.py`：新增前端状态 `requestHistory`、Request History 区块、刷新按钮、状态徽标、历史表格渲染和生成后自动刷新。
- `scripts/serve_playground.py`：启动输出里新增 `request_history=<url>`，把新端点和其他本地 API 一起暴露出来。
- `tests/test_server.py`：验证 JSONL 读取、坏行统计、最近记录倒序、HTTP endpoint、limit 错误和流式日志回读。
- `tests/test_playground.py`：验证生成的 HTML 包含请求历史表格、刷新按钮、加载函数和 `/api/request-history`。
- `b/57/图片` 与 `b/57/解释/说明.md`：保存本版测试、smoke、结构检查、Playwright 页面和文档检查证据。

## 核心数据结构和字段

`build_request_history_payload(request_log_path, limit=20)` 返回的是面向 UI 和脚本消费的字典：

```text
status
request_log
request_log_exists
limit
newest_first
total_log_records
invalid_record_count
record_count
summary
requests
```

其中 `summary` 记录：

- `total_log_records`：日志中成功解析出的 JSON 对象数量。
- `returned_records`：本次按 limit 返回的记录数量。
- `invalid_record_count`：坏 JSON 行或非对象行数量。
- `latest_timestamp`：返回列表第一条的时间。
- `ok_count`、`timeout_count`、`cancelled_count`、`error_count`、`bad_request_count`：返回记录里的状态计数。
- `returned_status_counts`：返回记录按状态聚合。
- `returned_endpoint_counts`：返回记录按端点聚合。

`requests` 中的单条记录不是原始日志的完整复制，而是白名单字段归一化后的结果。它保留：

- 通用字段：`timestamp`、`endpoint`、`status`、`client`。
- checkpoint 字段：`checkpoint`、`checkpoint_id`、`requested_checkpoint`。
- pair 字段：`left_checkpoint_id`、`right_checkpoint_id`、`requested_left_checkpoint`、`requested_right_checkpoint`。
- 请求参数：`prompt_chars`、`max_new_tokens`、`temperature`、`top_k`、`seed`。
- 输出摘要：`generated_chars`、`continuation_chars`、left/right 输出字符数。
- 流式字段：`stream_chunks`、`stream_timed_out`、`stream_cancelled`、`stream_elapsed_seconds`。
- 产物字段：`artifact_json`、`artifact_html`。
- 错误字段：`error`。

这种白名单方式让 UI 不依赖完整原始日志格式，也避免把后续可能加入的大字段直接塞进浏览器表格。

## 服务端运行流程

`/api/request-history` 是只读 GET 路由。请求进入 `create_handler(...).do_GET` 后：

1. 从 query string 读取 `limit`。
2. 默认 limit 是 `20`，最大值是 `200`。
3. 如果 limit 小于 1、超过最大值或不是整数，返回 `400`。
4. 读取 `inference_requests.jsonl`。
5. 跳过空行，统计坏 JSON 行。
6. 只接收 JSON object，非 object 行也算 invalid。
7. 取最近 `limit` 条，按 newest first 返回。
8. 生成状态计数、端点计数和请求列表。

如果日志文件不存在，接口不会报错，而是返回空历史：

```text
request_log_exists: false
total_log_records: 0
record_count: 0
requests: []
```

这样 playground 静态页面或新 run 目录第一次打开时不会因为没有日志而失败。

## Playground 运行流程

`render_playground_html` 现在把 `requestHistory: []` 放进 `MiniGPTPlayground` 初始状态，并在 Live Generate 下方插入 Request History 区块。

页面加载时：

```text
DOMContentLoaded
 -> buildCommands()
 -> loadCheckpoints()
 -> loadCheckpointComparison()
 -> loadRequestHistory()
```

`loadRequestHistory` 请求 `/api/request-history?limit=12`。成功后把 `data.requests` 写入 `MiniGPTPlayground.requestHistory`，再调用 `renderRequestHistory`。失败时显示 “Start scripts/serve_playground.py for request history.”，这说明当前只是打开了静态 HTML，没有启动本地 API 服务。

`renderRequestHistory` 每行展示：

- Time：请求时间。
- Endpoint：例如 `/api/generate-stream`。
- Status：`ok`、`timeout`、`cancelled`、`bad_request`、`error`。
- Checkpoint：优先显示 `checkpoint_id`，pair 请求显示 left checkpoint。
- Prompt：prompt 字符数。
- Output：普通请求显示生成字符数，pair 请求显示 left/right 字符数。
- Stream：流式请求显示 chunk 数和 timeout/cancelled 标记。
- Elapsed：流式耗时。

`generateLive` 和 `generatePairLive` 的 finally 分支会延迟调用 `loadRequestHistory`。延迟很短，目的是给服务端写 JSONL 留出时间，让用户点完生成后能看到表格跟着刷新。

## 输出和证据

`/api/request-history` 是正式本地 API 输出，不是调试临时接口。它可以被 playground 使用，也可以被脚本读取，用于后续做 request detail export、history filtering 或本地推理审计。

`inference_requests.jsonl` 仍然是原始证据；v57 不重写它，只读它。`requests` 是面向 UI 的归一化视图，`summary` 是面向快速概览的聚合视图。坏行统计让日志损坏时也能被发现，而不是静默忽略。

`b/57/图片/04-playwright-request-history.png` 来自真实 Chrome/Playwright，并且页面通过临时本地 `serve_playground.py` 服务打开，所以它证明的是“浏览器可以通过 HTTP 端点加载请求历史”，不只是静态 HTML 里存在一段表格。

## 测试覆盖

`tests/test_server.py` 覆盖三层：

- `test_request_history_payload_reads_recent_records`：构造包含 ok、timeout、cancelled 和坏 JSON 行的日志，断言最近记录倒序、limit 生效、invalid count 生效、状态/端点计数正确，并确认原始大字段不会进入归一化记录。
- `test_http_health_and_generate`：确认 `/api/health` 暴露 `request_history_endpoint`，普通 `/api/generate` 写入日志后能通过 `/api/request-history` 读回，非法 limit 返回 `400`。
- 流式生成测试：确认 `/api/generate-stream` 写入的 `stream_chunks` 能被历史端点读回。

`tests/test_playground.py` 覆盖 HTML 和 JS 入口：

- `requestHistoryTable`
- `requestHistoryBody`
- `refreshRequestHistoryButton`
- `/api/request-history`
- `loadRequestHistory`
- `renderRequestHistory`

全量 `python -m unittest discover -s tests` 和 `python -m compileall src tests scripts` 作为回归证据，说明 v57 没有破坏前面训练、评估、治理、playground 和 release gate 链路。

## 和前面版本的关系

v55 让本地推理“能流式输出”。v56 让流式推理“有超时、有取消、有状态日志”。v57 则把这份状态日志带回 UI，让它“可查询、可概览、可复查”。这仍然不是生产监控系统，但已经从手动翻 JSONL 推进到本地 API 和浏览器视图。

后续如果继续沿这条线走，最自然的是给 Request History 加过滤、单条详情展开、导出 CSV/JSON，或者把 request history 纳入 project audit。

## 一句话总结

v57 把 MiniGPT 的本地推理日志从“后台留下证据”推进到“前台能直接读取和复查证据”的阶段。
