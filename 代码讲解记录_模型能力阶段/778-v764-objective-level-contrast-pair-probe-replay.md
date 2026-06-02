# v764 objective-level contrast pair-probe replay 代码讲解

## 本版目标和边界

v764 的目标是独立验证 v763 checkpoint。v763 已经在训练运行内出现 direct pair hit，但 direct probes 不等于 heldout pair prompt 迁移，因此 v764 复用 pair-probe replay 机制，对 exact、spaced、arrow 三种 pair prompt surface 做 replay。

本版不训练，不改 checkpoint，不做 promotion。它只回答：v763 的 direct hit 是否能迁移到 pair prompt replay？

## 前置路线

- v762：生成 objective-level contrast corpus。
- v763：训练 fresh tiny checkpoint，并观察 direct pair hit。
- v764：对 v763 checkpoint 做独立 pair-probe replay。

## 关键产物

- `e/764/解释/model-capability-required-term-pair-readiness-objective-level-contrast-pair-probe-replay/model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay.json`
  - v764 主报告。
  - 记录三种 prompt surface 的 replay_full 和 hit counts。

- `e/764/解释/model-capability-required-term-pair-readiness-objective-level-contrast-pair-probe-replay/pair-probe-replay-runs/`
  - 每种 prompt surface 的底层 replay 报告。
  - exact、spaced、arrow 都有独立运行目录。

## replay rows

| spec | prompt | required | replay full | default hits | suppression hits |
| --- | --- | --- | --- | ---: | ---: |
| exact-heldout-pair | `fixed=|loss=` | true | true | 2 | 2 |
| spaced-heldout-pair | `fixed= | loss=` | false | true | 2 | 2 |
| arrow-heldout-pair | `fixed -> | loss ->` | false | true | 2 | 2 |

这和 v756 exact-surface repair replay 的 partial 结果明显不同。v764 不是只在训练脚本里命中，而是在独立 replay 中三种 pair surface 都 pair-full。

## 运行和验证

真实运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay.py e\763\解释\model-capability-required-term-pair-readiness-objective-level-contrast-training-run --out-dir e\764\解释\model-capability-required-term-pair-readiness-objective-level-contrast-pair-probe-replay --require-pass --force
```

输出核心：

```text
decision=pair_readiness_fixed_preserving_transfer_pair_probe_replay_ready
exact_heldout_pair_full=True
required_all_pair_full=True
pair_full_count=3
```

Playwright 快照确认 HTML 中可见：

- `Exact pair True`
- `Required all True`
- `Pair-full count 3`
- `Claim pair_probe_replay_ready`

截图位于：

```text
e/764/图片/v764-objective-level-contrast-pair-probe-replay.png
```

## 证据链角色

v764 是独立 replay 层。它把 v763 的 direct-hit checkpoint 推进到 pair-probe replay-ready，但后续仍应做 route comparison 和 stricter promotion guards，避免单次 seed 直接过度宣传。

一句话总结：v764 给出了 objective-level contrast 路线目前最强的 pair prompt 迁移证据。
