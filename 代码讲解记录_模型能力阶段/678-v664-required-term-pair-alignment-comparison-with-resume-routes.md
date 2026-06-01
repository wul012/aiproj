# v664 required-term pair alignment comparison with resume routes

## 本版目标和边界

v664 目标是把 v660、v662 两条真实 checkpoint continuation 路线放回 generation/internal alignment comparison，和 v621、v630、v640 的旧锚点一起比较。

它解决的是路线判断问题：resume 已经能执行，但是否值得继续沿着 naive continuation 分支推进，需要同一套矩阵证据来回答。本版不训练新模型，也不宣称模型质量提升。

## 前置链路

前置 evidence 来自三类能力：

- v630: `loss-internal-joint-cycle`，自由生成首次达到 pair-full，但 forced-choice 内部只有 partial match。
- v640/v641: `joint-cycle-internal-repair`，内部 forced-choice 达到 pair match，但自由生成退化。
- v660-v663: 从 v630 checkpoint 继续训练到 internal-repair / light-merge，两条 resume 路线都没有恢复 aligned pair-full。

## 关键修改

### `src/minigpt/model_capability_required_term_pair_generation_internal_alignment_comparison.py`

本版修正 `_issues()` 的边界：`internal_expected_best_terms=[]` 不再是输入错误。

这个改动很关键，因为 v663 的 `refresh_forced_choice_not_recovered` 是一个真实诊断结果，而不是损坏报告。如果比较器把“没有内部命中”当作坏输入，它就无法表达失败路线，只会阻断后续路线判断。

修正后，比较器仍然校验：

- refresh report status 必须为 `pass`
- training status 必须为 `pass`
- checkpoint 必须存在
- forced-choice status 必须为 `pass`

但内部命中数量可以为 0，并作为 `internal_missed_terms=["fixed", "loss"]` 进入矩阵。

### `tests/test_model_capability_required_term_pair_generation_internal_alignment_comparison.py`

新增测试 `test_no_internal_expected_best_terms_is_a_valid_failed_route`。

它构造 `generation_terms=["loss"]`、`internal_terms=[]` 的路线，断言：

- report `status=pass`
- `failed_count=0`
- `internal_expected_best_terms=[]`
- `alignment_class=partial_tradeoff`

这个测试保护的是负样本可比较性：失败路线不能被误判为输入损坏。

## 运行证据

本版运行：

```powershell
python -B scripts\run_model_capability_required_term_pair_generation_internal_alignment_comparison.py --source loss-internal-first-token e\621\解释\model-capability-required-term-pair-loss-internal-first-token-seed-3535 e\624\解释\model-capability-required-term-pair-loss-internal-forced-choice-diagnostic --source loss-internal-joint-cycle e\630\解释\model-capability-required-term-pair-loss-internal-joint-cycle-seed-3535 e\631\解释\model-capability-required-term-pair-loss-internal-joint-cycle-forced-choice --source joint-cycle-internal-repair e\640\解释\model-capability-required-term-pair-joint-cycle-internal-repair-seed-3535 e\641\解释\model-capability-required-term-pair-joint-cycle-internal-repair-forced-choice --source v630-internal-repair-resume e\660\解释\model-capability-required-term-pair-v630-to-internal-repair-resume-seed-3535 e\661\解释\model-capability-required-term-pair-v630-internal-repair-resume-forced-choice --source v630-light-merge-resume e\662\解释\model-capability-required-term-pair-v630-light-merge-resume-seed-3535 e\663\解释\model-capability-required-term-pair-v630-light-merge-resume-forced-choice --out-dir e\664\解释\model-capability-required-term-pair-alignment-comparison-with-resume-routes --require-pass --force
```

核心输出：

- `status=pass`
- `decision=keep_generation_pair_full_and_repair_internal_preference`
- `generation_pair_full_count=1`
- `internal_pair_full_count=2`
- `aligned_pair_full_count=0`
- `best_source_labels=loss-internal-first-token,loss-internal-joint-cycle`

## 链路角色

v664 的角色不是选择新 checkpoint，而是把 resume branch 放回同一张路线图里。

结果说明：

- v630 仍是自由生成 pair-full 的主要锚点。
- v640 仍是内部 pair-full 的主要锚点。
- v660/v662 两条 continuation 没有成为 aligned candidate。
- 下一步应做 route decision / closeout，而不是继续盲目加 continuation 变体。

## 测试覆盖

本版运行 targeted test：

```powershell
python -m pytest tests\test_model_capability_required_term_pair_generation_internal_alignment_comparison.py -q -o cache_dir=runs\pytest-cache-v664-rule
```

结果为 `6 passed`。其中新增测试覆盖了“内部 zero-hit 仍是有效负样本”的边界。

## 截图与归档

- 运行解释：`e/664/解释/说明.md`
- HTML evidence：`e/664/解释/model-capability-required-term-pair-alignment-comparison-with-resume-routes/`
- 截图：`e/664/图片/v664-alignment-comparison-with-resume-routes.png`

一句话总结：v664 让路线矩阵能接纳真实失败的 resume 负样本，并确认 naive continuation 没有改变当前双锚点判断。
