# v730 surface mismatch diagnostic

## 本版目标和边界

v730 的目标是解释 v729 objective-structure training 为什么两个 direct probes 都 miss。

本版不训练、不改 corpus、不做 patch。它只读两个来源：

- v727 objective-structure contract。
- v729 objective-structure training run。

然后判断 direct prompt surface mismatch 是否成立。

## 前置链路

```text
v727 contract
 -> task-id / paired-block rows, no exact direct prompt rows
v728 materialization
 -> 5760 corpus lines
v729 training
 -> fixed= and loss= both miss
v730 diagnostic
 -> direct surface mismatch detected
```

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_readiness_surface_mismatch_diagnostic.py`
  - 读取 contract 和 training report。
  - 计算 raw surface reference、missed terms、surface class。
  - 输出 decision 和 recommended next artifact。
- `src/minigpt/model_capability_required_term_pair_readiness_surface_mismatch_diagnostic_artifacts.py`
  - 负责 JSON/CSV/TXT/Markdown/HTML 输出。
- `scripts/run_model_capability_required_term_pair_readiness_surface_mismatch_diagnostic.py`
  - CLI 入口，要求同时传入 `--contract` 和 `--training-run`。
- `tests/test_model_capability_required_term_pair_readiness_surface_mismatch_diagnostic.py`
  - 覆盖 mismatch detected、已命中 direct term 时失败、五格式输出。

## 核心判断

v730 的 summary 核心字段：

```text
default_hit_terms=[]
default_missed_terms=['fixed', 'loss']
both_direct_terms_missed=True
exact_prompt_overlap_count=0
raw_surface_reference_count=0
surface_mismatch_detected=True
recommended_next_artifact=pair_readiness_direct_prompt_bridge_contract_patch
```

判断成立的条件是：

- training report pass。
- training decision 是 no-pair-full。
- default replay 至少有 fixed/loss 两行。
- fixed 和 loss 都 miss。
- contract training rows 里没有 exact direct prompt row。
- contract training rows 里也没有 raw `fixed=` / `loss=` surface reference。

## 为什么不是模型能力提升

v730 只是 diagnostic。

它不会把 v729 的结果解释成能力提升；相反，它说明当前 objective rows 离 heldout raw prompt 太远。后续应该补 bridge rows，再重新物化和训练。

## 证据

运行证据：

- `e/730/解释/model-capability-required-term-pair-readiness-surface-mismatch-diagnostic/`
- `e/730/图片/v730-surface-mismatch-diagnostic.png`

截图显示：

```text
Mismatch=True
Hits=[]
Misses=['fixed', 'loss']
Raw refs=0
```

## 一句话总结

v730 将 v729 的双 direct miss 定位为 raw prompt surface mismatch，为下一版 direct prompt bridge patch 提供证据。
