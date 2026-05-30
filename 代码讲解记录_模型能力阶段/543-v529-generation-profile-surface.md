# v529 generation profile surface 代码讲解

## 本版目标与边界

v529 的目标是把 v528 证明稳定有价值的 blocked-token 解码，变成用户能明确选择的 generation profile。此前用户需要知道底层字段 `blocked_token_texts`，还要手动传 `"\n"` 与 `"\r"`。这对实验代码可以接受，对 API/playground 使用面不够友好。

本版新增 profile 名称：

```text
suppress_newline_tokens
```

它只是一个显式选项，不改变默认行为。`default` profile 不屏蔽任何 token。

## 前置链路

前置版本：

- v526：core generator 支持 `blocked_token_texts`。
- v527：fresh checkpoint 对照证明单 seed 默认解码也可能 strict full。
- v528：三 seed sweep 证明 baseline 只有 `2/3` seeds strict full，而 blocked-token profile 达到 `3/3` seeds strict full。

v529 接着把这个 profile 暴露给真实使用入口。

## 关键文件

- `src/minigpt/generation_profiles.py`
  - 新增 profile registry。
  - 定义 `default` 与 `suppress_newline_tokens`。
  - 提供 `generation_profile_options()`、`resolve_generation_profile()`、`merge_blocked_token_texts()`。
- `src/minigpt/server_contracts.py`
  - `GenerationRequest` 新增 `generation_profile`。
  - `parse_generation_request()` 解析 profile，并把 profile 的 blocked tokens 与显式 blocked tokens 合并。
  - `GenerationResponse` 与 `GenerationStreamChunk` 返回 profile 元数据。
- `src/minigpt/server_generator.py`
  - response/stream chunk 携带 `generation_profile`。
- `src/minigpt/server_post_routes.py`
  - SSE start/end payload 记录 profile 与 blocked-token 信息。
- `src/minigpt/server_logging.py`
  - 请求日志记录 `generation_profile`、`blocked_token_texts`、`blocked_token_count`。
- `scripts/generate.py`
  - 新增 `--generation-profile`、`--blocked-token-text` 和 `--seed`。
  - 改为通过 `MiniGPTGenerator` 走与服务端一致的生成路径。
- `src/minigpt/playground.py` 与 `src/minigpt/playground_script.py`
  - playground 增加 Profile 下拉框。
  - live generate、pair generate、命令构建器都会携带 profile。

## 核心数据结构

`GenerationProfile`：

```text
id
label
description
blocked_token_texts
```

当前 registry：

```text
default -> ()
suppress_newline_tokens -> ("\n", "\r")
```

`GenerationRequest` 新字段：

```text
generation_profile: str = "default"
blocked_token_texts: tuple[str, ...] = ()
```

解析规则：

1. 读取 `generation_profile`。
2. 查 profile registry，未知 profile 直接报错。
3. 取出 profile 自带的 blocked token texts。
4. 与用户显式传入的 `blocked_token_texts` 去重合并。
5. 继续走 v526 的 core generator blocked-token path。

这样 profile 是高层语义，`blocked_token_texts` 仍保留为低层扩展口。

## 核心流程

API 路径：

```text
payload.generation_profile
 -> parse_generation_request()
 -> merge_blocked_token_texts()
 -> MiniGPTGenerator.generate()
 -> MiniGPT.generate(blocked_token_ids=...)
 -> GenerationResponse.to_dict()
```

Playground 路径：

```text
Profile select
 -> selectedGenerationProfile()
 -> payload.generation_profile
 -> /api/generate-stream or /api/generate-pair
```

CLI 路径：

```text
scripts/generate.py --generation-profile suppress_newline_tokens
 -> parse_generation_request()
 -> MiniGPTGenerator
```

三条路径最后都会到同一条 generator 实现，避免 CLI 和服务端行为分叉。

## 真实结果解释

v529 使用 v528 seed `528` checkpoint 对 `omega:` 做对照。

默认 CLI 输出：

```text
omega: los
sssssss
```

profile CLI 输出：

```text
omega: losssssssss
```

API 响应中记录：

```text
generation_profile=suppress_newline_tokens
blocked_token_texts=["\n","\r"]
blocked_token_count=1
```

这证明 profile 不只是静态 UI 控件，而是真正进入了解码请求和响应审计链。

## 测试覆盖

新增/更新测试覆盖：

- `parse_generation_request()` 能把 `suppress_newline_tokens` 转成 `("\n","\r")`。
- 未知 profile 会被拒绝。
- server POST route 返回 profile 与 blocked-token metadata。
- request log 记录 profile 与 blocked-token 信息。
- playground HTML 包含 profile 下拉框、profile id 和 `--generation-profile` 命令参数。

这些测试保护的是“profile 名称到真实 generator 行为”的链路，而不是只检查前端文字。

## 运行证据

运行证据归档在：

```text
e/529/解释/generation-profile-playground/
e/529/图片/
```

截图：

```text
e/529/图片/01-generation-profile-playground.png
```

## 一句话总结

v529 把 v528 的 blocked-token 稳定性结论落成 CLI、API 和 playground 都能调用的显式 generation profile，并保持默认解码不变。
