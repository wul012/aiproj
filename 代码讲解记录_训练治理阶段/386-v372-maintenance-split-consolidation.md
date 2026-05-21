# 386-v372-maintenance-split-consolidation

## 本版目标与边界

v372 的目标是做一次维护型拆分收口：把 release bundle、maintenance policy governance artifacts、promoted seed handoff artifacts 三条已经持续增长的报告/证据链路拆到更专注的模块里。

这一版不做新训练能力、不改 CLI 参数、不改 JSON/CSV/Markdown/HTML 输出 schema，也不改变旧模块可导入的公开函数。它解决的是“后续继续推进功能时，单文件职责太宽、定位成本变高”的维护问题。

## 前置路线

这个版本来自近期的维护节奏判断：aiproj 已经进入训练治理和证据链稳定阶段，不能只继续增加新治理链，也不能让 artifact/report 文件持续变宽。v372 延续此前的拆分原则，把编排入口、数据上下文、产物渲染和兼容导出分开。

## 关键文件与链路角色

- `src/minigpt/release_bundle.py`
  - 现在更像 release bundle 的门面和编排入口。
  - 它负责调用上下文组装、summary 构建、artifact 收集和最终写入逻辑。
  - 旧的 `build_release_bundle`、CLI 和产物输出路径保持不变。

- `src/minigpt/release_bundle_support.py`
  - 承接 release bundle 的底层支持逻辑。
  - 主要包含 JSON 读取、路径解析、默认 release name、summary、release status、artifact collection。
  - 这些函数属于“输入整理和状态归纳”，不直接承担大段 Markdown/HTML 叙述。

- `src/minigpt/release_bundle_contexts.py`
  - 承接 release bundle 的上下文采集逻辑。
  - 包括 request history、benchmark history、CI workflow hygiene、coverage、audit checks、recommendations。
  - 这些字段会进入 release bundle summary 和 handoff 报告，是后续 release gate、release readiness 和 registry 继续消费的证据来源。

- `src/minigpt/maintenance_policy_artifacts.py`
  - 保留维护策略 artifact 的总入口和兼容表面。
  - 这样调用方不需要知道 governance stabilization 的渲染细节被移到了新文件。

- `src/minigpt/maintenance_policy_governance_artifacts.py`
  - 承接 governance stabilization 的 JSON、CSV、Markdown、HTML 产物写入。
  - 这里的产物是治理稳定性证据，不是模型能力证明；它说明某条 proposal 是被已有治理链吸收、需要复核，还是进入扩展候选。

- `src/minigpt/promoted_training_scale_seed_handoff_artifacts.py`
  - 保留 seed handoff artifact 写入、文件名约定和兼容导出。
  - 仍然是 promoted seed handoff 的产物入口。

- `src/minigpt/promoted_training_scale_seed_handoff_sections.py`
  - 承接 seed handoff Markdown/HTML section 的渲染。
  - 它把 handoff summary、review context、clean evidence 和 automation receipt 可视化逻辑从写文件编排里分离出来。

## 核心数据流

```text
release inputs
  -> release_bundle_contexts.py 收集上下文
  -> release_bundle_support.py 归纳 summary/status/artifacts
  -> release_bundle.py 编排 bundle 产物

maintenance policy review
  -> maintenance_policy_artifacts.py 统一入口
  -> maintenance_policy_governance_artifacts.py 写 governance stabilization 证据

promoted seed handoff report
  -> promoted_training_scale_seed_handoff_artifacts.py 写入产物
  -> promoted_training_scale_seed_handoff_sections.py 渲染 Markdown/HTML sections
```

这三个拆分都遵循同一个边界：入口文件保留外部契约，新文件承接内部职责，测试继续从旧入口和现有产物行为验证。

## 测试覆盖

本版运行了语法检查和定向测试：

```powershell
python -m py_compile src/minigpt/release_bundle.py src/minigpt/release_bundle_support.py src/minigpt/release_bundle_contexts.py src/minigpt/maintenance_policy_artifacts.py src/minigpt/maintenance_policy_governance_artifacts.py src/minigpt/promoted_training_scale_seed_handoff_artifacts.py src/minigpt/promoted_training_scale_seed_handoff_sections.py
python -m pytest tests/test_release_bundle.py tests/test_maintenance_policy.py tests/test_maintenance_policy_artifacts.py tests/test_promoted_training_scale_seed_handoff.py tests/test_promoted_training_scale_seed_handoff_receipt.py -q
```

测试结果是 `86 passed`。覆盖重点不是“新功能路径”，而是确认拆分后旧入口仍能生成相同类别的 release bundle、maintenance policy artifact 和 promoted seed handoff 证据。

## 运行证据

运行截图和解释归档到 `d/372`：

- `d/372/解释/说明.md`：说明本版目标、拆分边界、验证命令和 tag 含义。
- `d/372/解释/v372-maintenance-split-evidence.html`：本地证据页，汇总拆分后的模块职责和验证结果。
- `d/372/图片/01-maintenance-split-evidence.png`：Playwright 打开的本地证据页截图。

## 一句话总结

v372 把继续做训练治理功能前的维护边界先收紧：入口稳定、产物不变、职责更清楚。
