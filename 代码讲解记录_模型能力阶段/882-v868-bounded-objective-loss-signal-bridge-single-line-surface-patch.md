# v868：bounded objective loss signal bridge single-line surface patch

## 本版目标和边界

v868 的目标是把 v867 的 label echo 诊断落成一个可训练的 patch corpus。v867 已经说明 v865 pair-binding checkpoint 在 v866 replay 中没有输出 `fixed loss`，而是把有限输出预算消耗在 `answer:` / `ans` 这类标签回声上。

本版不训练，也不 replay 新 checkpoint。它只读前置证据，生成 no-anchor 单行 completion surface 样本，把失败 prompt 和目标答案放在同一条文本 surface 上，给下一版训练使用。

边界：

- 不修改 v836 objective contract。
- 不使用 decoder anchor。
- 不声明模型已经学会 `fixed loss`。
- 不把 patch corpus 本身当作模型能力证据。

## 前置链路

```text
v864 pair-binding patch
 -> v865 pair-binding training run
 -> v866 pair-binding replay comparison
 -> v867 pair-binding zero-hit diagnostic
 -> v868 single-line surface patch
```

v868 是对负结果的定向修补：不是继续加训练步数，而是先修训练样本的表面形态。

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge_single_line_surface_patch.py`
  - 核心 patch 构建模块。
  - 读取 zero-hit diagnostic、replay comparison 和 source corpus。
  - 检查 label echo、zero-hit replay、replay ready、diagnostic ready 和 no-anchor。
  - 生成 patch examples 与 patched corpus。

- `src/minigpt/bounded_objective_loss_signal_bridge_single_line_surface_patch_artifacts.py`
  - 输出 JSON、CSV、JSONL、corpus、TXT、Markdown、HTML。
  - HTML 报告展示 stats 和 Patch Examples 表。

- `scripts/build_bounded_objective_loss_signal_bridge_single_line_surface_patch.py`
  - CLI 入口。
  - 支持 `--zero-hit-diagnostic`、`--replay-comparison`、`--source-corpus`、`--out-dir`、`--require-patch-ready`、`--force`。

- `tests/test_bounded_objective_loss_signal_bridge_single_line_surface_patch.py`
  - 覆盖成功构建、label echo 缺失时阻断、writer 和 CLI 链路。

- `e/868/解释/bounded-objective-loss-signal-bridge-single-line-surface-patch/`
  - v868 真实 patch 证据目录。

- `e/868/图片/v868-bounded-objective-loss-signal-bridge-single-line-surface-patch-html.png`
  - Playwright MCP 截图证据。

## 核心输入输出

输入一共有三类：

```text
zero_hit_diagnostic.summary
replay_comparison.summary + replay_rows
source prepared_corpus.txt
```

其中关键判断来自：

```text
bounded_objective_loss_signal_bridge_pair_binding_zero_hit_diagnostic_ready=True
all_cases_label_echo=True
bounded_objective_loss_signal_bridge_pair_binding_replay_comparison_ready=True
any_hit_case_count=0
```

输出的核心字段是：

```text
status
decision
failed_count
issues
patch_examples
patched_corpus_text
loss_signal_bridge_single_line_surface_patch
summary
interpretation
```

`patch_examples` 是后续训练消费的 JSONL 行来源；`patched_corpus_text` 是完整训练语料。两者都是训练输入，不是最终能力证明。

## Patch 样本设计

v868 生成三类样本：

```text
single_line_case_surface
direct_label_surface
completion_surface_single_line
```

第一类直接从 replay rows 的失败 prompt 改写：

```text
Answer with exactly two tokens: fixed loss
answer:
```

变成：

```text
Answer with exactly two tokens: fixed loss answer: fixed loss
```

这让目标答案和 prompt 标签处在同一行，降低 tiny 模型只续写标签的概率。

第二类提供直接标签面：

```text
answer: fixed loss
completion: fixed loss
target: fixed loss
```

第三类保留无标签的纯目标 completion：

```text
fixed loss
```

这避免 patch corpus 只强化 `answer:` / `completion:` 这些前缀。

## 契约检查

`_checks()` 做了几类保护：

- `diagnostic_passed`：v867 诊断必须是 pass。
- `diagnostic_ready`：zero-hit 诊断必须完成。
- `label_echo_confirmed`：必须确认所有 case 都是 label echo。
- `zero_hit_replay`：v866 replay 必须仍是零命中，避免误把 partial/pass 结果走进这个 patch。
- `replay_passed` / `replay_ready`：源 replay comparison 自身必须可用。
- `patch_examples_present`：必须生成训练样本。
- `decoder_anchor_free`：所有样本都必须保持 `decoder_anchor=False`。

这些检查让 v868 只在“零命中 + 标签回声”的狭窄场景启用，避免变成泛化的重写工具。

## 真实运行结果

命令：

```text
python -B scripts/build_bounded_objective_loss_signal_bridge_single_line_surface_patch.py
  --zero-hit-diagnostic e/867/解释/bounded-objective-loss-signal-bridge-pair-binding-zero-hit-diagnostic
  --replay-comparison e/866/解释/bounded-objective-loss-signal-bridge-pair-binding-replay-comparison
  --source-corpus e/865/解释/bounded-objective-loss-signal-bridge-pair-binding-training-run/run/prepared_corpus.txt
  --out-dir e/868/解释/bounded-objective-loss-signal-bridge-single-line-surface-patch
  --require-patch-ready
  --force
```

输出：

```text
status=pass
decision=bounded_objective_loss_signal_bridge_single_line_surface_patch_ready
single_line_surface_patch_ready=True
patch_example_count=14
single_line_case_example_count=6
direct_label_example_count=6
completion_surface_example_count=2
decoder_anchor_example_count=0
model_quality_claim=single_line_surface_patch_only
next_step=train_bounded_objective_loss_signal_bridge_single_line_surface_patch
```

## 测试覆盖

focused 测试：

```text
python -m pytest tests/test_bounded_objective_loss_signal_bridge_single_line_surface_patch.py -q -o cache_dir=runs/pytest-cache-v868-focus
```

结果：

```text
3 passed
```

测试保护了三件事：

- 正常输入能生成 14 条 patch examples，并保持 no-anchor。
- 如果 `all_cases_label_echo=False`，patch 会失败，不会误生成训练语料。
- writer 和 CLI 会输出 JSON、CSV、JSONL、corpus、TXT、Markdown、HTML。

## 运行证据

- 解释目录：`e/868/解释/bounded-objective-loss-signal-bridge-single-line-surface-patch/`
- 截图目录：`e/868/图片/`
- Playwright MCP 截图：`e/868/图片/v868-bounded-objective-loss-signal-bridge-single-line-surface-patch-html.png`

截图确认 HTML 报告可打开，标题、解释、stats 和 Patch Examples 表格可见。

## 一句话总结

v868 把 pair-binding zero-hit 的 label echo 负结果转成 no-anchor 单行 completion surface 训练语料，让下一版可以用真实训练检验这个修补是否比继续加步数更有效。
