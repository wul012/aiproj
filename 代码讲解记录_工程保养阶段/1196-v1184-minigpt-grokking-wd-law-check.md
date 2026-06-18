# v1184：grokking 权重衰减剂量结论复核

## 本版目标和边界

v1184 的目标很明确：它不再训练一个新模型，也不再扩大 v1183 的能力声明，而是在 v1183 的真实 GPU 剂量-反应实验之后补上一层可复核的 artifact contract check。v1183 已经证明，在 toy-scale 模数加法 `a + b = c (mod 97)` 上，weight decay 不是一个简单的“越大越好”旋钮；它更像一个剂量区间：太小不 grok，适中时 grok 且 `wd=1.0` 最快，太大时仍能记忆训练集却不再泛化。这个结论很有价值，但也很容易在后续引用中被压扁成一句“加大 weight decay 会加速 grokking”。v1184 正是为了防止这种结论漂移。

本版边界同样重要：v1184 是只读检查，不加载 checkpoint，不调用训练循环，不重新跑 v1183 的 5 seeds × 5 weight-decay arms，不声称模型能力又提升了一次。它消费的唯一上游真相是 `f/1183/解释/grok_wd_law_v1183/grok_wd_law_v1183.json`。如果这个 JSON 的 summary 写着内部最优，但 dose rows 或 seed rows 无法重新推出同一个结论，本版必须失败；如果上游结果本身是保守的内部最优，本版应该通过，并把关键推导结果写成 JSON/CSV/Markdown/HTML，供后续版本继续引用。

## 为什么 v1184 必须跟在 v1183 后面

v1183 最值得记录的地方不是“跑出了一个漂亮正结果”，而是它在运行过程中修正了一次过度声称。第一轮判定逻辑只看会 grok 的子区间 `[0.3, 1.0]`，于是把 `t_gen` 从 26560 降到 14920 解读成 `monotone_acceleration`。但完整 sweep 里还有 `wd=3.0`：它 5/5 记忆，却 0/5 grok，即使追加 100k-step 探针也没有恢复。这说明高端不是“更慢一点”，而是过度正则化导致泛化消失。v1183 后来把 verdict 改成 `wd_dose_response_interior_optimum`，这是正确的。

不过，只靠 README 或说明文字记住这件事是不够的。后续如果有人只拿 `fastest_grok_wd=1.0` 或 `monotone_t_gen_decrease=True` 这类字段做自动汇总，就仍有可能重新误写成“单调加速”。v1184 把这段经验固化成检查规则：既要承认 `wd=1.0` 比 `wd=0.3` 快很多，也要同时要求 `wd=3.0` 这只高端 arm 被识别为“记忆成功但 grok 失败”。只有两个事实同时存在，才能叫“内部最优”。

## 新增文件角色

`src/minigpt/grok_wd_law_check_v1184.py` 是本版核心模块。它提供 `build_grok_wd_law_check`、`write_grok_wd_law_check_outputs` 和 `resolve_exit_code` 三个对外入口。调用方既可以传入一个已经读取好的 report dict，也可以传入 JSON 文件或输出目录；如果传的是目录，模块通过 `locate_wd_law_report` 查找默认文件名 `grok_wd_law_v1183.json`。这延续了最近几个版本的 artifact check 风格：入口既适合单测构造内存 fixture，也适合真实 CLI 消费磁盘证据。

`scripts/check_grok_wd_law_v1184.py` 是命令行入口。它接收 `wd_law_report`、`--out-dir`、`--grok-rate-threshold`、`--min-fastest-gap-steps`、`--require-pass` 和 `--force`。默认阈值为 `grok_rate >= 0.6`，最快点和次快点之间至少相差 `1000` step 才算 materially faster。`--require-pass` 会在检查失败时返回非零码，方便 CI 或后续 release gate 使用；如果只是人工探索，也可以不传这个参数，让脚本输出失败报告但不阻断外层流程。

`tests/test_grok_wd_law_check_v1184.py` 是防退化测试。它不依赖真实 v1183 大 JSON，而是构造一个小型 v1183-like report fixture，包含 5 个 wd dose rows 和 25 个 seed rows。测试覆盖通过路径，也覆盖几个最危险的失败路径：把 verdict 篡改回单调加速、让最强 `wd=3.0` 也 grok、把 summary 里的阈值改错、以及让最强 dose 的 seed rows 从“记忆但不 grok”变成“也 grok”。这些都是 v1184 最需要防住的结论污染。

## 输入输出结构

输入 JSON 主要有三层。第一层是顶层 `status` 和 `decision`，代表 v1183 报告自身是否有效以及最终判定。第二层是 `summary`，里面记录 `seeds`、`wds`、`grok_threshold_wd`、`fastest_grok_wd`、`censored_below_threshold`、`high_end_grok_censored`、`interior_optimum`、`too_much_wd_breaks_memorization`、`boundary` 等摘要字段。第三层是 `rows` 和 `seed_rows`：`rows` 是按 weight_decay 聚合后的剂量行，记录每个 dose 的 `mem_rate`、`grok_rate`、`t_gen_mean` 等；`seed_rows` 是每个 seed × weight_decay 的原始结果行，负责证明 strongest dose 的 5 个 seed 是否真的全部记忆、全部没有 grok。

输出报告仍然采用项目已有的 readability artifact 格式：顶层 `status`、`decision`、`failed_count`、`issues`，中间 `summary` 放复核后的关键数字，`rows`/`check_rows` 放每条检查。生成文件包括 JSON、CSV、TXT、Markdown 和 HTML。JSON 是后续机器消费的主证据；CSV 适合快速扫 check rows；Markdown 和 HTML 是人工阅读入口；截图则证明 HTML 在真实浏览器中可渲染且关键字段可见。

## 核心流程

核心流程分三步。第一步是定位与读取源报告：`locate_wd_law_report` 支持文件路径或目录路径，目录路径下默认寻找 `grok_wd_law_v1183.json`。读取后用 `as_dict`、`list_of_dicts`、`number_or_default` 这些 report_utils 工具做轻量防御，避免缺字段或类型异常直接把脚本炸掉。

第二步是从 rows 和 seed_rows 重新计算事实。`_row_metrics` 会按 weight_decay 排序 dose rows，找出 `grok_rate >= threshold` 且有 `t_gen_mean` 的 grok rows。第一个 grok row 是 `threshold_wd`，`t_gen_mean` 最小的 grok row 是 `fastest_wd`，前两快的差值是 `fastest_gap_steps`。它还计算低端是否 censored：阈值是否大于最小 wd；高端是否 censored：最大 wd 的 `grok_rate` 低于阈值但 `mem_rate >= 0.999`。这最后一个条件非常关键，因为它区分的是“正则化太强导致不泛化”，不是“模型根本没学会训练集”。

第三步是把重新计算的事实和 summary 声明逐条对齐。`_checks` 返回一组结构化 check rows：源报告必须 `status=pass`；顶层 decision 和 summary verdict 必须都是 `wd_dose_response_interior_optimum`；dose rows 数量和 seed rows 数量必须完整；所有 dose 都要达到记忆；重新计算的 grok 阈值和最快 wd 必须等于 summary；最快 wd 不能是扫参边界；最快差距必须大于阈值；低端和高端 censoring 必须成立；最强 dose 的 seed rows 必须 5/5 memorized 且 0/5 grokked；最后还要保留 toy-scale boundary。

## 检查项的机理

`source_status_pass` 和 `source_verdict_interior_optimum` 是最外层合同。它们保证本版不拿一个失败报告或错误 headline 来当上游。`grid_complete_rows` 保证 sweep 没有缺 dose 或缺 seed；如果只有一部分结果，内部最优就可能只是采样偏差。`all_doses_memorize` 是为了把“训练失败”和“泛化失败”分开：grokking 讨论的是先记忆后泛化，所以每个 dose 至少要证明能记住训练集。

`grok_threshold_matches_summary` 和 `fastest_wd_matches_summary` 是 summary-vs-row 对账。它们防止人工改了摘要但没改底层行，或者行发生变化但摘要没更新。`fastest_is_interior` 则是本版的核心语义守门：如果最快点落在最小或最大 wd，就不能叫内部最优。`fastest_gap_material` 防止把微小差距包装成强结论，本版默认要求至少相差 1000 step，真实 v1183 的差距是 11640 step，远高于阈值。

`low_end_censored` 和 `high_end_censored_not_broken` 是剂量-反应两端。低端说的是 weight decay 不足时 grok 不可靠；高端说的是 weight decay 太强时虽然仍能记忆，但不再 grok。`strongest_seed_rows_memorize_not_grok` 把高端结论落到每个 seed 上，避免只靠聚合行。`not_monotone_acceleration_claim` 专门防 v1183 曾经出现过的错误：即使 `monotone_t_gen_decrease=True` 在 grokking 子区间成立，也不能盖过完整 sweep 的 `interior_optimum=True`。`boundary_present` 则把结论锁在 toy-scale 单任务剂量-反应，不把它说成通用 scaling law。

## 真实运行证据

本版真实运行命令为：

```powershell
python scripts\check_grok_wd_law_v1184.py f\1183\解释\grok_wd_law_v1183 --out-dir f\1184\解释\grok_wd_law_check_v1184 --require-pass --force
```

运行结果为 `status=pass`、`decision=wd_law_interior_optimum_reconstructed`、`failed_count=0`。重新计算出的阈值是 `0.3`，最快点是 `1.0`，最快 `t_gen=14920.0`，次快 `t_gen=26560.0`，差距 `11640.0` step。低端 censored 和高端 censored 都为 True；最强 dose 的记忆率为 `1.0`，grok 率为 `0.0`，seed row 层面也是 `strongest_seed_mem_count=5`、`strongest_seed_grok_count=0`。

HTML 报告通过 Playwright MCP 打开并截图，截图保存到 `f/1184/图片/grok-wd-law-check-v1184.png`。这个截图不是新的模型证据，而是“本版 check 报告可读、关键字段可见”的运行归档。机器证据仍然以 JSON 为准，人工证据以 Markdown/HTML/截图为准。

## 测试覆盖

单测覆盖分为通过路径和变异失败路径。通过路径确认正常 v1183-like fixture 能得到 `status=pass`、`decision=wd_law_interior_optimum_reconstructed`，并重新算出阈值、最快点、两端 censoring。变异路径分别篡改 headline、篡改高端 grok、篡改阈值、篡改 strongest seed rows。每个变异都必须让对应 check id 出现在 `issues` 里。

CLI 测试会把 fixture 写成临时 `grok_wd_law_v1183.json`，调用真实脚本并要求 `--require-pass` 返回 0，同时确认输出 JSON 和 HTML 存在。这保证本版不是只有内存函数可用，而是能作为命令行 contract check 接入后续自动化。后续完整验证还会跑 v1179/v1183/v1184 的链路测试，确保本版没有破坏上游 grokking 原语和 dose-response 报告。

## 链路角色

v1179 证明 weight decay vs no-decay 的二元差异；v1180 复核 v1179 的证据；v1181 把曲线压成阶段；v1182 做 seed-wise 反事实对照；v1183 扫 weight decay 强度，得到内部最优剂量-反应；v1184 则把 v1183 的结论从“报告文字”固定成“可重建合同”。这条链路的重点不是让治理报告堆得更多，而是让每一个正结论都能被底层行数据重新推出来，避免口径漂移。

一句话总结：v1184 没有让模型更聪明，但让 v1183 的真实 grokking 剂量发现更稳固、更难被误读，把“内部最优”从 README 叙述变成了可执行、可失败、可引用的证据合同。
