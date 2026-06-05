# v904 target-hidden tokenizer-covered holdout real replay 代码讲解

## 本版目标和边界

v904 是 v902/v903 之后的真实模型执行版。

v902 构造了 target-hidden tokenizer-covered holdout suite，v903 证明这套 suite 的 scoring contract 可用。v904 则加载真实 v890 checkpoint/tokenizer，对这 5 个 target-hidden prompt 做真实续写，并判断 continuation 是否同时包含 `fixed` 和 `loss`。

明确不做：

- 不重新训练模型。
- 不修改 v902 suite。
- 不把 replay 通过直接升级为 promotion。
- 不把 bounded target-hidden suite 通过解释成广义语言模型能力。

本版的结论必须保守：真实 replay 通过是强信号，但还需要下一版 review。

## 前置链路

本版使用：

- v902 target-hidden holdout suite。
- v903 target-hidden holdout dry-run。
- v890 real checkpoint/tokenizer。

前置能力关系是：

```text
v901 review blocks leaked v900 result
  -> v902 builds target-hidden tokenizer-covered suite
  -> v903 dry-runs positive/negative scoring
  -> v904 real-replays v890 checkpoint
```

## 关键文件

### `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_real_replay.py`

这是本版核心 real replay builder。

入口函数：

```python
build_target_hidden_tokenizer_covered_holdout_real_replay(...)
```

输入：

- v902 suite report。
- v903 dry-run report。
- checkpoint path。
- tokenizer path。
- device。
- 可选 generator runner，供测试注入 fake continuation。

输出：

- `status`
- `decision`
- `check_rows`
- `replay_rows`
- `replay_errors`
- `summary`
- `interpretation`

### `locate_target_hidden_tokenizer_covered_holdout_suite`

定位 v902 suite JSON。它支持传目录或 JSON 文件，传目录时自动拼接：

```text
bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_suite.json
```

### `locate_target_hidden_tokenizer_covered_holdout_dry_run`

定位 v903 dry-run JSON。它同样支持目录或文件。

这两个 locator 让 v904 可以稳定消费上游产物，不依赖人工复制路径。

### `_generate_case`

`_generate_case` 是真实模型执行入口。

它从 suite case 的 `prompt_case` 中读取：

- `prompt`
- `max_new_tokens`
- `temperature`
- `top_k`
- `seed`

然后构造 `GenerationRequest`，调用：

```python
MiniGPTGenerator(checkpoint, tokenizer, device=device).generate(request).to_dict()
```

这意味着 v904 不是 dry-run，也不是 fixture replay，而是真实加载 checkpoint 进行生成。

### `_run_cases`

`_run_cases` 遍历所有 suite cases：

- 调用 generator。
- 取出 continuation。
- 用 `_score` 判断是否命中 expected terms。
- 写出 replay row。
- 捕获异常到 `replay_errors`。

每条 replay row 包含：

- `case_id`
- `source_case_id`
- `prompt`
- `continuation`
- `generated`
- `hit_terms`
- `missed_terms`
- `case_pass`
- generation 参数。

这些字段既能给 HTML 展示，也能给下一版 review 读取。

### `_checks`

v904 的 checks 分成三类。

上游证据检查：

- v902 suite 必须 pass。
- v902 suite ready 字段必须为 true。
- v902 的 `target_hidden_case_count` 必须等于 case count。
- v903 dry-run 必须 pass。
- v903 dry-run ready 字段必须为 true。

执行环境检查：

- checkpoint 文件存在。
- tokenizer 文件存在。
- case 非空。

执行完整性检查：

- 每个 case 都执行。
- 没有 replay errors。

注意：这里没有把模型通过作为 `status=pass` 的必要条件。`status` 表示 replay 执行链路是否有效，模型是否通过写在 summary 和 decision 里。这让失败 replay 也能成为有效诊断证据。

### `_summary`

summary 汇总模型结果：

- `passed_case_count`
- `failed_case_count`
- `any_hit_case_count`
- `zero_hit_case_count`
- `pass_rate`
- `holdout_model_quality_ready`
- `model_quality_claim=target_hidden_holdout_replay_only`
- `next_step=review_target_hidden_tokenizer_covered_holdout_replay_result`

本版真实结果是 5/5，所以：

```text
holdout_model_quality_ready=True
pass_rate=1.0
```

但 `promotion_ready=False` 仍然保留，因为必须先 review。

### `_decision`

decision 分三种：

- 输入或执行失败：`fix_..._inputs`
- 全部 case 通过：`..._passed_review_required`
- 部分命中：`..._partial_model_gap`
- 零命中：`..._zero_hit_model_gap`

v904 真实运行走的是 passed review required 分支。

### `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_real_replay_artifacts.py`

这是报告渲染层。

它输出：

- JSON：完整 replay 证据。
- CSV：复用已有 bounded replay CSV writer。
- TXT：命令行摘要。
- Markdown：人读 replay rows。
- HTML：截图证据。

HTML 展示：

- quality ready。
- passed count。
- any hit / zero hit。
- pass rate。
- replay rows 的 continuation。
- checks。

### `scripts/run_bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_real_replay.py`

这是本版 CLI。

关键参数：

```powershell
--holdout-suite
--dry-run
--checkpoint
--tokenizer
--device
--require-execution-pass
--require-model-pass
--force
```

真实归档运行只用了 `--require-execution-pass`，没有使用 `--require-model-pass`。这是有意的：即使模型不过，也应该保留 replay 诊断证据。

### `tests/test_bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_real_replay.py`

测试覆盖：

- checkpoint/tokenizer 不存在时，即使 fake runner 能返回 continuation，也必须失败。
- fake runner 返回 `fixed loss` 时，模型质量 ready。
- fake runner 返回 `fixed only` 时，执行通过但模型质量不 ready。
- artifacts 和 CLI 都能连通。

测试把“执行通过”和“模型通过”分开，是 v904 的关键工程约束。

## 真实运行结果

真实 v904 使用 v890 checkpoint/tokenizer，5 个 target-hidden case 全部通过：

```text
status=pass
decision=bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_real_replay_passed_review_required
holdout_model_quality_ready=True
passed_case_count=5
any_hit_case_count=5
zero_hit_case_count=0
pass_rate=1.0
promotion_ready=False
model_quality_claim=target_hidden_holdout_replay_only
next_step=review_target_hidden_tokenizer_covered_holdout_replay_result
```

Continuation 摘要：

```text
target-hidden-answer_learned_pair -> " fixed loss\n\n\n\nfixed los"
target-hidden-return_target_pair -> " fixed loss\n\n\n\n\n\nfixed l"
target-hidden-contrast_route_pair -> " fixed loss\n\n\n\n\n\nfixed l"
target-hidden-jsonish_answer_terms -> " fixed loss\n\n\n\n\n\n\n\n\n\nfix"
target-hidden-self_check_pair -> " fixed loss\n\n\n\n\nfixed lo"
```

## 截图和归档

归档位置：

- `e/904/解释/说明.md`
- `e/904/图片/v904-bounded-objective-loss-signal-bridge-target-only-memory-target-hidden-tokenizer-covered-holdout-real-replay.png`
- `e/904/解释/bounded-objective-loss-signal-bridge-target-only-memory-target-hidden-tokenizer-covered-holdout-real-replay`

截图证明：

- `Quality ready=True`
- `Passed=5/5`
- `Any hits=5`
- `Pass rate=1.0`
- `Promotion=False`

## 后续链路

下一版应做 review，而不是立刻 promotion。

review 要回答：

- 5 个 target-hidden prompt 是否仍然过于同质。
- `learned pair`、`target pair` 等措辞是否仍然构成强提示。
- 是否需要更宽 prompt family。
- 是否可以进入下一层 promotion gate。

这会把 v904 的强信号转成更稳的工程判断。

## 一句话总结

v904 首次在 target-hidden holdout 上给出真实 checkpoint 5/5 通过证据，但仍保持 review gate，把模型能力结论从“可喜结果”放回可复核的工程链路里。
