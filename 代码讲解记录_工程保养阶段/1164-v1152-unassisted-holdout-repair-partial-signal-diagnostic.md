# v1152 unassisted holdout repair partial signal diagnostic 代码讲解

## 本版目标与边界

v1152 的目标很窄，但它在当前模型能力路线里很关键：解释 v1151 为什么只得到 `fixed` 的 partial signal，而没有得到 `loss` 和 `fixed loss` full-pair。v1151 已经完成一次真实 replay：它使用 v1150 的 tiny checkpoint，拿 v1149 固化下来的 target-free holdout prompts 做生成，然后按 `fixed`、`loss`、full-pair 三个层次计数。真实结果是 5 个 case 中 4 个能生成 `fixed`，0 个能生成 `loss`，0 个达到 full-pair。这不是失败到没有任何信号，也不是足以推进 promotion 的成功；它处在一个容易被误读的位置。

因此 v1152 不做三件事。第一，不继续训练；因为还没有把问题定位清楚，继续训练容易把新数据和旧问题混在一起。第二，不把 v1151 的 partial signal 改写成模型能力提升结论；`fixed` 可见只能说明当前训练对第一个目标词产生了局部影响，不能证明模型学会了完整修复语义。第三，不更改 v1149、v1150、v1151 的历史产物；v1152 只读这些产物，输出一份新的诊断报告。这个边界让本版在证据链里承担“解释和分流”的角色，而不是承担“修复和宣称”的角色。

本版解决的问题可以概括为一句话：把“4/5 fixed，0/5 loss”从一个看起来像半成功的数字，转换成可执行的下一步工程任务。诊断报告最后给出的 `next_step=build_unassisted_loss_suffix_repair_seed`，就是下一版应当构造 loss-suffix repair seed 的依据。

## 前置路线与输入证据

v1152 直接站在 v1149-v1151 三个版本之上。v1149 负责把 v1148 的 repair blueprint 物化为训练语料、JSONL、target-free holdout prompts 和训练命令提示。v1150 使用 v1149 的 corpus 做 bounded CPU training，产出 checkpoint、tokenizer、metrics、manifest 和 training handoff。v1151 再消费 v1150 handoff，用同一组 v1149 target-free prompts 对 checkpoint 做真实 replay。

这条链路有两个重要约束。首先，holdout prompt 不能带目标词，否则模型生成 `fixed` 或 `loss` 时就无法区分是模型续写还是 prompt 泄漏。其次，v1151 的结果不能越过 promotion boundary；即使 full-pair 成功，也最多成为“候选”，需要跨 seed 或重复 replay 复核。v1152 继承这个边界：它只读 `f/1151/解释/unassisted-holdout-repair-replay-comparison-v1151/unassisted_holdout_repair_replay_comparison_v1151.json` 和 `f/1149/解释/unassisted-holdout-repair-seed-corpus-v1149/unassisted_holdout_repair_seed_corpus_v1149.json`，然后生成一份诊断报告。

为什么还要读 v1149 seed corpus，而不是只读 v1151 replay？因为 replay 只告诉我们现象：哪些 case 命中了 `fixed`，哪些 case 命中了 `loss`。要解释原因，必须回头看训练语料结构。v1149 中 target-free full-pair 示例有 6 个，fixed-first 示例有 2 个，loss-after-fixed 的示例只有 1 个，而且它是 training-only context：prompt 已经包含 `answer: fixed`，completion 才是 ` loss`。这意味着 `loss` 主要被放在“已经看见 fixed 的上下文”之后学习，而 v1151 的 target-free replay 要求模型先从 prompt 生成 `fixed`，再继续生成 `loss`。在 tiny 模型、短训练、极小语料条件下，模型学到第一个目标词但没学稳第二个目标词，是合理且需要专门补强的数据问题。

## 新增模块的角色

核心新增文件是 `src/minigpt/unassisted_holdout_repair_partial_signal_diagnostic_v1152.py`。它提供默认路径、定位函数、JSON 读取函数、报告构建函数、输出函数和退出码函数。这个模块没有引入新模型依赖，也没有调用 generator；它的输入是两个已经归档的 JSON report，输出是 JSON/CSV/TXT/Markdown/HTML 五种可读报告。

`default_v1151_replay_comparison_path()` 和 `default_v1149_seed_corpus_path()` 固化了本版默认读取的归档位置。这样 CLI 在真实运行时不需要用户重复传路径，同时测试仍然可以通过参数传入临时目录。`locate_v1151_replay_comparison()` 和 `locate_v1149_seed_corpus()` 保持了项目近期报告工具的一贯风格：如果传入目录，就在目录下拼默认 JSON 文件名；如果传入文件，就直接使用该文件。这一层看似小，但对归档和 CLI 兼容很重要，因为实际工作中常常有人传报告目录而不是具体 JSON 文件。

`build_unassisted_holdout_repair_partial_signal_diagnostic_v1152()` 是主入口。它先从 v1151 report 里取 `summary` 和 `rows`，从 v1149 report 里取 `summary` 和 `rows`；然后分别构造 replay profile 和 seed profile；接着跑 source checks；最后生成 findings、diagnosis、summary 和 interpretation。这里的设计重点是把“输入是否有效”和“模型是否还有问题”分开。source checks 失败时，报告 `status=fail`，说明不能诊断；source checks 通过时，即使 findings 里有 blocker，也代表诊断报告本身完成了。

这种分层避免了一个常见误区：把“报告发现 blocker”误判成“报告失败”。v1152 的 blocker 是模型修复路线上的 blocker，不是报告运行失败。比如 `loss_absent_in_all_replay_cases` 的 severity 是 blocker，因为它阻止模型能力 promotion；但它不应该让 v1152 的 `status` 变成 fail。只要 v1151/v1149 源报告自洽，诊断就应当通过，并把 blocker 明确写出来。

## 核心数据结构与字段语义

v1152 的输出报告仍然采用项目已有 readability report 结构：顶层包括 `schema_version`、`title`、`generated_at`、`status`、`decision`、`failed_count`、`issues`、`rows`、`check_rows`、`summary` 和 `interpretation`。新增的业务结构主要是 `replay_profile`、`seed_profile` 和 `diagnosis`。

`replay_profile` 描述 v1151 的生成结果。它包含 `case_count`、`fixed_hit_case_count`、`loss_hit_case_count`、`full_pair_case_count`、`zero_hit_case_count`、`fixed_only_case_count`、`partial_signal_visible`、`loss_missing`、`full_pair_missing`、`zero_hit_case_ids`、`fixed_only_case_ids` 和 `context_window_drift_case_ids`。这些字段把 replay 的表格结果压成几组可判断指标。比如真实 v1151 中 `fixed_only_case_count=4`，说明模型不是完全没有学到目标词；`loss_hit_case_count=0` 和 `full_pair_case_count=0` 则说明能力还没有恢复到目标状态。

`seed_profile` 描述 v1149 训练语料结构。它包含 `example_count`、`target_free_pair_example_count`、`loss_after_fixed_training_context_count`、`fixed_first_example_count`、`unique_prompt_count`、`repeated_prompt_count` 和 `loss_suffix_context_tied`。其中最有解释力的是 `loss_after_fixed_training_context_count`。真实报告里这个值是 1，说明 loss-after-fixed 的专门证据存在，但很少，而且是 training-only context。结合 v1151 的 `loss_hit_case_count=0`，可以提出一个更具体的根因假设：`loss` 后缀没有在 target-free replay 场景里被学稳。

`diagnosis` 是本版的判断层。真实运行给出 `root_cause_hypothesis=loss_suffix_context_tied_and_underlearned_after_fixed`。这个名字有意保守：它是基于当前证据的假设，不是不可推翻的结论。字段 `evidence_basis` 会列出固定依据，例如 fixed 命中数、loss 命中数、target-free pair 示例数和 loss-after-fixed training-only 示例数。字段 `blocking_findings` 列出阻断 promotion 的 findings；字段 `model_quality_claim=partial_signal_diagnostic_only` 明确说明本版不是模型质量提升声明；字段 `promotion_ready=False` 保持边界。

`rows` 在本版不是 replay generation rows，而是 diagnostic findings。每行包含 `finding_id`、`severity`、`status`、`actual`、`inference` 和 `recommended_action`。例如 `fixed_signal_visible` 是 info，说明已有信号；`loss_absent_in_all_replay_cases` 和 `full_pair_absent` 是 blocker，说明不能 promotion；`loss_suffix_context_tied` 是 warn，说明数据结构可能解释当前问题；`next_repair_action` 是 action，直接指向下一版应做的 loss-suffix repair seed。

## CLI 与运行流程

新增脚本 `scripts/diagnose_unassisted_holdout_repair_partial_signal_v1152.py` 是本版命令入口。默认情况下，它读取归档中的 v1151 replay report 和 v1149 seed corpus report，输出到 `output/unassisted-holdout-repair-partial-signal-diagnostic-v1152`。参数 `--replay` 和 `--seed-corpus` 支持传文件或目录；`--out-dir` 支持指定输出目录；`--require-diagnostic-ready` 会在诊断无法完成时返回非零退出码；`--force` 用于清理已有输出目录后重新生成。

真实运行命令是：

```powershell
python scripts/diagnose_unassisted_holdout_repair_partial_signal_v1152.py --out-dir output\unassisted-holdout-repair-partial-signal-diagnostic-v1152 --require-diagnostic-ready --force
```

该命令输出 `status=pass`、`decision=unassisted_holdout_repair_partial_signal_diagnostic_ready`、`fixed_hit_case_count=4`、`loss_hit_case_count=0`、`full_pair_case_count=0`、`root_cause_hypothesis=loss_suffix_context_tied_and_underlearned_after_fixed` 和 `next_step=build_unassisted_loss_suffix_repair_seed`。这组输出把 v1151 的现象收束成下一步明确动作：不是继续解释 partial signal，也不是直接 promotion，而是构造新的 loss-suffix repair seed。

CLI 最后调用 `write_unassisted_holdout_repair_partial_signal_diagnostic_v1152_outputs()`，通过现有 `write_readability_outputs()` 写出 JSON、CSV、TXT、Markdown 和 HTML。HTML 再由 Playwright MCP 打开并截图，截图保存在 `f/1152/图片/unassisted-holdout-repair-partial-signal-diagnostic-v1152.png`。归档说明保存在 `f/1152/解释/说明.md`，报告文件保存在 `f/1152/解释/unassisted-holdout-repair-partial-signal-diagnostic-v1152/`。

## 测试覆盖

新增测试文件是 `tests/test_unassisted_holdout_repair_partial_signal_diagnostic_v1152.py`。测试的第一条路径构造一个与真实 v1151 类似的 replay report：5 个 case 中 4 个 fixed 命中，0 个 loss 命中，并且 seed report 中有 1 个 loss-after-fixed training-only 示例。断言覆盖 `status=pass`、`decision=unassisted_holdout_repair_partial_signal_diagnostic_ready`、ready flag、各类计数、root cause、next step 和 `promotion_ready=False`。这条测试保证本版不会把 partial signal 误判成 full-pair 恢复，也不会把诊断报告错误标为失败。

第二条测试把 v1151 replay report 的 `status` 改成 fail，确认 source check 会阻断诊断，并且 `--require-diagnostic-ready` 对应的退出码为 1。这保护了输入边界：如果上游 replay 没有结构性通过，v1152 不能继续做解释。

第三条测试删除 seed report 里的 `loss_after_model_fixed` 行，确认 root cause 会从 `loss_suffix_context_tied_and_underlearned_after_fixed` 降级为 `loss_suffix_underlearned_after_fixed`。这个测试不是为了证明哪个根因一定正确，而是为了保护诊断逻辑确实会根据 seed corpus 结构变化而变化，而不是写死结论。

第四条测试覆盖输出和 CLI wiring。它在临时目录写入 replay JSON 和 seed JSON，分别以目录形式传给 CLI，确认 `locate_v1151_replay_comparison()` 和 `locate_v1149_seed_corpus()` 能正确解析目录输入，并确认 JSON/CSV/TXT/Markdown/HTML 五类输出都生成。这样本版的报告构建函数、定位函数、CLI 参数和 readability 输出链路形成闭环。

## 运行证据与后续角色

本版真实证据归档在 `f/1152`。JSON 是机器可消费证据，CSV 便于表格检查，TXT 便于 CI 或命令行快速读取，Markdown 便于代码评审阅读，HTML 和截图用于人工审查。截图中能看到关键摘要：诊断 ready、case_count 为 5、fixed 命中 4、loss 命中 0、full-pair 命中 0、root cause hypothesis 指向 loss suffix context tied，并且 next step 是 build loss suffix repair seed。

v1152 在路线上的角色是“诊断闸门”。它不直接提升模型能力，但它防止下一版盲目推进。没有 v1152，后续可能会继续堆训练轮次，或者误以为 fixed signal 已经足够。加入 v1152 后，下一版有了明确目标：补强 target-free 场景下 `fixed -> loss` 的后缀续写证据，并在新训练后继续用同一组 holdout prompts 或明确分层的新 prompts 做 replay。这样项目从“看到一个现象”走到“为现象建立可复核解释和下一步修复入口”。

## 一句话总结

v1152 把 v1151 的 fixed-only partial signal 诊断为 loss suffix 在 target-free replay 中仍未学稳，明确禁止 promotion，并把下一步收敛到 loss-suffix repair seed。
