# v166 project audit context split 代码讲解

## 本版目标

v166 的目标是把 `project_audit.py` 里的 request-history summary 和 CI workflow hygiene 检查/上下文映射，拆到 `project_audit_contexts.py`。

这一版解决的是项目审计模块的职责边界问题。`project_audit.py` 已经在较早版本把 Markdown/HTML/JSON artifact 输出拆到了 `project_audit_artifacts.py`，所以 v166 不再重复拆报告层，而是拆更接近审计输入语义的外部治理上下文：本地推理请求历史是否健康、GitHub Actions workflow 策略是否健康。

本版明确不做三件事：

- 不改变 `project_audit.json` schema。
- 不改变 `write_project_audit_outputs()`、Markdown、HTML 的输出格式。
- 不改变 `scripts/audit_project.py` 的 CLI 参数和调用方式。

## 前置路线

v146-v151 把 CI workflow hygiene 证据逐步接入 project audit、release bundle、release readiness、registry 和 maturity summary。v164 又把 request-history endpoint 处理拆出了 server。到了 v166，`project_audit.py` 仍然混合了 registry/model card 检查、request-history 检查、CI workflow 检查和上下文字段映射。

因此这版的路线是：

```text
registry/model card inputs
 -> project_audit.py
 -> project_audit_contexts.py
 -> request_history_context / ci_workflow_context
 -> project_audit_artifacts.py
```

## 关键文件

- `src/minigpt/project_audit.py`：继续负责读取 registry/model card/request-history/CI hygiene 输入，构建 run rows、核心 audit checks、summary 和 recommendations。
- `src/minigpt/project_audit_contexts.py`：新增模块，负责 request-history summary check、request-history context、CI workflow hygiene check、CI workflow context。
- `tests/test_project_audit.py`：新增直接测试，验证 helper 对 pass/warn/missing 输入的映射。
- `README.md`：更新当前版本、能力矩阵、版本标签、项目结构和 v166 截图说明。
- `c/166/解释/说明.md`：说明每张运行截图证明的链路。
- `代码讲解记录_项目成熟度阶段/README.md`：登记 v166 讲解。

## 核心数据结构

### request-history check

`build_request_history_summary_check()` 返回一个 audit check：

```text
id
title
status
detail
evidence
```

当 summary 缺失时，状态是 `warn`，detail 会说明缺少 `request_history_summary.json`。当 summary 存在时，它读取：

- `status`
- `total_log_records`
- `invalid_record_count`
- `timeout_rate`
- `bad_request_rate`
- `error_rate`

只有 `status == "pass"` 时审计 check 才是 pass，否则进入 warn。

### request-history context

`build_request_history_context()` 返回供 audit/report 下游消费的摘要：

- `available`
- `request_log`
- `status`
- `total_log_records`
- `invalid_record_count`
- `timeout_count`
- `bad_request_count`
- `error_count`
- `timeout_rate`
- `bad_request_rate`
- `error_rate`
- `unique_checkpoint_count`
- `latest_timestamp`

这是机器可消费的上下文字段，不是最终展示文案。

### CI workflow hygiene check

`build_ci_workflow_hygiene_check()` 同样返回 audit check。它读取：

- `status`
- `decision`
- `action_count`
- `node24_native_action_count`
- `failed_check_count`
- `forbidden_env_count`
- `missing_step_count`
- `python_version`

只有 `status == "pass"` 时 check 为 pass，否则为 warn。

### CI workflow context

`build_ci_workflow_context()` 把 CI hygiene report 摘成 audit 上下文，供 release bundle、readiness 和 maturity 等下游继续使用。

## 核心函数

### `build_project_audit()`

主函数仍在 `project_audit.py`。它继续解析输入路径，读取 JSON，并组装最终 audit report。变化只在于：

```text
build_request_history_context(...)
build_ci_workflow_context(...)
```

替代了旧的私有 context 函数。

### `_build_checks()`

核心 run coverage checks 仍留在 `project_audit.py`。其中 request-history 和 CI workflow 两个外部治理 check 改为调用：

```text
build_request_history_summary_check(...)
build_ci_workflow_hygiene_check(...)
```

这让 `_build_checks()` 继续表达“有哪些检查”，而不再承担每种外部治理证据的字段格式化细节。

## 测试覆盖

本版测试覆盖三层：

- `tests.test_project_audit` 原有完整项目、缺失 experiment card、request-history warn、CI hygiene fail、artifact 输出、HTML escaping、facade identity 测试继续通过。
- 新增 `test_project_audit_context_helpers_map_statuses_and_missing_inputs`，直接验证 context helper 的 status、detail、evidence 和 missing 输入行为。
- 全量 unittest 验证 release bundle、release gate、readiness、maturity 等下游不会因为 audit context 拆分而断开。

## 运行证据

`c/166/图片/` 保存本版截图：

- `01-project-audit-tests.png`：project audit 局部测试通过。
- `02-project-audit-context-smoke.png`：直接 helper smoke 验证 request-history 和 CI workflow hygiene 的 warn/missing 映射。
- `03-maintenance-smoke.png`：module pressure 仍为 pass。
- `04-source-encoding-smoke.png`：源码编码和 Python 3.11 兼容检查通过。
- `05-full-unittest.png`：全量 unittest 通过。
- `06-docs-check.png`：README、讲解、`c/166` 和关键源码/测试索引对齐。

## 边界说明

`project_audit_contexts.py` 不是 artifact 模块，也不是新的 release gate。它只负责把外部治理证据转换成 project audit 的 check 和 context 字段。

最终是否 release-ready 仍由 release bundle、release gate 和 readiness 层判断。v166 提升的是 audit builder 的可维护性和外部治理上下文的可测试性。

## 一句话总结

v166 把 project audit 的 request-history 与 CI workflow hygiene 上下文逻辑独立出来，让 `project_audit.py` 从 538 行降到 404 行，同时保持 audit schema、输出和 CLI 入口不变。
