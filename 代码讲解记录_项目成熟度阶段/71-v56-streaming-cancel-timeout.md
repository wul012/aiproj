# 第五十六版代码讲解：streaming cancel and timeout

## 本版目标、来源和边界

v55 已经把 MiniGPT 本地推理从一次性 JSON 响应推进到 `/api/generate-stream` 的 SSE token 流。它解决了“能不能边生成边看”的问题，但还有两个工程边界没有处理：服务端没有明确的流式耗时上限，浏览器端也没有一个显式取消当前生成的入口。

v56 的目标是给这条流式链路加边界：服务端增加 `max_stream_seconds`，超过时间后返回 `timeout` SSE 事件并保留 partial response；playground 增加 `Stop` 按钮，用 `AbortController` 取消当前 fetch stream；服务端遇到浏览器断连时记录 `cancelled`，而不是再尝试写错误事件。

本版不做队列调度、不做多用户鉴权、不做强制杀掉底层 PyTorch 线程，也不把 playground 变成生产推理服务。它仍然是本地学习项目，但让本地流式推理更像一个有操作边界的工程接口。

## 所在链路

```text
serve_playground --max-stream-seconds
 -> InferenceSafetyProfile.max_stream_seconds
 -> /api/generate-stream
 -> token event loop
 -> timeout event when elapsed >= limit
 -> inference_requests.jsonl status=timeout
 -> playground Stop button / AbortController
```

这一层回答的问题是：流式生成开始后，用户和服务端是否都有办法避免它无限占住当前交互。

## 关键文件

- `src/minigpt/server.py`：新增 `max_stream_seconds`、`stream_timeout_payload`、timeout event 写出、client disconnect 处理和 timeout/cancelled 日志字段。
- `src/minigpt/playground.py`：新增 `liveStopButton`、`AbortController`、`stopLiveGeneration` 和 timeout event 展示。
- `scripts/serve_playground.py`：新增 `--max-stream-seconds` CLI 参数，并写入 `InferenceSafetyProfile`。
- `tests/test_server.py`：新增慢速 stream stub，覆盖 timeout SSE 顺序、partial response 和 JSONL 日志。
- `tests/test_playground.py`：确认 HTML 包含 Stop 按钮、AbortController、取消函数和 timeout 文案。
- `README.md`、`b/56/解释/说明.md`：同步 v56 能力、截图和 tag 说明。

## 核心数据结构和字段

`InferenceSafetyProfile` 新增：

- `max_stream_seconds`：流式生成允许持续的最大秒数，默认 `30.0`。

这个字段会出现在 `/api/health` 的 `safety` 中，也会由 `scripts/serve_playground.py --max-stream-seconds` 覆盖。

`stream_timeout_payload` 生成 timeout 事件的数据：

- `done: false`
- `reason: "timeout"`
- `elapsed_seconds`
- `max_stream_seconds`
- `chunk_count`
- `response`

其中 `response` 是一个 `GenerationResponse` 字典，保留 prompt、partial generated、partial continuation、采样参数、checkpoint、tokenizer 和 checkpoint id。它是最终证据的一部分，不是调试字段。

JSONL 日志新增：

- `status: "timeout"`
- `stream_chunks`
- `stream_timed_out`
- `stream_cancelled`
- `stream_elapsed_seconds`

这些字段让后续 request history 或 audit 能区分正常完成、参数错误、运行错误、超时截断和浏览器主动取消。

## 服务端运行流程

`/api/generate-stream` 仍然先写 `start`，再循环写 `token`。v56 在 token 写出后记录 elapsed time：

```text
started_at = monotonic()
for chunk in generator.stream(request):
    write token
    elapsed = monotonic() - started_at
    if elapsed >= max_stream_seconds:
        write timeout
        break
```

如果没有超时，流程和 v55 一样写 `end`。如果超时，则不写 `end`，而是写 `timeout`，并用 partial response 写日志。这样客户端能清楚知道这不是正常完成，也不是连接错误，而是服务端主动按边界截断。

## Playground 运行流程

`generateLive` 现在会创建一个 `AbortController`，并把 `controller.signal` 传给 fetch。生成开始时：

- `Stream Generate` 按钮禁用。
- `Stop` 按钮启用。
- 当前 controller 存到 `MiniGPTPlayground.streamController`。

点击 `Stop` 时，`stopLiveGeneration` 调用 `abort()`。浏览器抛出 `AbortError` 后，输出框追加 `[stream cancelled]`，按钮状态恢复。如果服务端随后遇到 `BrokenPipeError`、`ConnectionAbortedError` 或 `ConnectionResetError`，它会把请求写成 `status: cancelled`，不再向已经断开的连接写 error 事件。

如果服务端返回 `timeout` 事件，`readGenerationStream` 用 partial response 更新输出，并追加：

```text
[stream timeout after N chunk(s)]
```

这两个路径不同：Stop 是浏览器主动取消；timeout 是服务端按安全边界截断。

## 输出和证据

`timeout` SSE 事件是正式 API 语义，后续脚本或 UI 可以依赖它判断 partial generation 是否可用。`stream_timed_out`、`stream_cancelled` 和 `stream_elapsed_seconds` 是 JSONL 日志证据，适合后续做 playground request history 或推理审计。

`b/56/图片` 保存本版运行截图。Playwright 截图打开生成后的 playground，证明 `Stream Generate` 和 `Stop` 控制同时出现在真实浏览器里。

## 测试覆盖

`tests/test_server.py` 覆盖：

- `stream_timeout_payload` 会保留 partial response 和 checkpoint id。
- `/api/health` 暴露 `max_stream_seconds`。
- 慢速 stream 在很小的 `max_stream_seconds` 下返回 `start -> token -> timeout`。
- timeout 事件包含 `done: false`、`reason: timeout`、partial generated 和 chunk count。
- JSONL 日志记录 `status: timeout`、`stream_timed_out: true` 和 elapsed seconds。
- 取消日志路径能记录 `status: cancelled`、`stream_cancelled: true` 和 partial response。

`tests/test_playground.py` 覆盖：

- `liveStopButton` 存在。
- `AbortController` 被写入 HTML。
- `stopLiveGeneration` 存在。
- timeout 展示文案存在。

全量 `python -m unittest discover -s tests` 和 `python -m compileall src scripts tests` 作为回归证据，证明 v56 没破坏前面版本的训练、评估、治理和报告链路。

## 和前面版本的关系

v55 让本地推理服务“能流式输出”。v56 让它“有边界并可取消”。这不是新的模型能力，但它是推理服务化的必要小台阶：体验上能停止，证据上能解释为什么结束。

## 一句话总结

v56 把 MiniGPT 的本地流式推理从“能吐 token”推进到“能被用户停止，也能被服务端按时间边界截断并记录证据”的阶段。
