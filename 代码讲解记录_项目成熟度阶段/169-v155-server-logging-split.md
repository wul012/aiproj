# 第一百五十五版代码讲解：server logging split

## 本版目标

v155 的目标是把 MiniGPT 本地 HTTP server 的 request-history 事件构造从 `server.py` 拆到 `server_logging.py`。

这一版解决的问题是：`server.py` 已经负责路由、请求解析、生成调用、SSE 输出、文件服务、错误响应、日志写入。如果继续把 request-history 事件 schema 的字段拼装也放在 handler 方法里，后续修改日志字段会牵动 HTTP handler，维护风险变高。

明确不做：

- 不改变 `/api/generate`、`/api/generate-stream`、`/api/generate-pair`、`/api/generate-pair-artifact` 的 HTTP 契约。
- 不改变 `inference_requests.jsonl` 的写入位置和 JSONL 格式。
- 不改变 request history 查询、过滤、CSV 导出和 detail API。
- 不新增服务端持久化层。

## 前置路线

v113 以后，server 已经陆续拆出：

- `pair_artifacts.py`
- `server_contracts.py`
- `server_generator.py`

v155 顺着同一条服务端收口路线，把“日志事件构造”也变成纯函数模块：

```text
HTTP handler
  -> parse request
  -> call generator
  -> build log event
  -> append inference_requests.jsonl
  -> request history view/export/detail
```

拆分后，handler 仍然拥有 append 时机；`server_logging.py` 只负责把上下文整理成 dict。

## 关键文件

```text
src/minigpt/server.py
src/minigpt/server_logging.py
tests/test_server_logging.py
tests/test_server.py
README.md
c/155/解释/说明.md
```

`server_logging.py` 新增两个纯函数：

- `build_generation_log_event`
- `build_pair_generation_log_event`

`server.py` 保留：

- `create_handler`
- HTTP route dispatch
- JSON request body parsing
- SSE 输出
- `append_inference_log`
- 静态文件和 playground 文件服务
- 旧 facade 导出

## 事件数据结构

单次生成事件包含：

- `endpoint`
- `status`
- `client`
- `checkpoint`
- `checkpoint_id`
- `requested_checkpoint`
- `prompt_chars`
- `max_new_tokens`
- `temperature`
- `top_k`
- `seed`
- `generated_chars`
- `continuation_chars`
- `tokenizer`
- stream 相关字段：`stream_chunks`、`stream_timed_out`、`stream_cancelled`、`stream_elapsed_seconds`
- `error`

双模型生成事件包含：

- `endpoint`
- `status`
- `client`
- `left_checkpoint`
- `left_checkpoint_id`
- `right_checkpoint`
- `right_checkpoint_id`
- `requested_left_checkpoint`
- `requested_right_checkpoint`
- generation 参数字段
- `left_generated_chars`
- `left_continuation_chars`
- `right_generated_chars`
- `right_continuation_chars`
- `generated_equal`
- `continuation_equal`
- `artifact_json`
- `artifact_html`
- `error`

这些字段仍由 `request_history.py` 读取、归一化、过滤和导出。

## facade 兼容

历史调用方如果从 `server.py` 使用日志 helper，仍然可用：

```python
from minigpt.server import build_generation_log_event
from minigpt.server import build_pair_generation_log_event
```

v155 在 `server.py` 中从 `server_logging.py` re-export 这两个函数。

测试断言：

```python
server.build_generation_log_event is server_logging.build_generation_log_event
server.build_pair_generation_log_event is server_logging.build_pair_generation_log_event
```

这证明旧 facade 和新模块没有形成两套日志 schema。

## 运行流程

普通生成：

```text
POST /api/generate
  -> parse_generation_request
  -> resolve_checkpoint_option
  -> generator.generate
  -> build_generation_log_event
  -> append_inference_log
  -> response.to_dict
```

流式生成：

```text
POST /api/generate-stream
  -> parse_generation_request
  -> generator.stream
  -> SSE start/token/end 或 timeout/error
  -> build_generation_log_event
  -> append_inference_log
```

双模型生成：

```text
POST /api/generate-pair
  -> parse_generation_pair_request
  -> resolve left/right checkpoint
  -> generator.generate(left/right)
  -> pair_generation_payload
  -> build_pair_generation_log_event
  -> append_inference_log
```

`server_logging.py` 不写文件，不碰 HTTP 对象，也不读取 request history。这样它可以被单元测试直接覆盖。

## 测试覆盖

`tests/test_server_logging.py` 新增纯函数测试：

- generation log event 会记录 request、response 和 stream 字段。
- 没有 checkpoint option 时会使用默认 checkpoint。
- pair generation log event 会记录左右 checkpoint、生成长度差异判断和 artifact 路径。
- `server.py` facade 和 `server_logging.py` 是同一函数对象。

原有 server 测试继续覆盖真实 HTTP 行为：

- `/api/health`
- `/api/generate`
- `/api/generate-stream`
- `/api/generate-pair`
- `/api/generate-pair-artifact`
- request history 查询、过滤、CSV、detail
- bad request 日志
- timeout/cancelled stream 日志

## 维护压力结果

拆分前：

```text
server.py: 617 lines
largest_module=src\minigpt\server.py
```

拆分后：

```text
server.py: about 580 lines
server_logging.py: about 117 lines
largest_module=src\minigpt\server_contracts.py
module_pressure_status=pass
module_warn_count=0
```

这说明 server 不再是最大模块，且日志拆分没有制造新的 warn 模块。

## 运行截图和证据

v155 运行证据放在：

```text
c/155/图片
c/155/解释/说明.md
```

截图覆盖：

- server logging/server HTTP/server contracts/server generator 测试。
- 纯函数 smoke。
- maintenance/module pressure smoke。
- source encoding smoke。
- full unittest。
- docs keyword check。

## 一句话总结

v155 把本地推理服务的 request-history 日志事件构造从 HTTP handler 中抽出来，让服务端运行链路更清楚，也让日志证据 schema 更容易独立测试。
