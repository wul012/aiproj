# v854：bounded objective unassisted repair seed revision partial-hit diagnostic

## 本版目标和边界

v854 的目标是解释 v853 的 partial required-term signal：为什么模型已经能输出 `fixed`，但还不能稳定输出完整的 `fixed loss`。

边界：

- 不继续训练。
- 不修改 v836 contract。
- 不使用 decoder anchor。
- 不把 partial hit 当成 contract recovery。

这版只做诊断，把下一步从“继续训练”收束为“定向 curriculum patch”。

## 前置链路

v853 的真实 replay 结果是：

```text
passed_case_count=0
any_hit_case_count=2
zero_hit_case_count=1
hit_terms=['fixed']
missed_terms=['fixed', 'loss']
```

这说明模型已经不是 v848 的全零命中，但也没有通过任何 contract case。

## 关键新增文件

- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic.py`
  - 读取 replay、seed revision、training run 和 corpus，生成 case diagnostic 与 root causes。
- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
- `scripts/diagnose_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_partial_hit.py`
  - CLI 入口。
- `tests/test_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic.py`
  - 覆盖 partial-hit ready、无 partial-hit 失败、writer/CLI。
- `e/854/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed-revision-partial-hit-diagnostic/`
  - 保存真实诊断报告。
- `e/854/图片/v854-bounded-objective-unassisted-repair-seed-revision-partial-hit-diagnostic-html.png`
  - Playwright MCP 截图。

## 核心数据结构

每个 replay case 会被转换成 `case_diagnostics`：

```text
case_id
hit_terms
missed_terms
partial_hit
zero_hit
missed_terms_present_in_corpus
continuation_preview
```

这个结构把“有没有命中任意词”和“有没有通过 contract”分开。

例如 v853 中：

```text
canonical_direct_completion -> hit fixed, missed loss
minimal_direct_completion   -> hit fixed, missed loss
completion_label_surface    -> missed fixed/loss
```

## root causes

v854 输出 6 个 root causes：

```text
first_term_only_uptake
loss_term_not_stabilized
prompt_surface_still_zero_hit
corpus_contains_missed_terms
no_case_passed_contract
unassisted_path_confirmed
```

其中最关键的是前两个：

- `first_term_only_uptake` 说明模型会走向正确表面，但停在第一个 required term。
- `loss_term_not_stabilized` 说明 `loss` 在 corpus 中存在，失败不再是“数据完全缺失”，而是训练/生成 uptake 不稳定。

## 真实运行命令

```text
python scripts/diagnose_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_partial_hit.py --replay-comparison e/853/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed-revision-replay-comparison --seed-revision e/851/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed-revision --training-run e/852/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed-revision-training-run --corpus e/851/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed-revision/model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_corpus.txt --out-dir e/854/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed-revision-partial-hit-diagnostic --require-diagnostic-ready --force
```

## 真实结果

```text
status=pass
decision=model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic_ready
partial_hit_case_count=2
zero_hit_case_count=1
hit_terms=['fixed']
missed_terms=['fixed', 'loss']
root_cause_count=6
model_quality_claim=partial_required_term_signal_diagnosed
next_action=build_bounded_objective_unassisted_repair_seed_revision_curriculum_patch
```

## 测试覆盖

focused pytest 覆盖：

- fixed-only partial hit 可以生成 ready diagnostic。
- 没有 partial hit 时 diagnostic fail。
- CLI 和 writer 输出 JSON/CSV/TXT/Markdown/HTML。

```text
3 passed
```

全量验证：

```text
py_compile: pass
full pytest: 1741 passed
source encoding: source_count=1276 clean_count=1276 bom_count=0 syntax_error_count=0
git diff --check: pass
```

## 运行证据

HTML 截图：

```text
e/854/图片/v854-bounded-objective-unassisted-repair-seed-revision-partial-hit-diagnostic-html.png
```

Playwright MCP snapshot 确认页面展示：

```text
Status=pass
Partial hits=2
Zero hits=1
Hit terms=['fixed']
Missed terms=['fixed', 'loss']
Claim=partial_required_term_signal_diagnosed
Next action=build_bounded_objective_unassisted_repair_seed_revision_curriculum_patch
```

## 一句话总结

v854 把 revised no-anchor checkpoint 的进展定性为 first-term-only partial uptake，并把下一步收束到 loss/prompt-surface curriculum patch。
