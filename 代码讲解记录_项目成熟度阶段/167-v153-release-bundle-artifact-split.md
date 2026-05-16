# 第一百五十三版代码讲解：release bundle artifact split

## 本版目标

v153 是一次针对真实维护压力的收口型重构。
v152 的 maintenance smoke 显示 `release_bundle.py` 是当前 module pressure 的 warn 模块。
本版目标是把 release bundle 的 JSON/Markdown/HTML 渲染写出层拆到独立 artifact 模块，让主模块回到“构建 release bundle 数据”的职责。

本版解决的问题：

- `release_bundle.py` 同时负责读取输入、构建 summary、收集 artifacts、渲染 Markdown、渲染 HTML、写出文件和维护 HTML 样式。
- 这些职责混在一个文件里，让模块越过维护压力阈值。
- 后续如果继续给 release bundle 增加证据字段，很容易把构建逻辑和展示逻辑缠在一起。

本版不做：

- 不改变 release bundle JSON schema。
- 不改变 release status、audit status、CI workflow context、request history context 的规则。
- 不新增新的 release gate 或 readiness 逻辑。
- 不改变脚本和旧测试的导入方式。

## 前置路线

本版承接两条路线：

```text
v147 -> release bundle begins carrying CI workflow hygiene evidence
v152 -> maintenance smoke shows release_bundle.py as module pressure watch/warn
v153 -> split release bundle artifact rendering from bundle construction
```

这是一版“按维护证据行动”的重构，不是继续堆功能。

## 关键文件

```text
src/minigpt/release_bundle.py
src/minigpt/release_bundle_artifacts.py
tests/test_release_bundle.py
README.md
c/153/解释/说明.md
```

`release_bundle.py` 现在保留：

- `build_release_bundle()`
- 输入路径解析
- JSON 读取
- summary 构建
- artifact 列表收集
- request history / CI workflow context 汇总
- recommendations

`release_bundle_artifacts.py` 新增并接管：

- `write_release_bundle_json()`
- `render_release_bundle_markdown()`
- `write_release_bundle_markdown()`
- `render_release_bundle_html()`
- `write_release_bundle_html()`
- `write_release_bundle_outputs()`
- Markdown 表格、HTML section、artifact link、style 等展示辅助函数

## facade 兼容

为了不破坏已有调用，`release_bundle.py` 继续导出旧函数名：

```text
render_release_bundle_html
render_release_bundle_markdown
write_release_bundle_html
write_release_bundle_json
write_release_bundle_markdown
write_release_bundle_outputs
```

这些名字现在从 `release_bundle_artifacts.py` import。
因此脚本仍可以继续：

```python
from minigpt.release_bundle import build_release_bundle, write_release_bundle_outputs
```

这和项目里之前 `maturity_artifacts`、`generation_quality_artifacts`、`training_portfolio_artifacts` 的拆分方式一致。

## 核心数据流

拆分前：

```text
release_bundle.py
  -> build release bundle payload
  -> render markdown
  -> render html
  -> write json/markdown/html
```

拆分后：

```text
release_bundle.py
  -> build release bundle payload

release_bundle_artifacts.py
  -> render markdown/html
  -> write json/markdown/html
```

release bundle payload 本身没有变化。
渲染层读取的仍然是同一个 `bundle: dict[str, Any]`。

## 测试覆盖

`tests/test_release_bundle.py` 原有测试继续覆盖：

- ready release summary
- explicit CI workflow hygiene path
- missing audit warning
- output files写出
- HTML escaping

本版新增：

```text
test_release_bundle_keeps_legacy_artifact_exports
```

断言：

```text
release_bundle.render_release_bundle_html is release_bundle_artifacts.render_release_bundle_html
release_bundle.render_release_bundle_markdown is release_bundle_artifacts.render_release_bundle_markdown
release_bundle.write_release_bundle_outputs is release_bundle_artifacts.write_release_bundle_outputs
release_bundle.write_release_bundle_json is release_bundle_artifacts.write_release_bundle_json
```

这能防止 facade 兼容被误删。

## 维护压力结果

拆分前：

```text
release_bundle.py: 709 lines
module_pressure_status=watch
module_warn_count=1
largest_module=src/minigpt/release_bundle.py
```

拆分后：

```text
release_bundle.py: about 409 lines
release_bundle_artifacts.py: about 331 lines
module_pressure_status=pass
module_warn_count=0
largest_module=src/minigpt/release_readiness.py
```

这说明本版不是为了形式拆分，而是直接消除了当前 module pressure warn。

## 证据边界

v153 证明的是 release bundle 代码结构更可维护，artifact 输出层和 payload 构建层边界更清楚。

它不证明模型生成能力提升，不改变发布门禁，也不改变 release bundle 的业务语义。

## 运行与归档

v153 的运行截图和解释放在：

```text
c/153/图片
c/153/解释/说明.md
```

截图覆盖 release bundle 测试、CLI smoke、maintenance/module pressure smoke、source encoding hygiene、全量 unittest 和文档对齐检查。

## 一句话总结

v153 把 release bundle 的展示输出层从主构建模块中拆出，让 module pressure 回到 pass，并保持旧导入路径完全兼容。
