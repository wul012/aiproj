# v195 training evaluation timestamp helper consolidation 代码讲解

## 本版目标

v195 的目标是小范围收敛重复 timestamp helper。

此前这些模块都自己定义了同款函数：

```text
src/minigpt/benchmark_scorecard.py
src/minigpt/training_portfolio.py
src/minigpt/training_portfolio_batch.py
```

函数内容都是：

```text
datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
```

而项目已经有共享工具：

```text
src/minigpt/report_utils.py -> utc_now()
```

v195 把这三个训练评估链模块迁到共享 helper。它解决的是“重复小工具函数来源不统一”的问题，不改变业务行为。

本版明确不做：

- 不全仓迁移所有 `_utc_now()`。
- 不改变时间格式。
- 不改变 report schema。
- 不改 `generated_at`、`started_at`、`finished_at` 字段名。
- 不处理 `_dict/_list_of_dicts` 重复问题。

## 前置路线

v194 先拆了较大的 `training_run_evidence.py`，解决大文件膨胀。

v195 接着处理更小的 helper 重复：

```text
v194 large module split
 -> v195 timestamp helper consolidation
```

这个顺序比较稳：先处理维护压力最大的文件，再处理横向重复 helper。

## 关键文件

```text
src/minigpt/report_utils.py
src/minigpt/benchmark_scorecard.py
src/minigpt/training_portfolio.py
src/minigpt/training_portfolio_batch.py
tests/test_benchmark_scorecard.py
tests/test_training_portfolio.py
tests/test_training_portfolio_batch.py
c/195/图片
c/195/解释/说明.md
```

`report_utils.py` 是共享 helper 来源。

`benchmark_scorecard.py` 负责 benchmark scorecard 的 `generated_at`。

`training_portfolio.py` 负责 portfolio report 的 `generated_at`，以及执行 step 的 `started_at`、`finished_at`。

`training_portfolio_batch.py` 负责 batch plan/report 的 `generated_at`。

## 改动方式

`benchmark_scorecard.py` 原来导入：

```python
from datetime import datetime, timezone
```

并本地定义：

```python
def utc_now() -> str:
    ...
```

v195 改为：

```python
from .report_utils import utc_now
```

`training_portfolio.py` 和 `training_portfolio_batch.py` 改为：

```python
from minigpt.report_utils import utc_now
```

调用点保持不变：

```python
"generated_at": generated_at or utc_now()
started_at = utc_now()
finished_at = utc_now()
```

所以这版是 helper 来源迁移，不是字段逻辑重写。

## 为什么只迁这三个模块

项目里还有其他 `_utc_now()` 或 `utc_now()` 重复定义。但 v195 只处理训练评估链中的三个直接相关模块：

```text
benchmark scorecard
single training portfolio
batch training portfolio
```

原因是：

- 这三个模块最近 v189-v193 连续参与真实训练证据链。
- 这三个模块都有 focused tests。
- 改动可以保持在十几行以内。
- 不会引发跨 release/readiness/server/request-history 的大范围联动。

剩余模块可以后续按领域分批迁移。

## 输出契约

时间字段仍然是 UTC ISO 字符串：

```text
2026-05-17T00:00:00Z
```

涉及字段包括：

```text
benchmark_scorecard.generated_at
training_portfolio.generated_at
training_portfolio.step_results[].started_at
training_portfolio.step_results[].finished_at
training_portfolio_batch.generated_at
```

本版不改变这些字段的存在、名字或格式。

## 测试如何覆盖

focused tests 覆盖：

- `tests.test_benchmark_scorecard`
- `tests.test_training_portfolio`
- `tests.test_training_portfolio_batch`

这些测试保护 scorecard 构建、portfolio 计划、portfolio artifact 输出、batch dry-run、batch comparison 和 pair mode 输出。

此外，本版还做了 timestamp contract smoke，确认这些输出仍包含 `T` 和 `Z` 形式的 UTC 时间字符串。

## 运行证据

v195 运行截图放在：

```text
c/195/图片
c/195/解释/说明.md
```

关键证据包括：

```text
focused tests: pass
py_compile: pass
source scan: no local utc_now() in the three target modules
timestamp contract smoke: pass
full unittest: pass
source encoding: pass
docs check: pass
```

## 一句话总结

v195 把训练评估链上重复的 timestamp helper 收敛到 `report_utils.utc_now()`，在不改变输出契约的前提下减少了小型工具函数漂移。
