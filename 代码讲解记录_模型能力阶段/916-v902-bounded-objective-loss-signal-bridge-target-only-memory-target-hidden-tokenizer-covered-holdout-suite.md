# v902 target-hidden tokenizer-covered holdout suite 代码讲解

## 本版目标和边界

v902 的目标是补上 v901 指出的评估漏洞：v900 虽然在 v898 tokenizer-covered holdout suite 上得到 5/5，但 v901 发现这 5 个 prompt 全部直接包含目标词 `fixed` 或 `loss`，所以不能把它当作更强的模型能力证据。

本版做一件事：重新构造一套 target-hidden tokenizer-covered holdout suite。

明确不做：

- 不重新训练模型。
- 不运行 checkpoint replay。
- 不把 suite construction 解释成模型质量提升。
- 不改变 scoring contract，仍要求 continuation 同时包含 `fixed` 和 `loss`。

这使 v902 成为 v901 到 v903 的中间证据：先把测试题修干净，再进入 dry-run 和 real replay。

## 前置链路

本版接在以下链路之后：

- v898 构造 tokenizer-covered holdout suite，解决中文 prompt 不在 v890 tokenizer 里的问题。
- v899 对 v898 suite 做正反 dry-run，确认 scoring contract 本身可执行。
- v900 用真实 v890 checkpoint replay v898 suite，得到 5/5。
- v901 审核 v900 replay，发现 v898 prompt 泄漏目标词，阻断 promotion。

v902 直接消费 v901 的 `next_step=build_target_hidden_tokenizer_covered_holdout_suite`，并复用 v898 的 suite shape。

## 关键文件

### `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_suite.py`

这是本版核心 builder。

主要职责：

- 定位 v901 replay review JSON。
- 定位 v898 source holdout suite JSON。
- 读取 v890 tokenizer。
- 构造 5 个 target-hidden candidate cases。
- 检查 prompt 是否 tokenizer-covered。
- 检查 prompt 是否隐藏 `fixed/loss`。
- 输出 suite JSON 的完整判断结果。

核心入口是：

```python
build_target_hidden_tokenizer_covered_holdout_suite(...)
```

它的输入是已经解析好的 replay review、source holdout suite，以及 tokenizer 路径。输出是一个 dict report，包含：

- `status`
- `decision`
- `failed_count`
- `issues`
- `check_rows`
- `coverage_rows`
- `benchmark_suite`
- `summary`
- `interpretation`

### `target_hidden_candidate_prompt_seed_text`

这个函数把本版 5 个 prompt 拼成训练 tokenizer 覆盖测试用的 seed text。它不是训练语料，只是为了单测和覆盖判断复用同一批 prompt。

这样做避免测试里手写另一份 prompt 后出现漂移。

### `_candidate_prompt_specs`

这里定义 5 个新的 prompt：

```text
answer with the learned pair
answer:

return the target pair
output:

contrast route pair
result:

jsonish answer_terms target pair
answer_terms:

self check requires target pair
final answer:
```

它们的共同点：

- 都是 ASCII。
- 都能被 v890 tokenizer 覆盖。
- 都不含 `fixed`。
- 都不含 `loss`。
- 仍要求下游 continuation 生成 `fixed/loss`。

这就是 v902 相比 v898 的关键变化。

### `_coverage_rows`

`_coverage_rows` 对每个 candidate case 做两类检查：

- `prompt_unknown_count`：prompt 中有多少字符不在 tokenizer vocabulary。
- `leaked_terms`：prompt 是否直接包含 expected terms。

然后派生：

- `tokenizer_covered = prompt_unknown_count == 0`
- `target_hidden = not leaked_terms`

这两个字段是 v902 的核心证据。v898 只证明 tokenizer-covered，v902 进一步要求 target-hidden。

### `_checks`

本版 check rows 保护 8 个边界：

- v901 replay review 必须是 pass。
- v901 必须明确把 next step 指向 target-hidden suite。
- v898 source suite 必须是 pass。
- tokenizer 文件必须存在。
- candidate case count 必须继承 source case count。
- coverage rows 必须覆盖所有 case。
- 所有 prompt 必须 tokenizer-covered。
- 所有 prompt 必须 target-hidden。

其中最后两条合起来定义了本版是否真正解决 v901 指出的泄漏问题。

### `_suite`

`_suite` 生成下游可消费的 benchmark suite：

- `suite_name=route-promotion-objective-level-contrast-target-hidden-tokenizer-covered-holdout-suite`
- `suite_version=v902`
- `boundary=target_hidden_ascii_tokenizer_covered_holdout_only`
- `model_quality_claim=not_claimed`
- `proposed_next_artifact=bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_dry_run`

`cases` 只有在 `status=pass` 时输出，防止失败情况下的半成品 suite 被误用。

### `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_suite_artifacts.py`

这是本版报告渲染层。

它输出：

- JSON：完整机器可读证据。
- CSV：coverage rows，适合快速检查每个 case 的 covered/hidden 状态。
- TXT：命令行摘要。
- Markdown：人读归档。
- HTML：截图证据。

v902 没有继续复用 v898 的 renderer，而是显式渲染：

- `target_hidden_case_count`
- `source_target_leakage_case_count`
- `target_hidden`
- `leaked_terms`

这样 HTML 和 CSV 都能直接证明本版修的不是普通 coverage，而是 target leakage。

### `scripts/build_bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_suite.py`

这是本版 CLI。

关键参数：

```powershell
--replay-review
--source-holdout-suite
--tokenizer
--out-dir
--require-suite-ready
--force
```

CLI 支持传 JSON 文件或输出目录。它会自动通过 locator 找到固定文件名，构造 report，写出 5 种产物，并在 `--require-suite-ready` 下把失败转换为退出码 1。

这让 v902 可以进入本地验证、CI 验证或后续脚本串联。

### `tests/test_bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_suite.py`

测试覆盖 4 个场景：

- 正常构造 suite：5 个 case、5 个 covered、5 个 target-hidden、0 unknown token。
- v901 review 没有路由到 target-hidden suite 时失败。
- tokenizer 不覆盖 prompt 时失败。
- artifacts 和 CLI 都能写出预期文件。

测试里还明确断言每个 prompt 不包含 `fixed` 和 `loss`。这条断言直接保护 v901 发现的问题不要回归。

## 真实运行结果

本版真实运行使用：

- v901 review。
- v898 source suite。
- v890 tokenizer。

输出摘要：

```text
status=pass
failed_count=0
candidate_case_count=5
tokenizer_covered_case_count=5
target_hidden_case_count=5
candidate_prompt_unknown_token_count=0
source_target_leakage_case_count=5
promotion_ready=False
model_quality_claim=suite_construction_only
next_step=run_target_hidden_tokenizer_covered_holdout_dry_run
```

这说明 v902 成功构造了更干净的 holdout suite，但仍然没有证明模型已经具备目标能力。

## 截图和归档

运行证据放在：

- `e/902/解释/说明.md`
- `e/902/图片/v902-bounded-objective-loss-signal-bridge-target-only-memory-target-hidden-tokenizer-covered-holdout-suite.png`
- `e/902/解释/bounded-objective-loss-signal-bridge-target-only-memory-target-hidden-tokenizer-covered-holdout-suite`

HTML 截图用于确认：

- `Status=pass`
- `Covered cases=5`
- `Target-hidden cases=5`
- `Unknown tokens=0`
- coverage rows 中每行 `Target Hidden=True`

## 后续链路

下一版最自然的动作是 v903：对 v902 suite 做 dry-run。

dry-run 应该继续保守：

- 正例 continuation `fixed loss` 应通过 5/5。
- 负例 continuation 不含完整 `fixed/loss` 时应失败。
- 不运行模型。
- 不声明 promotion。

只有 dry-run 证明 scoring contract 自身没问题后，才进入真实 checkpoint replay。

## 一句话总结

v902 把 v901 的目标词泄漏问题转成一套可复核、tokenizer-covered、target-hidden 的新 holdout suite，让后续模型能力验证不再被 prompt 直接泄漏污染。
