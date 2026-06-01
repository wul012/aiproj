# v618 required-term pair contrast-free batch closeout

## 本版目标和边界

v618 是 v609-v618 的批次收口。它把 first-token 诊断、contrast-free 语料、三次真实训练、比较、路线决策和 forced-choice 诊断合并成一个 closeout。

本版不训练新模型，不新增 objective；它只做结论收束和验证。

## 输入证据

```text
v610 corpus contract
v611 contrast-free training
v612 delimiter-span training
v613 context-switch training
v614 comparison
v615 route decision
v617 forced-choice diagnostic
```

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_contrast_free_batch_closeout.py
src/minigpt/model_capability_required_term_pair_contrast_free_batch_closeout_artifacts.py
scripts/run_model_capability_required_term_pair_contrast_free_batch_closeout.py
tests/test_model_capability_required_term_pair_contrast_free_batch_closeout.py
```

## 运行结果

```text
status=pass
decision=close_contrast_free_batch_and_design_loss_internal_preference_objective
refresh_pair_full_count=0
forced_choice_full_match_source_count=0
closeout_ready=True
```

这个结果把“采样没有 pair-full”和“内部 forced-choice 也没有 full match”连到一起，避免继续把失败归因于解码参数。

## 测试覆盖

新增测试覆盖：

- 正常输入会得到 `close_contrast_free_batch_and_design_loss_internal_preference_objective`。
- forced-choice 如果发现 full internal match，closeout 会失败，防止误停潜在候选。
- JSON/CSV/text/Markdown/HTML 输出可生成。

## 一句话总结

v618 结束 contrast-free batch，并把下一批方向明确到 loss internal preference objective。
