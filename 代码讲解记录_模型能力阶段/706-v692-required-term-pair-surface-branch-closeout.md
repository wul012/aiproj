# v692 required-term pair surface branch closeout

## 本版目标和边界

v692 的目标是关闭 v679-v691 的 required-term pair surface policy 分支。这个分支从一个具体 surface failure 出发，最后形成了稳定的 contextual decode aid，同时明确不能 promotion。v692 把这条链路压成一份 closeout 报告，便于后续回看。

本版不训练、不运行 generation、不新增变体。它是证据链收口，不是新能力实验。

## 前置链路

本版显式消费七个里程碑：

- v679：surface failure diagnostic。
- v681：surface policy replay。
- v684：surface policy leakage risk。
- v685：surface policy budget sweep。
- v688：surface variant replay。
- v690：surface baseline contrast。
- v691：surface route decision。

这七个节点覆盖问题定位、解码策略、风险边界、预算、变体鲁棒性、baseline 对照和路线决策。

## 关键文件

### `src/minigpt/model_capability_required_term_pair_surface_branch_closeout.py`

核心函数 `build_surface_branch_closeout()` 接收一个 `reports` 字典，要求包含：

```text
surface_failure
policy_replay
leakage_risk
budget_sweep
variant_replay
baseline_contrast
route_decision
```

它会生成：

- `milestone_rows`：每个里程碑的 version、status、decision、关键 value 和 finding。
- `summary.milestone_count`：真实运行是 7。
- `summary.contextual_decode_aid_ready`：真实运行是 `True`。
- `summary.promotion_allowed`：固定 `False`。
- `summary.recommended_next_route`：`minimal_prompt_surface_objective`。
- `interpretation.model_quality_claim`：`contextual_decode_aid_closed_branch`。

`locate_closeout_source()` 支持目录输入：CLI 传入目录时，会根据 source id 自动补齐对应 JSON 文件名。

### `scripts/run_model_capability_required_term_pair_surface_branch_closeout.py`

CLI 要求显式传入七个 source 参数。这个设计有意保持严格：closeout 不能偷偷漏掉某个关键证据。

### `tests/test_model_capability_required_term_pair_surface_branch_closeout.py`

测试覆盖：

- 七个 source 都 pass 时，分支被关闭为 contextual decode aid。
- 缺少 route decision 时失败。
- 五种输出格式正常渲染。

## 真实运行证据

命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_surface_branch_closeout.py --surface-failure e\679\解释\model-capability-required-term-pair-surface-failure-diagnostic --policy-replay e\681\解释\model-capability-required-term-pair-surface-policy-replay --leakage-risk e\684\解释\model-capability-required-term-pair-surface-policy-leakage-risk --budget-sweep e\685\解释\model-capability-required-term-pair-surface-policy-budget-sweep --variant-replay e\688\解释\model-capability-required-term-pair-surface-variant-replay --baseline-contrast e\690\解释\model-capability-required-term-pair-surface-baseline-contrast --route-decision e\691\解释\model-capability-required-term-pair-surface-route-decision --out-dir e\692\解释\model-capability-required-term-pair-surface-branch-closeout --require-pass --force
```

结果：

- `status=pass`
- `decision=required_term_pair_surface_branch_closed_as_contextual_decode_aid`
- `milestone_count=7`
- `contextual_decode_aid_ready=True`
- `promotion_allowed=False`
- `recommended_next_route=minimal_prompt_surface_objective`
- `model_quality_claim=contextual_decode_aid_closed_branch`

截图：

- `e/692/图片/v692-surface-branch-closeout.png`

说明：

- `e/692/解释/说明.md`

## 收口含义

v692 把本批次结论固定下来：当前分支不是失败，它产出了稳定可用的 contextual decode aid；但它也不是模型能力晋升，因为 non-leaking baseline 仍不稳定。后续如果继续追能力，应该启动 minimal-prompt objective，而不是继续扩 contextual variants。

## 验证

```powershell
python -m py_compile src\minigpt\model_capability_required_term_pair_surface_branch_closeout.py scripts\run_model_capability_required_term_pair_surface_branch_closeout.py tests\test_model_capability_required_term_pair_surface_branch_closeout.py
python -m pytest tests\test_model_capability_required_term_pair_surface_branch_closeout.py -q -o cache_dir=runs\pytest-cache-v692
```

结果：

- `py_compile` 通过。
- `3 passed in 0.10s`。

## 一句话总结

v692 将 v679-v691 收口为“稳定 contextual decode aid 已闭环，minimal prompt 模型能力仍待新 objective”的阶段结论。
