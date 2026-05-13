# 第五十五版代码讲解：streaming playground generation

## 本版目标、来源和边界

v12 已经把 playground 变成本地服务，v38 增加推理安全边界，v39-v42 又补了 checkpoint 选择、checkpoint 对比、side-by-side generation 和可保存 pair artifact。到 v54 为止，项目的治理证据很完整，但本地 live generation 仍然是一次请求、一次 JSON 响应，用户只能等整段生成结束后再看到结果。

v55 的目标是把 MiniGPT 的本地推理服务推进到流式输出：服务端新增 `/api/generate-stream`，用 Server-Sent Events 返回 `start/token/end/error` 事件；playground 的 live 按钮改成 `Stream Generate`，通过浏览器 fetch stream 边读边更新输出。

本版不改变训练目标，不引入外部大模型，不做 WebSocket，不做并发队列、取消按钮、超时熔断或生产级鉴权。它仍然是本地学习项目的推理体验增强，重点是让“逐 token 自回归生成”这件事在代码和浏览器里更直观。

## 所在链路

```text
prompt + sampling settings + checkpoint selector
 -> parse_generation_request
 -> resolve_checkpoint_option
 -> MiniGPTGenerator.stream
 -> MiniGPT.sample_next
 -> SSE start/token/end events
 -> playground readGenerationStream
 -> liveOutput incremental text
 -> inference_requests.jsonl
```

这一层回答的问题是：MiniGPT 是否只能等完整结果，还是可以像真实本地推理服务一样，把每一步采样结果变成可消费的事件流。

## 关键文件

- `src/minigpt/model.py`：新增 `MiniGPT.sample_next`，把原来 `generate` 里的单步 logits、top-k、softmax、multinomial 逻辑拆出来，供同步生成和流式生成共同使用。
- `src/minigpt/server.py`：新增 `GenerationStreamChunk`、`MiniGPTGenerator.stream`、`sse_message` 和 `/api/generate-stream` 路由。
- `src/minigpt/playground.py`：把 Live Generate 按钮改成 `Stream Generate`，用 `fetch('/api/generate-stream')` 读取 response body stream，并解析 SSE。
- `scripts/serve_playground.py`：启动时打印 `generate_stream=<url>/api/generate-stream`，方便命令行确认服务能力。
- `tests/test_model.py`：验证 `sample_next` 返回一个合法 token。
- `tests/test_server.py`：验证 SSE 格式、health endpoint、HTTP streaming 事件顺序、最终响应和 JSONL 日志。
- `tests/test_playground.py`：验证静态 playground HTML 包含 `Stream Generate`、`/api/generate-stream` 和 stream reader。
- `README.md`、`b/55/解释/说明.md`：同步 v55 版本说明、截图索引和运行证据。

## 核心数据结构

`GenerationStreamChunk` 表示一次 token 事件：

- `index`：本次生成中的 token 序号，从 0 开始。
- `token_id`：模型采样出的 token id。
- `text`：该 token id 解码后的文本。
- `generated`：包含 prompt 的累计完整文本。
- `continuation`：不含 prompt 的累计续写文本。
- `checkpoint`：实际使用的 checkpoint 路径。
- `tokenizer`：实际使用的 tokenizer 名称。

HTTP 返回时，服务端会额外加上 `checkpoint_id`，这样浏览器和日志能知道这次 token 来自 default、candidate 或其他已注册 checkpoint。

`sse_message(event, data)` 负责把事件转成标准 SSE 文本：

```text
event: token
data: {"index": 0, "text": "..."}
```

它输出的是 bytes，直接写入 `wfile`，每次 `_write_sse` 后都会 `flush()`，让浏览器能尽快读到事件。

## 服务端运行流程

`/api/generate-stream` 和 `/api/generate` 共用同一套请求解析：

1. `_read_json_body` 检查 body 大小并解析 JSON。
2. `parse_generation_request` 检查 prompt、`max_new_tokens`、temperature、top-k、seed 和 checkpoint selector。
3. `resolve_checkpoint_option` 找到可用 checkpoint。
4. `_send_sse_headers` 写出 `text/event-stream; charset=utf-8`。
5. 先写 `start` 事件，说明 prompt、采样参数和 checkpoint。
6. `MiniGPTGenerator.stream` 逐步调用 `MiniGPT.sample_next`。
7. 每个 `GenerationStreamChunk` 写成 `token` 事件。
8. 最后写 `end` 事件，里面带最终 `GenerationResponse`。
9. `_log_generation` 写入 `inference_requests.jsonl`，包括 endpoint、状态、生成长度和 `stream_chunks`。

如果校验失败发生在 SSE header 之前，服务端仍返回普通 JSON 400，这方便老的 HTTP 客户端处理错误。如果错误发生在流已经打开之后，服务端写 `error` SSE 事件。

## 模型层变化

原来的 `MiniGPT.generate` 自己包含完整循环：

```text
idx -> logits -> top_k -> softmax -> multinomial -> cat -> repeat
```

v55 把单步部分拆成 `sample_next`：

```text
idx -> sample_next -> next_idx
```

然后 `generate` 继续调用 `sample_next` 循环拼接，所以旧接口行为不变。`MiniGPTGenerator.stream` 则在每次 `sample_next` 之后立即 decode，并 yield 一个 `GenerationStreamChunk`。这样流式输出来自真实采样循环，不是把最终字符串事后切块。

## Playground 运行流程

`generateLive` 现在请求 `/api/generate-stream`。浏览器端不使用 `EventSource`，因为本项目需要 POST JSON body；它使用 fetch 返回的 `response.body.getReader()`。

`readGenerationStream` 做三件事：

- 用 `TextDecoder` 把字节流转成文本。
- 按空行切分 SSE block。
- 用 `parseSseEvent` 解析 `event:` 和 `data:` 行。

收到 `start` 时，输出框先显示 prompt。收到 `token` 时，用事件中的 `generated` 更新输出框。收到 `end` 时，用最终 response 校准输出。收到 `error` 时，显示错误信息。

## 输出和证据

`/api/generate-stream` 是服务端最终能力，不是临时调试端点。它适合本地 playground、脚本客户端或后续实验 UI 复用。

`inference_requests.jsonl` 仍然是推理日志证据。本版新增的关键字段是：

- `endpoint: "/api/generate-stream"`
- `stream_chunks`
- `generated_chars`
- `continuation_chars`
- `tokenizer`

`b/55/图片` 保存本版运行截图，`b/55/解释/说明.md` 解释每张截图证明什么。Playwright 截图打开的是生成后的 `playground.html`，用真实 Chrome 验证 `Stream Generate` 流式入口已经出现在浏览器页面里。

## 测试覆盖

`tests/test_model.py` 的新测试确保 `sample_next` 返回形状为 `(1, 1)` 的合法 token id，保护模型层单步采样接口。

`tests/test_server.py` 覆盖：

- `sse_message` 会保留中文并输出标准 SSE block。
- `/api/health` 暴露 `generate_stream_endpoint`。
- `/api/generate-stream` 返回 `text/event-stream`。
- 事件顺序是 `start -> token -> token -> end`。
- token 事件带累计 `generated`。
- end 事件带最终 response。
- JSONL 日志记录 `/api/generate-stream` 和 `stream_chunks`。

`tests/test_playground.py` 覆盖静态 HTML 中存在 `Stream Generate`、`/api/generate-stream` 和 `readGenerationStream`，避免 UI 回退到旧的同步 endpoint。

全量 `python -m unittest discover -s tests` 和 `python -m compileall src scripts tests` 作为回归证据，证明 v55 没破坏前面 54 个版本的主要链路。

## 和前面版本的关系

v12 解决“浏览器如何调用本地模型”，v38 解决“本地推理边界怎么限制”，v39-v42 解决“多 checkpoint 和 pair 输出怎么对比、保存”。v55 解决的是更底层的体验问题：自回归生成本来就是一步一步采样，浏览器也应该能看到这个过程。

它不会替代 `/api/generate`，因为一次性 JSON 对脚本和测试仍然更简单；它是在旁边新增一个更接近真实推理体验的流式接口。

## 一句话总结

v55 把 MiniGPT 从“本地服务能生成一整段文本”推进到“本地服务能暴露真实逐 token 采样事件，并让 playground 边生成边显示”的阶段。
