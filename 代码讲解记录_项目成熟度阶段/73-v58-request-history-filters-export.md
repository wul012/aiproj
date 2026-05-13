# 第五十八版代码讲解：request history filters and CSV export

## 本版目标、来源和边界

v57 已经把 `inference_requests.jsonl` 变成 `/api/request-history` 和 playground Request History 表格。它解决了“能不能不用手动打开 JSONL 也能看到最近推理请求”的问题，但还停留在浏览最近若干条记录：如果日志里同时有普通生成、流式生成、pair 请求、超时和错误，用户还需要肉眼扫表格。

v58 的目标是给这条本地请求历史链路补筛选和导出：服务端支持 `status`、`endpoint`、`checkpoint` 三种查询过滤，并支持 `format=csv`；playground 增加对应控件和 Export CSV 链接，让当前筛选结果可以直接交给后续分析或表格软件。

本版不做全文搜索、不做分页、不做数据库索引、不做权限控制，也不做单条请求详情页。它仍然只读本地 JSONL，但让“最近请求视图”变成一个更实用的复查入口。

## 所在链路

```text
inference_requests.jsonl
 -> build_request_history_payload(status/endpoint/checkpoint)
 -> requests + matching_log_records + filters
 -> request_history_to_csv(...)
 -> GET /api/request-history?status=ok&checkpoint=wide&format=csv
 -> playground filters + Export CSV
```

这条链路回答的问题是：当本地推理日志变多后，能不能只看我关心的状态、端点或 checkpoint，并把这部分记录导出。

## 关键文件

- `src/minigpt/server.py`：新增 `REQUEST_HISTORY_CSV_COLUMNS`、过滤参数、过滤函数、CSV 转换函数和 `_send_text`。
- `src/minigpt/playground.py`：新增筛选控件、query 构造、Export CSV 链接、匹配数量展示和服务端错误信息展示。
- `tests/test_server.py`：新增过滤和 CSV 测试，验证 checkpoint 过滤能匹配 pair 请求右侧 checkpoint。
- `tests/test_playground.py`：验证生成 HTML 包含筛选控件、导出链接和 JS 函数。
- `b/58/图片` 与 `b/58/解释/说明.md`：保存测试、smoke、结构检查、Playwright 页面和文档检查证据。

## 服务端核心数据结构

`build_request_history_payload` 新增三个可选参数：

- `status_filter`
- `endpoint_filter`
- `checkpoint_filter`

返回 payload 新增：

- `matching_log_records`：过滤后匹配的总记录数，不受 limit 影响。
- `filters`：回显本次实际使用的过滤条件。
- `summary.matching_records`：和 `matching_log_records` 一致，方便 UI 统一从 summary 读取。

这和 `record_count` 的含义不同：`record_count` 是返回给前端的数量，会受 limit 截断；`matching_log_records` 是过滤后总匹配数，用来告诉用户“当前筛选一共命中多少条”。

## 过滤规则

过滤发生在归一化之后，而不是直接操作原始 JSONL。流程是：

```text
raw json lines
 -> _request_history_record(...)
 -> _filter_request_history_records(...)
 -> newest-first limit
```

`status` 和 `endpoint` 是大小写不敏感的精确匹配。`checkpoint` 会匹配这些字段：

- `checkpoint_id`
- `requested_checkpoint`
- `left_checkpoint_id`
- `right_checkpoint_id`
- `requested_left_checkpoint`
- `requested_right_checkpoint`

这样 pair 请求中只要左侧或右侧命中了目标 checkpoint，也会被返回。这一点很重要，因为 pair 请求没有单一的 `checkpoint_id`。

## CSV 输出

`format=csv` 不改变过滤逻辑。服务端先构造正常 JSON payload，再把 `payload["requests"]` 转为 CSV：

```text
GET /api/request-history?status=ok&checkpoint=wide&format=csv
```

CSV 使用固定列 `REQUEST_HISTORY_CSV_COLUMNS`，包括时间、端点、状态、checkpoint、请求参数、输出字符数、pair 比较字段、流式字段、artifact 路径和 error。固定列的好处是：即使某些记录没有某个字段，导出的表头也稳定，后续表格或脚本不用猜列。

布尔值导出为 `true` / `false`，空值导出为空字符串。响应头使用：

```text
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="request_history.csv"
```

这说明 CSV 是正式导出产物，不是调试文本。

## Playground 运行流程

Request History 区块新增四个控件：

- Status 下拉：`all`、`ok`、`timeout`、`cancelled`、`bad_request`、`error`。
- Endpoint 下拉：普通生成、流式生成、pair 生成、pair artifact。
- Checkpoint 输入框：手动输入 `default`、`wide` 等 checkpoint id。
- Limit 数字输入：1 到 200。

`requestHistoryQuery(format)` 会读取控件状态，拼出 `/api/request-history?...`。没有值的过滤条件不会进入 query。Export CSV 链接复用同一组控件，只是额外带上 `format=csv`。

刷新成功后，状态栏显示：

```text
N shown / M matched / T recorded
```

这三个数分别表示当前返回数量、当前过滤命中总数、日志总记录数。用户可以知道自己看到的是全部记录，还是被 limit 截断后的前几条。

## 输出和证据

`/api/request-history` 的 JSON 输出仍然是 UI 主数据源；`format=csv` 是当前筛选结果的导出视图。两者共用过滤逻辑，所以不会出现 UI 看到一组记录、CSV 导出另一组记录的分裂。

`b/58/图片/02-request-history-filter-smoke.png` 证明 HTTP smoke 真正写入了三类记录，并按 `status=ok`、`endpoint=/api/generate-pair`、`checkpoint=wide` 命中一条 pair 请求。`04-playwright-request-history-filters.png` 证明筛选控件和 Export CSV 在真实浏览器中可见。

## 测试覆盖

`tests/test_server.py` 重点保护：

- `matching_log_records` 和 `record_count` 的区别。
- `filters` 回显。
- `checkpoint_filter` 能匹配 pair 请求的 right checkpoint。
- CSV header 稳定。
- 布尔字段导出为 `false`。
- HTTP `format=csv` 返回 `text/csv`。

`tests/test_playground.py` 重点保护：

- status/endpoint/checkpoint/limit 控件存在。
- Export CSV 链接存在。
- `requestHistoryQuery` 和 `updateRequestHistoryExportLink` 写入 HTML。
- UI 使用 `matching_records` 展示匹配数量。

全量 `python -m unittest discover -s tests` 和 `python -m compileall src tests scripts` 作为回归证据，说明新增过滤/导出没有破坏原有 MiniGPT 教学链路。

## 和前面版本的关系

v57 是“能看见请求历史”。v58 是“能从请求历史里筛出关注对象，并导出这部分证据”。这仍然不是完整监控平台，但已经让本地 playground 的请求历史具备了基本复查工作流：过滤、查看、导出。

后续如果继续沿这条线走，最自然的是做单条请求详情抽屉、JSON 导出、或把 request history 的统计纳入 project audit。

## 一句话总结

v58 把 Request History 从静态最近记录表推进到可筛选、可导出的本地推理证据入口。
