# 第五十九版代码讲解：request history detail JSON

## 本版目标、来源和边界

v58 已经把 `inference_requests.jsonl` 变成可筛选、可 CSV 导出的 Request History。它解决了“能不能从很多本地推理请求里筛出关注对象并导出”的问题，但仍然缺少一层追溯能力：当表格里某一行看起来异常时，用户还需要手动打开 JSONL 文件，数行、复制、比对字段，才能看到原始日志。

v59 的目标是给请求历史补上“单条记录可追溯”闭环：每条有效 JSONL 记录在读取时获得可见 `log_index`，服务端新增 `/api/request-history-detail?log_index=N`，返回这一行的 normalized 视图和 raw 原始 JSON；playground 的 Request History 表格新增 `Log` 列、`Details` 按钮和 `JSON` 链接。

本版不做数据库索引、不做全文搜索、不改变日志写入格式、不把无效 JSON 行包装成详情记录，也不做远程权限控制。它仍然是本地学习项目里的 lightweight 追溯能力，核心边界是：只读现有 `inference_requests.jsonl`，通过行号定位有效记录。

## 所在路线

```text
v55 streaming generation
 -> v56 timeout/cancel logging
 -> v57 request history list
 -> v58 filters + CSV export
 -> v59 per-row detail JSON
```

这条线的重点不是提升模型参数规模，而是把本地推理体验从“能跑一次生成”推进到“生成过程、异常状态、请求参数和结果证据都能被复查”。v59 把列表视图和原始日志重新接了起来，让表格里的每一行都能回到 JSONL 中的确定位置。

## 关键文件

- `src/minigpt/server.py`：新增 `log_index` 读取链路、`build_request_history_detail_payload`、`/api/request-history-detail` 路由，以及 CSV 的 `log_index` 列。
- `src/minigpt/playground.py`：Request History 表格新增 `Log` 列、行级 `Details` 按钮、行级 `JSON` 链接和详情输出面板。
- `tests/test_server.py`：覆盖行号保留、详情 payload、HTTP 详情接口、400/404 错误、CSV header。
- `tests/test_playground.py`：覆盖详情面板、详情 URL、详情函数、`log_index` 和 per-row JSON 下载链接写入 HTML。
- `README.md`、`b/README.md`、`b/59/解释/说明.md`：同步本版能力、截图和证据索引。

## 核心数据结构

v59 仍然不改变日志文件本身。日志还是一行一个 JSON object，例如：

```json
{"timestamp":"2026-05-13T14:41:38Z","endpoint":"/api/generate-pair","status":"ok","left_checkpoint_id":"default","right_checkpoint_id":"wide"}
```

新增的 `log_index` 是读取时生成的行号，不写回日志文件。它来自 `_read_inference_log_entries(path)`：

```text
physical JSONL line number
 -> valid dict record
 -> (log_index, record)
```

这里的 `log_index` 使用 1-based 物理行号。好处是用户看到 `log_index=4` 时，可以直接理解为 JSONL 文件第 4 行；即使第 2 行是坏 JSON，后面的有效行也不会被重新编号，排错时不会和文件内容错位。

详情 payload 的核心结构是：

```json
{
  "status": "ok",
  "request_log": ".../inference_requests.jsonl",
  "request_log_exists": true,
  "log_index": 4,
  "total_log_records": 3,
  "invalid_record_count": 1,
  "normalized": {"log_index": 4, "endpoint": "/api/generate-pair", "status": "ok"},
  "record": {"timestamp": "...", "endpoint": "/api/generate-pair", "status": "ok"}
}
```

`normalized` 是 UI 和 CSV 关心的稳定字段视图；`record` 是原始 JSON object，用于保留未来字段、错误字段和 pair artifact 字段等完整证据。

## 服务端运行流程

`build_request_history_payload` 从 v58 的“读取 records”改成“读取 entries”：

```text
_read_inference_log_entries(log_path)
 -> [(line_number, raw_record), ...] + invalid_count
 -> _request_history_record(raw_record, log_index=line_number)
 -> _filter_request_history_records(...)
 -> newest-first limit
```

这样列表 payload 的每条 `requests[]` 都带 `log_index`。CSV 也把 `log_index` 放在第一列，确保导出的表格能回到 JSONL 文件。

详情 API 走另一条更短的链路：

```text
GET /api/request-history-detail?log_index=4
 -> _request_history_log_index_from_query(...)
 -> build_request_history_detail_payload(log_path, 4)
 -> scan entries
 -> return normalized + raw record
```

如果 `log_index` 缺失或小于 1，服务端返回 400；如果它指向空行、坏 JSON 行或不存在的行，服务端返回 404。这个区别很重要：400 表示请求参数不合法，404 表示参数格式合法但没有对应的有效日志记录。

## Playground 流程

Request History 表格新增第一列 `Log`。每行的动作区包含两个入口：

- `Details`：调用 `showRequestHistoryDetail(logIndex)`，通过 `fetch('/api/request-history-detail?log_index=N')` 读取详情，然后把完整 JSON pretty-print 到 `requestHistoryDetailOutput`。
- `JSON`：直接链接到同一个详情端点，并设置 `download="request_history_N.json"`，方便把单条记录作为独立证据保存。

UI 中保留 v58 的筛选和 CSV 导出逻辑。也就是说，筛选控制的是列表和整体 CSV；行级 Details/JSON 控制的是某一条记录。两者不会互相覆盖。

## 输出和证据

本版的主要输出不是新的模型 artifact，而是本地推理请求历史的可追溯接口：

- `/api/request-history`：列表仍然是 UI 主数据源，现在每行带 `log_index`。
- `/api/request-history-detail?log_index=N`：单条详情 JSON，是本版新增的排错与证据接口。
- CSV：继续由 `request_history_to_csv` 生成，现在第一列是 `log_index`。
- Playground：详情面板是浏览器可见证据，证明用户可以从列表进入单条 raw/normalized JSON。

`b/59/图片/05-playwright-request-history-detail-open.png` 是最关键截图：它展示真实浏览器里第一行 request 被打开后，页面出现 `Request #4`，并显示 `normalized` 与 `record` 两层 JSON。

## 测试覆盖

`tests/test_server.py` 的新增断言保护这些行为：

- 列表 payload 中最近记录的 `log_index` 保留物理行号，而不是压缩后的序号。
- 坏 JSON 行计入 `invalid_record_count`，但不会成为可读取详情。
- `build_request_history_detail_payload` 返回 `normalized` 和 `record`。
- `log_index=0` 抛出参数错误，指向坏行的 `log_index=2` 抛出 not found。
- HTTP `/api/request-history-detail?log_index=1` 可返回 raw request，缺失参数返回 400，不存在记录返回 404。
- CSV header 以 `log_index` 开头。

`tests/test_playground.py` 的断言保护这些行为：

- HTML 包含 `/api/request-history-detail`。
- 页面包含 `showRequestHistoryDetail`、`requestHistoryDetailUrl`、`requestHistoryDetailPanel` 和 `requestHistoryDetailOutput`。
- 页面包含 `log_index` 和 `request_history_${logIndex}.json`，说明行级 JSON 下载入口被写入。

全量 `python -m unittest discover -s tests` 和 `python -m compileall src tests scripts` 用作回归证据，说明本版没有破坏训练、评估、registry、release gate、playground server 等既有链路。

## 和前后版本的关系

v57 解决“能看见最近请求”；v58 解决“能筛选并导出一组请求”；v59 解决“能追溯其中一条请求的原始 JSON”。这三版合在一起，让本地推理日志具备了列表、筛选、批量导出和单条详情四种基本复查动作。

后续如果继续沿这条线推进，更合理的方向不是再拆更多小按钮，而是把 request history 的统计结果接入 project audit 或 maturity summary，例如统计最近请求的 timeout rate、bad request rate、checkpoint 使用分布和 pair artifact 产出情况。

## 一句话总结

v59 把 Request History 从“可筛选导出的列表”推进到“每一行都能回到原始 JSONL 证据”的本地推理追溯入口。
