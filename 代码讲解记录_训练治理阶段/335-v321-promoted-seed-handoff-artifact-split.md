# v321 promoted seed handoff artifact split

## 本版目标和边界

v320 解决的是 tiny comparison smoke 的实验预算问题。v321 回到训练治理链路里最重的一块：`promoted_training_scale_seed_handoff_artifacts.py`。

这版的目标不是改决策规则，也不是改 seed handoff 的业务状态，而是把最明显的 artifact 压力拆开：

- receipt JSON / text
- receipt check 字段与文本
- embedded receipt check 字段与文本
- handoff assurance 字段与文本

它们原本都堆在一个接近千行的文件里。v321 把这部分移动到 `promoted_training_scale_seed_handoff_receipt_artifacts.py`，让主 artifact 文件只保留门面组装和 CSV/Markdown/HTML 的主体渲染。

边界很重要：这不是重构业务，只是把“读取、格式化、写文件”这一层拆成更清晰的生产边界。外部导入路径和函数名保持不变。

## 前置能力

本版基于：

- v313-v314 的 promoted seed handoff receipt / assurance contract。
- v320 之后稳定的 tiny smoke 主线。
- 既有的 `promoted_training_scale_seed_handoff` 门面模块和相关测试。

v321 只做 artifact 层拆分，不改变 `build_promoted_training_scale_seed_handoff()` 的数据结构，也不改变 `check_promoted_training_scale_seed_handoff_*` 的规则。

## 关键文件

- `src/minigpt/promoted_training_scale_seed_handoff_receipt_artifacts.py`
  - 新增 receipt artifact 子模块。
  - 承接 automation receipt builder、receipt text renderer、receipt JSON/text writer。
  - 承接 receipt check / embedded receipt check / handoff assurance 的字段投影与 HTML section。

- `src/minigpt/promoted_training_scale_seed_handoff_artifacts.py`
  - 保留 CSV、Markdown、HTML 的主渲染与输出门面。
  - 从新 receipt artifact 子模块导入 receipt/check/assurance helper。
  - 对外仍导出同名函数，调用方无需改 import 路径。

- `tests/test_promoted_training_scale_seed_handoff.py`
  - 新增 `receipt_artifact_module` 导入。
  - 断言 handoff module、artifact module、receipt artifact module 的 receipt builder/renderer 是同一实现。

- `README.md`
  - 当前版本升级到 v321。
  - 说明这版是 promoted seed handoff artifact split。

- `d/321`
  - 保存本版运行截图和解释。

## 核心数据结构

receipt artifact 子模块继续处理三个层次的摘要：

1. `build_promoted_training_scale_seed_handoff_automation_receipt(report)`
   - 从 handoff report 中提取 schema v2 automation receipt。
   - 保留 `automation_decision`、`automation_exit_code`、`gate_*`、`failed_requirements` 和 CI regression 计数。

2. `_receipt_check_fields(report)` / `_embedded_receipt_check_fields(report)` / `_handoff_assurance_fields(report)`
   - 把 report 中的检查对象转成 CSV/Markdown/HTML 需要的平面字段。
   - 这些字段主要服务于 machine-readable 证据和可审计文本。

3. `_receipt_check_section(report)` / `_embedded_receipt_check_section(report)` / `_handoff_assurance_section(report)`
   - 生成 HTML 中的表格 section。
   - 仍然属于 artifact rendering，而不是业务判断。

主 artifact 文件保留的核心输出仍是：

- CSV
- Markdown
- HTML
- JSON writer 门面

## 运行流程

`build_promoted_training_scale_seed_handoff()` 生成的 report 仍旧是统一入口。v321 只改变 artifact 写出的分工：

```text
handoff report
  -> promoted_training_scale_seed_handoff_artifacts.py
     -> main CSV/Markdown/HTML
     -> reexported receipt artifact helpers
  -> promoted_training_scale_seed_handoff_receipt_artifacts.py
     -> receipt JSON/text
     -> receipt/check/assurance field projections
     -> receipt/check/assurance HTML sections
```

调用方不用知道 helper 被拆到哪里，只要继续调用原有 `write_promoted_training_scale_seed_handoff_outputs()` 和 receipt helper 即可。

## 输入输出

输入还是同一个 promoted seed handoff report dict。

输出分两类：

- 主 artifact 输出
  - `promoted_training_scale_seed_handoff.json`
  - `promoted_training_scale_seed_handoff.csv`
  - `promoted_training_scale_seed_handoff.md`
  - `promoted_training_scale_seed_handoff.html`

- receipt artifact 输出
  - `promoted_training_scale_seed_handoff_automation_receipt.json`
  - `promoted_training_scale_seed_handoff_automation_receipt.txt`

这些输出仍然是只读证据文件，不是新的业务状态。

## 测试覆盖

- `tests.test_promoted_training_scale_seed_handoff`
  - 断言 artifact module 与 handoff module 的 receipt builder/renderer 仍然同一引用。
  - 新增 receipt artifact module 同一引用断言，证明拆分后外部 API 没断。
- `tests.test_promoted_training_scale_seed_handoff_receipt`
  - 继续覆盖 receipt checker、embedded receipt checker 和 handoff assurance smoke。
- focused tests
  - 56 个相关测试通过，覆盖了 handoff artifact / receipt / assurance 链路。
- py_compile
  - 确认拆分后的两个模块都能编译。

这组测试保护的是“artifact boundary 迁移不破坏导出契约”，不是新的业务结论。

## 运行证据

归档位置：

```text
d/321/图片
d/321/解释/说明.md
```

截图会证明：

- 测试通过。
- 真实导入仍然指向同一实现。
- 旧的 handoff artifact 门面还在。
- 新 receipt artifact 模块已经承接实现。
- 代码扫描能找到拆分后的边界。

## 一句话总结

v321 把 promoted seed handoff 最重的 artifact 逻辑拆成 receipt 专用模块，让报告输出边界更清楚，但对外 API、测试契约和业务语义保持不变。
