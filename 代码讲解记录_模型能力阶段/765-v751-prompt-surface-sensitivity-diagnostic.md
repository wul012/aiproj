# v751 prompt-surface sensitivity diagnostic 代码讲解

## 本版目标和边界

v751 的目标是解释 v749 与 v750 之间的差异。v749 在训练脚本内观察到 pair-full，v750 独立 replay 后只得到 partial：exact heldout pair 不过，但 arrow surface 过。

本版不再训练，也不增加 rows。它做的是诊断归因：判断问题是否是 prompt surface sensitivity，并把 promotion blocked 的理由写成结构化证据。

## 前置路线

- v749：fixed-preserving transfer corpus 训练后，训练脚本内 pair-full observed。
- v750：独立 replay 发现 exact-heldout-pair 未通过，arrow-heldout-pair 通过。
- v751：把这两个事实合并，明确下一步不是 promotion，而是 exact-surface repair。

这条路线的价值在于防止项目把训练内瞬时观察过度解释成 checkpoint 成熟。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_diagnostic.py`
  - 诊断核心。
  - 输入 training run report 和 pair-probe replay report。
  - 输出 surface rows、checks、summary、decision 和 interpretation。
  - `surface_sensitivity_observed` 的定义是 required surface miss 且 optional surface pass。

- `src/minigpt/model_capability_required_term_pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_diagnostic_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
  - HTML 同时展示 summary cards、surface rows 和 input checks。

- `scripts/run_model_capability_required_term_pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_diagnostic.py`
  - CLI 入口。
  - 第一个参数是 v749 training run。
  - 第二个参数是 v750 pair-probe replay。

- `tests/test_model_capability_required_term_pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_diagnostic.py`
  - 覆盖 sensitivity found、ready for promotion guard、bad training source、locator、artifact 输出。

## 输入输出结构

输入一：v749 training run。

```text
decision=pair_readiness_training_pair_full_observed
summary.pair_full_observed=True
```

输入二：v750 pair-probe replay。

```text
decision=pair_readiness_fixed_preserving_transfer_pair_probe_replay_partial
summary.exact_heldout_pair_full=False
summary.required_all_pair_full=False
summary.pair_full_count=1
```

输出：v751 diagnostic。

```text
decision=pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_found
surface_sensitivity_observed=True
promotion_blocked=True
required_missed_surface_ids=['exact-heldout-pair']
optional_pair_full_surface_ids=['arrow-heldout-pair']
```

## 核心判断

v751 的关键判断不是“模型不会 pair-full”，而是更细：

```text
exact-heldout-pair: fixed=|loss= -> required_surface_missed
spaced-heldout-pair: fixed= | loss= -> optional_surface_missed
arrow-heldout-pair: fixed -> | loss -> -> pair_full_surface
```

所以结论是 prompt surface sensitive。模型对 arrow surface 有一定 pair-full 能力，但对 exact required surface 还不稳。

## checks 保护了什么

- `training_passed`
  - v749 training run 必须通过。

- `training_pair_full_observed`
  - 诊断只对已经观察到 pair-full 的训练结果成立。

- `replay_passed`
  - v750 replay 必须执行干净。

- `surface_rows_present`
  - replay 必须有 surface rows。

- `required_surface_present`
  - 至少要有 required prompt，否则无法判断 promotion 是否 blocked。

这些 checks 防止诊断在输入不完整时给出误导性路线建议。

## 测试和验证

Focused tests：

```powershell
python -m pytest tests\test_model_capability_required_term_pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_diagnostic.py -q -o cache_dir=runs\pytest-cache-v751-focused
```

结果为 5 个测试通过。

真实运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_diagnostic.py e\749\解释\model-capability-required-term-pair-readiness-fixed-preserving-transfer-training-run e\750\解释\model-capability-required-term-pair-readiness-fixed-preserving-transfer-pair-probe-replay --out-dir e\751\解释\model-capability-required-term-pair-readiness-fixed-preserving-transfer-prompt-surface-sensitivity-diagnostic --require-pass --force
```

Playwright 快照确认 HTML 中可见：

- `Decision pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_found`
- `Sensitive True`
- `Promotion blocked True`
- `Required missed exact-heldout-pair`
- `Optional passed arrow-heldout-pair`

截图位于：

```text
e/751/图片/v751-prompt-surface-sensitivity-diagnostic.png
```

## 证据链角色

v751 是一次收敛版诊断。它把“训练内看到 pair-full”和“独立 replay 不 fully ready”之间的矛盾变成明确后续路线：不要 promotion，不要扩大 broad rows，先做 minimal exact-surface repair plan。

一句话总结：v751 将 fixed-preserving transfer route 的问题定位到 exact prompt surface，为下一版最小修复计划提供依据。
