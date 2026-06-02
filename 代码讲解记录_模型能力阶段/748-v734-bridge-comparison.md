# v734 bridge comparison

## 本版目标和边界

v734 的目标是比较 v729 和 v733 两个真实训练结果。

本版不训练模型、不生成 corpus。它只读两个 training run report，判断 direct-prompt bridge patch 是否带来收益。

## 前置链路

```text
v729 objective-structure training
 -> hit count 0, non-term surface
v731 direct-prompt bridge patch
v732 bridge corpus
v733 bridge training
 -> hit count 0, loss prompt fixed pollution
v734 bridge comparison
 -> no improvement, pollution introduced
```

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_readiness_bridge_comparison.py`
  - 读取两个 training run。
  - 计算 hit delta、pollution count、non-term surface count。
  - 输出 bridge route 的收益判断。
- `src/minigpt/model_capability_required_term_pair_readiness_bridge_comparison_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
- `scripts/run_model_capability_required_term_pair_readiness_bridge_comparison.py`
  - CLI 入口，要求 `--objective` 和 `--bridge`。
- `tests/test_model_capability_required_term_pair_readiness_bridge_comparison.py`
  - 覆盖 no-improvement with pollution、improvement、五格式输出。

## 核心比较字段

v734 的 summary：

```text
objective_default_hit_count=0
bridge_default_hit_count=0
default_hit_delta=0
bridge_improved=False
bridge_loss_prompt_fixed_pollution_count=1
bridge_pollution_introduced=True
failure_shape_changed=True
```

decision：

```text
pair_readiness_bridge_no_improvement_introduced_fixed_pollution
```

## 工程判断

这版的价值在于避免继续错误迭代。

v733 虽然加入了 raw `fixed=` / `loss=` bridge rows，但并没有恢复 direct hits。更重要的是，它把 v729 的 non-term surface miss 变成了 `loss=` fixed pollution。继续沿着“再加 bridge rows”的方向，很可能重复早期 fixed-absorption 问题。

## 证据

运行证据：

- `e/734/解释/model-capability-required-term-pair-readiness-bridge-comparison/`
- `e/734/图片/v734-bridge-comparison.png`

截图显示：

```text
Objective hits=0
Bridge hits=0
Hit delta=0
Pollution=True
```

## 一句话总结

v734 证明 direct-prompt bridge patch 无收益且引入 fixed pollution，应关闭该路线并换 objective surface。
