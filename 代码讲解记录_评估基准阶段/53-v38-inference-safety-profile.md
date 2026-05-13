# 53-v38-inference-safety-profile

## 本版目标、来源和边界

v38 的目标是把本地 playground server 从“能调用 `/api/generate`”推进到“知道本地推理 API 的边界、模型信息和请求记录”。v12 已经有本地 server，v37 已经能比较不同 run；现在需要让一个 run 被服务时也能回答：

```text
这个 API 当前服务的是哪个 checkpoint？
请求最多能生成多少 token？
prompt、temperature、top_k 是否有边界？
请求是否留下了可追踪日志？
```

本版不做三件事：

- 不把服务开放成公网生产服务，默认仍是本地 `127.0.0.1`。
- 不做用户认证、速率限制或多用户隔离。
- 不引入外部推理框架，只加轻量 HTTP API 安全边界和证据记录。

## 本版处在评估链路的哪一环

当前链路是：

```text
checkpoint / tokenizer / run manifest
 -> playground server
 -> inference safety profile
 -> /api/health / /api/model-info / /api/generate
 -> inference_requests.jsonl
 -> smoke / structure check / Playwright evidence
```

v38 的重点不是提升模型质量，而是让“模型被本地调用”这件事有边界、有自描述、有日志。

## 关键文件

```text
src/minigpt/server.py
scripts/serve_playground.py
tests/test_server.py
src/minigpt/__init__.py
README.md
b/38/解释/说明.md
```

核心逻辑在 `server.py`。CLI 只把这些能力暴露成参数，保持原有 `--run-dir`、`--checkpoint`、`--tokenizer`、`--device` 用法兼容。

## 新增安全画像

新增 `InferenceSafetyProfile`：

```python
InferenceSafetyProfile(
    max_prompt_chars=2000,
    max_new_tokens=512,
    min_temperature=0.05,
    max_temperature=2.0,
    max_top_k=200,
    max_body_bytes=16 * 1024,
)
```

`parse_generation_request` 会根据这个 profile 检查：

- prompt 不能为空，也不能超过 `max_prompt_chars`。
- `max_new_tokens` 必须在 `1..max_new_tokens`。
- `temperature` 必须在配置范围内。
- `top_k` 为 0/空时表示关闭，否则必须在 `1..max_top_k`。
- HTTP body 不能超过 `max_body_bytes`。

这样 playground server 不再只是把请求直接交给模型，而是先做一层明确的本地边界检查。

## 新增 API 端点

v38 后 server 暴露：

```text
GET  /api/health
GET  /api/model-info
POST /api/generate
```

`/api/health` 会返回 endpoint 名称、安全画像和 request log 路径。`/api/model-info` 会从 `run_manifest.json`、`train_config.json`、`model_report.json` 和 `dataset_version.json` 中汇总 checkpoint、tokenizer、模型配置、参数量、dataset version、fingerprint 和 Git 信息。

## 请求日志

`/api/generate` 的成功或失败都会写入 JSONL：

```text
inference_requests.jsonl
```

每条记录包含：

- `timestamp`
- `endpoint`
- `status`
- `client`
- `checkpoint`
- `prompt_chars`
- `max_new_tokens`
- `temperature`
- `top_k`
- `seed`
- `generated_chars` / `continuation_chars`
- `error`

日志只记录长度、参数和错误，不记录完整 prompt 内容，避免把用户输入默认写进证据文件。

## CLI 行为

`scripts/serve_playground.py` 新增参数：

```powershell
--max-prompt-chars
--max-new-tokens-limit
--min-temperature
--max-temperature
--max-top-k
--max-body-bytes
--request-log
```

启动时会打印：

```text
serving=http://127.0.0.1:8000/
model_info=http://127.0.0.1:8000/api/model-info
request_log=runs/minigpt/inference_requests.jsonl
safety={...}
```

这让命令行截图能直接说明当前服务边界。

## 测试覆盖链路

`tests/test_server.py` 覆盖：

- 默认 generation request 解析。
- 自定义 safety profile 的 prompt/token/temperature/top_k 限制。
- `/api/health` 返回安全画像和 model-info endpoint。
- `/api/model-info` 读取 run metadata。
- `append_inference_log` 写入 JSONL。
- HTTP server 成功生成时写入 `ok` 日志。
- HTTP server 拒绝坏请求时写入 `bad_request` 日志。

这些断言保护的是推理 API 边界和可追踪性，而不是具体浏览器样式。

## 归档和截图证据

本版运行证据放在：

```text
b/38/图片
b/38/解释/说明.md
```

关键截图包括：

```text
01-unit-tests.png
02-server-safety-smoke.png
03-server-safety-structure-check.png
04-playwright-model-info.png
05-docs-check.png
```

其中 `02` 证明 HTTP smoke 覆盖 health/model-info/generate/reject/log；`03` 证明日志和 metadata 字段能被脚本检查；`04` 证明 `/api/model-info` 可以被真实 Chrome 打开；`05` 证明 README、b/38 和讲解索引已经闭环。

## 一句话总结

v38 把 MiniGPT 的本地推理服务从“能调用模型”推进到“有安全画像、有模型自描述、有请求日志、有浏览器验证证据”的阶段。
