# 56-v41-side-by-side-generation

## 本版目标、来源和边界

v41 的目标是把 v40 的 checkpoint comparison shortcuts 从“能看候选 checkpoint 的差异”推进到“能用同一个 prompt 同时调用两个 checkpoint 并直接比较输出”。v39 解决了 checkpoint 选择，v40 解决了 checkpoint 快速比较；现在要让 playground 回答更接近模型能力的问题：

```text
同一个 prompt 和同一组采样参数下，两个 checkpoint 的生成结果是否相同？
左右 checkpoint 分别路由到了哪个模型文件？
这次 pair generation 是否留下了 request log 证据？
前端能否在一个页面里选择左右 checkpoint 并看到双栏输出？
```

本版不做三件事：

- 不把 pair generation 结果保存成长期实验 artifact；本版只做 live API 和日志证据。
- 不替代 eval suite 或 generation quality；这里只提供人工快速观察入口。
- 不实现流式 token 输出；左右两栏仍等待完整生成返回。

## 本版处在评估链路的哪一环

当前链路是：

```text
checkpoint selector
 -> checkpoint compare table
 -> left/right checkpoint selectors
 -> /api/generate-pair
 -> left/right GenerationResponse
 -> pair comparison summary
 -> inference_requests.jsonl
 -> Playwright browser evidence
```

v41 的重点是让“两个候选 checkpoint 的生成结果差异”在本地 playground 中直接可见。它不是标准化评估，但它让后续做 pair artifact、固定 prompt 对照和人工巡检更自然。

## 关键文件

```text
src/minigpt/server.py
src/minigpt/playground.py
scripts/serve_playground.py
src/minigpt/__init__.py
tests/test_server.py
tests/test_playground.py
README.md
b/41/解释/说明.md
```

`server.py` 负责 pair request 解析、左右 checkpoint 路由、pair response 和日志。`playground.py` 负责左右 checkpoint 选择和双栏输出。测试覆盖 API 与前端 wiring，文档和 b/41 归档负责把证据链收口。

## GenerationPairRequest

v41 新增 `GenerationPairRequest`：

```python
@dataclass(frozen=True)
class GenerationPairRequest:
    left: GenerationRequest
    right: GenerationRequest
```

它复用已有 `GenerationRequest`，避免为 prompt、max_new_tokens、temperature、top_k、seed 再写一套校验规则。`parse_generation_pair_request` 会从同一个 JSON body 里读取公共采样参数，然后分别写入：

```text
left_checkpoint
right_checkpoint
```

如果没有 `right_checkpoint`，就返回 `ValueError`。这是为了避免用户以为自己在做双 checkpoint 对比，实际只调用了默认 checkpoint。

## 新增 API

v41 新增：

```text
POST /api/generate-pair
```

请求体示例：

```json
{
  "prompt": "人工智能",
  "max_new_tokens": 80,
  "temperature": 0.8,
  "top_k": 30,
  "seed": 42,
  "left_checkpoint": "default",
  "right_checkpoint": "wide"
}
```

服务端会分别解析左右 selector，通过 `resolve_checkpoint_option` 找到真实 checkpoint，然后复用 `generator_for` 的缓存加载逻辑。左右生成都成功后返回：

```text
status
prompt
max_new_tokens
temperature
top_k
seed
left
right
comparison
```

其中 `left` 和 `right` 是带 `checkpoint_id` 的 `GenerationResponse`。`comparison` 记录：

```text
same_checkpoint
generated_equal
continuation_equal
left_generated_chars
right_generated_chars
generated_char_delta
left_continuation_chars
right_continuation_chars
continuation_char_delta
```

这些字段不判断“谁更好”，只描述两个输出是否相同以及长度差异。

## 请求日志

v41 给 pair generation 增加独立日志事件：

```text
endpoint=/api/generate-pair
status=ok / bad_request / error
left_checkpoint_id
right_checkpoint_id
requested_left_checkpoint
requested_right_checkpoint
prompt_chars
max_new_tokens
temperature
top_k
seed
left_generated_chars
right_generated_chars
generated_equal
continuation_equal
error
```

这和 v39/v40 的单次 `/api/generate` 日志保持同一个 `inference_requests.jsonl` 文件，但 endpoint 不同，后续可以区分普通生成和双 checkpoint 对照。

## Playground 前端

`playground.py` 新增 `Side-by-Side Generate` 区块：

```text
select#pairLeftCheckpointSelect
select#pairRightCheckpointSelect
button#pairGenerateButton
output#pairGenerateStatus
pre#pairLeftOutput
pre#pairRightOutput
```

页面加载 `/api/checkpoints` 后，会同时填充 live generate 下拉框和 pair 左右下拉框。默认左侧使用 default，右侧优先使用第二个可用 checkpoint；如果只有一个 checkpoint，左右都回退到 default。

点击 `Generate Pair` 后，前端发送：

```javascript
left_checkpoint: left.id
right_checkpoint: right.id
```

然后把 `data.left.generated` 和 `data.right.generated` 分别写进左右输出栏，并在状态里显示 `generated_equal` 和字符长度 delta。

## CLI 行为

`scripts/serve_playground.py` 启动时新增输出：

```text
generate_pair=http://127.0.0.1:8000/api/generate-pair
```

这让命令行截图能证明 v41 的 pair endpoint 已经暴露。`--checkpoint-candidate` 继续沿用 v39/v40 的候选 checkpoint 机制。

## 测试覆盖链路

`tests/test_server.py` 覆盖：

- `parse_generation_pair_request` 复用采样参数并解析左右 checkpoint。
- 缺少 `right_checkpoint` 会被拒绝。
- `/api/health` 暴露 `generate_pair_endpoint`。
- `/api/generate-pair` 能把 left 路由到 default，把 right 路由到 candidate。
- pair response 返回左右 `checkpoint_id` 和 comparison summary。
- `inference_requests.jsonl` 记录 `/api/generate-pair`、left/right checkpoint id 和 requested selector。

`tests/test_playground.py` 覆盖：

- HTML 包含左右 checkpoint selector。
- HTML 包含 `pairGenerateButton`。
- 脚本会请求 `/api/generate-pair`。
- payload 中包含 `left_checkpoint` 和 `right_checkpoint`。

这些测试保护的是从浏览器控件到 pair API，再到日志证据的完整路径。

## 归档和截图证据

本版运行证据放在：

```text
b/41/图片
b/41/解释/说明.md
```

关键截图包括：

```text
01-unit-tests.png
02-generate-pair-smoke.png
03-generate-pair-structure-check.png
04-playwright-generate-pair.png
05-docs-check.png
```

其中 `02` 证明 HTTP smoke 覆盖 pair endpoint、左右路由、comparison summary 和 bad request；`03` 证明结构检查覆盖 pair response、pair log 和前端控件；`04` 证明真实 Chrome 能打开 side-by-side generation 区块；`05` 证明 README、b/41 和讲解索引已经闭环。

## 一句话总结

v41 把 MiniGPT 的 playground 从“能选择和比较 checkpoint 元数据”推进到“能用同一个 prompt 同时调用两个 checkpoint，并把输出差异和请求证据记录下来”的阶段。
