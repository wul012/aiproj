# v672 required-term pair dual-boundary seed 3535

## 本版目标和边界

v672 用 v671 新增的 explicit dual-objective boundary corpus 跑真实 seed 3535 训练。目标是验证这个 corpus 是否能恢复 fixed/loss pair-full。

本版只证明单 seed targeted pair refresh signal，不证明稳定能力，也不直接 promotion。

## 前置链路

- v669 定位 constrained decode 后剩余 miss 在 fixed。
- v670 形成 dual-objective boundary plan。
- v671 将 plan 注册为 corpus mode。

v672 是这条路线的第一次真实训练。

## 运行命令

```powershell
python -B scripts\run_model_capability_required_term_pair_coexistence_refresh.py --out-dir e\672\解释\model-capability-required-term-pair-dual-boundary-seed-3535 --seed 3535 --corpus-mode equals_surface_no_pair_id_loss_internal_explicit_dual_boundary_repair --repeat 220 --bridge-repeat 16 --max-iters 2200 --eval-iters 2 --batch-size 16 --block-size 16 --n-layer 1 --n-head 1 --n-embd 64 --learning-rate 0.005 --max-new-tokens 12 --temperature 0.2 --top-k 1 --device cpu --require-pass --force
```

## 核心结果

- `decision=required_term_pair_coexistence_refresh_pair_full_observed`
- `training_status=pass`
- `checkpoint_exists=True`
- `default_pair_full_variant_count=1`
- `suppression_pair_full_variant_count=1`
- `pair_full_observed=True`

replay 中：

- `fixed=` 命中 `fixed`
- `loss=` 命中 `loss`

default 和 suppress_newline_tokens 都达到 pair-full。

## 解释

v672 是正向模型证据，但边界要明确：

- 它是单 seed。
- 它是 fixed/loss targeted pair。
- 它还没有 forced-choice 内部诊断。
- 它不能代表一般 LLM 质量提升。

下一步应立刻跑 forced-choice diagnostic，确认内部偏好是否也达到了 pair-full。

## 证据归档

- JSON/text/Markdown/HTML: `e/672/解释/model-capability-required-term-pair-dual-boundary-seed-3535/`
- checkpoint: `e/672/解释/model-capability-required-term-pair-dual-boundary-seed-3535/pair-coexistence-refresh-run/checkpoint.pt`
- 截图: `e/672/图片/v672-dual-boundary-seed-3535.png`
- 解释: `e/672/解释/说明.md`

一句话总结：v672 证明 explicit dual-boundary corpus 在 seed 3535 上能恢复自由生成 pair-full，但还需要内部诊断和多 seed 验证。
