# v750 fixed-preserving transfer pair-probe replay 代码讲解

## 本版目标和边界

v750 的目标是给 v749 checkpoint 增加独立 replay 入口。v749 在训练脚本内观察到 pair-full，但那还不是 promotion 证据；v750 重新读取 checkpoint/tokenizer，并在多个 heldout pair prompt surface 上生成，判断结果是否稳定。

本版不训练模型，不修改 corpus，不接受 checkpoint。它只回答一个问题：v749 的 pair-full 是否能在独立 replay 中复现。

## 为什么需要新 adapter

项目里已有 `direct_completion_pair_probe_replay`，但它的 CLI 输入是 direct-completion route comparison。v749 的输入不是 route comparison，而是 fixed-preserving transfer training run。

v750 新增的 adapter 没有复制底层生成逻辑，而是复用现有 replay engine：

- checkpoint/tokenizer 加载仍由 generation profile replay 链路负责。
- pair prompt specs 沿用现有 exact/spaced/arrow 三种 surface。
- v750 只把输入语义从 route comparison 改为 training run，并把输出 decision 改成 fixed-preserving transfer route 的名字。

这样可以避免重复实现模型加载和采样，同时不会把 v749 错写成 direct-completion route。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay.py`
  - v750 adapter 核心。
  - `locate_fixed_preserving_transfer_pair_probe_replay_source()` 支持输入 training run JSON 或输出目录。
  - `build_fixed_preserving_transfer_pair_probe_replay()` 读取训练报告，复用 existing pair-probe replay engine，再重写 title、decision、interpretation 和 boundary。
  - 输出 decision 包括 ready、partial、not-ready、fix 四类。

- `src/minigpt/model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
  - HTML 聚焦展示 exact pair、required all、pair-full count、claim 和 replay rows。

- `scripts/run_model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay.py`
  - CLI 入口。
  - 输入 v749 training run 目录。
  - `--require-pass` 只要求 replay 执行成功；partial 是有效结果，不是执行失败。

- `tests/test_model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay.py`
  - 覆盖 exact pair ready、required prompt miss、目录定位、artifact 输出。
  - 同时回归 direct-completion replay 测试，确认 adapter 没破坏原有能力。

## 输入输出结构

输入是 v749 training run：

```text
e/749/解释/model-capability-required-term-pair-readiness-fixed-preserving-transfer-training-run
```

核心输入字段包括：

- `decision=pair_readiness_training_pair_full_observed`
- `settings.seed=3535`
- `training.checkpoint_path`
- `training.tokenizer_path`

输出是 v750 replay report：

```text
status=pass
decision=pair_readiness_fixed_preserving_transfer_pair_probe_replay_partial
exact_heldout_pair_full=False
required_all_pair_full=False
pair_full_count=1
model_quality_claim=pair_probe_replay_partial
```

## replay rows 解释

v750 复测三种 pair prompt surface：

| surface | prompt | required | result |
| --- | --- | --- | --- |
| exact-heldout-pair | `fixed=|loss=` | true | 只命中 1 个 term |
| spaced-heldout-pair | `fixed= | loss=` | false | 只命中 1 个 term |
| arrow-heldout-pair | `fixed -> | loss ->` | false | 命中 2 个 terms |

这个结果说明模型不是完全没有 pair surface 能力，但能力依赖 prompt 表面形式。required exact prompt 未通过，所以不能 promotion。

## 测试和验证

Focused tests：

```powershell
python -m pytest tests\test_model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay.py tests\test_model_capability_required_term_pair_readiness_direct_completion_pair_probe_replay.py -q -o cache_dir=runs\pytest-cache-v750-focused
```

结果为 8 个测试通过。

真实 replay 命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay.py e\749\解释\model-capability-required-term-pair-readiness-fixed-preserving-transfer-training-run --out-dir e\750\解释\model-capability-required-term-pair-readiness-fixed-preserving-transfer-pair-probe-replay --require-pass --force
```

Playwright 快照确认 HTML 中可见：

- `Decision pair_readiness_fixed_preserving_transfer_pair_probe_replay_partial`
- `Exact pair False`
- `Required all False`
- `Pair-full count 1`
- `arrow-heldout-pair` replay full 为 True

截图位于：

```text
e/750/图片/v750-fixed-preserving-transfer-pair-probe-replay.png
```

## 证据链角色

v750 是 v749 训练结果的复核层。它阻止项目过早把训练脚本内的 direct pair hit 写成 promotion，并把下一步问题缩小为 prompt-surface sensitivity。

一句话总结：v750 把 fixed-preserving transfer checkpoint 从“训练内观察到 pair-full”推进到“独立 replay partial”，明确 promotion 还差 exact heldout pair。
