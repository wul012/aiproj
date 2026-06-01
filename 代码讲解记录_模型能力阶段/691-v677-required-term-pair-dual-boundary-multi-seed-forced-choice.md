# v677 required-term pair dual-boundary multi-seed forced-choice

## 本版目标和边界

v677 的目标是对 v676 三个 dual-boundary seed 的 checkpoint 运行 forced-choice 诊断，判断内部偏好是否和自由生成稳定性一样不稳定。

本版不训练新模型，不改 v676 seed stability，不新增新的 corpus mode。它只读取 v676 每个 seed 的 refresh sidecar，并复用已有 forced-choice diagnostic。

## 前置链路

v676 的 generation seed stability 结果是：

- seed `1535`: pair-full
- seed `2535`: no pair-full
- seed `3535`: pair-full

这说明 dual-boundary 还不是稳定 generation baseline。v677 检查的是另一层：即使自由生成没吐完整，模型内部是否仍然知道 `fixed=` 应该接 fixed、`loss=` 应该接 loss。

## 运行命令

```powershell
python -B scripts\run_model_capability_required_term_pair_refresh_forced_choice_diagnostic.py --report e\676\解释\model-capability-required-term-pair-dual-boundary-seed-stability\seed-reports\seed-1535 --label dual-boundary-seed-1535 --report e\676\解释\model-capability-required-term-pair-dual-boundary-seed-stability\seed-reports\seed-2535 --label dual-boundary-seed-2535 --report e\676\解释\model-capability-required-term-pair-dual-boundary-seed-stability\seed-reports\seed-3535 --label dual-boundary-seed-3535 --out-dir e\677\解释\model-capability-required-term-pair-dual-boundary-multi-seed-forced-choice --device cpu --require-pass --force
```

## 核心结果

- `expected_best_prompt_count=6`
- `fixed_prompt_expected_best_count=3`
- `loss_prompt_expected_best_count=3`
- `forced_choice_full_match_source_count=3`
- `best_internal_sources=dual-boundary-seed-1535, dual-boundary-seed-2535, dual-boundary-seed-3535`

这说明三个 seed 都在 forced-choice 内部评分层面通过了 fixed/loss 双 prompt。

## 链路意义

v677 解释了 v676 的部分稳定性：

- 不是所有 seed 都能自由生成 pair-full。
- 但所有 seed 的内部 forced-choice 都已经能区分 fixed/loss。

因此下一步应做 batch closeout 或 failure-boundary comparison，把结论写清楚：dual-boundary 修复了内部偏好稳定性，但生成表面仍不稳定。

## 测试与证据

测试运行：

```powershell
python -m pytest tests\test_model_capability_required_term_pair_refresh_forced_choice_diagnostic.py -q -o cache_dir=runs\pytest-cache-v677
```

运行证据：

- JSON/CSV/text/Markdown/HTML: `e/677/解释/model-capability-required-term-pair-dual-boundary-multi-seed-forced-choice/`
- 截图: `e/677/图片/v677-dual-boundary-multi-seed-forced-choice.png`
- 解释: `e/677/解释/说明.md`

一句话总结：v677 把 dual-boundary 的结论细分为“内部偏好稳定、自由生成不稳定”。
