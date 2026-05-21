# 381-v367 release bundle benchmark readiness

## 本版目标和边界

v366 已经让 project audit 消费 benchmark history readiness requirement。v367 继续向下游推进一层，把同一份 requirement 接入 release bundle。这样发布交接报告不会因为 audit summary 是旧的 `pass` 就忽略 standalone benchmark history 中更新后的 `fail`。

本版不推进 release gate、release readiness 或 registry comparison。它只处理 release bundle 的 summary、context、Markdown/HTML 和 CLI stdout。

## 关键文件

- `src/minigpt/release_bundle.py`
  - `_benchmark_history_context()` 读取 benchmark history 的 `readiness_requirement` 字段。
  - `_status_from_benchmark_context()` 把 requirement fail 或非零 exit code 视为 `warn`。
  - `_benchmark_history_summary_status()` 在 audit summary 与 standalone history 之间选择更保守结果。
  - `_release_status()` 在 audit pass 但 benchmark history warn 时返回 `review-needed`。

- `src/minigpt/release_bundle_artifacts.py`
  - Markdown summary 增加 benchmark history readiness、exit 和 reasons。
  - HTML stats 增加 `Bench readiness` 和 `Bench readiness exit`。

- `scripts/build_release_bundle.py`
  - stdout 输出 requirement status、exit code 和 failed reasons。

- `tests/test_release_bundle.py`
  - 默认 fixture 增加 pass requirement，保证 ready release 不被误降级。
  - 新增 stale audit 测试：audit 是 pass，但 standalone benchmark history requirement fail 时，bundle 降为 `review-needed`。
  - 输出测试覆盖 Markdown/HTML 新字段。

## 核心数据结构

输入来自 benchmark history：

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

release bundle summary 新增字段：

```json
{
  "benchmark_history_status": "warn",
  "benchmark_history_readiness_requirement_status": "fail",
  "benchmark_history_readiness_requirement_exit_code": 1,
  "benchmark_history_readiness_requirement_failed_reasons": ["insufficient_ready_entries"],
  "release_status": "review-needed"
}
```

这里的关键不是新增一个显示字段，而是采用更保守的状态合并：如果 standalone history 比 audit summary 更新，并且它显示 requirement fail，release bundle 会进入 review。

## 运行流程

1. `build_release_bundle()` 读取 registry、model card、project audit 和 benchmark history。
2. `_benchmark_history_context()` 从 benchmark history 解析 summary、entries 和 readiness requirement。
3. `_benchmark_history_summary_status()` 合并 audit summary 与 standalone history status。
4. `_release_status()` 如果 audit pass 但 benchmark history warn，则输出 `review-needed`。
5. Markdown、HTML 和 CLI stdout 同步展示 requirement 字段。

## 测试覆盖

- `test_build_release_bundle_summarizes_ready_release` 验证 pass requirement 的 release 仍为 `release-ready`。
- `test_build_release_bundle_warns_when_history_requirement_fails_even_if_audit_is_stale_pass` 验证 stale audit pass 不能覆盖 standalone history fail。
- `test_write_release_bundle_outputs` 验证 Markdown/HTML 报告包含 readiness 字段。

## 运行截图和证据

- `d/367/图片/01-release-bundle-readiness-requirement-review.png`
- `d/367/解释/说明.md`

截图样例中 audit 仍是 pass，但 benchmark history readiness requirement fail，所以 release bundle 被降为 review-needed。

## 一句话总结

v367 让 benchmark history readiness gate 进入 release bundle 交接层，避免 stale audit pass 掩盖最新模型评估门禁失败。
