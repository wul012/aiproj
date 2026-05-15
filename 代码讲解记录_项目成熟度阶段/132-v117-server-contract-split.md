# v117 server contract split 代码讲解

## 本版目标

v117 继续执行 v110 的 module pressure audit 路线，目标是把 `server.py` 中不依赖 HTTP handler、也不触发真实模型推理的契约逻辑抽成独立模块：

```text
server_contracts.py -> safety profile、请求/响应结构、请求解析、checkpoint metadata、health/model-info/compare payload、SSE/pair payload
server.py           -> HTTP handler、本地服务器、真实 generate/stream 调用、请求日志写入、文件服务
```

本版解决的问题是：v112 和 v113 已经把 pair artifact 保存、request history 核心逻辑从 server 中拆出去，但 `server.py` 仍然承担大量“纯契约/纯 payload”逻辑。v117 把这些稳定边界继续拆出，让 server 主体更专注于本地 HTTP 编排。

本版明确不做：

- 不改 `/api/health`、`/api/model-info`、`/api/checkpoints`、`/api/checkpoint-compare`、`/api/generate`、`/api/generate-stream`、`/api/generate-pair` 和 `/api/generate-pair-artifact` 路由。
- 不改 `MiniGPTGenerator.generate()` 和 `MiniGPTGenerator.stream()` 的模型加载、采样和流式生成流程。
- 不改 request history JSONL 写入格式。
- 不改 playground 的请求字段和页面交互。

## 前置路线

v117 接在这条维护收口路线后面：

```text
v110 module pressure audit
 -> v112 pair artifact split
 -> v113 request history core split
 -> v115 playground asset split
 -> v116 registry data/render split
 -> v117 server contract split
```

这说明当前的重点不是继续堆新 API，而是把已经成熟的本地推理边界按职责分层。server 主体应该保留“活的运行时编排”，而把可复用、可单测、无副作用的 contract/payload 逻辑放到独立模块。

## 关键文件

```text
src/minigpt/server_contracts.py
src/minigpt/server.py
tests/test_server_contracts.py
README.md
代码讲解记录_项目成熟度阶段/README.md
c/117/图片
c/117/解释/说明.md
```

`src/minigpt/server_contracts.py` 是本版新增的契约层。它保存 dataclass、请求解析、checkpoint discovery、health/model-info/checkpoint-compare payload、SSE 消息格式、stream timeout payload 和 pair generation payload。

`src/minigpt/server.py` 仍然是旧 public API 的入口。它从 `server_contracts.py` 导入这些符号，所以旧代码继续写：

```python
from minigpt.server import InferenceSafetyProfile, parse_generation_request
```

不会被破坏。与此同时，`server.py` 自身继续负责 `MiniGPTGenerator`、`create_handler()`、`run_server()`、HTTP 响应、SSE 写入、request log 和本地文件服务。

`tests/test_server_contracts.py` 是新增测试。它直接导入 `server_contracts`，验证 contract 模块可以脱离 HTTP handler 独立生成 payload，并验证 `minigpt.server` 的旧导出仍然指向新实现。

## 核心数据结构

`InferenceSafetyProfile` 仍然定义本地推理边界：

- `max_prompt_chars`：prompt 最大字符数。
- `max_new_tokens`：单次生成最大 token 数。
- `min_temperature` / `max_temperature`：采样温度边界。
- `max_top_k`：top-k 上限。
- `max_body_bytes`：HTTP 请求体大小上限。
- `max_stream_seconds`：流式生成最大持续时间。

`GenerationRequest` 是单次生成请求：

- `prompt`
- `max_new_tokens`
- `temperature`
- `top_k`
- `seed`
- `checkpoint`

`GenerationPairRequest` 包含左右两个 `GenerationRequest`，用于 side-by-side generation。

`GenerationResponse` 是生成结果结构，包含 prompt、完整 generated、continuation、采样参数、checkpoint 和 tokenizer。

`GenerationStreamChunk` 是 SSE token 流里的单个 chunk，记录 index、token_id、text、generated、continuation、checkpoint 和 tokenizer。

`CheckpointOption` 是 checkpoint selector 的基础结构，保存 id、name、path、exists、is_default、tokenizer_path、tokenizer_exists 和 source。

## 核心函数

`parse_generation_request(payload, safety_profile)` 把 HTTP JSON 或脚本传入的 dict 解析成 `GenerationRequest`。它负责校验 prompt 非空、长度限制、max_new_tokens、temperature、top_k 和 seed。这个函数是安全边界的一部分，不触发模型。

`parse_generation_pair_request(payload, safety_profile)` 解析左右 checkpoint 请求。它把 `left_checkpoint` 和 `right_checkpoint` 写入两个子请求，并复用 `parse_generation_request()` 做统一校验。

`discover_checkpoint_options(run_dir, checkpoint_path, tokenizer_path, checkpoint_candidates)` 扫描默认 checkpoint、候选 checkpoint、`checkpoints/*.pt` 和嵌套 run 的 `checkpoint.pt`，生成稳定的 `CheckpointOption` 列表。

`build_health_payload()` 生成 `/api/health` 的响应字典。它只看文件是否存在、安全配置和 checkpoint 数量，不加载模型。

`build_model_info_payload()` 生成 `/api/model-info` 的响应字典。它读取 `run_manifest.json`、`train_config.json`、`model_report/model_report.json` 和 `dataset_version.json`，汇总 tokenizer、model_config、parameter_count、dataset_version、dataset_fingerprint、git 和 artifact_count。

`build_checkpoint_compare_payload()` 生成 `/api/checkpoint-compare` 的响应字典。它比较 checkpoint 是否存在、tokenizer 是否存在、参数量差异、dataset 版本是否相同和模型配置是否相同。

`sse_message(event, data)` 负责把事件名和 JSON data 格式化为 Server-Sent Events 文本。

`stream_timeout_payload()` 在流式生成超时时生成标准 payload，保留 partial response、elapsed_seconds、chunk_count 和 timeout reason。

`pair_generation_payload()` 生成左右 checkpoint 的对比响应，记录左右生成结果、checkpoint_id、字符长度差异和 continuation 差异。

## 输入输出格式

本版没有引入新的用户可见 schema。已有 API 的 JSON 结构继续由旧函数名提供，只是实现位置移动到 `server_contracts.py`。

输出仍然包括：

- `/api/health` 的 health payload。
- `/api/model-info` 的 checkpoint/model metadata。
- `/api/checkpoints` 的 checkpoint selector 列表。
- `/api/checkpoint-compare` 的 checkpoint compare matrix。
- `/api/generate-stream` 的 SSE `start/token/timeout/end/error` 事件 data。
- `/api/generate-pair` 和 `/api/generate-pair-artifact` 的 pair generation payload。

这些 payload 是运行时 API 的契约，不是最终训练证据；但它们会被 playground、request history、pair artifact、dashboard 和后续治理模块消费。

## 测试覆盖

`tests/test_server_contracts.py` 新增三类断言：

- 直接用 `server_contracts.build_health_payload()`、`build_checkpoints_payload()` 和 `build_checkpoint_compare_payload()` 可以在没有 HTTP handler 的情况下生成 checkpoint 相关 payload。
- 直接用 `parse_generation_request()`、`parse_generation_pair_request()`、`stream_timeout_payload()` 和 `pair_generation_payload()` 可以生成请求、timeout 和 pair response 契约。
- `minigpt.server.InferenceSafetyProfile`、`parse_generation_request()`、`build_health_payload()`、`sse_message()` 等旧入口仍然与 `server_contracts` 中的新实现保持同一对象身份。

回归测试继续覆盖 `tests.test_server`、`tests.test_request_history`、`tests.test_pair_artifacts` 和 `tests.test_pair_batch`，确保 HTTP 端点、request history、pair artifact 和 pair batch 没有因拆分而改变。

## 运行证据

v117 的运行证据放在：

```text
c/117/图片
c/117/解释/说明.md
```

截图覆盖 server contracts 单测、server/request-history/pair 回归、compileall、全量 unittest、模块行数、maintenance pressure smoke、直接 contract payload 检查、Playwright/Chrome health endpoint 渲染和文档索引检查。

README 更新了当前版本、版本标签、结构说明和截图索引。阶段 README 追加了 `132-v117-server-contract-split.md`，说明这次拆分属于项目成熟度阶段的服务端维护收口，而不是新功能堆叠。

## 一句话总结

v117 把 server 从“HTTP 编排、推理运行、契约解析、checkpoint metadata 和 payload 构造混在一起”推进到“server runtime 与 server contracts 分离”的维护状态，让本地推理服务更容易继续安全演进。
