# v787 pair capacity sweep summary split

## 本版目标和边界

v787 是维护拆分版本，不新增 pair capacity sweep 功能，不改变 report schema，不改变训练参数、不改变 corpus 生成，也不改变 generation probe 行为。本版只把 `model_capability_required_term_pair_capacity_sweep.py` 中的 summary、decision 和 interpretation helper 拆到独立模块。

本版不改变：

- `build_model_capability_required_term_pair_capacity_sweep(...)` 的输入输出。
- 默认 capacity variants。
- pair 选择逻辑。
- `_run_pair_capacity_variant` 中的 corpus 写入、训练调用和 generation probe。
- `resolve_exit_code`。

## 为什么这一刀有必要

capacity sweep 文件同时包含两类逻辑：

- 有副作用的实验编排：写 capacity corpus、调用训练函数、读取 checkpoint、生成 probe row。
- 无副作用的解释归纳：统计 variant/pair hit、判断 capacity sweep decision、生成 source baseline、model quality claim、interpretation reason 和 next action。

这两类逻辑混在一个 616 行文件里，会让维护者在改解释口径时穿过训练副作用代码，也会让训练编排变更时误碰 summary 字段。v787 选择拆无副作用层，风险更低，也更便于测试定位。

## 关键文件

### `src/minigpt/model_capability_required_term_pair_capacity_sweep_summary.py`

新增模块承接：

- `summarize_required_term_pair_capacity_sweep`
- `summarize_capacity_variant_probe_rows`
- `summarize_pair_capacity_sweep`
- `capacity_sweep_decision`
- `source_baseline`
- `model_quality_claim`
- `interpretation_reason`
- `next_action`

它只消费 pairs、variants、capacity rows、probe rows 和 source summary，不读写文件，不调用训练，不生成 checkpoint。

### `src/minigpt/model_capability_required_term_pair_capacity_sweep.py`

主模块现在导入 summary 模块的函数，并继续负责：

- 定位 seed-stability source report。
- 生成默认 capacity variants。
- 选择 fragile pair。
- 归一化 variant 配置。
- 调用 `_run_pair_capacity_variant`。
- 组织最终 report。

拆分后该文件从 616 行降到 417 行。

## 数据流

```text
seed-stability report
  -> select fragile pairs
  -> normalize capacity variants
  -> _run_pair_capacity_variant
       -> write corpus
       -> train checkpoint
       -> generation probe rows
  -> capacity_sweep_summary helpers
       -> variant pair summaries
       -> pair capacity summaries
       -> decision / interpretation
  -> final capacity sweep report
```

v787 的边界是“副作用编排”和“无副作用归纳”分离。

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\model_capability_required_term_pair_capacity_sweep.py src\minigpt\model_capability_required_term_pair_capacity_sweep_summary.py
python -m pytest tests\test_model_capability_required_term_pair_capacity_sweep.py -q -o cache_dir=runs\pytest-cache-v787-focused
python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-v787
git diff --check
```

结果：

- focused tests: `4 passed`
- source encoding: `status=pass`
- diff check: pass

这些测试覆盖 recovered full-hit、partial only、training failure、outputs rendering 等场景。它们保护了 summary/decision 拆出后最终 report 仍保持原判断。

## 运行证据

本版运行证据归档在：

- `e/787/解释/说明.md`
- `e/787/解释/refactor-summary.html`
- `e/787/图片/v787-pair-capacity-sweep-summary-split.png`

HTML 证据页展示了拆分后的职责边界、行数变化和测试结果。截图用于确认归档页可打开，核心指标可见。

## 一句话总结

v787 把 pair capacity sweep 的解释归纳层从训练编排主文件中拆出，让实验副作用和决策摘要各自可维护。
