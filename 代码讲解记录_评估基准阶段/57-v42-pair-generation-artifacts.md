# 57-v42-pair-generation-artifacts

## 本版目标、来源和边界

v42 的目标是把 v41 的 side-by-side generation 从“浏览器里看一次结果”推进到“把这次左右 checkpoint 对比保存成可复查的本地证据”。v41 已经能用同一个 prompt 调用两个 checkpoint，并返回 left/right 输出和 comparison summary；v42 继续补上留档能力：

```text
同一次 pair generation 的请求、左右输出、对比摘要能不能保存下来？
保存后的 JSON/HTML 能不能从 playground 直接打开？
inference_requests.jsonl 能不能追踪这次请求生成了哪些 artifact？
```

本版不做三件事：

- 不把 pair artifact 升级成批量 benchmark；这里仍然是一次请求一次留档。
- 不判断哪一个 checkpoint 更好；`comparison` 只记录相同与否、长度差异和 checkpoint 是否相同。
- 不改变模型训练或采样算法；生成结果仍来自现有 `LocalGenerator` 和 `GenerationRequest`。

## 本版处在评估链路的哪一环

当前链路是：

```text
checkpoint selector
 -> checkpoint compare table
 -> /api/generate-pair
 -> /api/generate-pair-artifact
 -> pair_generations/*.json
 -> pair_generations/*.html
 -> inference_requests.jsonl artifact paths
 -> playground artifact link
 -> Playwright browser evidence
```

v42 的意义是让人工快速对比也具备“可追溯证据”。它还不是标准化评估集，但它让后续做固定 prompt pair batches、人工巡检、实验复盘时不再只依赖页面瞬时状态。

## 关键文件

```text
src/minigpt/server.py
src/minigpt/playground.py
scripts/serve_playground.py
src/minigpt/__init__.py
tests/test_server.py
tests/test_playground.py
README.md
b/42/解释/说明.md
```

`server.py` 负责新增保存端点、artifact schema、JSON/HTML 写入和日志路径；`playground.py` 负责增加 `Generate & Save Pair` 按钮和保存结果链接；`tests` 负责保护 API、HTML 和日志证据；`b/42` 保存真实运行截图。

## 保存端点

v42 新增：

```text
POST /api/generate-pair-artifact
```

这个端点复用 v41 的 pair generation 主流程：读取 prompt、采样参数、`left_checkpoint` 和 `right_checkpoint`，分别生成左右输出，然后构造同样的 pair payload。区别在于它会额外调用：

```python
write_pair_generation_artifacts(root, payload)
```

返回结果仍然包含 `status`、`left`、`right` 和 `comparison`，同时新增：

```text
artifact.json_path
artifact.html_path
artifact.json_href
artifact.html_href
```

其中 `*_path` 是本地文件路径，`*_href` 是 playground server 可以直接打开的相对链接。

## Artifact Schema

`write_pair_generation_artifacts` 会在 run 目录下创建：

```text
pair_generations/
```

并写入一对同名文件：

```text
<timestamp>-<left>-vs-<right>.json
<timestamp>-<left>-vs-<right>.html
```

JSON record 的核心字段是：

```text
schema_version = 1
kind = minigpt_pair_generation
created_at
run_dir
request
left
right
comparison
artifact
```

`request` 记录 prompt 和采样参数；`left` / `right` 记录两个 checkpoint 的生成结果；`comparison` 记录左右输出是否一致、字符长度差异和 checkpoint 是否相同；`artifact` 记录 JSON/HTML 的本地路径与可打开链接。

## HTML Report

`render_pair_generation_html` 把同一份 record 渲染成一个轻量 HTML 报告。页面包含：

```text
Created
Prompt
Sampling settings
Left checkpoint
Right checkpoint
Comparison summary
Left generated output
Right generated output
```

HTML 不是为了替代 dashboard，而是为了让一次 pair generation 可以脱离浏览器状态单独查看。字段渲染时会走 HTML escaping，避免 prompt 或 generated text 里的特殊字符破坏页面结构。

## Request Log

v42 继续沿用 `inference_requests.jsonl`，但保存版请求会记录：

```text
endpoint = /api/generate-pair-artifact
artifact_json
artifact_html
```

普通 `/api/generate-pair` 不会写 artifact 路径。保存版请求即使因为参数错误被拒绝，日志中的 endpoint 也保持为 `/api/generate-pair-artifact`，这样排查时能知道用户实际打的是保存端点。

## Playground 前端

`playground.py` 在 side-by-side 区块里新增：

```text
button#pairSaveButton
output#pairArtifactStatus
```

`Generate Pair` 仍然调用 `/api/generate-pair`，只做实时对比；`Generate & Save Pair` 调用 `/api/generate-pair-artifact`，生成完成后把返回的 `artifact.html_href` 渲染成 `Open saved pair HTML` 链接。这样页面既能保留轻量实时对比，也能在需要复盘时显式保存证据。

## CLI 行为

`scripts/serve_playground.py` 启动时现在会打印：

```text
generate_pair_artifact=http://127.0.0.1:8000/api/generate-pair-artifact
```

这让命令行截图能证明保存端点已经暴露，和 `generate_pair`、`checkpoints`、`checkpoint_compare` 等本地 API 保持同一套可见入口。

## 测试覆盖链路

`tests/test_server.py` 覆盖：

- `/api/health` 暴露 `generate_pair_artifact_endpoint`。
- `/api/generate-pair-artifact` 会写出 JSON 和 HTML 文件。
- JSON record 的 `kind`、checkpoint id、artifact path 和 comparison 字段可检查。
- HTML 报告包含生成内容。
- `inference_requests.jsonl` 会写入 artifact JSON/HTML 路径。

`tests/test_playground.py` 覆盖：

- HTML 包含 `pairSaveButton`。
- HTML 包含 `pairArtifactStatus`。
- 脚本里存在 `/api/generate-pair-artifact`。

这些测试保护的是从浏览器保存按钮到 server endpoint，再到本地 artifact 文件和 request log 的完整路径。

## 归档和截图证据

本版运行证据放在：

```text
b/42/图片
b/42/解释/说明.md
```

关键截图包括：

```text
01-unit-tests.png
02-generate-pair-artifact-smoke.png
03-generate-pair-artifact-structure-check.png
04-playwright-pair-artifacts.png
05-docs-check.png
```

其中 `02` 证明 HTTP smoke 覆盖保存端点、artifact 文件、HTML 内容、普通 pair 兼容和 bad request；`03` 证明 record schema、href、日志 artifact 路径和 playground 控件存在；`04` 证明真实 Chrome 能打开保存控件；`05` 证明 README、b/42 和讲解索引已经闭环。

## 一句话总结

v42 把 MiniGPT 的双 checkpoint 生成对比从“页面上的一次结果”推进到“可打开、可复查、可被日志追踪的本地 JSON/HTML 实验片段”。
