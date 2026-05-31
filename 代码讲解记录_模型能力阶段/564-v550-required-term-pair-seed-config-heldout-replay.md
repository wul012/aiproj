# v550 required-term pair seed config held-out replay 代码讲解

## 本版目标和边界

v549 证明 selected policy 可以重新 replay 已知 prompt shape。v550 进一步测试 prompt surface 泛化：用同一批 selected config/checkpoint，换成未直接训练的提示形式。

本版不训练新 checkpoint，也不扩大 corpus。它只改变 replay 时的 `scaffold_prompt`，检查 tiny GPT 是否对 `fixed/loss` 映射有一点表面迁移能力。

## 前置链路

输入来自 v548 policy：

- `535` 和 `2535` 使用 `v544-topk2-t080`。
- `1535` 使用 `v546-loss-calibrated-topk2-t080`。

v550 复用 v549 的源报告定位方式，但把 prompt specs 从原始 `fixed:` / `loss:` 换成 held-out surface。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_seed_config_heldout_replay.py`
  - 定义 `DEFAULT_HELDOUT_PROMPT_SPECS`。
  - 读取 v548 policy 和源 stability reports。
  - 对每个 selected seed/config 与每个 held-out spec 执行 generation-profile replay。
- `src/minigpt/model_capability_required_term_pair_seed_config_heldout_replay_artifacts.py`
  - 输出主报告和每个 held-out replay sidecar。
- `scripts/run_model_capability_required_term_pair_seed_config_heldout_replay.py`
  - CLI 入口，默认跑三种 held-out prompt specs。
- `tests/test_model_capability_required_term_pair_seed_config_heldout_replay.py`
  - 覆盖 ready、not-ready、artifact sidecar 和路径定位。

## Held-Out Prompt Specs

默认 specs：

```python
DEFAULT_HELDOUT_PROMPT_SPECS = (
    {"spec_id": "colon-spaced", "fixed_prompt": "fixed: ", "loss_prompt": "loss: "},
    {"spec_id": "equals", "fixed_prompt": "fixed=", "loss_prompt": "loss="},
    {"spec_id": "arrow", "fixed_prompt": "fixed -> ", "loss_prompt": "loss -> "},
)
```

每个 spec 会生成一个只含 fixed/loss 两个 term 的 replay source report。这样 `pair_full` 的含义仍然清楚：同一个 selected checkpoint 在该 prompt surface 下是否同时生成 fixed 和 loss。

## 真实结果

v550 真实运行结果：

```text
heldout_pair_full_count=8
row_count=9
heldout_pair_full_rate=0.8889
heldout_all_pair_full=False
```

唯一失败行：

```text
spec_id=equals
seed=1535
selected_config_id=v546-loss-calibrated-topk2-t080
replay_pair_full=False
```

这说明当前 selected policy 已经能跨大多数提示表面迁移，但 `1535` 对 equals prompt 仍存在缺口。

## 边界解释

v550 的结论比 v549 强，但仍不是生产泛化证明。它只覆盖三个 seed、三个 prompt surface 和 tiny checkpoint。它说明“提示表面迁移开始出现”，也指出下一步应定向分析 `1535 + equals`，而不是再盲目加新治理报告。

## 测试覆盖

测试覆盖：

- fake pair-full generator 下 held-out replay ready。
- fake fixed-only generator 下 not-ready。
- sidecar report 写入 `heldout-replay-reports/<spec>/<config>/seed-<seed>`。
- 输入目录定位默认 v548 selection JSON。

## 归档角色

`e/550` 保存了主 held-out report、每个 held-out replay sidecar、HTML 截图和 snapshot。它是后续定向修复 seed `1535` equals prompt 的证据入口。

一句话总结：v550 证明 selected config policy 对 held-out prompt surface 有 `8/9` 的迁移信号，同时把剩余缺口收敛到一个明确 case。
