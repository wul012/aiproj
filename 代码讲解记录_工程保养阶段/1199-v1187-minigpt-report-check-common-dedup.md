# v1187 MiniGPT report-check 公共脚手架去重 代码讲解

## 本版目标与边界

v1187 是一个维护版，不训练模型、不改任何行为、不增加模型能力。grokking 这条线到 v1186 已经收尾成一个完整故事（reproduce v1179 → characterize v1183 → audit v1180/81/82/84 → ship v1185 → use v1186）。在快速迭代里，codex 连续写的四个审计模块积累了一份逐字节重复的检查脚手架。本版按项目一贯的去重节奏（v1159/v1163/v1167/v1171/v1174/v1176：加一个 helper、只迁移当前活跃调用方、其他不动）把它收束掉。

边界写得很死：`behavior_identical_no_new_science_pure_maintenance`。这版唯一要证明的是“契约保持”——抽出来之后行为一模一样。

## 重复的三段代码

grokking 审计家族——`grok_evidence_check_v1180`、`grok_trajectory_phases_v1181`、`grok_paired_contrast_v1182`、`grok_wd_law_check_v1184`——每个模块都内联了三段**完全相同**的代码（先用 grep 确认四份逐字节一致再动手）：

1. `def _check(check_id, passed, expected, actual, detail)`：把一次检查压成 `{"id", "status": "pass"/"fail", "expected", "actual", "detail"}`。四份签名和函数体完全相同。
2. `failures = [check for check in checks if check["status"] != "pass"]`：收集未通过的检查行，喂给 `failed_count` / `issues` 和报告 `status`。四份相同。
3. `def resolve_exit_code(report, *, require_pass=False)`：`--require-pass` 时未通过返回 1，否则 0。四份逐字节相同。

这三段不是大块逻辑，但它们是“检查报告”这一类模块的公共合同。任由它在每个新审计模块里复制，迟早会出现“其中一份的 status 判定和别人不一致”的隐性分叉——和 v1176 完成 completion-mask 合同统一时担心的“训练合同分裂”是同一类风险。

## 新增模块 report_check_common

`src/minigpt/report_check_common.py` 提供三个函数：

```python
def check_row(check_id, passed, expected, actual, detail): ...
def collect_failures(checks): ...
def resolve_exit_code(report, *, require_pass=False): ...
```

`check_row` 就是原来的 `_check`，签名保持一致（positional），所以调用点不用改。`collect_failures` 用 `.get("status")` 取代 `["status"]`，对合法输入行为相同、对缺字段更稳。`resolve_exit_code` 原样搬过来。

名字取中性的 `report_check_common` 而不是 `grok_audit_common`，因为这三个 helper 本质是通用的“上游产物检查报告”工具，不是 grokking 专属。这样未来的检查模块（包括 PTQ 检查 v1177/v1178）也能复用。

## 四个模块怎么迁移

每个模块改四处：

1. 顶部加 `from minigpt.report_check_common import check_row as _check, collect_failures, resolve_exit_code`。
2. 删掉本地 `def resolve_exit_code(...)`。
3. 删掉本地 `def _check(...)`。
4. `failures = [check for check in checks if check["status"] != "pass"]` 改成 `failures = collect_failures(checks)`。

关键的合同保持点：`resolve_exit_code` 是 public（在各模块 `__all__` 里，CLI 通过 `from minigpt.grok_X import resolve_exit_code` 调用）。删掉本地定义后它由导入提供，仍然绑定在模块命名空间里，`__all__` 和 `from module import resolve_exit_code` 都照常工作。`_check` 是 private，用 `check_row as _check` 别名导入，内部所有 `_check(...)` 调用点一字不改。删除本地 def 时锚定在“紧随其后的那个 def”上（每个模块不同：v1180 是 `_group_rows`、v1181 是 `_curves_by_weight_decay`、v1182 是 `_pair_rows`、v1184 是 `_row_metrics`；`_check` 后面分别是 `_mean`/`_recommendations`/`_recommendations`/`_close`），这样空行间距天然正确，不会留下多余空行。

## 刻意不迁移的部分

PTQ 检查家族 v1177/v1178 有类似的 locate/read/exit-code 模式，但它们更早、用自己的 loader 习惯。本版不碰它们——和 v1171 维护时留下 dual-corpus transfer driver、v1163 留下 8 个 legacy 脚本是同一种克制：只迁移当前同构、活跃的调用方，避免把一次去重扩成一次大范围改动。未来 PTQ 检查若要复用，再迁移。

## 测试与契约保持证据

`tests/test_report_check_common.py` 测三个函数本身（check_row 形状、collect_failures 过滤、resolve_exit_code 的四种组合），外加一个 **single-source 身份断言**：

```python
for module in AUDIT_MODULES:
    assert module.resolve_exit_code is resolve_exit_code
    assert module._check is check_row
    assert module.collect_failures is collect_failures
```

这条断言保证迁移后四个模块用的是同一个函数对象，而不是又粘了一份副本——这正是 v1176 用过的“同一对象”守门思路，防止出现“common 改了、某个调用方的副本没改”的分叉。

契约保持的核心证据是：四个审计模块的测试文件**一字未改**，仍然全绿。focused 验证 `25 passed`（4 个审计模块测试 + 公共模块测试）。

## 链路角色与一句话总结

grokking 线在 v1186 收尾后，v1187 做了标准的去重维护，把审计脚手架的重复收束成单一可测来源。它不让模型更强，但让“检查报告”这一类模块在未来扩展时不会继续复制粘贴同一段合同。

一句话总结：v1187 把四个 grokking 审计模块里逐字节重复的 check-row 构造、failures 收集和 require-pass exit code 抽到 `report_check_common`，契约保持（审计模块测试未改全绿 + single-source 身份断言），是 grokking 线收尾后的标准去重维护版。
