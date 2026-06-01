# v685 required-term pair surface policy budget sweep

## 本版目标和边界

v685 的目标是对 v682 选出的 `pair_context_prefix` 做 continuation budget sweep。v684 已经明确它只是 contextual decode aid，不允许 promotion；v685 延续这个边界，进一步确认它需要多少 `max_new_tokens` 才能稳定覆盖 fixed/loss。

本版不训练新 checkpoint，不修改 corpus，不改变 v682 selected policy，也不把稳定 budget 解释成模型无条件能力。它只在既有三颗 dual-boundary checkpoint 上运行真实生成，把 budget 与 pair-full 稳定性对应起来。

## 前置链路

- v676 提供三颗 dual-boundary seed 的 checkpoint/tokenizer 和 seed-level replay 证据。
- v682 选择 `pair_context_prefix`，原因是它比 `dual_boundary_sentence` 更短，且不复用训练边界句。
- v684 记录这个策略的 contextual-anchor leakage risk，并保留 `promotion_allowed=False`。

v685 在这个基础上问一个工程问题：如果这个策略只能作为 decode aid，那么最小稳定生成预算是多少。

## 关键文件

### `src/minigpt/model_capability_required_term_pair_surface_policy_budget_sweep.py`

这是核心模块。它复用 v681 的 replay builder，而不是重新复制一套 generation 逻辑。

主要函数：

- `locate_budget_sweep_stability_source()`：支持目录或 JSON 输入，定位 v676 seed stability 报告。
- `locate_budget_sweep_selector_source()`：支持目录或 JSON 输入，定位 v682 selector 报告。
- `build_surface_policy_budget_sweep()`：读取 selected policy，按 budgets 多次调用 v681 replay builder，并汇总 budget-level 结果。
- `write_surface_policy_budget_sweep_outputs()`：输出 JSON/CSV/text/Markdown/HTML 五件套。

核心字段：

- `settings.token_budgets`：本次 sweep 的预算列表，真实运行是 `[4, 8, 12, 16]`。
- `selected_policy`：完整保留 `pair_context_prefix` 的模板和泄漏等级。
- `budget_rows`：每个 budget 的 seed 数、case 数、hit 数、pair-full seed 数和稳定状态。
- `case_rows`：带 `max_new_tokens` 的逐 case 生成结果，便于后续追溯是哪颗 seed、哪个 term 命中或失败。
- `summary.minimal_stable_budget`：最小稳定预算，真实运行是 `8`。
- `interpretation.model_quality_claim`：`contextual_decode_budget_candidate`，强调这仍是解码辅助。

### `scripts/run_model_capability_required_term_pair_surface_policy_budget_sweep.py`

CLI 接收：

```text
stability selector --budgets 4 8 12 16
```

它会解析输入目录、清理输出目录、调用 builder、写出五种产物，并在 `--require-pass` 下检查执行状态。注意 `--require-pass` 只表示 sweep 执行成功，不表示每个 budget 都稳定。

### `tests/test_model_capability_required_term_pair_surface_policy_budget_sweep.py`

测试用 fake checkpoint/tokenizer 文件和 fake generator 覆盖三件事：

- budget 4 不稳定、budget 8/12 稳定时，`minimal_stable_budget=8`。
- selector 输入失败时，报告 status 失败且 `require-pass` 会返回退出码 1。
- JSON/CSV/text/Markdown/HTML 五件套可以正常渲染。

这类测试保护的是 budget 归纳逻辑，不伪装成真实模型质量测试；真实模型生成由归档命令负责。

## 真实运行证据

运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_surface_policy_budget_sweep.py e\676\解释\model-capability-required-term-pair-dual-boundary-seed-stability e\682\解释\model-capability-required-term-pair-surface-policy-selector --out-dir e\685\解释\model-capability-required-term-pair-surface-policy-budget-sweep --budgets 4 8 12 16 --temperature 0.2 --top-k 1 --device cpu --require-pass --force
```

结果：

- `status=pass`
- `decision=required_term_pair_surface_policy_budget_stable_window_found`
- `stable_budgets=[8, 12, 16]`
- `minimal_stable_budget=8`
- `model_quality_claim=contextual_decode_budget_candidate`

预算明细：

- budget 4：`hit_case_count=3`，`pair_full_seed_count=0`，不稳定。
- budget 8：`hit_case_count=6`，`pair_full_seed_count=3`，稳定。
- budget 12：`hit_case_count=6`，`pair_full_seed_count=3`，稳定。
- budget 16：`hit_case_count=6`，`pair_full_seed_count=3`，稳定。

截图归档：

- `e/685/图片/v685-surface-policy-budget-sweep.png`

说明归档：

- `e/685/解释/说明.md`

## 为什么这个版本不是“小文档”

v685 做了真实生成 sweep。每个 budget 都会经过 v681 replay builder，读取三颗 checkpoint/tokenizer，对 fixed/loss 两个 term 各跑一次，所以总计 4 个 budget、3 个 seed、2 个 term，形成 24 个真实 generation case。

这个版本的价值在于把“selected policy 有用”进一步变成“在 8 token 以上才稳定”。后续如果做 variant replay，默认 budget 就不应该再拍脑袋用 12，而应该用 v685 证明过的最小稳定值 8。

## 验证

本版完成后运行：

```powershell
python -m py_compile src\minigpt\model_capability_required_term_pair_surface_policy_budget_sweep.py scripts\run_model_capability_required_term_pair_surface_policy_budget_sweep.py tests\test_model_capability_required_term_pair_surface_policy_budget_sweep.py
python -m pytest tests\test_model_capability_required_term_pair_surface_policy_budget_sweep.py -q -o cache_dir=runs\pytest-cache-v685
```

结果：

- `py_compile` 通过。
- `3 passed in 0.12s`。

## 一句话总结

v685 用真实三 seed 生成证明 `pair_context_prefix` 的最小稳定 continuation budget 是 8，为后续 surface variant replay 提供了可复核的默认预算。
