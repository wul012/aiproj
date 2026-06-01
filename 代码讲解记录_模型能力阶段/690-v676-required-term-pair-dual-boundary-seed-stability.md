# v676 required-term pair dual-boundary seed stability

## 本版目标和边界

v676 的目标是把 v675 选出的 aligned dual-boundary candidate 放到多 seed 重复实验里，确认它是不是稳定能力，而不是 seed 3535 的单点好运。

本版新增通用 `aligned_candidate_seed_stability` 能力。它不改变训练逻辑，只复用 required-term pair coexistence refresh，在多个 seed 下重复同一 corpus mode，并输出稳定性汇总。

本版不直接做推广，不跑 forced-choice 多 seed，也不把 partial result 包装成稳定能力。

## 前置链路

v675 已经给出：

- `decision=repeat_aligned_pair_full_candidate_before_promotion`
- `aligned_route_label=dual-boundary-seed-3535`
- `next_action=repeat the aligned candidate across seeds`

v676 正是执行这条 next action。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_aligned_candidate_seed_stability.py`: 读取 route decision，选择 aligned route corpus mode，并逐 seed 调用 coexistence refresh。
- `src/minigpt/model_capability_required_term_pair_aligned_candidate_seed_stability_artifacts.py`: 输出 JSON、CSV、text、Markdown、HTML 和每个 seed 的 sidecar refresh report。
- `scripts/run_model_capability_required_term_pair_aligned_candidate_seed_stability.py`: CLI 入口，支持 `--seeds`、训练参数、`--require-pass` 和 `--force`。
- `tests/test_model_capability_required_term_pair_aligned_candidate_seed_stability.py`: 覆盖 stable、partial、invalid input、sidecar 输出。

## 输入输出格式

输入：

- `e/675/解释/model-capability-required-term-pair-route-decision-with-dual-boundary/`

运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_aligned_candidate_seed_stability.py e\675\解释\model-capability-required-term-pair-route-decision-with-dual-boundary --out-dir e\676\解释\model-capability-required-term-pair-dual-boundary-seed-stability --seeds 1535 2535 3535 --repeat 220 --bridge-repeat 16 --max-iters 2200 --eval-iters 2 --batch-size 16 --block-size 16 --n-layer 1 --n-head 1 --n-embd 64 --learning-rate 0.005 --max-new-tokens 12 --temperature 0.2 --top-k 1 --device cpu --require-pass --force
```

输出：

- `model_capability_required_term_pair_aligned_candidate_seed_stability.json`
- `model_capability_required_term_pair_aligned_candidate_seed_stability.csv`
- `model_capability_required_term_pair_aligned_candidate_seed_stability.txt`
- `model_capability_required_term_pair_aligned_candidate_seed_stability.md`
- `model_capability_required_term_pair_aligned_candidate_seed_stability.html`
- `seed-reports/seed-*/` 每个 seed 的 refresh sidecar

## 核心字段语义

- `aligned_route`: 从 v675 route decision 继承的候选路线。
- `settings.corpus_mode`: 实际重复训练的 corpus mode。
- `seed_rows`: 每个 seed 的训练和 replay 结果。
- `pair_full_seed_count`: 复现 pair-full 的 seed 数量。
- `stable_pair_full`: 是否所有 seed 都 pair-full。
- `partial_pair_full`: 是否只有部分 seed pair-full。

## 本版结果

v676 的真实结果是：

- seed `1535`: pair-full
- seed `2535`: no pair-full
- seed `3535`: pair-full

汇总：

- `pair_full_seed_count=2`
- `pair_full_seed_rate=0.6667`
- `stable_pair_full=False`
- `decision=required_term_pair_aligned_candidate_partial_stability`

这说明 dual-boundary 方向有真实增益，但仍未稳定到可推广程度。

## 测试与证据

验证命令：

```powershell
python -m py_compile src\minigpt\model_capability_required_term_pair_aligned_candidate_seed_stability.py src\minigpt\model_capability_required_term_pair_aligned_candidate_seed_stability_artifacts.py scripts\run_model_capability_required_term_pair_aligned_candidate_seed_stability.py tests\test_model_capability_required_term_pair_aligned_candidate_seed_stability.py
python -m pytest tests\test_model_capability_required_term_pair_aligned_candidate_seed_stability.py -q -o cache_dir=runs\pytest-cache-v676-unit
```

运行证据：

- JSON/CSV/text/Markdown/HTML: `e/676/解释/model-capability-required-term-pair-dual-boundary-seed-stability/`
- 截图: `e/676/图片/v676-dual-boundary-seed-stability.png`
- 解释: `e/676/解释/说明.md`

一句话总结：v676 让 dual-boundary 候选进入多 seed 复核，并用 2/3 pair-full 的结果明确保留 partial stability 边界。
