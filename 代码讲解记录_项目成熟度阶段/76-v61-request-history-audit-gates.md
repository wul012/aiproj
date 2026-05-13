# 第六十一版代码讲解：request history audit gates

## 本版目标、来源和边界

v60 已经把 `inference_requests.jsonl` 聚合成 `request_history_summary.json`，并让 maturity summary 能读取这份上下文。但到 v60 为止，请求历史稳定性仍然更像“可读报告”：它能说明最近本地推理有没有 timeout、bad_request、error，却还没有进入 project audit、release bundle 和 release gate policy。

v61 的目标是把这份 summary 变成发布治理链路中的正式证据：project audit 要能检查它，release bundle 要能携带它，release gate 要能要求它。这样本地 playground 的请求历史不再只是演示痕迹，而是能参与“这个版本是否适合交付/展示”的判断。

本版不做三件事：不重新设计 request history JSONL 格式，不扩展 playground UI，不把所有 timeout 都判为失败。v61 的边界是治理接入：把已有 summary 读入审计和门禁，而不是改变模型推理本身。

## 路线位置

这版来自 v57-v60 的本地推理可追溯路线：

- v57：请求历史列表。
- v58：请求历史过滤和 CSV 导出。
- v59：单条请求 detail JSON。
- v60：请求历史稳定性 summary。
- v61：summary 进入 audit、bundle、gate。

它也延续 v25-v34 的发布治理路线：project audit 负责检查，release bundle 负责打包证据，release gate 负责做最终 pass/warn/fail 决策。

## 关键文件

- `src/minigpt/project_audit.py`：新增 `request_history_summary_path` 参数、自动路径发现、`request_history_context`、summary 字段和 `request_history_summary` 审计检查。
- `src/minigpt/release_bundle.py`：把 request history summary 加入 bundle input、summary、context 和 evidence artifacts。
- `src/minigpt/release_gate.py`：新增 `require_request_history_summary` policy 字段，并增加 `request_history_summary_audit_check` 门禁检查。
- `src/minigpt/release_gate_comparison.py`：profile comparison 记录 request-history-summary requirement，并在 delta explanation 里解释 legacy 与标准策略差异。
- `scripts/audit_project.py`：新增 `--request-history-summary` 参数，命令输出 request history status/records。
- `scripts/build_release_bundle.py`：新增 `--request-history-summary` 参数，bundle 输出 request history status。
- `scripts/check_release_gate.py`：新增 `--allow-missing-request-history-summary`，可显式绕过新门禁要求。
- `scripts/compare_release_gate_profiles.py`：新增 profile comparison 级别的 request history summary requirement override。
- `tests/test_project_audit.py`、`tests/test_release_bundle.py`、`tests/test_release_gate.py`、`tests/test_release_gate_comparison.py`：覆盖新链路。

## 核心数据结构

project audit 新增三个层次的数据。

第一层是路径字段：

```json
{
  "request_history_summary_path": "runs/request-history-summary/request_history_summary.json"
}
```

这个字段说明 audit 使用的是哪份 summary。它不是最终判断本身，而是证据来源索引。

第二层是 `request_history_context`：

```json
{
  "available": true,
  "status": "pass",
  "total_log_records": 4,
  "invalid_record_count": 0,
  "timeout_rate": 0.0,
  "bad_request_rate": 0.0,
  "error_rate": 0.0
}
```

它是从 v60 summary 中抽取的审计上下文，供 Markdown/HTML 和后续 bundle 消费。这里保留的是稳定性判断需要的最小字段，不复制整份 recent requests。

第三层是 audit check：

```json
{
  "id": "request_history_summary",
  "title": "Request history summary is clean",
  "status": "pass",
  "detail": "status=pass; records=4; invalid=0; timeout_rate=0; error_rate=0."
}
```

这个 check 是 release gate 真正读取的门禁输入。v61 把 request history 的稳定性从“字段”提升成“检查项”，是本版最关键的结构变化。

## project audit 运行流程

`build_project_audit` 的流程变为：

1. 读取 registry。
2. 解析 model card 路径。
3. 解析 request history summary 路径。
4. 读取 model card 和 request history summary。
5. 构建 run rows。
6. 构建 audit checks。
7. 汇总 pass/warn/fail、score、ready runs 和 request history summary 字段。

路径解析支持两种方式：CLI 显式传 `--request-history-summary`，或按默认位置自动找 `runs/request-history-summary/request_history_summary.json`。显式参数适合 smoke/CI，默认路径适合常规项目运行。

## release bundle 运行流程

`build_release_bundle` 的作用是把证据打包。v61 后它新增三类 request history summary 证据：

- `request_history_summary_json`
- `request_history_summary_md`
- `request_history_summary_html`

这些 artifact 是 release bundle 的最终证据之一。JSON 给机器消费，Markdown 给文本审阅，HTML 给浏览器审阅。它们不是临时文件，只要进入 bundle，就表示这个 release 可以追溯到具体的本地推理稳定性摘要。

bundle 还会在 `summary` 里写入：

```json
{
  "request_history_status": "pass",
  "request_history_records": 4
}
```

这让 release overview 不必展开 audit checks，也能看到本地推理请求历史是否清洁。

## release gate 策略

v61 给 policy profile 新增 `require_request_history_summary`：

- `standard`: true
- `review`: true
- `strict`: true
- `legacy`: false

这样设计是为了同时满足两个目标：新版本默认要求 request history summary 审计检查，旧 bundle 仍然可以用 legacy profile 复查。release gate 新增的检查 id 是：

```text
request_history_summary_audit_check
```

当 policy 要求它时：

- audit checks 里没有 `request_history_summary`：fail。
- `request_history_summary` 是 `warn`：warn。
- `request_history_summary` 是 `pass`：pass。

这比直接读取 bundle 的 summary 字段更稳，因为 gate 只认 audit check，避免不同模块各自解释 request history 状态。

## profile comparison 的意义

profile comparison 现在会把 `require_request_history_summary_audit_check` 写入 row，并在 delta explanation 里说明 requirement 的变化。最典型的差异是 standard 与 legacy：

```text
Request-history-summary requirement changes from True to False.
```

这句话的价值是让人知道 legacy 通过并不代表证据更完整，而是 policy 对旧 bundle 做了兼容。

## 测试覆盖

`tests/test_project_audit.py` 覆盖两条关键路径：clean summary 让完整项目通过，watch/warn summary 会让 audit overall 进入 warn，并产生 review recommendation。

`tests/test_release_bundle.py` 覆盖 request history summary 被带入 bundle inputs、summary 和 artifacts，防止 bundle 只引用 audit 而漏掉原始 summary 证据。

`tests/test_release_gate.py` 覆盖 standard policy 要求 request history summary、legacy policy 允许缺失、warn summary 传导为 gate warn，以及显式 override 能关闭要求。

`tests/test_release_gate_comparison.py` 覆盖 profile comparison 中 standard 与 legacy 的差异，尤其是缺失 request history summary 时 legacy 为什么能通过。

## 与 README、截图和归档的关系

README 把当前版本提升到 v61，并说明 project audit、release bundle、release gate policy 都已经消费 request history summary。`b/61` 保存 smoke、Playwright 和文档检查截图，证明这不是只改源码，而是完成了运行证据闭环。

## 一句话总结

v61 把 request history summary 从“本地推理稳定性报告”提升为 project audit、release bundle 和 release gate policy 都能识别的发布治理证据。
