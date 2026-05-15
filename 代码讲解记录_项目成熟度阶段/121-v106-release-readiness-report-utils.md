# 第一百零六版代码讲解：Release Readiness 接入 report_utils

## 本版目标

v106 的目标是把 `release_readiness.py` 接入 `report_utils`，让发布就绪总览 dashboard 也使用公共报告基础工具。

它解决的问题是：v97 已经让 `release_bundle.py` 复用公共 JSON 写出、UTC 时间和 HTML 转义；v99-v105 又把 project audit、model card、experiment card、dataset card、run manifest、data preparation、data quality 逐步接入同一套基础设施。但 `release_readiness.py` 仍然保留自己的 `utc_now()`、JSON 写出、HTML 转义、dict/list 归一化 helper。v106 把这些通用部分收回公共层。

本版明确不做：

- 不改变 `ready`、`review`、`blocked`、`incomplete` 的判断规则。
- 不改变 release bundle、release gate、project audit、request history summary、maturity summary 的读取顺序。
- 不改变 panel 的 key、title、status、detail 和 source path 语义。
- 不改变 action recommendation 的生成规则。
- 不改变 Markdown/HTML 输出结构和 CSS。
- 不改变 missing JSON、非法 JSON、非 object JSON 的 warning 处理方式。
- 不改变 release readiness comparison、registry、release gate 或 release bundle 的业务逻辑。

## 路线来源

v106 延续 report-utils consolidation 路线。

相关发布治理链路是：

```text
registry
 -> project audit
 -> release bundle
 -> release gate
 -> request history summary
 -> maturity summary
 -> release readiness dashboard
```

v97 把 release bundle 接入公共工具，v99-v105 继续把上游治理证据层接入公共工具。v106 迁移的是 release readiness dashboard，也就是把这些证据合到一个发布就绪总览里的那一层。

这让发布就绪总览和上游证据在 JSON 写出、时间戳、HTML 转义、dict/list 归一化上使用同一个基础合同，同时把 dashboard 自己的发布判断继续留在模块内部。

## 关键文件

- `src/minigpt/release_readiness.py`
  - 删除本地 `datetime/timezone` 和 `html` 依赖。
  - 引入 `report_utils.utc_now`、`write_json_payload`、`html_escape`、`as_dict`、`list_of_dicts`。
  - `write_release_readiness_json()` 改为调用公共 JSON 写出。
  - 删除本地 `_dict()`、`_list_of_dicts()` 和 `_e()`。
  - 保留 `_string_list()`，因为本模块需要过滤空字符串，而公共 `string_list()` 会保留空值。

- `tests/test_release_readiness.py`
  - 本版不改测试文件。
  - 原有测试继续覆盖 ready、incomplete、blocked、JSON/Markdown/HTML 输出和 HTML escape。

- `README.md`
  - 当前版本更新到 v106。
  - shared report infrastructure 更新到 v83-v106。
  - 增加 v106 tag 和 `c/106` 截图说明。

- `代码讲解记录_项目成熟度阶段/README.md`
  - 增加 `121-v106-release-readiness-report-utils.md` 索引。
  - 当前阶段基线更新到 v106。

- `c/106/解释/说明.md`
  - 解释本版六张截图分别证明什么。

## 核心迁移点

迁移前，release readiness 自己实现：

```python
utc_now()
write_release_readiness_json()
_dict()
_list_of_dicts()
_e()
```

迁移后，通用语义来自：

```python
from minigpt.report_utils import (
    as_dict as _dict,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    utc_now,
    write_json_payload,
)
```

`write_release_readiness_json()` 变成：

```python
def write_release_readiness_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)
```

这让 release readiness 的 JSON 输出行为和 release bundle、project audit、model card、experiment card、dataset card、run manifest、data preparation、data quality 保持一致。

## 保留本地 helper 的原因

本版没有把下列 helper 迁走：

- `_summary`
- `_readiness_status`
- `_decision`
- `_registry_panel`
- `_bundle_panel`
- `_audit_panel`
- `_gate_panel`
- `_request_history_panel`
- `_maturity_panel`
- `_actions`
- `_evidence`
- `_resolve_optional_path`
- `_read_required_json`
- `_read_json`
- `_panel_section`
- `_evidence_section`
- `_list_section`
- `_stat`
- `_style`
- `_markdown_table`
- `_evidence_lines`
- `_fmt`
- `_fmt_bytes`
- `_string_list`
- `_md`

这些函数表达的是 release readiness dashboard 自己的业务语义。

例如：

- `_readiness_status` 决定 release 是否 ready、review、blocked 或 incomplete。
- `_actions` 把 fail/warn panel 和 gate check 转成发布前行动建议。
- `_resolve_optional_path` 定义显式路径、bundle hints、默认 candidate 的优先级。
- `_read_json` 定义缺失、非法 JSON、非 object JSON 如何进入 warnings。
- `_panel_section` 和 `_evidence_section` 定义 HTML dashboard 的展示结构。
- `_string_list` 会过滤空字符串，和公共 `string_list` 的“保留所有项”语义不同，所以留在本地。

如果把这些迁到 `report_utils`，公共层会开始承载 release-readiness-specific 发布判断和展示规则，边界会变差。

## 数据结构和字段语义

release readiness dashboard 的主要输出仍然包括：

- `schema_version`
  - dashboard schema 版本。

- `title`
  - HTML/Markdown 报告标题。

- `generated_at`
  - 生成时间。v106 起来自公共 `utc_now()`。

- `bundle_path`
  - 输入 release bundle 的路径。

- `inputs`
  - registry、project audit、release gate、request history summary、maturity summary 的解析路径。

- `summary`
  - 发布就绪总览。
  - 包含 `readiness_status`、`decision`、`release_status`、`gate_status`、`audit_status`、`request_history_status`、`maturity_status`、`ready_runs`、`missing_artifacts`、panel 计数等。

- `panels`
  - 每个证据来源的一张 panel。
  - 每项包含 `key`、`title`、`status`、`detail`、`source_path`。

- `actions`
  - 发布前行动建议。
  - fail/warn panel、gate fail/warn check、audit recommendations、bundle recommendations 都会进入这里。

- `evidence`
  - 从 release bundle artifacts 提取出来的证据表。

- `warnings`
  - 缺失或非法输入产生的 warning。

v106 不改变这些字段，只改变公共写出、转义和归一化工具来源。

## 运行流程

release readiness dashboard 的流程仍然是：

```text
release_bundle.json
 -> resolve registry/audit/gate/request-history/maturity inputs
 -> read optional JSON evidence with warnings
 -> build registry/bundle/audit/gate/request/maturity panels
 -> compute readiness summary and decision
 -> collect actions and bundle evidence
 -> write JSON/Markdown/HTML outputs
```

v106 改变的是：

- `generated_at` 使用公共 `utc_now`。
- release readiness JSON 使用公共 `write_json_payload`。
- HTML 文本转义使用公共 `html_escape`。
- dict/list normalization 使用公共 `as_dict` 和 `list_of_dicts`。

## 测试覆盖

本版使用 `tests.test_release_readiness` 做行为回归。

关键断言包括：

- 完整 evidence bundle 仍然得到 `readiness_status=ready` 和 `decision=ship`。
- 缺少 release gate 时仍然得到 `readiness_status=incomplete`，gate panel 为 `warn`。
- gate fail 时仍然得到 `readiness_status=blocked`，gate panel 为 `fail`，actions 里保留 gate check 失败原因。
- `write_release_readiness_outputs()` 仍然写出 JSON、Markdown、HTML 三类产物。
- HTML 渲染仍然转义 `<Readiness>`，不会把用户文本当成标签注入页面。

同时跑 `tests.test_report_utils`，确保公共工具行为稳定。

## 证据闭环

v106 的证据放在 `c/106`：

- `01-unit-tests.png` 证明聚焦测试、compileall 和全量 unittest 通过。
- `02-release-readiness-ready-smoke.png` 证明完整证据输入仍然生成 ready/ship 输出。
- `03-release-readiness-blocked-smoke.png` 证明 gate fail 输入仍然生成 blocked/block 输出和 gate action。
- `04-release-readiness-structure-check.png` 证明通用 helper 已迁移，release-readiness-specific helper 保留。
- `05-playwright-release-readiness-html.png` 证明 release readiness HTML 能被真实 Chrome 打开。
- `06-docs-check.png` 证明 README、`c/README.md`、阶段讲解索引和 v106 讲解互相对齐。

## 一句话总结

v106 把 release readiness dashboard 接入公共报告基础设施，让发布就绪总览和 release bundle、project audit、model/data/experiment/run 证据共享同一套基础工具，同时保留发布判断、panel、action 和 evidence table 的本地业务语义。
