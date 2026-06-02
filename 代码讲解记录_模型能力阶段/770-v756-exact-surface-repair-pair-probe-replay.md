# v756 exact-surface repair pair-probe replay 代码讲解

## 本版目标和边界

v756 的目标是独立复核 v755 checkpoint。v755 在训练脚本内 pair-full，但这不等于 checkpoint 能通过 required exact heldout pair prompt；v756 重新加载 checkpoint/tokenizer，并执行 exact/spaced/arrow 三种 pair prompt surface replay。

本版不训练模型，不修改 corpus，不 promotion。它只判断 v753-v755 exact-surface repair route 是否真正改善独立 replay。

## 前置路线

- v753：增加 4 条 near-exact pipe/equals bridge rows。
- v754：物化为 7680 行 corpus。
- v755：训练脚本内观察到 pair-full。
- v756：独立 replay 复核。

这条路线的重点是让训练内观察接受外部复核。

## 使用的能力

v756 复用 v750 新增的 replay adapter：

```text
scripts/run_model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay.py
```

虽然脚本名里保留 fixed-preserving transfer，这是因为它复用同一个 training-run-to-pair-probe adapter；本版输入实际是 v755 exact-surface repair training run。

## 核心输出字段

v756 输出：

```text
decision=pair_readiness_fixed_preserving_transfer_pair_probe_replay_partial
exact_heldout_pair_full=False
required_all_pair_full=False
pair_full_count=1
model_quality_claim=pair_probe_replay_partial
```

这说明 replay 执行成功，但 required exact surface 没过。

## replay rows 解释

v756 replay rows 为：

| surface | prompt | result |
| --- | --- | --- |
| exact-heldout-pair | `fixed=|loss=` | 只命中 1 个 term |
| spaced-heldout-pair | `fixed= | loss=` | 只命中 1 个 term |
| arrow-heldout-pair | `fixed -> | loss ->` | 命中 2 个 terms |

这个结果和 v750 的形态一致。也就是说，v753-v755 没有把 arrow surface 的 pair-full 能力迁移到 exact heldout surface。

## 运行证据

运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay.py e\755\解释\model-capability-required-term-pair-readiness-exact-surface-repair-training-run --out-dir e\756\解释\model-capability-required-term-pair-readiness-exact-surface-repair-pair-probe-replay --require-pass --force
```

Playwright 快照确认 HTML 中可见：

- `Decision pair_readiness_fixed_preserving_transfer_pair_probe_replay_partial`
- `Exact pair False`
- `Required all False`
- `Pair-full count 1`
- exact-heldout-pair replay full 为 False
- arrow-heldout-pair replay full 为 True

截图位于：

```text
e/756/图片/v756-exact-surface-repair-pair-probe-replay.png
```

## 证据链角色

v756 是 exact-surface repair route 的负反馈复核。它阻止项目把 v755 的训练内 pair-full 当成成熟能力，并提示下一版应做 ineffective comparison 或 closeout。

一句话总结：v756 将 exact-surface repair route 的真实状态定为 independent replay partial，promotion 继续 blocked。
