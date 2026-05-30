# v532 required-term pair generation profile replay 代码讲解

## 本版目标和边界

v529-v531 已经完成了 generation profile 的端到端表面：CLI、API、playground、endpoint 和 contract check 都能识别 `suppress_newline_tokens`。但这还没有回答一个更重要的问题：它是否能解决 fixed/loss pair 共存问题。

v532 因此回放 v502 的 fixed/loss branch-retention checkpoint，分别使用 `default` 和 `suppress_newline_tokens` 两个 profile 生成 `fixed:`、`loss:`，并按变体统计 pair-full 是否出现。

本版明确不做：

- 不重新训练模型。
- 不修改 v529-v531 的 profile 行为。
- 不把解码 profile 的效果当成训练能力提升。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_generation_profile_replay.py`
  - 负责读取 v502 branch-retention sweep、选取 fixed/loss terms 和训练变体、调用生成器并计算命中。
- `src/minigpt/model_capability_required_term_pair_generation_profile_replay_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML 报告。
- `scripts/run_model_capability_required_term_pair_generation_profile_replay.py`
  - CLI 入口，支持 `--variant-limit`、`--profiles`、`--require-pass`。
- `tests/test_model_capability_required_term_pair_generation_profile_replay.py`
  - 用 fake generator 覆盖无收益、有收益、输出渲染三条路径。
- `e/532/解释/model-capability-required-term-pair-generation-profile-replay/`
  - 真实 v502 checkpoint 回放报告。
- `e/532/图片/01-model-capability-required-term-pair-generation-profile-replay.png`
  - HTML 报告截图。

## 核心流程

`build_model_capability_required_term_pair_generation_profile_replay()` 的输入是 v502 的 `model_capability_required_term_pair_branch_retention_sweep.json`。它从 source report 中读取：

- `targets[0].terms`：得到 `fixed:` 和 `loss:` 两个 scaffold prompt。
- `training_rows`：得到 3 个 branch-retention 变体的 checkpoint/tokenizer。
- `probe_rows`：复用当时的 generation seed，保证回放尽量贴近历史测量。

然后对每个变体、每个 term、每个 profile 跑一次生成：

```text
variant x term x profile
```

默认 profile 走普通解码；`suppress_newline_tokens` 通过 `parse_generation_request()` 合并 profile blocked token texts，再由 `MiniGPTGenerator` 进入真实模型生成路径。

## 关键字段

`case_rows` 是最细粒度证据，每行记录：

- `variant_id`
- `profile_id`
- `term`
- `prompt`
- `generation_seed`
- `generated`
- `continuation`
- `continuation_hit`
- `newline_cleanup_hit`
- `blocked_token_count`

`variant_rows` 把同一变体同一 profile 下的 fixed/loss 合并：

- `hit_terms`
- `missed_terms`
- `pair_full_hit`

`profile_rows` 再按 profile 汇总：

- `continuation_hit_count`
- `pair_full_variant_count`
- `blocked_token_count_total`

最后 `summary` 对比 default 和 suppression：

```text
default_pair_full_variant_count
suppression_pair_full_variant_count
suppression_hit_delta
suppression_pair_full_delta
```

## 真实运行结果

真实命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_generation_profile_replay.py e\502\解释\model-capability-required-term-pair-branch-retention-sweep\model_capability_required_term_pair_branch_retention_sweep.json --out-dir e\532\解释\model-capability-required-term-pair-generation-profile-replay --variant-limit 3 --force --require-pass
```

结果：

```text
status=pass
decision=generation_profile_no_pair_coexistence_gain
default_pair_full_variant_count=0
suppression_pair_full_variant_count=0
suppression_hit_delta=0
```

这说明 newline suppression 在 v502 fixed/loss pair-retention checkpoint 上没有制造新的 pair-full 变体。它仍然是 loss-alias newline 表面的解码清理，而不是 pair 共存修复。

## 测试覆盖

测试没有依赖真实 PyTorch 训练，而是用 fake generator 锁住统计逻辑：

- `fake_generate_fixed_branch`：无论 profile 都偏向 fixed，报告应是 no gain。
- `fake_generate_suppression_pair_gain`：suppression profile 命中 fixed/loss，报告应进入 improves pair coexistence。
- 输出测试验证 JSON、CSV、text、Markdown、HTML 都能生成。

真实 PyTorch 生成路径由 v532 运行证据覆盖，单测则保护决策逻辑。

## 链路角色

v532 是从 profile 治理回到模型能力路线的一版。它把 v529-v531 的可用 profile 放到 fixed/loss pair 历史问题上复验，并得出一个保守结论：接下来不要继续靠 newline suppression 解决 pair coexistence，应设计新的训练目标。

一句话总结：v532 证明 generation profile 是解码表面工具，不是 fixed/loss pair 共存能力的替代训练方案。
