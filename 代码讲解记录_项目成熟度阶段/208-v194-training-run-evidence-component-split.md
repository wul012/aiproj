# v194 training run evidence component split 代码讲解

## 本版目标

v194 的目标是做一次轻量、定向的质量优化：拆分 `training_run_evidence.py`。

这个模块在 v193 后已经达到 580 行，内部同时承担：

```text
读取 run artifacts
构造 artifact rows
构造 readiness checks
构造 summary
构造 training/data/eval/quality/scorecard/sample sections
构造 recommendations
数值和嵌套字段 helper
对外 re-export artifact writers
```

这已经超过 aiproj 当前对大文件的维护压力阈值。v194 把其中的组件逻辑移到新模块，保留原 public API 不变。

本版明确不做：

- 不改变 training run evidence JSON schema。
- 不改变 readiness score、ready/review/blocked 判定规则。
- 不迁移 artifact writer。
- 不顺手收敛全仓 `utc_now` 或 `_dict`。
- 不改测试入口样板。

## 前置路线

v194 接在 v186-v193 的真实训练证据链之后：

```text
v186 real training run evidence
 -> v187 eval summary
 -> v188 generation quality summary
 -> v189 benchmark scorecard summary
 -> v190 path compatibility
 -> v191 pair baseline
 -> v192 external baseline
 -> v193 batch external baseline
 -> v194 evidence component split
```

也就是说，这不是“为了拆而拆”。前面连续扩展训练证据链后，模块职责自然变宽，v194 是一次必要的收口。

## 关键文件

```text
src/minigpt/training_run_evidence.py
src/minigpt/training_run_evidence_components.py
tests/test_training_run_evidence.py
c/194/图片
c/194/解释/说明.md
```

`training_run_evidence.py` 仍然是入口模块。用户和脚本继续从这里调用 `build_training_run_evidence()`，也继续从这里拿 artifact writer facade。

`training_run_evidence_components.py` 是新增组件层，负责所有纯数据结构构造逻辑。

`tests/test_training_run_evidence.py` 没有改变契约，它继续验证 ready/review/blocked、eval/quality/scorecard 摘要、HTML escaping 和输出文件。

## 拆分后的职责

拆分后主模块负责：

```text
_read_json()
_load_history_records()
_merge_history_summary()
_artifact_rows()
build_training_run_evidence()
artifact writer re-export
```

新增组件模块负责：

```text
build_checks()
build_summary()
training_section()
data_section()
sample_section()
evaluation_section()
quality_section()
scorecard_section()
recommendations()
_check()
_nested_pick()
_int()
_float()
```

主模块行数从：

```text
580
```

降到：

```text
151
```

新增组件模块为：

```text
456
```

两个文件都低于 500 行，符合本阶段“轻量定向拆分”的目标。

## 为什么不继续拆第二层

`training_run_evidence_components.py` 虽然也接近 500 行，但它现在是一个纯组件模块，内部函数之间共享同一组状态语义：

```text
check status
summary counters
section fields
recommendation rules
value conversion helpers
```

继续拆成 checks/sections/recommendations 三个文件也可以，但本版会变成更大范围重构，收益没有当前第一刀明显。v194 选择停在“入口文件瘦身 + 组件集中”的平衡点。

## 核心数据流

`build_training_run_evidence()` 的数据流仍然是：

```text
run_dir
 -> read train_config/run_manifest/metrics/history/eval/quality/scorecard
 -> artifact_rows
 -> evaluation_section / quality_section / scorecard_section
 -> build_checks
 -> build_summary
 -> training_section / data_section / sample_section
 -> recommendations
 -> report
```

区别只是中间构造函数来自 `training_run_evidence_components.py`。

## 对外契约为什么没有变化

原入口仍然存在：

```python
build_training_run_evidence(run_dir, ...)
```

原 re-export 仍然存在：

```python
render_training_run_evidence_html
render_training_run_evidence_markdown
write_training_run_evidence_outputs
```

输出 report 的核心字段也不变：

```text
summary
training
data
evaluation
quality
scorecard
sample
checks
artifacts
warnings
recommendations
```

所以调用方不需要改 import，也不需要改读取 JSON 的字段。

## 测试如何保护行为

`tests/test_training_run_evidence.py` 继续覆盖：

- 完整 run artifacts 得到 `summary.status == ready`。
- readiness score 为 100。
- checkpoint 缺失会 blocked。
- eval suite 缺失但非 required 时进入 review。
- generation quality 缺失进入 review。
- benchmark scorecard 缺失进入 review。
- Markdown/HTML 输出仍包含 Evaluation、Generation Quality、Benchmark Scorecard。
- HTML title escape 不回退。

本版还额外做了 contract smoke，确认拆分后 ready run 的 eval、quality、scorecard 和 recommendations 仍存在。

## 运行证据

v194 运行截图放在：

```text
c/194/图片
c/194/解释/说明.md
```

关键证据包括：

```text
focused tests: pass
py_compile: pass
line count: 580 -> 151
component count: 456
full unittest: pass
source encoding: pass
docs check: pass
```

## 一句话总结

v194 把训练运行证据从膨胀的单入口文件拆成“编排入口 + 组件构造层”，在不改变外部契约的前提下降低了后续维护成本。
