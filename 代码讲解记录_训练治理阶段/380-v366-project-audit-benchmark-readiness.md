# 380-v366 project audit benchmark readiness

## 本版目标和边界

v364 生成 benchmark history readiness requirement，v365 让 maturity narrative 消费这个门禁。v366 的目标是把同一个门禁接入 project audit，让审计入口也能识别“history 有 ready entry，但 readiness requirement 失败”的情况。

本版不继续推进 release bundle、release gate 或 release readiness。那些属于更下游的发布链路，下一版可以再接。v366 只处理 project audit 的上下文、summary、报告和 CLI 输出。

## 关键文件

- `src/minigpt/project_audit_contexts.py`
  - `build_benchmark_history_context()` 读取 `readiness_requirement.status`、`decision`、`exit_code` 和 `failed_reasons`。
  - `build_benchmark_history_check()` 把 requirement fail 或非零 exit code 视为 `warn`。
  - check detail 中写入 requirement 状态、exit 和失败原因，方便人读检查。

- `src/minigpt/project_audit.py`
  - audit summary 增加 `benchmark_history_readiness_requirement_status`、`benchmark_history_readiness_requirement_exit_code` 和失败原因。
  - `_benchmark_history_status()` 把 requirement fail 纳入 benchmark history warn 判定。

- `src/minigpt/project_audit_artifacts.py`
  - Markdown summary 增加 benchmark history readiness、exit 和 reasons。
  - HTML stats 增加 `Bench readiness` 和 `Bench readiness exit`。

- `scripts/audit_project.py`
  - stdout 输出 readiness requirement 字段，便于 CI 和 smoke 脚本直接读取。

- `tests/test_project_audit.py`
  - 默认 benchmark history fixture 增加 pass requirement，保证正常路径不降级。
  - 新增 requirement failure 测试：ready entry 存在但 requirement fail 时，audit 和 benchmark_history check 都是 warn。
  - 输出测试覆盖 Markdown/HTML 的新字段。

## 核心数据结构

输入字段来自 benchmark history：

```json
{
  "readiness_requirement": {
    "status": "fail",
    "decision": "stop",
    "exit_code": 1,
    "failed_reasons": ["insufficient_ready_entries"]
  }
}
```

project audit summary 新增字段：

```json
{
  "benchmark_history_readiness_requirement_status": "fail",
  "benchmark_history_readiness_requirement_exit_code": 1,
  "benchmark_history_readiness_requirement_failed_reasons": ["insufficient_ready_entries"]
}
```

这些字段让审计报告能区分两种情况：

- 有 benchmark history ready entry，且 readiness requirement 通过。
- 有 ready entry，但本次要求更严格，requirement 失败，需要审计 review。

## 运行流程

1. `build_project_audit()` 读取 registry、model card 和 benchmark history。
2. `build_benchmark_history_context()` 解析 history summary、entries 和 readiness requirement。
3. `build_benchmark_history_check()` 根据 entry/ready/review/regression/model claim 和 requirement 状态决定 pass/warn。
4. `_build_summary()` 把 requirement 字段写入 audit summary。
5. Markdown、HTML、CLI stdout 同步展示同一组字段。

## 测试覆盖

- `test_build_project_audit_passes_complete_project` 验证 pass requirement 不影响完整项目通过。
- `test_build_project_audit_warns_for_benchmark_history_readiness_requirement_failure` 验证 requirement fail 会把 audit 降级为 warn，并进入 check detail。
- `test_write_project_audit_outputs` 验证 Markdown/HTML 报告包含 readiness 字段。
- context helper 测试覆盖 tiny-smoke/not-claimed 与 readiness fail 同时出现的审计细节。

## 运行截图和证据

- `d/366/图片/01-project-audit-readiness-requirement-warning.png`
- `d/366/解释/说明.md`

截图中的样例显示 `benchmark_history_ready=1` 但 `benchmark_history_readiness_requirement_status=fail`，因此审计结果为 `warn`。

## 一句话总结

v366 让 benchmark history readiness gate 从 maturity narrative 继续进入 project audit，降低了失败评估证据被误判为 clean audit evidence 的风险。
