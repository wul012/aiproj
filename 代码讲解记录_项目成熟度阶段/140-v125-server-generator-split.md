# v125 server generator split 代码讲解

## 本版目标

v125 继续按 v110 module pressure audit 做定向收口，目标是把 `server.py` 里的 `MiniGPTGenerator` 抽成独立模块：

```text
server.py           -> HTTP routes, SSE, request logging, pair generation orchestration
server_generator.py -> PyTorch checkpoint/tokenizer loading, device selection, generate/stream
```

本版解决的问题是：`server.py` 同时承载 HTTP handler、request parsing、response writing、SSE streaming、request-history logging、pair generation orchestration 和真实 PyTorch generator。v117 已经把契约和 payload helper 抽到 `server_contracts.py`，v125 继续把模型生成类抽出，让 server 主文件更聚焦在 HTTP 编排。

本版明确不做：

- 不改 `/api/health`、`/api/checkpoints`、`/api/checkpoint-compare`、`/api/model-info`、`/api/generate`、`/api/generate-stream`、`/api/generate-pair`、`/api/generate-pair-artifact` 等路由。
- 不改 SSE event 名称、timeout payload、stream logging 和 cancellation logging。
- 不改 request-history JSONL 字段。
- 不改 pair generation payload 和 artifact 写入。
- 不移除 `from minigpt.server import MiniGPTGenerator` 旧导出。

## 前置路线

v125 接在这条服务端治理路线后面：

```text
v112 pair artifact split
 -> v113 request history core split
 -> v117 server contract split
 -> v125 server generator split
```

这说明服务端治理不是一次性大重构，而是按稳定边界逐步拆分：先拆 pair artifact 保存，再拆 request history 数据处理，再拆纯契约和 payload，最后拆真实模型 generator。

## 关键文件

```text
src/minigpt/server.py
src/minigpt/server_generator.py
tests/test_server_generator.py
README.md
c/125/图片
c/125/解释/说明.md
```

`src/minigpt/server_generator.py` 是本版新增模块，负责 `MiniGPTGenerator`：

- 记录 checkpoint path、tokenizer path 和 device。
- 懒加载 torch、tokenizer、GPTConfig、MiniGPT 和 checkpoint state dict。
- 执行一次性 `generate()`。
- 执行逐 token `stream()`。
- 处理 `auto`/`cpu`/`cuda` device 选择。

`src/minigpt/server.py` 继续是本地推理服务主模块：

- `create_handler()` 生成 `BaseHTTPRequestHandler` 子类。
- `do_GET()` 处理 health、checkpoint、request-history、model-info 和静态 playground 文件。
- `do_POST()` 处理 generate、stream generate、pair generate 和 pair artifact。
- `_log_generation()` / `_log_pair_generation()` 写入 request-history JSONL。
- `_send_json()` / `_send_text()` / `_send_sse_headers()` / `_write_sse()` / `_send_file()` 负责响应写入。

## 核心数据结构

`MiniGPTGenerator` 消费的请求和输出仍来自 `server_contracts.py`：

- `GenerationRequest`：prompt、max_new_tokens、temperature、top_k、seed、checkpoint。
- `GenerationResponse`：prompt、generated、continuation、采样参数、checkpoint、tokenizer、checkpoint_id。
- `GenerationStreamChunk`：逐 token 输出的 index、token_id、text、generated、continuation、checkpoint、tokenizer。

v125 不改变这些 dataclass，也不改变它们的 `to_dict()` 结果。

## 核心函数

`MiniGPTGenerator.generate(request)`
加载模型和 tokenizer，把 prompt 编码成 token ids，按 block size 裁剪，按 seed 固定随机性，然后调用模型的 `generate()` 得到完整输出。返回 `GenerationResponse`。

`MiniGPTGenerator.stream(request)`
加载同一组模型和 tokenizer，逐步调用 `model.sample_next()`，每个 token 产出一个 `GenerationStreamChunk`。HTTP 层仍在 `server.py` 里负责把这些 chunk 包装成 SSE event。

`MiniGPTGenerator._load()`
懒加载 checkpoint、tokenizer、config 和模型权重。第一次加载后缓存在 `_loaded`，避免每次请求重复加载。

`MiniGPTGenerator._device(torch)`
统一处理 `auto`、`cpu` 和 `cuda`。如果用户明确请求 `cuda` 但不可用，继续抛出原来的 RuntimeError。

## 输入输出边界

v125 后的本地推理流程是：

```text
HTTP request
 -> server.py parse request / resolve checkpoint / log result
 -> server_generator.py MiniGPTGenerator.generate() or stream()
 -> server.py JSON/SSE response
 -> request_history.py append log
```

`server_generator.py` 不知道 HTTP status、headers、SSE event 名称、request-history JSONL 路径或 pair artifact 输出路径。它只关心模型加载和 token 生成。

## 测试覆盖

`tests/test_server_generator.py` 新增三类断言：

- `server.MiniGPTGenerator is server_generator.MiniGPTGenerator`，保护旧导出。
- `create_handler()` 的默认 `generator_factory` 仍然是 `MiniGPTGenerator`，保护 handler 默认行为。
- 默认 tokenizer path 会落在 checkpoint 同目录的 `tokenizer.json`，显式 tokenizer path 能覆盖默认值，并且 `_loaded` 初始为 `None`。

原有 `tests/test_server.py` 继续覆盖：

- health/model-info/checkpoint payload。
- `/api/generate`。
- `/api/generate-stream` start/token/end/timeout。
- cancelled stream logging。
- `/api/generate-pair` 和 `/api/generate-pair-artifact`。
- bad request handling。

原有 `tests/test_server_contracts.py` 继续覆盖契约模块和 server facade export。

## 运行证据

v125 的运行证据放在：

```text
c/125/图片
c/125/解释/说明.md
```

关键证据包括：

- server generator 新测试、server contracts 回归、server HTTP 回归、compileall 和全量 unittest。
- maintenance batching/module pressure smoke，证明 `server.py` 从 678 非空行降到 588 非空行，warn 模块从 2 个降到 1 个。
- direct contract check，证明旧导出、默认 tokenizer 路径、显式 tokenizer 路径和 `create_handler()` 默认 generator factory 都稳定。
- 文档闭环检查，证明 README、`c/README.md`、项目成熟度阶段 README 和本讲解文件都引用 v125。

这些截图不是临时调试文件，而是 v125 tag 的运行证明。临时 smoke 目录仍按 cleanup gate 删除。

## 一句话总结

v125 把本地推理 server 从“HTTP 编排和 PyTorch 生成混在一个文件”推进到“server 编排层和 generator 生成层分离”，让服务端继续保持可运行，同时降低大文件维护压力。
