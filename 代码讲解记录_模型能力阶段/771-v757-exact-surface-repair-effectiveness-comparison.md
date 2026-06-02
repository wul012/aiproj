# v757 exact-surface repair effectiveness comparison 代码讲解

## 本版目标和边界

v757 的目标是判断 v753-v756 exact-surface repair route 是否有效。它不再训练，也不再添加 rows，而是把 v750 baseline replay 与 v756 repaired replay 做逐 surface 对比。

本版边界很明确：如果 exact surface 没改善，就关闭这条 near-exact repair route，避免继续堆类似 rows。

## 前置路线

- v750：fixed-preserving transfer checkpoint 独立 replay partial。
- v753-v755：新增 near-exact rows、物化、训练。
- v756：exact-surface repair checkpoint 独立 replay 仍 partial。
- v757：对比 v750 和 v756，确认是否有真实改善。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_readiness_exact_surface_repair_effectiveness_comparison.py`
  - 比较核心。
  - 输入 baseline replay 和 repaired replay。
  - 按 `spec_id` 对齐 exact/spaced/arrow rows。
  - 计算 default hit delta 和 pair-full delta。
  - 输出 effective、partial improvement、ineffective stop route 三类 decision。

- `src/minigpt/model_capability_required_term_pair_readiness_exact_surface_repair_effectiveness_comparison_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
  - HTML 展示 summary cards、comparison rows 和 checks。

- `scripts/run_model_capability_required_term_pair_readiness_exact_surface_repair_effectiveness_comparison.py`
  - CLI 入口。
  - 第一个参数是 v750 baseline replay。
  - 第二个参数是 v756 repaired replay。

- `tests/test_model_capability_required_term_pair_readiness_exact_surface_repair_effectiveness_comparison.py`
  - 覆盖 ineffective stop、partial improvement、ready for promotion guard、locator、artifact 输出。

## 输入输出结构

输入一：v750 baseline replay。

```text
exact_heldout_pair_full=False
pair_full_count=1
```

输入二：v756 repaired replay。

```text
exact_heldout_pair_full=False
pair_full_count=1
```

输出：v757 comparison。

```text
decision=pair_readiness_exact_surface_repair_ineffective_stop_route
repair_effective=False
repair_ineffective=True
exact_default_hit_delta=0
exact_pair_full_delta=0
```

## comparison rows 解释

v757 对齐三种 surface：

| surface | before full | after full | before hits | after hits | delta |
| --- | --- | --- | --- | --- | --- |
| exact-heldout-pair | False | False | 1 | 1 | 0 |
| spaced-heldout-pair | False | False | 1 | 1 | 0 |
| arrow-heldout-pair | True | True | 2 | 2 | 0 |

结果没有任何 improvement rows，也没有 regressed rows。问题不是变坏，而是无效。

## 测试和验证

Focused tests：

```powershell
python -m pytest tests\test_model_capability_required_term_pair_readiness_exact_surface_repair_effectiveness_comparison.py -q -o cache_dir=runs\pytest-cache-v757-focused
```

结果为 5 个测试通过。

真实运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_exact_surface_repair_effectiveness_comparison.py e\750\解释\model-capability-required-term-pair-readiness-fixed-preserving-transfer-pair-probe-replay e\756\解释\model-capability-required-term-pair-readiness-exact-surface-repair-pair-probe-replay --out-dir e\757\解释\model-capability-required-term-pair-readiness-exact-surface-repair-effectiveness-comparison --require-pass --force
```

Playwright 快照确认 HTML 中可见：

- `Decision pair_readiness_exact_surface_repair_ineffective_stop_route`
- `Effective False`
- `Ineffective True`
- `Exact hit delta 0`
- exact/spaced/arrow comparison rows delta 均为 0。

截图位于：

```text
e/757/图片/v757-exact-surface-repair-effectiveness-comparison.png
```

## 证据链角色

v757 是路线止损层。它让项目不再继续沿着 near-exact bridge rows 堆数据，而是转向 objective/decoding alternatives。

一句话总结：v757 用逐 surface 对比证明 exact-surface repair route 无效，应关闭该路线并寻找新方向。
