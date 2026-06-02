# v781 maturity release context split

## 本版目标和边界

v781 是维护拆分版本，不新增模型能力、不新增 maturity 字段、不改变 maturity artifact 输出格式。它只把 `maturity.py` 中的 release readiness comparison context 归一化逻辑拆成独立模块。

本版不改变：

- `build_maturity_summary` 的签名和返回结构。
- maturity summary 的 JSON/CSV/Markdown/HTML renderer。
- release readiness trend status 的判断顺序。
- coverage governance chain 对 maturity 的调用方式。

## 为什么这一刀有必要

`maturity.py` 原本已经混合了多层职责：

- 从 README、归档目录、代码讲解目录发现版本。
- 根据 `CAPABILITY_SPECS` 生成 capability matrix。
- 汇总整体 maturity status。
- 从 registry 中提取 release readiness comparison delta summary。
- 根据 release readiness delta 判断 maturity 是否需要降级为 review。

其中 release readiness context 是字段最密、最容易跟随 release comparison 扩展而增长的一块。把它留在主文件中，会让 maturity 的能力矩阵逻辑和 release delta 字段映射纠缠在一起。

## 关键文件

### `src/minigpt/maturity_release_context.py`

新增模块提供：

- `build_release_readiness_context(registry)`：从 registry 中读取 `release_readiness_comparison_counts` 和 `release_readiness_delta_summary`，生成 maturity 使用的 release context。
- `release_readiness_trend_status(context)`：根据 coverage、benchmark、CI、status delta、panel change 等字段生成趋势状态。

这个模块只消费 registry dict，不读取文件，不写 artifact。

### `src/minigpt/maturity.py`

主文件通过别名导入：

```python
from minigpt.maturity_release_context import build_release_readiness_context as _release_readiness_context
```

主文件保留：

- `build_maturity_summary`
- 版本发现
- capability row 构建
- maturity summary 聚合
- phase timeline
- registry/request history context
- recommendations

拆分后主文件从 664 行降到 494 行。

## 数据流

```text
registry.json
  -> build_release_readiness_context
  -> release_readiness_context
  -> build_maturity_summary
  -> maturity summary
```

这说明 release context 模块是 maturity 的输入归一化层，不是新的 maturity report。

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\maturity.py src\minigpt\maturity_release_context.py
python -m pytest tests\test_coverage_governance_chain.py tests\test_maturity_artifacts.py -q -o cache_dir=runs\pytest-cache-v781-focused
```

结果 `3 passed`。覆盖点包括 maturity summary artifact 输出和 coverage governance chain 中 maturity/narrative 的联动，能确认 release context 拆分没有破坏 maturity 下游消费。

## 运行证据

本版运行证据归档在：

- `e/781/解释/说明.md`
- `e/781/解释/refactor-summary.html`
- `e/781/图片/v781-maturity-release-context-split.png`

这些证据用于记录拆分边界、行数变化和测试结果。

## 一句话总结

v781 把 maturity 的 release-readiness comparison 字段映射和趋势判定抽到独立模块，让 maturity 主文件回到项目成熟度矩阵和汇总编排职责。
