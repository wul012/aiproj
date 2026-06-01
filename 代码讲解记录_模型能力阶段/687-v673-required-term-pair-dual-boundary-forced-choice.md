# v673 required-term pair dual-boundary forced-choice

## 本版目标和边界

v673 对 v672 dual-boundary checkpoint 做 forced-choice 诊断，确认内部偏好是否和自由生成结果一致。

本版不训练新模型，不做多 seed 结论；它只验证 v672 单 seed 的内部信号。

## 前置链路

v672 已经达到：

- `pair_full_observed=True`
- default profile pair-full
- suppress_newline_tokens profile pair-full

但这只能说明生成文本里出现了 fixed/loss。v673 检查的是 teacher-forced candidate scoring：给定 `fixed=` 和 `loss=`，模型内部是否更偏好正确 term。

## 运行命令

```powershell
python -B scripts\run_model_capability_required_term_pair_refresh_forced_choice_diagnostic.py --report e\672\解释\model-capability-required-term-pair-dual-boundary-seed-3535 --label dual-boundary-seed-3535 --out-dir e\673\解释\model-capability-required-term-pair-dual-boundary-forced-choice --device cpu --require-pass --force
```

## 核心结果

- `decision=refresh_forced_choice_internal_pair_match`
- `expected_best_prompt_count=2`
- `forced_choice_full_match_source_count=1`
- `best_internal_sources=dual-boundary-seed-3535`

这说明：

- `fixed=` prompt 内部更偏好 fixed。
- `loss=` prompt 内部更偏好 loss。
- v672 的 pair-full 不是纯输出偶然，而有内部评分支撑。

## 链路角色

v673 是 v672 从“生成正信号”升级为“生成 + 内部双信号”的关键证据。

下一步必须做 alignment comparison，把它和 v630、v640、v660-v663 等历史路线放在同一张矩阵里。如果矩阵显示 aligned pair-full，才能进入 route decision 和 seed stability。

## 证据归档

- JSON/CSV/text/Markdown/HTML: `e/673/解释/model-capability-required-term-pair-dual-boundary-forced-choice/`
- 截图: `e/673/图片/v673-dual-boundary-forced-choice.png`
- 解释: `e/673/解释/说明.md`

一句话总结：v673 确认 explicit dual-boundary checkpoint 在单 seed 上同时具备生成 pair-full 和内部 pair match。
