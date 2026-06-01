# v615 required-term pair contrast-free route decision

## 本版目标和边界

v615 做 contrast-free batch 的路线决策。它不是简单读取 v614 comparison，而是同时读取 v608 closeout 与 v609 first-token diagnostic，避免机械重复 loss-rebalance。

本版不训练，不新增语料，只给下一步实验排序。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_contrast_free_route_decision.py
src/minigpt/model_capability_required_term_pair_contrast_free_route_decision_artifacts.py
scripts/run_model_capability_required_term_pair_contrast_free_route_decision.py
tests/test_model_capability_required_term_pair_contrast_free_route_decision.py
e/615/解释/model-capability-required-term-pair-contrast-free-route-decision/
```

## 输入输出

输入：

```text
v608 fixed-retention batch closeout
v609 first-token preference diagnostic
v614 contrast-free objective comparison
```

输出：

```text
status=pass
decision=stop_contrast_free_routes_and_run_forced_choice_diagnostic
pair_full_route_count=0
fixed_only_route_count=2
prior_loss_rebalance_stopped=True
requires_forced_choice_diagnostic=True
```

## 决策逻辑

如果 contrast-free route 出现 pair-full，则转入 seed stability。

如果没有 pair-full，且 v608 已经停止 loss-rebalance，且 v609 已确认 first-token conflict，则不继续做相似语料训练，而转入 forced-choice / teacher-forced 诊断。

## 测试覆盖

测试确认：

- fixed-only routes + prior stop + first-token conflict 会要求 forced-choice diagnostic。
- pair-full route 会转 seed stability。
- prior closeout 未停止时会失败。
- JSON/CSV/text/Markdown/HTML 五种输出可生成。
- locator 支持 output directory。

## 一句话总结

v615 把 contrast-free batch 从“继续调语料”转为“先看 checkpoint 内部偏好”。
