# 25. v12 Playground Server

这一版新增 `src/minigpt/server.py` 和 `scripts/serve_playground.py`，让 v11 的静态 Playground 能通过本地 HTTP 服务调用真实生成接口。

## 文件角色

`server.py` 负责三件事：

- 校验浏览器发来的生成参数
- 提供 `/api/health` 和 `/api/generate`
- 懒加载 checkpoint、tokenizer 和 MiniGPT 模型

`serve_playground.py` 是命令行入口，用来启动本地服务：

```powershell
python scripts/serve_playground.py --run-dir runs/minigpt --device cpu
```

## 核心流程

```text
browser playground.html
 -> POST /api/generate
 -> parse_generation_request
 -> MiniGPTGenerator lazy load checkpoint
 -> tokenizer.encode(prompt)
 -> model.generate(...)
 -> tokenizer.decode(...)
 -> JSON response
```

## 关键代码

`GenerationRequest` 保存 prompt、max_new_tokens、temperature、top_k 和 seed。

`parse_generation_request` 对这些字段做边界检查，例如 prompt 不能为空、`max_new_tokens` 必须在 1 到 512 之间、temperature 必须大于 0。

`MiniGPTGenerator` 会在第一次请求时加载模型。这样启动 HTTP 服务时不会立刻占用模型加载时间，也方便单元测试用 stub generator 替换真实模型。

`create_handler` 返回一个 `BaseHTTPRequestHandler` 子类。它处理：

- `GET /`：返回 `playground.html`
- `GET /api/health`：返回 run 目录和关键文件是否存在
- `POST /api/generate`：执行本地生成并返回 JSON

## 前端变化

`playground.py` 增加了 `Live Generate` 区块。静态打开时仍可复制命令；通过 server 打开时，点击 Generate 会调用 `/api/generate`。

## 一句话总结

v12 把 MiniGPT 从“能生成本地 HTML 报告”推进到“能通过浏览器调用本地模型生成”，这是后续做流式输出和更完整 Web UI 的入口。
