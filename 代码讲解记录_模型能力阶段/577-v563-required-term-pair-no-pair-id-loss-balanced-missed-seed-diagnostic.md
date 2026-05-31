# v563 required-term pair no-pair-id loss-balanced missed-seed diagnostic 代码讲解

## 本版目标和边界

v562 把 v561 的单 seed 成功降温为 `1/3` partial stability。v563 的目标不是继续训练，而是先弄清楚 missed seeds 为什么失败：如果问题在 continuation 后段，可以继续增强 continuation；如果问题在首 token，就应该优先修 first-token preference。

本版只读 v562 报告和 checkpoint，不新增 corpus、不改训练参数、不扩大模型。

## 前置链路

- v561：seed `1535` 在 no-pair-id + loss-balanced objective 下 pair-full。
- v562：同一 objective 扩到 seeds `535,1535,2535` 后只剩 `1535` 成功。

v563 是 v562 的诊断层，用来决定下一步该训练什么。

## 关键文件

- `scripts/run_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic.py`
  - CLI 入口，本版复用既有脚本。
- `src/minigpt/model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic.py`
  - 读取稳定性报告，对每个 seed 的 checkpoint 做首 token 排名诊断。
- `e/563/解释/model-capability-required-term-pair-no-pair-id-loss-balanced-missed-seed-diagnostic/`
  - 保存 JSON、CSV、text、Markdown、HTML 和 Playwright snapshot。
- `e/563/图片/01-model-capability-required-term-pair-no-pair-id-loss-balanced-missed-seed-diagnostic.png`
  - 诊断报告截图。

## 输入输出格式

输入是 v562 stability 目录：

```text
e/562/解释/model-capability-required-term-pair-equals-surface-no-pair-id-loss-balanced-stability
```

输出主报告的核心字段：

```json
{
  "decision": "required_term_pair_colon_immediate_first_token_gap",
  "summary": {
    "seed_count": 3,
    "missed_seed_count": 2,
    "missed_first_token_gap_count": 2
  }
}
```

每个 seed row 会记录：

- `pair_full_observed`
- `first_token_decision`
- `expected_top_count`
- `fixed_expected_rank`
- `loss_expected_rank`
- `observed_continuation_hit_count`

## 真实结果

v563 的结论是：

```text
535  -> expected_top=0/2, fixed_rank=2, loss_rank=4
1535 -> expected_top=1/2, fixed_rank=1, loss_rank=3
2535 -> expected_top=1/2, fixed_rank=2, loss_rank=1
```

两个 missed seeds 都属于 first-token gap。seed `535` 两个目标首 token 都不是 top，seed `2535` 的 loss 首 token 是 top，但 fixed 仍排第 2。

## 测试和验证角色

本版没有新增代码，验证重点是：

- diagnostic CLI 能从 v562 目录读取 stability report。
- JSON/CSV/Markdown/HTML 输出都完整生成。
- HTML 报告可由 Playwright 打开并截图。
- 后续收口仍需全量 pytest、source encoding 和 `git diff --check`。

## 归档角色

`e/563` 是 v562 missed seeds 的原因定位证据。它把下一步从“继续加 continuation 训练”改成“先增强 fixed/loss 首 token 偏好”，避免盲目扩语料。

一句话总结：v563 证明 v562 的剩余问题主要是 first-token ranking gap，下一版应做 first-token preference objective。

