# v658 required-term pair schedule approximation batch closeout

## 本版目标和边界

v658 是 v649-v658 十版的收口。它不再新增语料，而是把 v657 的 loss-guarded checkpoint 做 forced-choice，再放回 comparison 和 route decision，最后生成 schedule approximation closeout。

本版不声明模型能力提升。它的结论是停止当前单语料 schedule approximation 分支。

## 输入链路

本版消费：

- v657 refresh：loss-guarded 真实训练。
- v658 forced-choice：loss-guarded 内部评分。
- v658 alignment comparison：加入 surface-first 与 loss-guarded 后的完整矩阵。
- v658 route decision：确认主线是否变化。

## 核心结果

forced-choice 结果：

- `expected_best_prompt_count=1`
- `forced_choice_full_match_source_count=0`
- `loss` prompt 仍偏向 `fixed`

comparison 结果：

- `generation_pair_full_count=1`
- `internal_pair_full_count=2`
- `aligned_pair_full_count=0`

route decision：

- `selected_generation_route=loss-internal-joint-cycle`
- `internal_anchor_route=joint-cycle-internal-repair`
- `direct_promotion_ready=False`

closeout：

- `decision=stop_single_corpus_schedule_approximations`

## 为什么停止该分支

这一批已经验证了两种单语料近似：

- surface-first schedule：变成 fixed-only。
- loss-guarded schedule：变成 no-hit / 字符漂移。

二者都没有复现 v630 的 generation pair-full，更没有达到 aligned pair-full。因此继续微调类似语料的收益很低。

## 运行证据

产物写入：

- `e/658/解释/model-capability-required-term-pair-loss-guarded-schedule-forced-choice/`
- `e/658/解释/model-capability-required-term-pair-alignment-comparison-with-loss-guarded-schedule/`
- `e/658/解释/model-capability-required-term-pair-route-decision-with-loss-guarded-schedule/`
- `e/658/解释/model-capability-required-term-pair-schedule-approximation-batch-closeout/`
- `e/658/图片/v658-schedule-approximation-batch-closeout.png`

## 一句话总结

v658 把两阶段单语料近似路线正式收口为负向分支，保留 v630/v640 分离证据，下一步应研究真正续训或解码约束。
