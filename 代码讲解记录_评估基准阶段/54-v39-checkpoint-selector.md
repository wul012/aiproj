# 54-v39-checkpoint-selector

## 本版目标、来源和边界

v39 的目标是把 v38 的本地 playground server 从“安全地服务一个 checkpoint”推进到“能发现、展示并选择多个 checkpoint”。v37 已经能做 baseline model comparison，v38 已经有 `/api/model-info` 和请求日志；现在需要让浏览器端和 API 端都能回答：

```text
当前 run 目录里有哪些 checkpoint 可以选？
默认 checkpoint 是哪个？
用户选择 wide/tiny 之类候选模型后，/api/generate 是否真的路由到它？
请求日志里能不能留下所选 checkpoint 的证据？
```

本版不做三件事：

- 不实现跨机器模型仓库或远程 checkpoint 下载。
- 不把 checkpoint 选择变成训练调度系统。
- 不比较生成质量，只保证本地服务链路能明确选择和记录 checkpoint。

## 本版处在评估链路的哪一环

当前链路是：

```text
run directory
 -> default checkpoint / candidate checkpoint
 -> /api/checkpoints
 -> playground checkpoint dropdown
 -> /api/model-info?checkpoint=<id>
 -> /api/generate { checkpoint }
 -> inference_requests.jsonl
 -> smoke / structure check / Playwright evidence
```

v39 的重点是让“同一个 playground 里切换不同 checkpoint”成为可测试、可记录的工程能力。它不是直接提高模型能力，而是为后续 checkpoint comparison、live eval、服务化展示打基础。

## 关键文件

```text
src/minigpt/server.py
src/minigpt/playground.py
scripts/serve_playground.py
src/minigpt/__init__.py
tests/test_server.py
tests/test_playground.py
README.md
b/39/解释/说明.md
```

`server.py` 负责 checkpoint 发现、解析、路由和日志。`playground.py` 负责浏览器下拉框和请求 payload。`serve_playground.py` 把候选 checkpoint 作为 CLI 参数暴露出来。

## CheckpointOption

新增 `CheckpointOption` 描述一个可选 checkpoint：

```python
@dataclass(frozen=True)
class CheckpointOption:
    id: str
    name: str
    path: str
    exists: bool
    is_default: bool
    tokenizer_path: str | None
    tokenizer_exists: bool
    source: str
```

字段语义：

- `id` 是前端和 API 使用的稳定选择值，例如 `default`、`candidate`、`checkpoints-wide`。
- `path` 是真实 checkpoint 路径。
- `exists` 用于区分配置了但文件不存在的候选项。
- `is_default` 标记 run 目录主 checkpoint。
- `tokenizer_path` 和 `tokenizer_exists` 说明这个 checkpoint 对应哪个 tokenizer。
- `source` 记录候选项来自 default、显式 CLI candidate，还是目录发现。

## Checkpoint 发现

`discover_checkpoint_options` 会从三类来源组装候选项：

```text
1. 默认 checkpoint：run_dir/checkpoint.pt 或 --checkpoint 指定路径
2. 显式候选项：--checkpoint-candidate PATH，可重复传入
3. 常见目录候选项：run_dir/checkpoints/*.pt
```

发现过程会做去重和 id 归一化。默认项使用 `default`，候选项优先用父目录名或文件名生成可读 id；如果冲突，就自动加数字后缀。这样浏览器不用拿绝对路径当选择值，也避免 Windows 路径直接进入 API 参数。

## 新增 API

v39 后本地 server 暴露：

```text
GET  /api/health
GET  /api/checkpoints
GET  /api/model-info?checkpoint=<id>
POST /api/generate
```

`/api/checkpoints` 返回：

```text
status
run_dir
default_checkpoint_id
count
checkpoints[]
```

`/api/model-info` 会读取 query string 里的 `checkpoint`，把选中的 checkpoint 和 tokenizer 传给 `build_model_info_payload`，并在输出里写入 `checkpoint_id`。如果没有传 checkpoint，就使用默认项。

`/api/generate` 的 JSON payload 现在支持：

```json
{
  "prompt": "人工智能",
  "checkpoint": "wide",
  "max_new_tokens": 80,
  "temperature": 0.8,
  "top_k": 30,
  "seed": 42
}
```

服务端会先通过 `resolve_checkpoint_option` 找到真实 checkpoint，再从缓存中取对应 `MiniGPTGenerator`。不存在或文件缺失的 checkpoint 会返回 `400 bad_request`。

## Playground 前端

`playground.py` 新增 checkpoint 下拉框：

```text
select#checkpointSelect
output#checkpointStatus
```

页面加载时调用 `/api/checkpoints`，把返回的候选项填进下拉框。选择项变化后会重新生成 command snippets，并在 live generation 请求中加入：

```javascript
payload.checkpoint = checkpoint.id;
```

这样前端展示、命令提示和 API 请求使用的是同一个选择状态。

## CLI 行为

`scripts/serve_playground.py` 新增：

```powershell
--checkpoint-candidate PATH
```

可以重复传入多个候选 checkpoint。启动后会打印：

```text
serving=http://127.0.0.1:8000/
model_info=http://127.0.0.1:8000/api/model-info
checkpoints=http://127.0.0.1:8000/api/checkpoints
checkpoint_count=...
```

这让命令行截图能直接证明 checkpoint selector 已经被服务端识别。

## 请求日志

v39 保留 v38 的 `inference_requests.jsonl`，并新增两类字段：

```text
checkpoint_id
requested_checkpoint
```

`checkpoint_id` 表示最终解析成功并用于生成的 checkpoint；`requested_checkpoint` 保留请求里传入的原始 id。成功请求会记录真实选中项；错误请求也会记录原始选择值，方便定位前端或调用方传错了什么。

## 测试覆盖链路

`tests/test_server.py` 覆盖：

- `discover_checkpoint_options` 能发现默认项、显式候选项和 `checkpoints/*.pt`。
- `/api/health` 返回 checkpoint endpoint、数量和默认 id。
- `/api/checkpoints` 返回可用于前端下拉框的候选项。
- `/api/model-info?checkpoint=candidate` 使用指定 checkpoint。
- `/api/generate` 传入 `checkpoint` 后路由到对应 generator。
- 请求日志写入 `checkpoint_id` 和 `requested_checkpoint`。
- 坏 checkpoint 请求返回 `400` 并记录 `bad_request`。

`tests/test_playground.py` 覆盖：

- 静态 playground HTML 包含 `checkpointSelect`。
- 页面脚本会请求 `/api/checkpoints`。
- live generation payload 会发送 `payload.checkpoint`。

这些断言保护的是 checkpoint selector 的端到端链路，而不是某个具体测试 fixture 的文本输出。

## 归档和截图证据

本版运行证据放在：

```text
b/39/图片
b/39/解释/说明.md
```

关键截图包括：

```text
01-unit-tests.png
02-checkpoint-selector-smoke.png
03-checkpoint-selector-structure-check.png
04-playwright-checkpoint-selector.png
05-docs-check.png
```

其中 `02` 证明本地 HTTP smoke 能发现 default/wide、用 wide 生成并拒绝 missing；`03` 证明结构检查覆盖 API、日志和前端 payload；`04` 证明真实 Chrome 能打开带 selector 的 playground；`05` 证明 README、b/39 和讲解索引已经闭环。

## 一句话总结

v39 把 MiniGPT 的本地 playground 从“单 checkpoint 推理页面”推进到“可发现、可选择、可路由、可记录 checkpoint 的本地推理实验入口”。
