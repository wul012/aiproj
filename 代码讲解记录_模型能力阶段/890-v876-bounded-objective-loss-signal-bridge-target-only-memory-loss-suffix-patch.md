# v876：bounded objective loss signal bridge target-only memory loss-suffix patch

## 本版目标和边界

v876 的目标是把 v875 的 `loss_suffix_uptake_gap` 诊断转成下一轮训练语料。v875 说明模型已经稳定到达 `fixed l`，所以 v876 不再做大而散的 target-only memory，而是构造窄口径的 `loss` 后缀和 `fixed loss` pair patch。

本版不训练，不 replay，不声称模型能力提升。它只生成 JSONL examples 和 patched corpus，供 v877 训练使用。

## 前置链路

```text
v874 target-only memory replay partial-hit
 -> v875 loss suffix diagnostic
 -> v876 loss-suffix patch corpus
```

这条链路比前面更细：先证明有 partial signal，再定位缺口，再写对应的训练样本。

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch.py`
  - v876 核心 patch 构建模块。
  - 读取 v875 diagnostic、v874 replay comparison 和 v873 prepared corpus。
  - 校验 `all_cases_loss_prefix=True` 和 `loss_hit_case_count=0`。
  - 生成 pair、loss suffix、prefix bridge、minimal label pair 四类样本。

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch_artifacts.py`
  - 输出 JSON、CSV、JSONL、corpus、TXT、Markdown、HTML。

- `scripts/build_bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch.py`
  - CLI 入口。
  - 支持 `--partial-hit-diagnostic`、`--replay-comparison`、`--source-corpus`、`--out-dir`、`--require-patch-ready`、`--force`。

- `tests/test_bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch.py`
  - 覆盖成功构建、非 all-prefix 输入阻断、writer 和 CLI。

## 样本结构

每条 replay case 生成五条样本：

```text
target_pair_memory x2
loss_suffix_memory x1
loss_prefix_bridge x1
minimal_label_pair x1
```

三条 case 共 15 条，再加 12 条 global memory，总数：

```text
patch_example_count=27
```

其中最关键的是：

```text
fixed l
loss
fixed loss
```

这条 `loss_prefix_bridge` 直接对应 v874/v875 观察到的 `fixed l`。它的目的不是让模型背答案，而是把已出现的 partial continuation 继续推到完整 `loss`。

## 真实构建命令

```text
python -B scripts/build_bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch.py
  --partial-hit-diagnostic e/875/解释/bounded-objective-loss-signal-bridge-target-only-memory-partial-hit-diagnostic
  --replay-comparison e/874/解释/bounded-objective-loss-signal-bridge-target-only-memory-replay-comparison
  --source-corpus e/873/解释/bounded-objective-loss-signal-bridge-target-only-memory-training-run/run/prepared_corpus.txt
  --out-dir e/876/解释/bounded-objective-loss-signal-bridge-target-only-memory-loss-suffix-patch
  --require-patch-ready
  --force
```

输出：

```text
decision=bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch_ready
patch_example_count=27
target_pair_example_count=12
loss_suffix_example_count=9
loss_prefix_bridge_example_count=3
minimal_label_pair_example_count=3
decoder_anchor_example_count=0
model_quality_claim=loss_suffix_patch_only
```

## 测试覆盖

focused 测试：

```text
python -m pytest tests/test_bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch.py -q -o cache_dir=runs/pytest-cache-v876-focus
```

结果：

```text
3 passed
```

测试保护：

- all-prefix diagnostic 能生成 27 条 patch examples。
- 如果 `all_cases_loss_prefix=False`，patch 必须失败。
- writer 和 CLI 输出 JSON、CSV、JSONL、corpus、TXT、Markdown、HTML。

## 运行证据

- 解释目录：`e/876/解释/bounded-objective-loss-signal-bridge-target-only-memory-loss-suffix-patch/`
- 截图目录：`e/876/图片/`
- Playwright MCP 截图：`e/876/图片/v876-bounded-objective-loss-signal-bridge-target-only-memory-loss-suffix-patch-html.png`

## 一句话总结

v876 将 `fixed l` 的瓶颈转成精确训练语料，下一版可以直接测试 loss-suffix patch 是否让 replay 从 partial-hit 进入 full pair。
