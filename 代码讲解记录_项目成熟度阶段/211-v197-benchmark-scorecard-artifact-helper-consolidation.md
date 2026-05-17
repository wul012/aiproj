# v197 benchmark scorecard artifact helper consolidation 代码讲解

## 本版目标

v197 是 v196 的同一条质量路线，但边界放在 `benchmark_scorecard_artifacts.py`。

v196 已经把 `benchmark_scorecard.py` 的本地 `_dict()` 和重复 `_list_of_dicts()` 收回到 `report_utils`。本版继续处理 artifact writer 中残留的同类 helper，让 scorecard 构建入口和 artifact 输出入口使用同一套 dict/list normalization 规则。

本版不改 benchmark 评分、不改 scorecard schema、不新增 HTML 样式，也不做全仓库 helper 批量迁移。

## 为什么要改

`benchmark_scorecard_artifacts.py` 负责把 scorecard 写成 JSON、CSV、Markdown 和 HTML。它读取的结构包括：

- `components`
- `drilldowns.task_type`
- `drilldowns.difficulty`
- `rubric_scores.cases`
- `case_scores`
- `registry_context`

这些字段来自 JSON 风格的证据对象，读取时需要防御不确定类型。改动前 artifact writer 有自己的 `_dict()` 和 `_list_of_dicts()`：

- `_dict()` 和 `report_utils.as_dict()` 重复。
- `_list_of_dicts()` 的语义是 all-or-nothing：只有当整个列表全是 dict 时才返回列表，否则返回空列表。

这和 v196 后 scorecard 构建层使用的 `report_utils.list_of_dicts()` 不一致。共享 helper 的语义是过滤非 dict 项并保留有效 dict 行，更适合 artifact 导出，因为一个坏行不应该让整张 component/drilldown/rubric 表消失。

## 关键文件

### `src/minigpt/benchmark_scorecard_artifacts.py`

本版新增：

```python
from .report_utils import as_dict as _dict
from .report_utils import list_of_dicts as _list_of_dicts
```

并删除本地：

```python
def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return value if isinstance(value, list) and all(isinstance(item, dict) for item in value) else []


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
```

调用点没有改名，仍然用 `_dict()` 和 `_list_of_dicts()`，这样 artifact writer 的渲染逻辑保持稳定，改动集中在 helper 来源和 helper 语义上。

### `tests/test_benchmark_scorecard_artifacts.py`

新增测试 `test_artifacts_filter_non_dict_rows_after_helper_consolidation()`。

测试构造一个 scorecard，然后在三个 artifact 表输入中混入字符串：

- `components` 混入 `"ignored-component"`
- `drilldowns.task_type` 混入 `"ignored-task-row"`
- `rubric_scores.cases` 混入 `"ignored-rubric-row"`

再调用 `write_benchmark_scorecard_outputs()`，断言：

- component CSV 仍包含 `generation_quality,Generation Quality,warn`
- drilldown CSV 仍包含 `task_type,qa,warn,80.0000`
- rubric CSV 仍包含 `qa-hard,qa,hard,warn,72.5000`
- Markdown 仍包含 `Generation Quality`
- 三个 ignored 字符串都没有出现在对应 CSV 中

这说明 artifact writer 现在能跳过坏行，同时保留有效行。

## 运行流程

1. `write_benchmark_scorecard_outputs()` 调用 JSON、CSV、drilldown CSV、rubric CSV、Markdown、HTML 写出函数。
2. CSV writer 通过 `_list_of_dicts(scorecard.get("components"))` 遍历 component 行。
3. Drilldown writer 通过 `_dict(scorecard.get("drilldowns"))` 获取分组对象，再通过 `_list_of_dicts()` 获取 task/difficulty 行。
4. Rubric writer 通过 `_dict(scorecard.get("rubric_scores")).get("cases")` 获取 case 行。
5. Markdown/HTML renderer 也沿用同一 helper 语义。

因此，本版统一的是“artifact 输出层如何看待混合列表”的行为。

## 行为变化

这版有一个有意的轻微行为改进：

- 旧行为：列表里只要有非 dict 项，整个列表视为无效，导出空表。
- 新行为：过滤非 dict 项，保留 dict 行继续导出。

这个行为更符合报告输出的容错目标，也和 v196 后 scorecard 构建层的 mixed-list 处理一致。

## 验证

本版验证包括：

- focused tests：`tests.test_benchmark_scorecard_artifacts` 和 `tests.test_benchmark_scorecard`。
- syntax：`benchmark_scorecard_artifacts.py`、`report_utils.py`、`test_benchmark_scorecard_artifacts.py` 编译通过。
- contract smoke：临时 mixed-row scorecard 写出 CSV/Markdown，确认有效行保留、无效字符串跳过。
- source encoding：`scripts/check_source_encoding.py` 通过。
- full unittest：全量 `python -B -m unittest discover -s tests` 通过。

截图证据放在 `c/197/图片`，说明文件放在 `c/197/解释/说明.md`。

## 边界说明

本版不处理其他模块中的 `_dict()`、`_list_of_dicts()`，也不处理测试文件的 `sys.path.insert()` 样板。后者如果要优化，应该先确认当前 `unittest` 入口是否能通过统一测试加载方式受益，否则 `conftest.py` 对 `unittest` 并没有直接作用。

一句话总结：v197 让 benchmark scorecard artifact writer 使用共享 normalization helper，并把 artifact 导出从 all-or-nothing 行为推进到更稳的“过滤坏行、保留好行”。
