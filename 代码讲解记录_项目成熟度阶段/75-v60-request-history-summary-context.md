# 第六十版代码讲解：request history summary context

## 本版目标、来源和边界

v57 让本地推理请求历史可见，v58 让它可筛选和 CSV 导出，v59 让表格里的每一行都能回到 raw/normalized JSON。到这里，请求历史已经能回答“单条请求发生了什么”。v60 继续往上一层收口，回答“最近这一批本地推理请求整体稳不稳”。

本版目标是新增 request history summary：读取 `inference_requests.jsonl`，聚合状态计数、端点计数、checkpoint 计数、timeout/bad_request/error rate、stream/pair/artifact 数量、最近请求和建议，然后输出 JSON/CSV/Markdown/HTML。同时让 `build_maturity_summary.py` 可以读取这份 `request_history_summary.json`，把本地推理稳定性带入项目成熟度上下文。

本版不做实时监控、不做数据库、不改变 playground 交互，也不把 request history summary 直接变成 release gate 硬规则。它只生成只读证据产物，并让成熟度报告能看见这份证据。

## 所在路线

```text
inference_requests.jsonl
 -> /api/request-history
 -> /api/request-history-detail?log_index=N
 -> request_history_summary.json/csv/md/html
 -> maturity_summary.request_history_context
```

这条路线把“本地推理服务化”从体验层推到证据层：不是只证明浏览器能请求模型，而是能复查最近请求中是否有 timeout、bad_request、error、坏 JSON 行，以及哪些 endpoint/checkpoint 被使用。

## 关键文件

- `src/minigpt/server.py`：新增 `read_request_history_log_records`，把 v59 的 JSONL 解析和 `log_index` 归一化开放给 summary 模块复用。
- `src/minigpt/request_history_summary.py`：新增 summary builder、JSON/CSV/Markdown/HTML writer、HTML renderer、建议生成逻辑。
- `scripts/summarize_request_history.py`：新增 CLI，默认输入 `runs/minigpt/inference_requests.jsonl`，默认输出 `runs/request-history-summary`。
- `src/minigpt/maturity.py`：新增 `request_history_summary_path` 参数、`request_history_context`、Markdown/HTML Request History Context 区块，并把 v55-v60 纳入 local inference 能力线。
- `scripts/build_maturity_summary.py`：新增 `--request-history-summary` 参数和 CLI 输出字段。
- `tests/test_request_history_summary.py`：覆盖 summary 指标、输出文件、HTML escaping。
- `tests/test_maturity.py`：覆盖成熟度报告读取 request history summary，并确认 local inference 能力线覆盖 v60。

## 核心数据结构

request history summary 的主 payload 是：

```json
{
  "schema_version": 1,
  "title": "MiniGPT request history summary",
  "generated_at": "2026-05-13T00:00:00Z",
  "request_log": "runs/minigpt/inference_requests.jsonl",
  "summary": {
    "status": "warn",
    "total_log_records": 3,
    "invalid_record_count": 1,
    "ok_count": 2,
    "timeout_count": 1,
    "bad_request_count": 0,
    "error_count": 0,
    "timeout_rate": 0.3333,
    "bad_request_rate": 0.0,
    "error_rate": 0.0,
    "stream_request_count": 1,
    "pair_request_count": 1,
    "artifact_request_count": 1,
    "unique_checkpoint_count": 2,
    "latest_timestamp": "..."
  },
  "status_counts": {},
  "endpoint_counts": {},
  "checkpoint_counts": {},
  "recent_requests": [],
  "recommendations": []
}
```

`summary.status` 的规则是轻量启发式：

- `empty`：没有有效请求记录。
- `review`：存在 `error` 或 `bad_request`。
- `warn`：存在无效 JSONL 行。
- `watch`：存在 timeout 或 cancelled。
- `pass`：有效记录中没有上述问题。

这个状态不是发布判定，只是本地推理会话稳定性的阅读入口。

## 运行流程

`summarize_request_history.py` 的默认路径是：

```text
runs/minigpt/inference_requests.jsonl
 -> build_request_history_summary(...)
 -> write_request_history_summary_outputs(...)
 -> runs/request-history-summary/request_history_summary.json
 -> request_history_summary.csv
 -> request_history_summary.md
 -> request_history_summary.html
```

内部读取不重新实现 JSONL 解析，而是复用 `server.read_request_history_log_records`。这样 request history table、detail API 和 summary 报告对有效记录、坏行计数、`log_index` 的理解保持一致。

## 成熟度集成

`build_maturity_summary` 新增：

```text
request_history_summary_path: str | Path | None
```

如果用户显式传入 `--request-history-summary`，就读取该文件；否则默认尝试读取：

```text
runs/request-history-summary/request_history_summary.json
```

成熟度 summary 会新增：

- `summary.request_history_status`
- `summary.request_history_records`
- `summary.request_history_timeout_rate`
- `summary.request_history_error_rate`
- `request_history_context`

Markdown 和 HTML 都会渲染 `Request History Context` 区块。这样 v48 以来的成熟度总览不再只看 registry 和版本证据，也能看到最近本地推理会话是否稳定。

## 输出产物的角色

- `request_history_summary.json`：机器可读主证据，后续 maturity/audit/release gate 都应优先消费它。
- `request_history_summary.csv`：单行指标导出，适合表格、横向比较或脚本读取。
- `request_history_summary.md`：人读摘要，适合复制到报告或讲解文档。
- `request_history_summary.html`：浏览器证据，适合截图和展示。

这些文件是最终证据产物，不是临时日志。v60 的 smoke 产物在 `tmp/v60-smoke` 中生成，完成后按 cleanup gate 删除；归档只保留截图和说明。

## 测试覆盖

`tests/test_request_history_summary.py` 保护这些判断：

- `ok`、`timeout`、`bad_request` 和坏 JSON 行会被正确计数。
- `timeout_rate`、`bad_request_rate` 按有效记录总数计算。
- pair artifact 请求会计入 pair 和 artifact 数量。
- checkpoint 计数能同时覆盖普通请求和 pair 左右 checkpoint。
- 输出 JSON/CSV/Markdown/HTML 文件都存在。
- HTML 对标题、endpoint、checkpoint 等文本做转义。

`tests/test_maturity.py` 保护这些判断：

- maturity summary 能自动读取默认 request history summary。
- `request_history_status`、`request_history_records`、`request_history_context.timeout_rate` 能进入结果。
- Markdown/HTML 都包含 Request History Context。
- local inference capability 的 covered versions 包含 v60，target level 升到 5。

全量 `python -m unittest discover -s tests` 和 `python -m compileall src tests scripts` 用于保证新增 summary 链路没有破坏既有模型、评估、registry、release、playground 代码。

## 和前后版本的关系

v59 的单条详情适合排查“这一行为什么 timeout 或 bad_request”。v60 的摘要适合先判断“这一批请求里 timeout/bad_request/error 多不多”。二者合起来形成了两层复查路径：

```text
先看 summary 判断整体稳定性
 -> 再按 log_index 打开 detail 追具体问题
```

后续如果继续沿这条线推进，比较合理的是把 request history summary 中的 `review/warn/watch` 状态接入 project audit 或 release gate profile，但这需要先明确“本地服务稳定性”是否要成为发布条件。

## 一句话总结

v60 把 Request History 从单条排错入口推进为可进入项目成熟度报告的本地推理稳定性摘要。
