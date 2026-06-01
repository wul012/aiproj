# v657 required-term pair loss-guarded schedule seed 3535

## 本版目标和边界

v657 对 v656 新增的 loss-guarded schedule corpus 做真实训练。它验证一个具体假设：给 `loss` 更多生成行和 first-token guard，是否能修复 v655 观察到的 fixed-only collapse。

本版只覆盖 seed 3535 的 tiny 配置，不代表更大模型或真实两阶段训练。

## 输入输出

输入：

- corpus mode：`equals_surface_no_pair_id_loss_internal_loss_guarded_schedule_repair`
- seed：`3535`
- repeat：`320`
- bridge repeat：`24`
- max iters：`1800`

输出：

- `e/657/解释/model-capability-required-term-pair-loss-guarded-schedule-seed-3535/`
- checkpoint 和 tokenizer。
- HTML/Markdown/TXT/JSON 报告。
- Playwright 截图。

## 核心结果

报告显示：

- `decision=required_term_pair_coexistence_refresh_no_pair_full`
- `pair_full_observed=False`
- `default_pair_full_variant_count=0`
- `suppression_pair_full_variant_count=0`

Replay 细节：

- `fixed=` 生成 `lixelixelxe`，未命中 `fixed`。
- `loss=` 生成连续 `s`，未命中 `loss`。

## 解释

v656 的 loss guard 确实改变了模型行为，但不是向 pair-full 方向改变。它打破了 v651 的 fixed-only 局部稳定点，却没有形成新的 `loss` 命中，说明当前单语料权重调节过于粗糙。

## 链路意义

这让路线判断更明确：

- surface-first：fixed-only。
- loss-guarded：no-hit / 字符漂移。
- v630 joint-cycle 仍是唯一生成 pair-full 证据。

因此 v658 应该收口这个分支，而不是继续微调类似语料。

## 一句话总结

v657 证明 loss-guarded schedule 没有修复目标能力，反而削弱了已有 fixed 命中。
