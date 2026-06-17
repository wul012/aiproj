# v1182 MiniGPT grokking paired contrast 代码讲解

## 本版目标与边界

v1182 的目标，是把 v1179-v1181 已经建立起来的 grokking 证据链，再压缩成最容易向人解释的一张“同 seed 成对对照表”。v1179 已经完成真实训练，证明在模块加法任务上，weight decay arm 能够出现 delayed grokking，而 no-decay arm 只能记住训练集、不能在预算内泛化。v1180 证明这个结论能从 row summary 复核。v1181 进一步证明完整曲线能压缩出一致阶段：weight decay arm 是 `delayed_grok`，no-decay arm 是 `memorized_only_censored`。

但是 v1181 的 phase table 仍然是一行一个 seed/arm。读者如果想理解“同一个 seed 下，只有 weight decay 这个变量变了，结果发生了什么差异”，需要自己把两行拼起来看。v1182 就把这一步显式化：每个 seed 只输出一行，左侧代表 `weight_decay_on`，右侧代表 `weight_decay_off`，并计算 final validation gain、记忆步是否匹配、no-decay 是否 censored、with-decay 是否 delayed grok、with-decay 是否更早停止等字段。这样，weight decay 的 counterfactual 解释变得更短、更透明。

本版仍然有非常明确的边界。第一，不重新训练模型；输入是 v1181 的 phase report。第二，不重新解释原始曲线；曲线到 phase 的压缩已经由 v1181 完成，v1182 只把 phase rows 成对重排。第三，不扩大 v1179 的模型能力声明；这依然是 toy-scale modular addition 上的训练动力学案例，不是生产大模型质量证明。第四，不把 weight decay 说成普遍因果定律；本版只能说明在 v1179 这个受控实验里，同 seed、同 split、同 init 的 paired contrast 支持 weight-decay-driven grokking 这个局部结论。

## 前置链路

v1182 的直接输入是：

```text
f/1181/解释/grok_trajectory_phases_v1181/grok_trajectory_phases_v1181.json
```

这个输入已经包含 v1181 生成的 `phase_rows`。每个 seed 有两行：

- `arm=weight_decay_on`，正常情况下 phase 是 `delayed_grok`。
- `arm=weight_decay_off`，正常情况下 phase 是 `memorized_only_censored`。

v1182 的价值不是发明新指标，而是把这两行合成一行。这个设计看起来朴素，但对工程可读性很重要：机器学习实验里的“对照组”如果分散在多行、多文件、多图里，读者很容易只记住正向 arm 的漂亮曲线，忽略 no-decay arm 同样 memorized 的事实。v1182 把“两个 arm 都记住训练集，但只有 weight decay arm 泛化”写成同一行字段，从而降低误读概率。

## 新增模块

核心模块是 `src/minigpt/grok_paired_contrast_v1182.py`。它没有修改 v1181 文件，而是新增独立模块。原因和最近几版的拆分原则一致：v1181 负责 curve-to-phase，v1182 负责 phase-to-pair。两个转换的输入输出不同、检查项不同、读者用途也不同，分开维护更清楚。

模块公开入口包括：

- `locate_phase_report(path)`：支持传入 JSON 文件或输出目录。如果传入目录，就自动定位 `grok_trajectory_phases_v1181.json`。
- `read_json_report(path)`：读取 JSON object，复用 `report_utils.read_json_object`。
- `build_grok_paired_contrast_report(...)`：本版核心 builder，读取 phase report，生成 pair rows、summary、check rows。
- `write_grok_paired_contrast_outputs(report, out_dir)`：复用可读性报告工具写 JSON、CSV、txt、Markdown、HTML。
- `resolve_exit_code(report, require_pass=False)`：给 CLI 使用，支持 `--require-pass` 失败返回 1。

这些入口延续了近期 MiniGPT governance/report 模块的惯例：builder 只做纯数据转换和检查，writer 只做输出，CLI 只做参数解析和目录准备。这样既便于单测，也便于后续版本复用 builder。

## 输入模型

v1182 输入的是 v1181 phase report，核心字段有两个。

第一是 `summary`。这里读到：

- `seed_count`
- `source_status`
- `source_decision`
- `boundary`

这些字段决定 v1182 是否可以信任上游。特别是 `boundary=curve_phase_compression_only_no_training_rerun`，它提醒读者：v1182 是对 v1181 phase report 的二次整理，不是训练复现。

第二是 `phase_rows`。每个 phase row 包含：

- `seed`
- `arm`
- `phase`
- `memorized`
- `grokked`
- `t_mem`
- `t_gen`
- `grok_gap`
- `steps_run`
- `low_val_plateau_rate`
- `final_val_acc`

v1182 的 `_pair_rows(...)` 会按 seed 聚合这些行。它只接受两个 arm 名称：`weight_decay_on` 和 `weight_decay_off`。其他 arm 会被忽略。这是有意的，因为本版是专门解释 v1179 的 paired weight-decay ablation，不是通用多臂实验聚合器。

## Pair Row 的生成

`_pair_rows(phase_rows)` 会先构造一个字典：

```python
by_seed: dict[int, dict[str, dict[str, Any]]]
```

每个 seed 下最多有两个条目：

- `weight_decay_on`
- `weight_decay_off`

然后按 seed 排序，调用 `_one_pair_row(seed, on=..., off=...)` 生成输出行。

`_one_pair_row` 是本版最核心的函数。它从两个 phase row 中抽取字段，并计算几个关键差异：

- `t_mem_delta = off_t_mem - on_t_mem`
- `final_val_gain = on_final_val_acc - off_final_val_acc`
- `steps_saved_by_grok_stop = off_steps_run - on_steps_run`

其中 `final_val_gain` 是最直观的能力差异。真实 v1179/v1181 数据中，mean final validation gain 是 `0.8003984`，min final validation gain 仍有 `0.753687`。这意味着不是某一个 seed 特别漂亮，而是所有 seed 都有很大的验证集差距。

`t_mem_delta` 用来保护解释边界。如果 on/off 两个 arm 的训练集记忆时间差异很大，那么就不能说“它们都先同样记住训练集，后面只在泛化上分开”。真实结果里 5 个 seed 的 `t_mem` 都是 100，`matched_memorization_count=5`。

`steps_saved_by_grok_stop` 不是性能 claim，而是运行过程事实：with-decay arm 一旦 confirmed grok 就 early stop，而 no-decay arm 因为没有泛化，会跑满预算。真实均值是 `24760.0`。这个字段帮助读者理解为什么 no-decay 行的 `steps_run` 长得多：它不是更努力训练后泛化了，而是消耗预算仍然没有出现 `t_gen`。

## Pair Status

每个 pair row 会得到一个 `pair_status`。正常情况下是：

```text
weight_decay_counterfactual
```

它要求同时满足：

- on/off 两个 arm 都 memorized。
- 两个 arm 的 `t_mem` 一致。
- on arm phase 是 `delayed_grok`。
- off arm phase 是 `memorized_only_censored`。
- `final_val_gain > 0`。
- `steps_saved_by_grok_stop > 0`。

如果这些条件不满足，就标成：

```text
pair_needs_review
```

这不是直接报错，而是保留行级解释；最终 report 是否 pass 由 check rows 决定。这样的设计比直接丢弃坏 pair 更好，因为如果将来某个 seed 失败，读者能在 CSV/HTML 里看到是哪一对出了问题。

## Summary 和检查项

`_paired_summary(...)` 汇总 pair rows，输出：

- `matched_memorization_count`
- `on_delayed_grok_count`
- `off_memorized_censored_count`
- `no_decay_censored_count`
- `mean_final_val_gain`
- `min_final_val_gain`
- `mean_steps_saved_by_grok_stop`
- `longest_delay_seed`
- `largest_final_val_gain_seed`

真实 v1182 运行结果是：

- `pair_count=5`
- `matched_memorization_count=5`
- `on_delayed_grok_count=5`
- `off_memorized_censored_count=5`
- `no_decay_censored_count=5`
- `mean_final_val_gain=0.8003984`
- `min_final_val_gain=0.753687`
- `mean_steps_saved_by_grok_stop=24760.0`
- `longest_delay_seed=1341`
- `largest_final_val_gain_seed=1339`

这些数字直接构成最短的解释：同 seed、同记忆步，weight decay arm 泛化，no-decay arm 不泛化；泛化后的验证集差距很大。

检查项由 `_checks(...)` 生成。主要包括：

`source_phase_report_pass` 要求 v1181 上游是 pass。

`source_phase_decision_consistent` 要求上游 decision 是 `grokking_phase_profile_consistent`，防止拿错误阶段报告做成对解释。

`phase_rows_present` 要求 phase rows 数量等于 `seed_count * 2`。

`seed_pairs_complete` 要求 pair 数等于 seed_count。

`matched_memorization_all_pairs` 要求所有 pair 都在同一步完成记忆。这是 counterfactual 解释的底座。

`on_delayed_grok_all_pairs` 要求所有 on arm 都是 delayed grok。

`off_memorized_censored_all_pairs` 要求所有 off arm 都是 memorized-only censored 且没有 `t_gen`。

`final_validation_gain_large` 要求最小 final validation gain 不低于阈值，默认 `0.70`。这防止虽然方向正确，但差异很小的结果被讲成强对照。

`grok_stop_saves_steps` 要求每对里 no-decay arm 的 steps_run 都大于 on arm。这不是速度优化 claim，只是确认 no-decay arm 不是因为更早停止才没泛化。

`boundary_present` 要求继承 v1181 的 no-rerun boundary。

## CLI 入口

新增脚本是 `scripts/analyze_grok_paired_contrast_v1182.py`。真实运行命令为：

```powershell
python scripts\analyze_grok_paired_contrast_v1182.py f\1181\解释\grok_trajectory_phases_v1181 --out-dir f\1182\解释\grok_paired_contrast_v1182 --require-pass --force
```

它支持：

- `--min-final-val-gain`：默认 0.70，控制 paired contrast 的最小验证集收益阈值。
- `--require-pass`：如果 report 失败，返回 1。
- `--force`：覆盖已有输出目录。

这和 v1180/v1181 的 CLI 风格一致，后续如果要做一键链路脚本，也能顺序调用。

## 输出产物

本版输出在：

```text
f/1182/解释/grok_paired_contrast_v1182/
```

包含：

- `grok_paired_contrast_v1182.json`
- `grok_paired_contrast_v1182.csv`
- `grok_paired_contrast_v1182.txt`
- `grok_paired_contrast_v1182.md`
- `grok_paired_contrast_v1182.html`

截图在：

```text
f/1182/图片/grok-paired-contrast-v1182.png
```

JSON 是完整机器证据，CSV 是最适合比较 seed pair 的表，HTML 用于人工阅读和截图归档。

## 测试覆盖

新增测试文件是 `tests/test_grok_paired_contrast_v1182.py`。它覆盖了六类情况。

`test_builds_paired_counterfactual_rows` 验证正常 fixture 能生成 pass，pair 数、matched memorization、no-decay censored 和 min final gain 都正确。

`test_missing_off_pair_fails_pair_completeness` 删除一个 off arm，确认 rows 数量和 matched memorization 检查会失败。

`test_mismatched_memorization_step_fails` 把 off arm 的 `t_mem` 改成不同 step，确认 matched memorization 检查失败。

`test_no_decay_grok_breaks_counterfactual` 把 no-decay arm 改成 delayed grok，确认 off censored 检查失败。

`test_small_final_gain_fails_threshold` 把 off arm final val 提高，导致 final gain 不够，确认阈值检查失败。

`test_outputs_and_cli_are_wired` 验证 writer 和 CLI 都能生成 JSON/HTML，并在 `--require-pass` 下返回 0。

本地新增测试结果是 `6 passed`。完整收口时还会跑 v1179-v1182 grokking 链路聚焦测试、source encoding、diff check 和 GitHub Actions。

## 链路角色

v1182 是一个解释型工程版本。它不让模型更强，但让模型实验的因果叙事更稳。过去三版已经有实验、复核、阶段解释；本版把阶段解释压成 paired counterfactual，是最适合写进报告或答辩材料的一层。

如果只展示 v1179 的正向曲线，读者可能会以为模型“训练久了自然泛化”。如果展示 v1182 的 paired table，读者能看到：同一个 seed 下，no-decay 也能很快记住训练集，但 40000 step 仍不泛化；weight decay arm 在同样记住训练集之后，经历长平台，然后泛化到高验证准确率。这才是 grokking 现象里最值得讲的机制差异。

## 一句话总结

v1182 把 v1179 的 weight-decay grokking 结果整理成每个 seed 一行的成对反事实证据：同样记忆训练集，只有 weight decay arm 进入 delayed grok，而 no-decay arm 在预算内停留于记忆不泛化。
