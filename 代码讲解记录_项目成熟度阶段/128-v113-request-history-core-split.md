# 第一百一十三版代码讲解：Request History Core Split

## 本版目标

v113 的目标是继续落实 v110 的 `module pressure audit`，把 `server.py` 中已经稳定成形的 request-history 核心逻辑抽成独立模块 `request_history.py`。
这版不是新增一个展示页面，也不是继续拆一个很小的 utility 版本，而是把同一责任域里的 JSONL 写入、读取、过滤、详情查询、查询参数解析和 CSV 导出一次性收拢，回应“utils migration 不要每迁一个模块发一版”的节奏问题。

本版明确不做：
- 不修改 `/api/request-history` 或 `/api/request-history-detail` 的请求和响应契约。
- 不修改 playground 的请求历史 UI。
- 不修改推理、流式生成、pair generation 或 checkpoint selector。
- 不重写 `server.py` handler 主流程。
- 不回改已经发布的 v84-v107 git 历史。

## 路线来源

本版来自 v109-v112 的维护收口路线：

```text
v109 maintenance batching policy
 -> prevent tiny low-risk utility migrations from fragmenting future versions
 -> v110 module pressure audit identifies server.py as a critical large module
 -> v111 registry asset split handles display assets
 -> v112 pair artifact split handles saved pair evidence
 -> v113 request history core split handles local inference log evidence
```

request-history 适合这一版拆分，因为它已经有清晰的输入输出边界：
- 输入是本地 `inference_requests.jsonl`。
- 输出是 normalized request rows、summary payload、detail payload 和 CSV。
- HTTP handler 只需要调用这些函数并选择 JSON 或 CSV 响应。
- `request_history_summary.py` 也消费同一份 normalized rows，可以直接依赖新模块。

## 关键文件

- `src/minigpt/request_history.py`
  - 新增模块。
  - 承接 request-history 的核心数据处理：append JSONL、读取 JSONL、过滤、详情查询、CSV 导出、query string 解析。
- `src/minigpt/server.py`
  - 删除原先内嵌的 request-history helper。
  - 通过导入新模块保留原 public 函数名和 HTTP 行为。
  - 继续负责路由、HTTP 状态码、JSON/CSV 响应和推理日志写入调用。
- `src/minigpt/request_history_summary.py`
  - 从直接依赖 `server.py` 改为依赖 `request_history.py`。
  - 让 summary 层不再为了读 request log 反向耦合 HTTP server。
- `tests/test_request_history.py`
  - 新增模块级测试。
  - 直接锁住 request-history 核心契约，避免以后只通过 server 测试间接覆盖。
- `tests/test_server.py`
  - 原有 HTTP/request-history 回归继续作为 API 层保护。
- `tests/test_request_history_summary.py`
  - 继续证明 summary 层在解耦后能消费同一 normalized records。
- `README.md`、`c/113`、本讲解文件
  - 说明本版为什么属于收口型质量优化，并保存运行证据。

## 核心数据结构

request-history 的基础记录仍然来自 JSONL，每一行是一次本地推理请求事件：

```json
{
  "timestamp": "2026-05-15T01:02:03Z",
  "endpoint": "/api/generate-stream",
  "status": "timeout",
  "checkpoint_id": "candidate",
  "prompt_chars": 3,
  "stream_chunks": 2,
  "stream_timed_out": true
}
```

`request_history.py` 会把它规范化为 request-history row：

```json
{
  "log_index": 3,
  "timestamp": "2026-05-15T01:02:03Z",
  "endpoint": "/api/generate-stream",
  "status": "timeout",
  "checkpoint_id": "candidate",
  "prompt_chars": 3,
  "stream_chunks": 2,
  "stream_timed_out": true
}
```

`log_index` 是原 JSONL 文件里的真实行号，不是过滤后的序号。这样 `/api/request-history-detail?log_index=N` 可以稳定回到原始记录，即使中间有坏 JSON 行也不会错位。

## 核心函数

`append_inference_log(path, event)`

负责写入 JSONL。它会创建父目录，并追加：

```text
{"timestamp": "...", ...event}
```

它是 server 记录 `/api/generate`、`/api/generate-stream`、`/api/generate-pair` 和 `/api/generate-pair-artifact` 的底层入口。

`read_inference_log_entries(path)`

读取原始 JSONL，并返回：

```text
[(log_index, record), ...], invalid_count
```

空行会跳过；坏 JSON 或非 dict JSON 会计入 `invalid_count`。这保证坏日志不会让本地 playground 或 release evidence 崩掉。

`read_request_history_log_records(path)`

把原始 entries 转成 normalized rows，并保留 `log_index`。这是 summary、API payload 和测试共同消费的核心读取入口。

`build_request_history_payload(path, limit, status_filter, endpoint_filter, checkpoint_filter)`

生成 `/api/request-history` 的响应主体：

```json
{
  "status": "ok",
  "request_log_exists": true,
  "limit": 20,
  "newest_first": true,
  "total_log_records": 3,
  "matching_log_records": 2,
  "invalid_record_count": 1,
  "summary": {
    "timeout_count": 1,
    "returned_status_counts": {"timeout": 1, "ok": 1}
  },
  "requests": []
}
```

它负责 newest-first、limit、状态计数、endpoint 计数和筛选摘要。

`build_request_history_detail_payload(path, log_index)`

生成 `/api/request-history-detail` 的响应。它同时返回：
- `normalized`: 去掉大段生成文本后的可展示字段。
- `record`: 原始 JSONL 记录，用于排查请求细节。

如果 `log_index` 小于 1 会抛 `ValueError`；如果行号不存在或对应坏 JSON 会抛 `LookupError`。

`request_history_to_csv(records)`

把当前筛选后的 rows 导出 CSV。布尔值固定输出 `true` / `false`，空值输出空字符串，以保持 v58 以来的导出契约。

`request_history_filters_from_query(query)`

解析 HTTP query：

```text
status=ok&endpoint=/api/generate&checkpoint=candidate
```

并返回：

```python
{
    "status_filter": "ok",
    "endpoint_filter": "/api/generate",
    "checkpoint_filter": "candidate",
}
```

`checkpoint=all`、`checkpoint=*` 或空字符串会被清洗为 `None`。

## 运行流程

HTTP 侧流程保持不变：

```text
/api/request-history
 -> _request_history_limit_from_query()
 -> _request_history_filters_from_query()
 -> build_request_history_payload()
 -> optional request_history_to_csv()
 -> send JSON or CSV

/api/request-history-detail
 -> _request_history_log_index_from_query()
 -> build_request_history_detail_payload()
 -> send JSON or 404
```

变化只在内部依赖方向：

```text
before:
request_history_summary.py -> server.py -> request-history helpers

after:
server.py                  -> request_history.py
request_history_summary.py -> request_history.py
```

这让 `server.py` 更接近 HTTP orchestration，而不是同时承担日志解析库的职责。

## 为什么这是轻量质量优化

v113 没有把 `server.py` 主流程拆成多个 handler，也没有改 URL、状态码、生成逻辑或 playground 交互。它只抽离一个已经稳定的边界。

收益是：
- `server.py` 从约 1571 行降到约 1279 行。
- request-history 核心可以用纯单元测试验证，不需要每次启动 HTTP server。
- summary 层不再依赖 server 模块。
- 后续如果要增强 request-history，例如增加字段白名单、日志轮转、导出格式或 audit 规则，有了明确落点。

风险控制是：
- 原 public 函数名仍由 `server.py` 导出，旧测试和外部脚本不用改。
- 原 HTTP 回归测试继续覆盖 request-history API。
- 新增 `tests/test_request_history.py` 锁住模块自身行为。

## 测试覆盖

`tests/test_request_history.py` 覆盖：
- JSONL 写入带 timestamp。
- 坏 JSON 和非 dict JSON 计入 invalid count。
- newest-first 返回最近记录。
- status、endpoint、checkpoint 过滤。
- pair record 中的 left/right checkpoint 也能被 checkpoint filter 命中。
- detail payload 返回 normalized 和 raw record。
- query 参数解析、limit/log_index 错误处理。
- CSV 中布尔值输出为 `true` / `false`。
- raw log reader 返回未规范化记录。

`tests/test_server.py` 继续覆盖：
- `/api/request-history` JSON 和 CSV。
- `/api/request-history-detail` 成功、缺参数和 not found。
- generate/stream/pair 请求写入 request log。

`tests/test_request_history_summary.py` 继续覆盖：
- summary 从同一 JSONL 读取 normalized records。
- HTML/Markdown/CSV/JSON summary 仍然可生成。

## 证据闭环

v113 证据放在 `c/113`：
- `01-unit-tests.png`: request-history core、server、summary、compileall 和全量 unittest。
- `02-request-history-smoke.png`: server 行数下降、request-history payload/detail/CSV smoke。
- `03-request-history-structure-check.png`: 新模块、server 导入、summary 依赖、测试、文档和归档结构对齐。
- `04-request-history-output-check.png`: JSONL、payload、detail、CSV、raw reader 输出检查。
- `05-playwright-request-history-summary-html.png`: request-history summary HTML 在真实 Chrome 中渲染。
- `06-docs-check.png`: README、c/113、代码讲解和索引检查。

这些证据是最终归档，不是临时日志；临时 `tmp/`、测试缓存和 `__pycache__` 在完成前会清理。

## 一句话总结

v113 把 request-history 从 `server.py` 的厚模块中抽成独立核心模块，让本地推理日志证据链更可测、更可复用，同时保持 HTTP API 和 playground 行为不变。
