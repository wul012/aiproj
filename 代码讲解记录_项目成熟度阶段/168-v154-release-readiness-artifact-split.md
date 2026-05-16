# 第一百五十四版代码讲解：release readiness artifact split

## 本版目标

v154 的目标是把 release readiness dashboard 的 artifact 输出层从 `release_readiness.py` 拆到 `release_readiness_artifacts.py`。

这一版解决的问题不是“让发布就绪判断更复杂”，而是降低 `release_readiness.py` 的职责宽度：它应该负责读取 release bundle、release gate、project audit、request history、maturity summary 和 CI workflow hygiene evidence，构建 readiness dashboard payload；JSON/Markdown/HTML 的渲染写出则交给 artifact 模块。

明确不做：

- 不改变 readiness status、decision、panel status 的判定规则。
- 不改变 `scripts/build_release_readiness.py` 的命令行契约。
- 不改变 `release_readiness.json`、`release_readiness.md`、`release_readiness.html` 的文件名。
- 不新增新的治理报告类型。

## 前置路线

v153 已经把 release bundle 的 artifact 输出层拆到 `release_bundle_artifacts.py`。v154 沿用同一条维护节奏，把相邻的 release readiness dashboard 做相同边界拆分。

这属于“合同保持的维护收口”：

```text
release bundle
  -> release readiness dashboard
  -> release readiness comparison
  -> registry / maturity context
```

v154 只处理第二层 dashboard 的 artifact 输出边界，让构建逻辑和展示输出分开。

## 关键文件

```text
src/minigpt/release_readiness.py
src/minigpt/release_readiness_artifacts.py
tests/test_release_readiness.py
README.md
c/README.md
c/154/解释/说明.md
```

`release_readiness.py` 保留核心构建链路：

- `build_release_readiness_dashboard`
- `_summary`
- `_registry_panel`
- `_bundle_panel`
- `_audit_panel`
- `_gate_panel`
- `_request_history_panel`
- `_maturity_panel`
- `_ci_workflow_panel`
- `_actions`
- `_evidence`
- JSON input 读取和路径解析 helper

`release_readiness_artifacts.py` 新增并接管：

- `write_release_readiness_json`
- `render_release_readiness_markdown`
- `write_release_readiness_markdown`
- `render_release_readiness_html`
- `write_release_readiness_html`
- `write_release_readiness_outputs`
- Markdown table、HTML panel/evidence/list/style、byte formatting 等展示 helper

## facade 兼容

历史调用方可能仍然这样使用：

```python
from minigpt.release_readiness import write_release_readiness_outputs
from minigpt.release_readiness import render_release_readiness_html
```

v154 没有让这些 import 失效。`release_readiness.py` 从 `release_readiness_artifacts.py` 重新导入同名函数，因此旧 API 仍然存在。

测试里新增了 identity 断言：

```python
release_readiness.render_release_readiness_html is release_readiness_artifacts.render_release_readiness_html
release_readiness.render_release_readiness_markdown is release_readiness_artifacts.render_release_readiness_markdown
release_readiness.write_release_readiness_outputs is release_readiness_artifacts.write_release_readiness_outputs
release_readiness.write_release_readiness_json is release_readiness_artifacts.write_release_readiness_json
```

这比只测试输出文件存在更直接，因为它证明旧 facade 和新 artifact 模块没有形成两套实现。

## 核心数据流

v154 后的数据流是：

```text
release_bundle.json
release_gate/gate_report.json
audit/project_audit.json
request-history-summary/request_history_summary.json
maturity-summary/maturity_summary.json
ci-workflow-hygiene/ci_workflow_hygiene.json
        |
        v
release_readiness.py
  build_release_readiness_dashboard()
        |
        v
readiness payload dict
        |
        v
release_readiness_artifacts.py
  write_release_readiness_outputs()
        |
        v
release_readiness.json
release_readiness.md
release_readiness.html
```

payload 仍然是最终契约。artifact 模块只消费 payload，不重新读取上游证据，也不重新判定 readiness。

## 关键字段语义

`summary` 仍然表达发布就绪总览：

- `readiness_status`: `ready` / `review` / `blocked` / `incomplete`
- `decision`: `ship` / `review` / `block` / `collect-evidence`
- `gate_status`: release gate 的状态
- `audit_status`: project audit 的状态
- `ci_workflow_status`: CI workflow hygiene 的状态
- `request_history_status`: request history summary 的状态
- `missing_artifacts`: release bundle 汇总出的缺失 artifact 数

`panels` 仍然表达 dashboard 每个证据面板：

- `key`: 面板机器名
- `title`: 展示标题
- `status`: `pass` / `warn` / `fail`
- `detail`: 可读解释
- `source_path`: 对应证据文件

`evidence` 仍然来自 release bundle artifacts，只用于展示和追踪，不改变 readiness 判定。

## artifact 模块边界

`release_readiness_artifacts.py` 的职责是把 payload 写成三种形态：

- JSON：机器消费的结构化证据。
- Markdown：适合 README、讲解记录和人工审查。
- HTML：适合 dashboard 浏览和截图。

它不关心：

- release gate 是否通过。
- CI workflow hygiene 是 pass 还是 warn。
- request history 是否缺失。
- maturity summary 的语义是否足够。

这些都由 `release_readiness.py` 的构建层决定。

## 测试覆盖

`tests/test_release_readiness.py` 覆盖了两类风险。

第一类是行为不变：

- ready 状态会得到 `decision=ship`。
- 缺失 gate 会得到 incomplete/review action。
- failed gate 会 block。
- failed CI workflow hygiene 会进入 review，而不是 hard block。
- HTML 仍然转义 `<Readiness>`，避免标题注入。

第二类是 facade 兼容：

- 旧模块导出的 render/write 函数必须和新 artifact 模块是同一对象。

这样测试既保护 readiness 判定链路，也保护拆分带来的导入兼容。

## 维护压力结果

拆分前：

```text
release_readiness.py: 628 lines
```

拆分后：

```text
release_readiness.py: about 415 lines
release_readiness_artifacts.py: about 252 lines
```

维护压力 smoke 结果：

```text
module_pressure_status=pass
module_warn_count=0
largest_module=src\minigpt\server.py
```

这说明 release readiness 已不再是最大模块，且没有引入 warn 级模块。

## 运行截图和证据

v154 运行证据放在：

```text
c/154/图片
c/154/解释/说明.md
```

截图覆盖：

- release readiness 专项测试。
- release readiness CLI smoke。
- maintenance/module pressure smoke。
- source encoding smoke。
- full unittest。
- docs keyword check。

这些证据证明本版不是只移动代码，而是通过测试、CLI、维护压力、编码卫生和文档一致性形成闭环。

## 一句话总结

v154 把 release readiness dashboard 从“构建逻辑和展示输出混在一个模块”推进到“构建层与 artifact 输出层分离”，让发布就绪治理链继续保持可维护。
