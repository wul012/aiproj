# v171 server GET route split 代码讲解

## 本版目标

v171 的目标是把 `server.py` 中的 GET route dispatch 拆到 `server_routes.py`，让本地推理服务入口从“一个 handler 里同时放 GET 分发、POST 生成、streaming、pair generation、日志和响应 helper”继续向清晰边界收束。

它解决的问题是：`server.py` 在 v155-v164 之后已经陆续拆出了 logging、checkpoint payload、HTTP helper 和 request-history endpoint，但 `do_GET()` 仍然把 health、checkpoint selector、checkpoint compare、model-info、request-history、playground 和 run-file serving 混在主 handler 类里。GET 这部分是只读查询和静态产物服务，和 POST 生成链路的风险、状态和错误处理不同，适合成为独立 route dispatcher。

本版明确不做这些事：不改变 `/api/generate`、`/api/generate-stream`、`/api/generate-pair`、`/api/generate-pair-artifact`，不改变 generator cache，不改变 request logging schema，不改变 checkpoint discovery 语义，不改变 request-history JSON/CSV/detail 契约，也不改变旧的 `minigpt.server` facade 导出。

## 前置路线

这版接在服务入口拆分路线后面：

- v155 把 server request-log event 构造拆到 `server_logging.py`。
- v156 把 checkpoint discovery、health、model-info 和 checkpoint comparison payload 拆到 `server_checkpoints.py`。
- v159 把 JSON/text/SSE/file response helper 和 body parsing 拆到 `server_http.py`。
- v164 把 `/api/request-history` 和 `/api/request-history-detail` endpoint 处理拆到 `server_request_history.py`。

v171 是这条线的下一步：不继续拆 POST 生成主链路，而是把已经稳定的 GET 分发层拿出去。这样做的收益是清晰，但风险低，因为 GET 路由本身有现成的 HTTP 集成测试覆盖。

## 关键文件

- `src/minigpt/server_routes.py`：新增 GET route dispatcher，负责根据 request path 调用健康检查、checkpoint 列表、checkpoint comparison、request-history、model-info、playground 和 run-file serving。
- `src/minigpt/server.py`：`do_GET()` 改为调用 `handle_get_request()`，其余 POST、stream、pair generation、logging 和 helper method 保持在主 handler。
- `tests/test_server_routes.py`：新增 facade identity 测试，证明旧入口 `server.handle_get_request` 和新模块 `server_routes.handle_get_request` 是同一函数对象。
- `README.md`、`c/171/解释/说明.md`、`代码讲解记录_项目成熟度阶段/README.md`：记录版本能力、证据位置和讲解索引。

## 核心函数

`handle_get_request()` 是新模块的核心函数。它接收 handler 和服务创建时捕获的运行上下文：

- `handler`：HTTP handler 实例。函数只调用它已有的 `_send_json()`、`_send_file()`、`_serve_run_file()` 等方法，不自己写 socket。
- `request_path`：原始请求路径，用 `urlparse()` 拆出 path 和 query。
- `root`：当前 run 目录。
- `checkpoint`：默认 checkpoint 路径。
- `tokenizer_path`：默认 tokenizer 路径。
- `safety`：`InferenceSafetyProfile`，用于 health payload 展示当前安全限制。
- `request_log`：request-history JSONL 路径。
- `checkpoint_candidates`：候选 checkpoint 路径列表。
- `checkpoint_options`：`discover_checkpoint_options()` 预先解析出的 checkpoint 选择项。

这个函数本身不持有全局状态。所有状态都由 `create_handler()` 在创建 handler 类时注入，和旧版 `do_GET()` 使用的闭包变量一致。

## GET 路由流程

新流程和旧流程一一对应：

1. `/api/health` 调用 `build_health_payload()`，返回 run 目录、checkpoint、playground、sample lab、request log、endpoint 和 safety 信息。
2. `/api/checkpoints` 调用 `build_checkpoints_payload()`，返回默认 checkpoint 和候选 checkpoint 列表。
3. `/api/checkpoint-compare` 调用 `build_checkpoint_compare_payload()`，返回 checkpoint metadata 和相对 baseline 的差异。
4. `/api/request-history` 委托 `handle_request_history_endpoint()`，保留 limit/filter/CSV export 行为。
5. `/api/request-history-detail` 委托 `handle_request_history_detail_endpoint()`，保留 log_index 查询和错误映射。
6. `/api/model-info` 读取 query 中的 checkpoint selector，通过 `resolve_checkpoint_option()` 定位 checkpoint，再调用 `build_model_info_payload()`。
7. `/` 和 `/playground.html` 确保 `playground.html` 存在，不存在时调用 `write_playground()` 生成，然后用 `_send_file()` 返回。
8. 其他 GET path 交给 `_serve_run_file()`，继续使用 `server_http.py` 的路径逃逸保护和文件读取逻辑。

这说明 `server_routes.py` 是 route dispatch 层，不是新业务层。它只把请求转发到既有 contract、request-history、playground 和 HTTP helper 链路。

## server.py 的变化

`server.py` 的 `do_GET()` 从一段多分支逻辑变成一次 `handle_get_request()` 调用，并把原有闭包变量显式传入。

这样做有两个好处：

- handler 类里更清楚地区分 GET 查询入口和 POST 生成入口。
- 将来如果继续拆 route dispatch，可以围绕 `server_routes.py` 做单独测试，而不是每次都在 `server.py` 里加分支。

本版没有删除 `server.py` 里的旧 facade imports。原因是项目已经有 `tests/test_server_contracts.py`、`tests/test_server_checkpoints.py` 等测试保护旧导出，隐藏调用方也可能继续从 `minigpt.server` 导入 contract helper。v171 的策略是“实现移走，入口保留”。

## 测试覆盖

本版测试分三层：

- 定向服务测试：`python -B -m unittest tests.test_server_routes tests.test_server tests.test_server_request_history tests.test_server_contracts tests.test_server_checkpoints tests.test_server_http tests.test_server_logging tests.test_server_generator -v`。这组测试覆盖 GET endpoint、POST generation、request-history、checkpoint payload、HTTP helper、logging 和 generator facade。
- 全量测试：`python -B -m unittest discover -s tests -v`，确认 393 个测试通过，避免 route split 影响 release、registry、maturity、training-scale 等链路。
- 卫生检查：`check_source_encoding.py` 确认无 BOM、无 syntax error、Python 3.11 compatibility 干净；`check_maintenance_batching.py` 确认 module pressure 为 `pass`。

新增的 `tests/test_server_routes.py` 不复制 HTTP 行为测试，而是验证 facade identity：`server.handle_get_request is server_routes.handle_get_request`。HTTP 行为由 `tests/test_server.py` 中真实启动 `ThreadingHTTPServer` 的测试继续覆盖。

## 运行证据

v171 的运行截图归档在 `c/171`：

- `01-server-route-tests.png`：服务路由相关测试通过。
- `02-server-route-smoke.png`：旧 server facade 和新 route module 函数对象一致，并记录 `server.py` 491 行、`server_routes.py` 83 行。
- `03-maintenance-smoke.png`：维护批次检查仍提示节奏需要控制，但 module pressure 为 `pass`，本版属于服务入口收束而非 report-only 碎片化。
- `04-source-encoding-smoke.png`：源码编码和语法卫生通过。
- `05-full-unittest.png`：全量 393 个测试通过。
- `06-docs-check.png`：README、归档、代码讲解索引、源码和测试关键词一致。

这些截图是版本证据，不是临时日志。临时 `tmp_v171_*` 日志和 `runs/*v171` 检查输出会在提交前按 cleanup gate 清理。

## 边界说明

`server_routes.py` 不负责生成文本，不读写 request log，不构造 generation response，也不处理 SSE stream。它只处理 GET 分发，并复用已有 helper：

- contract payload 来自 `server_contracts.py` 和 `server_checkpoints.py`。
- request-history endpoint 来自 `server_request_history.py`。
- playground HTML 生成来自 `playground.py`。
- 文件返回和路径安全由 `server_http.py` 通过 handler method 间接执行。

因此 v171 不是新增推理能力，而是降低本地推理服务入口的职责密度，让后续服务化功能更容易定位和测试。

## 一句话总结

v171 把本地推理服务的 GET route dispatch 独立成 `server_routes.py`，让 `server.py` 从 519 行降到 491 行，同时保持 GET 语义、POST 推理链路、request-history 契约和旧 facade 导出全部不变。
