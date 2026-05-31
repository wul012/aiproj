# v549 required-term pair seed config replay 代码讲解

## 本版目标和边界

v548 已经生成 per-seed config-selection policy，但 policy 本身仍是从 coverage map 派生出来的。v549 的目标是重新连接源 stability report 与 checkpoint，对每个 selected seed/config 执行 generation-profile replay。

本版不训练新模型，不改变 v544/v546 的 checkpoint，也不改变 generation profile 定义。它验证的是：v548 选出来的配置是否能在现有 replay 机制下重新得到 pair-full。

## 前置链路

v549 读取：

- v548 `model_capability_required_term_pair_seed_config_selection.json`
- v548 `config_rows[].source_path` 指向的 v544/v546 stability report
- stability report 内嵌的 `seed_reports[].training.checkpoint_path`

因此链路从 policy artifact 回到真实 checkpoint，而不是停在表格层。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_seed_config_replay.py`
  - 定位 v548 policy。
  - 读取 selected config 对应的源 stability report。
  - 找到 selected seed 的内嵌 seed report。
  - 构造 generation-profile replay 所需的 source report。
  - 汇总 replay 是否 pair-full。
- `src/minigpt/model_capability_required_term_pair_seed_config_replay_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
  - 写入每个 seed 的 replay sidecar report。
- `scripts/run_model_capability_required_term_pair_seed_config_replay.py`
  - CLI 入口，支持输入 v548 输出目录。
  - 默认使用现有 generation profile set。
- `tests/test_model_capability_required_term_pair_seed_config_replay.py`
  - 覆盖 ready、not-ready、缺 source、artifact sidecar 和路径定位。

## 核心流程

1. 读取 v548 policy。
2. 对每个 `selection_row` 取 `selected_config_id` 和 `seed`。
3. 在 `config_rows` 中找到 selected config 的 `source_path`。
4. 读取源 stability report，并找到对应 seed 的 `seed_report`。
5. 将 seed report 转换为 generation-profile replay 的 source shape：

```json
{
  "targets": [{"pair_id": "01-fixed-loss", "terms": ["fixed", "loss"]}],
  "training_rows": [{"checkpoint_path": "...", "tokenizer_path": "..."}],
  "probe_rows": [{"term": "fixed"}, {"term": "loss"}]
}
```

6. 调用现有 `build_model_capability_required_term_pair_generation_profile_replay()`。
7. 根据 replay summary 判断该 selected seed 是否 pair-full。

## 真实结果

真实 v549 结果：

```text
replay_pair_full_seed_count=3
selected_replay_ready=True
policy_replay_gap_count=0
```

逐 seed：

- `535` 使用 `v544-topk2-t080`，default/suppression 都 pair-full。
- `1535` 使用 `v546-loss-calibrated-topk2-t080`，suppression pair-full。
- `2535` 使用 `v544-topk2-t080`，default/suppression 都 pair-full。

## 边界解释

这仍然不是生产级模型能力证明。它证明的是 selected policy 可以重新 replay 已知 seed/config/checkpoint 的 fixed/loss pair-full 覆盖。真正的下一层应该是 held-out prompt variants 或 fresh seed，检查这条 policy 是否具备迁移性。

## 测试覆盖

测试保护：

- selected config 能 replay pair-full 时 decision 为 ready。
- selected config replay 不出 pair-full 时进入 not-ready，并记录 policy gap。
- source report 缺失时 status 为 fail。
- sidecar replay reports 会写入 `replay-reports/<config>/seed-<seed>`。

## 归档角色

`e/549` 保存主 replay report、每个 selected seed 的 sidecar replay report、HTML 截图和 snapshot。它把 v548 policy 从“策略层”推进到“checkpoint replay 层”。

一句话总结：v549 证明 per-seed config-selection policy 能重新驱动真实 checkpoint replay，为后续 held-out 泛化检查建立了可执行入口。
