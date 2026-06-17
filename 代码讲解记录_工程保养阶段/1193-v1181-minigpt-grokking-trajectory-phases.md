# v1181 MiniGPT grokking trajectory phases 代码讲解

## 本版目标与边界

v1181 的目标，是把 v1179 已经完成的 grokking 真实实验再向“可解释、可复核、可教学展示”推进一层。v1179 训练了一个 1 层 MiniGPT，在 `a + b = c (mod 97)` 的模块加法任务上观察到了典型的 grokking 现象：模型很早记住训练集，但验证集在很长一段时间里仍接近随机水平，随后才突然泛化；并且这个现象只出现在 weight decay arm 中，no-decay ablation 能记忆却不泛化。v1180 已经做了一次证据复核，验证 summary 中的“5/5 grok、0/5 no-decay grok、mean gap、boundary”等关键结论可以从 rows 重新推导出来。

但 v1180 仍然偏“结论复核”：它回答“这个 headline claim 是否能从 rows 推出来”。v1181 解决的是另一个问题：如果要向读者解释 grokking 发生在哪里、为什么这不是普通学习曲线、为什么 no-decay 对照很重要，单看 summary 和十行 rows 还不够直观。v1179 的 JSON 中保存了完整 `curves`，每个 seed、每个 arm 都有按 step 记录的 train/val accuracy。v1181 就把这些曲线压缩成统一的 phase table，把每条曲线标成 `delayed_grok` 或 `memorized_only_censored`，并记录平台期长度、低验证准确率比例、最大验证跳变位置、曲线终点是否与 row summary 对齐等字段。

本版明确不做三件事。第一，不重新训练模型；所有输入都来自 v1179 的归档 JSON，因此 v1181 是“曲线阶段压缩”和“解释性证据整理”，不是新的模型能力实验。第二，不扩大 v1179 的模型质量声明；它仍然只是 toy-scale modular addition 上的训练动力学现象复现，不是大模型能力、生产质量或真实任务泛化声明。第三，不把曲线渲染成新图来替代原始证据；v1181 输出的是表格化 phase report，原始曲线仍然以 v1179 归档为准。

## 前置链路

本版来自最近三版的连续链路：

1. v1179：真实训练实验，生成 `grok_v1179.json/csv/txt/md/html`，其中包含 `summary`、`rows` 和 `curves`。
2. v1180：证据复核，读取 v1179 JSON，从 rows 重建 headline claim，验证 weight-decay-driven grokking 结论没有只依赖人工摘要。
3. v1181：轨迹阶段剖面，继续读取同一个 v1179 JSON，但重点转向 curves，把完整曲线压缩为每个 seed/arm 的阶段解释。

这条路线的价值在于，它把“我跑了一个实验”变成了三个层次的证据链：原始实验数据、结论可复核、过程可解释。对 MiniGPT 这个学习型 AI 工程来说，这比单纯继续追加训练脚本更重要，因为用户不仅需要看到模型结果，还需要理解为什么这个结果成立、哪些边界不能越过。

## 新增模块

本版核心文件是 `src/minigpt/grok_trajectory_phases_v1181.py`。它没有继续修改 v1180 的 `grok_evidence_check_v1180.py`，而是单独新增一个模块，原因很直接：v1180 负责“证据复核”，v1181 负责“轨迹阶段解释”，两个职责虽然都消费 v1179 JSON，但检查对象不同。如果把它们塞进同一个文件，短期看起来省文件，长期会把“检查 headline claim”和“解释 curve phase”两种逻辑缠在一起，不利于维护，也不符合当前仓库避免巨型文件的规则。

模块暴露的入口主要有五个：

- `locate_grok_report(path)`：支持用户传入 JSON 文件，也支持传入输出目录。如果传入目录，就自动寻找 `grok_v1179.json`。这和 v1180 的路径习惯一致，方便 CLI 和测试共用。
- `read_json_report(path)`：读取 JSON object，并使用 `utf-8-sig` 兼容潜在 BOM。它复用 `report_utils.read_json_object`，避免每个版本重复写 JSON 读取样板。
- `build_grok_trajectory_phase_report(...)`：本版最核心的 builder。它读取 summary、rows、curves，生成 phase rows、check rows 和最终 summary。
- `write_grok_trajectory_phase_outputs(report, out_dir)`：复用 `write_readability_outputs` 生成 JSON、CSV、text、Markdown、HTML 五种产物。
- `resolve_exit_code(report, require_pass=False)`：给 CLI 使用。默认结构生成成功就返回 0；如果用户加 `--require-pass`，则 phase report 失败时返回 1。

这些入口保持了项目近期治理工具的一贯风格：builder 是纯逻辑，writer 专门负责产物，CLI 只做参数解析和目录准备。这样测试可以直接测 builder，不必靠 subprocess 才能验证核心逻辑。

## 输入结构

v1181 的输入是 v1179 的 `grok_v1179.json`。这个 JSON 中有三个关键部分。

第一是 `summary`，包含全局配置和结论，例如：

- `seeds=5`
- `weight_decay_on=1.0`
- `weight_decay_off=0.0`
- `verdict=grokking_reproduced_wd_driven`
- `boundary=toy_scale_single_task_modular_addition_grokking_not_a_scaling_claim`

第二是 `rows`，每个 seed/arm 一行，共 10 行。每行包含 `seed`、`weight_decay`、`memorized`、`grokked`、`t_mem`、`t_gen`、`grok_gap`、`val_at_mem`、`final_val_acc`、`steps_run` 等字段。rows 是 v1180 的主要检查对象。

第三是 `curves`，这是 v1181 的重点。它按 weight decay 分组，形如：

```json
{
  "1.0": [[{"step": 0, "train_acc": ..., "val_acc": ...}, ...]],
  "0.0": [[{"step": 0, "train_acc": ..., "val_acc": ...}, ...]]
}
```

每个 weight decay key 对应 5 条曲线，顺序和 rows 中同 arm 的 seed 顺序一致。v1181 会把同一个 arm 下的第 N 条 curve 对齐到同一个 arm 下的第 N 行 row。这个对齐规则非常重要，因为原始 curves 里没有重复保存 seed 字段；seed 信息来自 rows。如果曲线数量缺失，或者 row 没有对应 curve，report 会失败。

## 曲线解析

`_curves_by_weight_decay(value)` 负责把 JSON 中的 curves 转成 `dict[float, list[list[point]]]`。原始 JSON 的 key 是字符串，比如 `"1.0"`、`"0.0"`，模块会用 `number_or_none` 转成 float。每条曲线再由 `_curve_points(curve)` 转成统一点位结构：

```python
{"step": int, "train_acc": float, "val_acc": float}
```

解析时会丢弃不合法点位，并按 step 排序。排序不是为了修改实验事实，而是为了让后续 plateau、jump、endpoint 检查不依赖 JSON 原始顺序。正常 v1179 输出本来就是按 step 递增，排序只是防御性处理。

## Phase Row 的生成

`_phase_rows(...)` 是 rows 和 curves 的对齐层。它维护一个 `indexes` 字典，记录每个 weight decay 已经消费到第几条曲线。遍历 rows 时，遇到 `weight_decay=1.0` 的第一行就取 curves `"1.0"` 下的第一条曲线，遇到第二行就取第二条，以此类推。这样不需要在 curve 内塞 seed，也能保持和 v1179 输出格式兼容。

每一行最终由 `_one_phase_row(...)` 生成。这个函数把 row 字段和 curve 字段合并，输出更适合阅读和检查的 phase row。关键字段包括：

- `phase`：阶段分类结果。
- `curve_points`：该行实际拥有多少个曲线点。
- `plateau_eval_count`：记忆之后、泛化之前的平台期 eval 点数量。对于未 grok 的 no-decay arm，则是从记忆点到运行结束的全部点。
- `low_val_plateau_count`：平台期中验证准确率低于阈值的点数量，默认阈值是 `0.5`。
- `low_val_plateau_rate`：低验证准确率点占平台期点的比例。
- `max_val_jump` 和 `max_val_jump_step`：记忆之后验证准确率最大单步增量和发生 step，用来帮助读者定位“突变”附近。
- `curve_endpoint_matches_row`：曲线最后一个点的 val accuracy 是否等于 row 里的 `final_val_acc`。
- `curve_mempoint_matches_row`：曲线中 `t_mem` 位置的 val accuracy 是否等于 row 里的 `val_at_mem`。

这两个 match 字段是本版很重要的防篡改检查。它们确保 phase table 不是拿了曲线另算一套解释，而是和 v1179 row summary 处在同一个数据事实里。如果有人改了 curve 终点或记忆点，但没同步 row，v1181 会失败。

## 阶段分类逻辑

`_classify_phase(...)` 是本版最核心的语义函数。它把每条 seed/arm 曲线压缩成四类之一：

- `not_memorized`：训练集也没有记住，说明训练本身不成立。
- `delayed_grok`：已经 memorized，也已经 grokked，并且 `grok_gap >= min_gap_steps`，同时 `val_at_mem < low_val_threshold`。默认 `min_gap_steps=1000`、`low_val_threshold=0.5`。这表示模型不是训练和验证一起上升，而是在训练集记忆之后，验证集仍然低了一段很长时间。
- `memorized_only_censored`：已经 memorized，但没有 grokked。这里的 censored 是统计意义上的“在当前运行预算内没有观察到泛化”，不是说它永远不会泛化。
- `immediate_or_ordinary_learning`：虽然 grokked，但 delay 不够长，或者记忆点验证准确率已经很高。这种情况不能叫 grokking，更像普通学习。

这个分类把 v1179 的口头描述变成了机器可检查字段。对本次真实数据，5 个 weight-decay seed 都是 `delayed_grok`，5 个 no-decay seed 都是 `memorized_only_censored`。

## Check Rows

v1181 不只输出 phase rows，还在 JSON 中保存 `check_rows`。这些 check rows 用来决定 `status` 是否为 pass。主要检查如下。

`source_status_pass` 要求上游 v1179 report 本身是 pass。否则 phase report 没有可信输入。

`source_verdict_wd_driven` 要求上游 verdict 是 `grokking_reproduced_wd_driven`。因为 v1181 的语义就是解释这个正向 grokking 结果；如果上游是 no-grok 或 review，阶段剖面可以生成，但不能作为同样的解释结论。

`curve_grid_complete` 要求 weight decay on/off 两个 arm 都各有 5 条曲线。它防止只拿部分 seed 解释整体结论。

`rows_have_matching_curves` 要求每个 row 都能找到曲线点。它保护 row/curve 对齐关系。

`curve_endpoints_match_rows` 和 `curve_mempoints_match_rows` 保护 curve 与 row summary 的一致性。终点不一致意味着 final accuracy 被篡改或来源混乱；记忆点不一致意味着 `val_at_mem` 这个判断 grokking delay 的关键字段不可信。

`wd_on_delayed_grok_all_seeds` 要求所有 with-decay seed 都分类为 `delayed_grok`。它不是只看 grok_rate，而是要求阶段语义也成立。

`wd_on_low_plateau_rate` 要求每个 with-decay seed 的平台期大部分 eval 点都保持低验证准确率。默认最低比例是 `0.70`。真实 v1179 的最小 seed 仍然超过这个阈值，mean 为 `0.8321`。这个检查防止把“验证集很快就升上去了”的普通学习误称为 grokking。

`wd_off_memorized_censored_all_seeds` 要求 no-decay arm 全部是“记住但未泛化”。这能把“训练失败”与“训练成功但没有 grok”区分开。

`paired_phase_separation` 要求每个 seed 都满足：weight-decay arm 是 delayed grok，而同 seed 的 no-decay arm 是 memorized-only censored。这个 paired 检查是解释 weight decay 作用的关键。

`boundary_present` 继续要求 toy-scale boundary 存在，避免把这个漂亮结果误推成生产级模型质量结论。

## CLI 入口

新增脚本是 `scripts/analyze_grok_trajectory_v1181.py`。实际运行命令为：

```powershell
python scripts\analyze_grok_trajectory_v1181.py f\1179\解释\grok_v1179 --out-dir f\1181\解释\grok_trajectory_phases_v1181 --require-pass --force
```

它支持几个可调参数：

- `--min-gap-steps`：默认 1000，决定 delayed grok 至少需要多长 gap。
- `--low-val-threshold`：默认 0.5，决定平台期“低验证准确率”的阈值。
- `--min-wd-on-low-plateau-rate`：默认 0.70，要求 with-decay 每个 seed 平台期中低验证准确率点的最低比例。
- `--require-pass`：如果 check 失败，则 CLI 返回 1。
- `--force`：覆盖已有输出目录。

CLI 自己不做复杂逻辑，只负责准备目录、调用 builder、写输出和打印 text summary。这种结构让测试可以集中打 builder，也让后续版本如果要复用 phase report，不必绕 CLI。

## 输出产物

本版输出在 `f/1181/解释/grok_trajectory_phases_v1181/`，包含：

- `grok_trajectory_phases_v1181.json`
- `grok_trajectory_phases_v1181.csv`
- `grok_trajectory_phases_v1181.txt`
- `grok_trajectory_phases_v1181.md`
- `grok_trajectory_phases_v1181.html`

其中 JSON 是完整机器可读证据，包含 `summary`、`phase_rows`、`check_rows` 和 `issues`。CSV 更适合快速扫每个 seed/arm 的 phase。HTML 用于运行截图和人工阅读。截图归档在 `f/1181/图片/grok-trajectory-phases-v1181.png`。

真实运行结果是：

- `status=pass`
- `decision=grokking_phase_profile_consistent`
- `curve_count=10`
- `wd_on_delayed_grok_count=5`
- `wd_off_memorized_censored_count=5`
- `paired_phase_separation_count=5`
- `wd_on_low_plateau_rate_mean=0.8321336571672611`
- `wd_on_min_gap=10400.0`
- `wd_on_max_gap=25100.0`
- `longest_delay_seed=1341`

这组数字说明 v1179 的 grokking 现象不仅 summary 成立，而且在曲线阶段上也成立：所有 weight-decay seed 都经历了足够长的低验证平台，所有 no-decay seed 都停留在记忆但未泛化的 censored 状态。

## 测试覆盖

新增测试文件是 `tests/test_grok_trajectory_phases_v1181.py`。它不是只测 happy path，而是覆盖了几个会破坏解释合同的负例。

`test_builds_phase_profile_from_curve_rows` 构造一个小型 grokking fixture，验证 builder 能输出 pass，且 delayed/censored/paired count 全部正确。

`test_missing_curves_fail_the_profile` 删除 curves，确认 `curve_grid_complete` 和 `rows_have_matching_curves` 会失败。这保护了“phase report 必须由曲线支持”的原则。

`test_endpoint_tamper_is_detected` 篡改其中一条曲线的终点 val accuracy，确认 `curve_endpoints_match_rows` 会失败。这保护 curve 和 row summary 的一致性。

`test_no_decay_grok_breaks_paired_phase_separation` 把 no-decay arm 篡改成也 grok，确认 no-decay censored 检查和 paired separation 检查都会失败。这保护 weight-decay-driven 的因果解释边界。

`test_outputs_and_cli_are_wired` 同时验证输出 writer 和 CLI：写出 JSON/HTML，并用 subprocess 跑脚本，确认 `--require-pass` 下成功返回 0。

本地聚焦测试结果为 `5 passed`。后续还会结合 v1179/v1180 相关测试、source encoding、diff check 和 GitHub Actions 做收口验证。

## 链路角色

v1181 的链路角色很明确：它不是新的模型训练能力，而是把已有正向模型现象变成“可解释阶段证据”。在项目叙事里，v1179 证明 MiniGPT 能在 toy modular arithmetic 上复现 grokking；v1180 证明这个 claim 能从归档 rows 复核；v1181 证明这个 claim 的曲线过程也能被压缩成一致的 phase table。三者合起来，才形成一个比较透明的训练动力学案例。

对用户理解 AI 模型原理来说，v1181 的意义也很直接。grokking 最容易被误解成“模型突然变聪明了”。phase table 把它拆开后，读者能看到：模型早就记住训练集，但验证集长期低迷；后面泛化不是简单的训练准确率提升，而是训练后很久才出现的验证集跃迁；no-decay 对照说明单纯记住训练集不等于泛化。这个解释比只给一张图更适合教学和答辩。

## 一句话总结

v1181 把 v1179 的 grokking 曲线压缩成可检查的阶段剖面，让“先记忆、长平台、后泛化，且只在 weight decay arm 中出现”从一句结论变成了每个 seed 都能复核的结构化证据。
