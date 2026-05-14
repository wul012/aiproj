# v97 release bundle report utility migration

## 本版目标

v97 的目标是把 `release_bundle.py` 中与公共 `report_utils.py` 语义一致的报告基础设施迁移出去，同时保留 release bundle 自己的显示格式化规则。

release bundle 是发布治理链路里的总包：它读取 registry、model card、project audit 和 request history summary，把这些证据整理成 `release_bundle.json`、Markdown 和 HTML。后续 release gate、release readiness dashboard 和 profile comparison 都会消费这个总包。

本版解决的问题是：`release_bundle.py` 原本保留私有 `utc_now`、`_list_of_dicts`、`_dict`、`_e` 和 JSON writer。这些与 `report_utils.py` 的语义一致，可以安全迁移。

## 本版明确不做什么

v97 不改变 release bundle 的发布状态判断。

保持不变的边界包括：

- project audit 缺失时仍然是 `needs-audit`。
- audit fail 时仍然是 `blocked`。
- audit pass 且 evidence 完整时仍然可以是 `release-ready`。
- registry、model card、project audit、request history summary 的自动路径解析不变。
- evidence artifact 的存在性、kind、size 统计不变。
- `scripts/build_release_bundle.py` 的参数和输出语义不变。

本版也不强行迁移全部 helper。`_md`、`_string_list`、`_fmt`、`_fmt_delta`、`_fmt_any`、`_fmt_bytes` 和 `_rank_label` 继续保留在模块内，因为它们承担 release bundle 的本地显示语义。

## 来自哪条路线

v83 新增 `report_utils.py`，后续逐步覆盖 training scale、promoted comparison 和 generation quality。
v97 把公共报告工具层推进到发布治理总包：

```text
registry + model card + project audit + request history summary
 -> release bundle
 -> release gate / release readiness
```

这说明公共工具层开始覆盖 release evidence 的聚合入口。

## 关键文件

`src/minigpt/release_bundle.py`

这是本版核心迁移文件。它继续负责读取发布证据输入、收集 artifacts、计算 summary、top runs、audit checks、request history context、recommendations 和 warnings，并输出 JSON/Markdown/HTML。

`src/minigpt/report_utils.py`

这是公共报告工具层。本版复用：

```text
as_dict as _dict
html_escape as _e
list_of_dicts as _list_of_dicts
utc_now
write_json_payload
```

`tests/test_release_bundle.py`

这是 release bundle 业务测试。它覆盖 release-ready、needs-audit、输出文件和 HTML escaping。

`tests/test_report_utils.py`

继续保护公共工具本身。v97 让 release bundle 成为新的消费者，因此公共层回归仍然必要。

`scripts/build_release_bundle.py`

这是 CLI 入口。本版不改参数，只用它做 ready 和 missing-audit 两条 smoke。

`c/97/`

保存本版运行截图和解释，包括 tests、smoke、结构检查、Playwright HTML 和文档对齐检查。

## 迁移前的重复点

迁移前，`release_bundle.py` 自己维护：

```text
utc_now
_list_of_dicts
_dict
_e
```

并手写 JSON 输出：

```text
Path(...).write_text(json.dumps(..., ensure_ascii=False, indent=2))
```

v97 将这些统一到 `report_utils.py`，减少不同报告模块之间的重复实现。

## 保留的本地 helper

`_md`

它依赖 `_fmt_any`，用于 release bundle Markdown 表格里的 `missing`、float 和换行处理。

`_string_list`

它会过滤空字符串，适合 recommendations 和 warnings 展示。

`_fmt` / `_fmt_delta` / `_fmt_any` / `_fmt_bytes` / `_rank_label`

这些都是 release bundle 的本地显示规则，用于 loss、delta、bytes 和 rank。它们不是通用 normalization，不应为了统一而迁移。

## 核心数据结构

`summary`

release bundle 的核心摘要：

```text
release_status
audit_status
audit_score_percent
run_count
best_run_name
best_val_loss
ready_runs
request_history_status
available_artifacts
missing_artifacts
```

`release_status` 是后续 release gate 和 readiness 使用的关键字段。

`artifacts`

每个 artifact 记录发布证据是否存在：

```text
key
title
path
exists
kind
size_bytes
description
```

`top_runs`

来自 model card 或 registry leaderboard，展示当前候选 run：

```text
name
path
status
best_val_loss_rank
best_val_loss
best_val_loss_delta
dataset_quality
eval_suite_cases
experiment_card_html
```

`audit_checks`

来自 project audit，用于说明 release bundle 为什么 pass、warn 或 fail。

## 输出格式说明

`release_bundle.json`

这是机器可读发布证据总包。v97 只把写出动作替换成 `write_json_payload`，字段结构不变。

`release_bundle.md`

这是人读交接版，包含 summary、inputs、top runs、audit checks、evidence artifacts、recommendations 和 warnings。v97 保留本地 `_md`，避免 Markdown 显示规则变化。

`release_bundle.html`

这是浏览器证据，展示发布状态、输入路径、top runs、audit checks 和 artifacts。v97 复用公共 `html_escape`。

## 运行流程

主流程保持不变：

```text
build_release_bundle
 -> _read_required_json
 -> _resolve_model_card_path
 -> _resolve_audit_path
 -> _resolve_request_history_summary_path
 -> _collect_release_artifacts
 -> _top_runs
 -> _build_summary
 -> write_release_bundle_outputs
```

其中 `_build_summary` 是发布状态判断核心，v97 没有改动。

## 测试如何覆盖链路

`test_build_release_bundle_summarizes_ready_release`

构造 registry、model card、project audit 和 request history summary，断言 release status 为 `release-ready`，并确认 artifacts 足够完整。

`test_build_release_bundle_marks_missing_audit`

删除 project audit，断言 release status 为 `needs-audit`，防止迁移后误把缺失审计当成可发布。

`test_write_release_bundle_outputs`

确认 JSON、Markdown、HTML 都能写出，并检查 Markdown/HTML 中的关键内容。

`test_render_release_bundle_html_escapes_run_text`

用 `<Release>` 和 `<script>` 输入，确认 HTML 转义仍然存在。

## 本版证据

v97 证据归档在：

```text
c/97/图片
c/97/解释/说明.md
```

关键截图包括：

- focused tests、compile check 和 full regression。
- ready smoke，证明完整证据仍然得到 `release-ready`。
- missing-audit smoke，证明缺失 audit 仍然得到 `needs-audit`。
- 结构检查，确认公共 helper 已引用、私有同义 helper 已移除、release-specific helper 被保留。
- Playwright/Chrome 打开生成后的 HTML 报告。
- README、阶段索引和 `c/README.md` 的 v97 文档检查。

## 后续推进原则

release bundle 是发布治理总包，后续迁移 release gate、release readiness 或 project audit 时要更加谨慎：

- 状态判定逻辑不随 helper 迁移改变。
- 缺失证据、失败审计、warning 的边界必须有 smoke。
- 模块特有显示格式化 helper 保留到本地，除非公共函数语义完全一致。

## 一句话总结

v97 把 release bundle 的公共报告基础设施迁移到 `report_utils`，让发布证据总包加入共享报告层，同时保留发布层特有的格式化语义。
