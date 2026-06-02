# v784 training portfolio summary split

## 本版目标和边界

v784 是维护拆分版本，不新增 training portfolio 功能，不改变 comparison report 的字段，也不改变 artifact writer、review recommendation 或 CLI 行为。本版只把 `training_portfolio_comparison.py` 中“读取单个 portfolio 的上下游 artifact 并归一化摘要”的逻辑拆到独立模块。

本版不改变：

- `build_training_portfolio_comparison(...)` 的输入输出。
- JSON/CSV/Markdown/HTML artifact 输出路径和字段。
- baseline 选择、delta 计算、recommendation 规则。
- 现有测试入口和 CLI 使用方式。

## 为什么这一刀有必要

`training_portfolio_comparison.py` 原来同时做两类事情：

- 前置摘要：解析每个 portfolio report，读取 run manifest、benchmark scorecard、dataset card、maturity narrative、generation quality 等 artifact，并把它们压成可比较字段。
- 横向比较：选择 baseline，计算 score/loss/token/artifact/CI regression delta，生成 summary 和 review 建议。

这两件事都合理，但混在一个 641 行文件里会让维护成本变高。后续如果 artifact schema 增加字段，开发者要穿过 baseline/delta/recommendation 大段代码；如果比较规则变化，也容易误碰 artifact 读取逻辑。

v784 的拆分把“单个 portfolio 摘要构造”收束成独立模块，让主模块更像比较协调器。

## 关键文件

### `src/minigpt/training_portfolio_comparison_portfolio.py`

新增模块，公开：

```python
build_training_portfolio_summary(report, name, index)
```

它的输入是一个 training portfolio report dict，以及外层给定的展示名和序号。它负责：

- 解析 `_source_path` 和 `project_root`。
- 读取 `execution` 与 `artifacts`。
- 根据 artifact 相对路径或绝对路径解析真实文件位置。
- 尝试读取 benchmark scorecard、dataset card、maturity narrative、run manifest、eval suite、generation quality。
- 提取 overall score、loss、token count、dataset readiness、generation quality、maturity release-readiness regression 等字段。
- 输出单个 portfolio summary dict，供主比较模块消费。

这个模块不做 baseline 选择，不比较多个 portfolio，也不生成最终 report artifact。

### `src/minigpt/training_portfolio_comparison.py`

主模块现在导入：

```python
from minigpt.training_portfolio_comparison_portfolio import build_training_portfolio_summary as _portfolio_summary
```

拆分后它保留：

- `load_training_portfolio`
- `build_training_portfolio_comparison`
- `_portfolio_delta`
- `_comparison_summary`
- `_select_baseline`
- `_delta_explanation`
- CI reason counts merge 和 detail formatting

它现在更清楚地承担“多 portfolio 横向比较”职责，而不再直接展开所有 artifact 读取细节。文件行数从 641 行降到 403 行。

## 数据流

```text
training_portfolio.json
  -> load_training_portfolio
  -> build_training_portfolio_summary
       -> read artifact JSON
       -> normalize one portfolio summary
  -> _portfolio_delta
  -> _comparison_summary
  -> review recommendations
  -> JSON/CSV/Markdown/HTML outputs
```

这条链路的关键是：v784 只移动了 `build_training_portfolio_summary` 所在层级，没有改变 summary 字段如何被后续比较层消费。

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\training_portfolio_comparison.py src\minigpt\training_portfolio_comparison_portfolio.py
python -m pytest tests\test_training_portfolio_comparison.py tests\test_training_portfolio_comparison_artifacts.py tests\test_training_portfolio_comparison_review.py -q -o cache_dir=runs\pytest-cache-v784-focused
python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-v784
git diff --check
```

结果：

- focused tests: `15 passed`
- source encoding: `status=pass`
- diff check: pass

这些测试覆盖 comparison report 构造、artifact writer 接线、legacy exports 和 review recommendation。也就是说，拆出 summary normalization 后，外层 comparison artifact 仍能按原契约生成。

## 运行证据

本版运行证据归档在：

- `e/784/解释/说明.md`
- `e/784/解释/refactor-summary.html`
- `e/784/图片/v784-training-portfolio-summary-split.png`

HTML 证据页展示了主文件行数变化、新模块职责、focused test 结果和 source encoding 状态。截图用于证明本版归档页面可打开、核心指标可见。

## 一句话总结

v784 把 training portfolio comparison 的输入摘要层拆出，让 artifact 读取和横向比较各守一层职责，为后续继续优化 portfolio 比较链路打下更干净的边界。
