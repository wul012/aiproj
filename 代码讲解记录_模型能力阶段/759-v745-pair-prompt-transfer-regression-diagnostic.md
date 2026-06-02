# v745 pair prompt transfer regression diagnostic 代码讲解

## 本版目标和边界

v745 的目标是把 v738、v740、v744 三段证据合并成一份可复核诊断：direct-completion surface 曾经在 direct probes 上 pair-full，但 pair-probe replay 不 ready；pair prompt transfer patch 训练后不仅没解决 pair prompt，还把 direct hits 从 2 降到 1。

本版解决的是路线判断问题。它不重新训练，不新增 rows，不改变模型配置；它只读取已有 JSON 报告，给出 full surrogate transfer patch route 是否继续的判断。

## 前置路线

v738 给出正向 direct 证据：`fixed=` 和 `loss=` 都能命中。

v740 给出负向 pair-probe 证据：exact `fixed=|loss=` 等 pair prompt surfaces 不能迁移，所以 v738 不能直接 promotion。

v744 给出 transfer 负证据：在 v742-v743 的 surrogate transfer rows 上训练后，只剩 `loss` 命中，`fixed` 被挤掉。

v745 把这三件事放到一个 contract-style diagnostic 中，避免后续继续沿着已回退路线堆数据。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_readiness_pair_prompt_transfer_regression_diagnostic.py`
  - 核心诊断逻辑。
  - 读取三份 report：direct-completion training、pair-probe replay、pair-transfer training。
  - 生成 `diagnostic_rows`、`summary`、`decision` 和 `interpretation`。
  - 保持文件职责单一，没有把 HTML/CSV 渲染放进核心逻辑。

- `src/minigpt/model_capability_required_term_pair_readiness_pair_prompt_transfer_regression_diagnostic_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
  - 负责把诊断 row 渲染成表格，并把关键 summary 字段显示到 HTML cards。

- `scripts/run_model_capability_required_term_pair_readiness_pair_prompt_transfer_regression_diagnostic.py`
  - CLI 入口。
  - 三个显式输入参数分别对应 v738、v740、v744。
  - `--require-pass` 只要求诊断输入完整，不要求模型能力成功。

- `tests/test_model_capability_required_term_pair_readiness_pair_prompt_transfer_regression_diagnostic.py`
  - Focused tests。
  - 覆盖回归路线关闭、transfer pair-full candidate、缺 checkpoint 失败、五种 artifact 输出。

## 核心数据结构

`diagnostic_rows` 有三类 evidence：

- `direct-completion-surface`
  - kind 为 `training`。
  - 从 v738 training report 提取 default profile 的 hit/miss。
  - v745 真实输入中 hits 是 `["fixed", "loss"]`，pair-full 为 `True`。

- `direct-completion-pair-probe`
  - kind 为 `pair_probe_replay`。
  - 从 v740 replay summary 提取 `exact_heldout_pair_full`。
  - v745 真实输入中 pair probe 为 `False`。

- `pair-prompt-transfer`
  - kind 为 `training`。
  - 从 v744 training report 提取 default profile 的 hit/miss。
  - v745 真实输入中 hits 是 `["loss"]`，missed 是 `["fixed"]`。

`summary` 的关键字段：

- `direct_completion_default_hit_count=2`
- `transfer_default_hit_count=1`
- `transfer_hit_delta_from_direct=-1`
- `fixed_regressed=True`
- `pair_probe_exact_heldout_pair_full=False`
- `transfer_route_closed=True`

这些字段合起来支持本版 decision：`pair_readiness_pair_prompt_transfer_regressed_stop_route`。

## 决策规则

如果任一输入 report 不是 `pass`，或者训练 report 没有 checkpoint，诊断 `status=fail`，decision 为 `fix_pair_prompt_transfer_regression_diagnostic_inputs`。

如果 transfer training 已经 pair-full，decision 为 `pair_readiness_pair_prompt_transfer_candidate_found`，但仍要继续 stricter replay 和 multi-seed stability。

如果 transfer hit count 比 direct-completion 低，或者 direct 命中过的 term 在 transfer 中消失，decision 为 `pair_readiness_pair_prompt_transfer_regressed_stop_route`。

v745 真实输入触发的是第三种：`fixed` 从命中变成漏掉，所以路线关闭。

## 测试和验证

Focused tests：

```powershell
python -m pytest tests\test_model_capability_required_term_pair_readiness_pair_prompt_transfer_regression_diagnostic.py -q
```

结果为 4 个测试通过。测试覆盖：

- 回归时关闭 transfer route。
- transfer 已 pair-full 时标记 candidate。
- 缺失 checkpoint 时 fail。
- JSON/CSV/TXT/Markdown/HTML 输出完整。

真实运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_pair_prompt_transfer_regression_diagnostic.py --direct-completion-training e\738\解释\model-capability-required-term-pair-readiness-direct-completion-surface-training-run\model_capability_required_term_pair_readiness_training_run.json --pair-probe-replay e\740\解释\model-capability-required-term-pair-readiness-direct-completion-pair-probe-replay\model_capability_required_term_pair_readiness_direct_completion_pair_probe_replay.json --transfer-training e\744\解释\model-capability-required-term-pair-readiness-pair-prompt-transfer-training-run\model_capability_required_term_pair_readiness_training_run.json --out-dir e\745\解释\model-capability-required-term-pair-readiness-pair-prompt-transfer-regression-diagnostic --require-pass --force
```

核心输出：

```text
decision=pair_readiness_pair_prompt_transfer_regressed_stop_route
transfer_hit_delta_from_direct=-1
fixed_regressed=True
transfer_route_closed=True
```

Playwright 截图证明 HTML 报告可读，并且关键统计字段全部可见。

## 证据链角色

v745 是一个路线收口版本。它没有增加训练功能，但防止项目在已经回退的 transfer patch 上继续浪费版本。

下一步不应该再扩大 full surrogate transfer rows；更合理的是做 fixed-preserving 的轻量目标，先解释为什么 v744 的 `fixed=` 续写变成了 `loss...`。

一句话总结：v745 把 v738/v740/v744 三段证据合成路线诊断，确认 full surrogate pair-transfer patch route 应停止。
