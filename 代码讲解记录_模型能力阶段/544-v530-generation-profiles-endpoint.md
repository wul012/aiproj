# v530 generation profiles endpoint 代码讲解

## 本版目标与边界

v530 的目标是把 v529 的 generation profile 从“前端静态选项 + 请求字段”进一步收束为运行时可查询契约。v529 已经让 CLI/API/playground 能传 `generation_profile`，但 playground 的 profile 列表仍主要来自生成 HTML 时嵌入的 page data。

本版新增：

```text
/api/generation-profiles
```

用于返回当前 server 支持的 profile registry。它不新增新的 profile，也不改变默认解码。

## 前置链路

前置版本：

- v528：证明 blocked-token profile 在 3 seed sweep 上比 baseline 更稳定。
- v529：把 `suppress_newline_tokens` 暴露给 CLI、API、playground。

v530 解决的是“profile 列表是否能被运行时服务统一发布”的契约问题。

## 关键文件

- `src/minigpt/generation_profiles.py`
  - 新增 `build_generation_profiles_payload()`。
  - 返回 `status`、`default_generation_profile_id`、`profile_count` 和 `profiles`。
- `src/minigpt/server_contracts.py`
  - 重新导出 `build_generation_profiles_payload()`。
  - `build_health_payload()` 中加入 `generation_profiles_endpoint` 和 `generation_profiles`。
- `src/minigpt/server_routes.py`
  - 新增 GET `/api/generation-profiles`。
- `src/minigpt/server.py`
  - facade 导出 profile payload builder。
- `src/minigpt/playground_script.py`
  - 新增 `loadGenerationProfiles()`。
  - playground 启动后请求 `/api/generation-profiles`，再刷新 Profile select。
- `tests/test_server_routes.py`
  - 覆盖新 endpoint 返回 profile registry。
- `tests/test_server_contracts.py`、`tests/test_server.py`、`tests/test_playground.py`
  - 覆盖 health payload 与 playground runtime script 变化。

## 核心数据结构

endpoint payload：

```text
status
default_generation_profile_id
profile_count
profiles[]
```

每个 profile 仍来自 v529 的 `GenerationProfile`：

```text
id
label
description
blocked_token_texts
```

当前 profile registry：

```text
default -> []
suppress_newline_tokens -> ["\n","\r"]
```

## 核心流程

server 路径：

```text
GET /api/generation-profiles
 -> server_routes.handle_get_request()
 -> build_generation_profiles_payload()
 -> handler._send_json(...)
```

playground 路径：

```text
DOMContentLoaded
 -> loadGenerationProfiles()
 -> fetch('/api/generation-profiles')
 -> MiniGPTPlayground.generationProfiles = data.profiles
 -> populateGenerationProfileSelect()
 -> buildCommands()
```

如果 endpoint 不可用，playground 仍会使用 HTML 内置 profiles 作为 fallback，因此离线静态查看不会失效。

## 真实结果解释

真实 server 查询：

```text
status=ok
default_generation_profile_id=default
profile_count=2
profiles=default,suppress_newline_tokens
```

health payload 同步暴露：

```text
generation_profiles_endpoint=/api/generation-profiles
```

Playwright 运行时检查返回：

```text
profiles=default,suppress_newline_tokens
command=... --generation-profile 'suppress_newline_tokens'
```

这证明 profile 下拉框不是孤立静态文案，而是能和 server registry 对齐。

## 测试覆盖

测试覆盖：

- GET route 返回 profile registry。
- health payload 带 profile endpoint 和 profiles。
- server facade 导出 profile payload builder。
- playground HTML/JS 包含 endpoint、loader 和 select 刷新逻辑。
- 既有 generation profile 解析、日志、POST route 测试继续通过。

## 运行证据

运行证据归档在：

```text
e/530/解释/generation-profiles-endpoint/
e/530/图片/
```

截图：

```text
e/530/图片/01-generation-profiles-endpoint-playground.png
```

## 一句话总结

v530 把 generation profile 变成运行时可查询的 server contract，让 playground、API 和 CLI 围绕同一个 profile registry 收束。
