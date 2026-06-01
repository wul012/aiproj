# v681 required-term pair surface policy replay

## 本版目标和边界

v681 的目标是把 v680 的 policy plan 变成真实 replay：对 v676 产出的三个 dual-boundary checkpoint，逐 seed、逐 term、逐 policy 重新生成，检查是否有 generation-surface policy 能稳定修复 v679 的 `loss` surface failure。

本版不训练新模型，不改 checkpoint，不运行被 v680 排除的 `target_echo_upper_bound`。它只测试 prompt/policy 对自由生成表面的影响。

## 前置链路

v679 定位了问题：

- seed `2535` 漏 `loss`。
- internal forced-choice 已经通过。

v680 规划了 replay policy：

- `single_label_default`
- `single_label_suppress_newline`
- `pair_context_prefix`
- `dual_boundary_sentence`

v681 负责真实执行这些 policy。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_surface_policy_replay.py`
  - 读取 seed stability 和 policy plan。
  - 从 embedded seed reports 中提取 checkpoint/tokenizer。
  - 调用 `MiniGPTGenerator` 执行真实生成。
  - 汇总 `case_rows`、`policy_summaries`、`seed_summaries`。

- `src/minigpt/model_capability_required_term_pair_surface_policy_replay_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML。
  - HTML 同时展示 policy summary 和 case rows。

- `scripts/run_model_capability_required_term_pair_surface_policy_replay.py`
  - CLI 入口，支持 `--max-new-tokens`、`--temperature`、`--top-k`、`--device`、`--require-pass`、`--force`。

- `tests/test_model_capability_required_term_pair_surface_policy_replay.py`
  - 用 fake generator 覆盖稳定 policy、无收益、坏输入和输出格式。

## 运行命令

```powershell
python -B scripts\run_model_capability_required_term_pair_surface_policy_replay.py e\676\解释\model-capability-required-term-pair-dual-boundary-seed-stability e\680\解释\model-capability-required-term-pair-surface-policy-plan --out-dir e\681\解释\model-capability-required-term-pair-surface-policy-replay --max-new-tokens 12 --temperature 0.2 --top-k 1 --device cpu --require-pass --force
```

## 核心字段语义

- `case_rows`: 每个 seed/term/policy 的生成结果。
- `policy_summaries`: 每个 policy 的命中 case 数、pair-full seed 数、是否三 seed 稳定。
- `seed_summaries`: 每个 seed 下哪些 policy 能 pair-full。
- `stable_pair_full_policy_ids`: 所有 seed 都 pair-full 的 policy。
- `best_policy_id`: 按 pair-full seed 数和 hit case 数排序的最佳 policy。

## 本版结果

真实 replay 结果：

- `stable_pair_full_policy_ids=['dual_boundary_sentence', 'pair_context_prefix']`
- `best_policy_id=dual_boundary_sentence`
- `stable_pair_full_policy_count=2`

这说明 contextual-anchor policy 能稳定修复自由生成表面，但不能证明 minimal prompt 下也稳定。

## 测试与证据

验证命令：

```powershell
python -m py_compile src\minigpt\model_capability_required_term_pair_surface_policy_replay.py src\minigpt\model_capability_required_term_pair_surface_policy_replay_artifacts.py scripts\run_model_capability_required_term_pair_surface_policy_replay.py tests\test_model_capability_required_term_pair_surface_policy_replay.py
python -m pytest tests\test_model_capability_required_term_pair_surface_policy_replay.py -q -o cache_dir=runs\pytest-cache-v681
```

运行证据：

- JSON/CSV/text/Markdown/HTML: `e/681/解释/model-capability-required-term-pair-surface-policy-replay/`
- 截图: `e/681/图片/v681-surface-policy-replay.png`
- 解释: `e/681/解释/说明.md`

一句话总结：v681 证明 dual-boundary checkpoint 在 contextual-anchor prompt 下能稳定 pair-full，但还需要 minimality/leakage 决策。
