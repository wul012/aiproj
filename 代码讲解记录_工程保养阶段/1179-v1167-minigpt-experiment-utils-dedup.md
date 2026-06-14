# 1179 · v1167 · MiniGPT experiment_utils 去重（契约保持保养）

## 本版目标与不做什么

按 AGENTS.md 的重构节奏（3-4 个功能版后做 1 个契约保持的保养版，前两次是 [[1171-v1159-minigpt-train-lm-dedup]] 抽 `train_lm`、v1163 抽 `script_runtime`），把 [[1176-v1164-minigpt-sft-instruction]]、[[1177-v1165-minigpt-sft-pretrain-transfer]]、[[1178-v1166-minigpt-dpo-preference]] 三个连续能力版攒下的实验脚手架重复债还掉。这三个多 seed 实验驱动反复出现三个相同原语：把每 seed 的指标列表聚合成 `(mean, std)`、从实验 config 新建 `MiniGPT`、对权重拍快照供之后 `load_state_dict`。

明确不做：不新增模型能力、不改训练超参、不改报告产物结构；不强行抽取那些只有一个使用方或与上下文耦合的片段。

## 关键文件与链路角色

- 新增 `src/minigpt/experiment_utils.py`，三个纯/近纯函数：
  - `mean_std(values)`：忽略 `None`/`NaN`，空返回 `(nan,0.0)`、单值 std=0。取 v1166 的 NaN-鲁棒版——对 v1164/v1165 不含 NaN 的输入完全等价，对 v1166 的 `last_loss` 列（sft_on_chosen 行为 NaN）必要。
  - `build_minigpt(vocab_size, config, *, dropout=0.0)`：鸭子类型读取 config 的 `block_size/n_layer/n_head/n_embd/use_rope`，返回 CPU 上的 `MiniGPT`（调用方 `.to(device)`）。
  - `clone_state(model)`：detached 状态字典快照。
- 迁移：`sft_instruction_v1164`（删 `_mean_std`+内联构建，删 `import statistics`/`GPTConfig`）、`sft_pretrain_transfer_v1165`（删 `_build`/`_mean_std`/内联 clone）、`dpo_preference_v1166`（删 `_build`/`_clone_state`/`_mean_std`）。
- 新增 `tests/test_experiment_utils.py`。

## 为什么这样划范围（保养版的判断）

抽取的判据是"被 ≥2 个模块逐字节重复、且与上下文低耦合"。`mean_std`（3 份）、`build_minigpt`（3 份，含 v1164 内联）、`clone_state`（v1165 内联 + v1166 函数）满足。**刻意不抽** `_significant`：它只有 v1166 一个使用方，而 v1164/v1165 是把同一 gap-减-合并标准差判据内联进各自的 `_gap`，那里还要 gap 数值本身用于报告——抽成共享函数要么制造单用户导入、要么改动其结构，违背"低风险"原则。这与 v1163 刻意不动 8 个历史脚本是同一种克制。`_param_l2_delta` 同理留在 v1166。

## RNG 一致性：为什么权重不变

最需要论证的是 `build_minigpt` 不改变行为。`MiniGPT.__init__` 用 `self.apply(self._init_weights)` 消耗 torch RNG。把 `MiniGPT(GPTConfig(...))` 这个构造调用原样搬进一个函数，不会改变它在 RNG 流中的位置——同一时刻、同一构造器、同样的字段，故初始化权重逐比特相同。`test_experiment_utils` 用"同 seed 两次 `build_minigpt` 权重逐键相等"钉死这一点。

## 测试如何真实覆盖与契约证据

`test_experiment_utils` 覆盖 `mean_std`（基本统计、单值 0 std、空 nan、忽略 None/NaN）、`build_minigpt`（按 config 字段建模 + 同 seed 确定性）、`clone_state`（取值相等且为独立副本——改活权重不动快照）。**最关键的契约证据是 v1164/v1165/v1166 的既有模块测试零改动仍全绿**（同 v1163 判据），证明三个实验驱动的报告结构、verdict、"pass 当且仅当 task_learned"不变量都没被这次重构动到。全量套件通过。

## 一句话总结

v1167 把 v1164/65/66 里逐字节重复的 `mean_std`/模型构建/状态快照三个原语收进 `experiment_utils.py`，删三处重复、迁三个模块、既有测试零改动全绿，并论证了 `build_minigpt` 的 RNG 一致性——一次克制而干净的契约保持保养，为后续对齐实验备好可复用脚手架。
