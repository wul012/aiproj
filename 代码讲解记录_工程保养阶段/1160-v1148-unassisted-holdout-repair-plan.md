# v1148 unassisted holdout repair plan：把 v1147 的失败形态变成可训练的修复蓝图

## 本版目标与边界

v1148 的目标不是再做一个空泛治理报告，而是把 v1147 已经确认的真实模型输出差距转成下一步可执行的 repair plan。v1147 的结论很具体：同一个 v1145 checkpoint 在 decoder-anchor 短前缀下有 5 个 fragment hit、4 个 loss anchor hit；换成无锚点 holdout-style prompts 之后，模型仍然能在 3 个 case 里冒出 `loss` 片段，但 `fixed` 命中数是 0，完整 `fixed/loss` pair 命中数也是 0。这个结果说明模型并非完全没有学习信号，但它还没有形成无锚点的 pair coexistence 能力。

如果 v1148 继续做“再解释一次 v1147”的只读报告，价值会很低；如果 v1148 立刻训练，又会缺少明确输入边界，容易把 `fixed` 或 `loss` 直接塞进评估 prompt，导致后续报告分不清模型主动生成和提示泄漏。因此本版选择中间路线：先把修复计划、验收门、禁止动作和 seed blueprint 固化为产物。它允许下一版做小训练，但本身不训练；它给出种子语料蓝图，但不把蓝图当成模型质量证据；它指出 `fixed` 是第一优先缺口，但不把 `loss` 的局部出现误写成完整恢复。

本版的边界字段非常重要。summary 里写 `model_quality_claim=plan_only`，表示它只是计划和输入蓝图，不是模型能力结果。`promotion_ready=False` 继续保留，表示即使计划生成成功，也不能进入晋升。`new_training_allowed=True` 则说明和旧的“只读治理计划”不同，v1148 已经明确授权下一版做 bounded repair training，因为当前证据足够说明需要训练修复，而不是继续只做诊断。

## 上游证据：为什么必须从 v1147 来

v1148 只消费 v1147 的 `decoder_anchor_holdout_comparison_v1147.json`。这个输入有几个关键字段：`decoder_anchor_holdout_comparison_ready=True`、`unassisted_fixed_hit_count=0`、`unassisted_loss_hit_count=3`、`unassisted_full_pair_count=0`、`next_step=build_unassisted_holdout_repair_plan`。这些字段共同定义了本版的触发条件。

其中 `unassisted_fixed_hit_count=0` 是最高优先级缺口。v1147 已经证明，loss suffix 有一定局部信号，说明模型不是完全随机；真正断掉的是无锚点场景下的 `fixed` 起始词和 `fixed/loss` 同时出现。v1148 的 work items 因此把 `recover_fixed_first_token` 设为 high priority，并在 acceptance gates 里要求后续修复至少让 3 个无锚点 replay case 的 continuation 出现 `fixed`。

`unassisted_loss_hit_count=3` 也不是被忽略。它意味着后续训练不能只猛补 `fixed`，还要保留已有 `loss` signal，所以 work item 里有 `preserve_loss_suffix_signal`，验收门里也有 `loss_signal_not_regressed`。这能防止下一版修复时出现一种常见坏结果：模型学会了固定输出 `fixed`，却丢掉了 `loss`，最终仍然没有完整 pair。

## 新增模块结构

核心模块是 `src/minigpt/unassisted_holdout_repair_plan_v1148.py`。它保持短名，不沿用历史上那些极长的 route-promotion 文件名。文件内部按职责分成：读取与定位、builder、输出 writer、work items、acceptance gates、blocked actions、seed blueprint、checks、summary 和 interpretation。这种拆法是为了继续遵守项目后期的维护规则：功能推进可以厚，但不要把所有逻辑塞进一个难以维护的巨型文件。

`locate_v1147_comparison` 支持 JSON 或目录输入。如果传入目录，就自动拼接 `decoder_anchor_holdout_comparison_v1147.json`。这跟 v1147 的 CLI 习惯一致，方便用户拿归档目录直接复跑。

`default_v1147_comparison_path` 负责构造默认归档路径：`f/1147/解释/decoder-anchor-holdout-comparison-v1147/decoder_anchor_holdout_comparison_v1147.json`。这里继续使用 `EXPLAIN_DIR_NAME="\u89e3\u91ca"`，避免中文目录在不同终端显示成乱码时影响源码可读性。它没有依赖当前工作目录里的 `output`，而是默认读正式归档证据。

`build_unassisted_holdout_repair_plan_v1148` 是主 builder。它先取 v1147 summary 和 rows，然后生成四类内容：`work_items`、`acceptance_gates`、`blocked_actions`、`repair_seed_blueprint_rows`。随后 `_checks` 验证输入是否满足计划触发条件；如果有任何前置条件不成立，report 就 fail。最后 `_plan` 和 `_summary` 输出下一步路线。

## Work items 的含义

本版生成 6 个 work items。第一个是 `materialize_unassisted_seed_blueprint`，它要求下一版把 seed blueprint 写成真正训练语料。第二个是 `recover_fixed_first_token`，这是从 v1147 的 `unassisted_fixed_hit_count=0` 直接推导出来的最高优先级训练目标。第三个是 `preserve_loss_suffix_signal`，用来保护 v1147 已经存在的 3 个 loss 片段命中。第四个是 `run_bounded_repair_checkpoint`，说明下一步训练应当是小而边界清晰的 CPU repair checkpoint，而不是扩大到不受控的大训练。第五个是 `replay_unchanged_unassisted_prompts`，要求用 v1147 原来的五个无锚点 prompts 复测，不能边训练边改评估题。第六个是 `compare_against_anchor_baseline`，要求把修复后的 unassisted pair 命中与 v1147 的 anchor baseline 放在同一个框架里看。

这些 work items 不是泛泛写“继续优化模型”。每一项都有 `priority`、`stage`、`description` 和 `expected_output`。这样 v1149 可以直接从 `proposed_next_artifact=unassisted_holdout_repair_seed_corpus_v1149` 接下去，而不是再重新讨论方向。

## Acceptance gates 与 blocked actions

acceptance gates 有 5 个。`evaluation_prompt_target_free` 要求复测 prompts 不含 `fixed` 或 `loss`，这是防止提示泄漏的核心门槛。`fixed_first_token_recovered` 要求至少三个无锚点 replay case 的 continuation 出现 `fixed`。`full_pair_recovered` 要求至少三个 unchanged unassisted replay cases 同时包含 `fixed` 和 `loss`。`loss_signal_not_regressed` 要求 loss 命中不低于 v1147 基线。`promotion_still_gated` 则提醒即使 repair replay 过了，也还需要 holdout scorecard 证据才能谈晋升。

blocked actions 则写清楚四件不能做的事。第一，不能把 loss-only 当恢复，因为 v1147 已经有 loss-only，这不是新能力。第二，不能把 decoder anchors 加回评估 prompt，否则会把本来要修的无锚点能力污染成锚点补全。第三，不能回写 v1145-v1147 的历史归档，修复必须消费历史证据，而不是修改历史结论。第四，不能从 plan 直接宣称模型晋升。

这两组字段让 v1148 的计划具备“能执行但不越界”的特征。它不是单纯列路线，也不是把下一版写死；它把后续版本能做什么、做到什么才算过、哪些捷径不能走都表达出来。

## Seed blueprint 的设计

`repair_seed_blueprint_rows` 是 v1148 最实际的新增产物。它包含 9 条蓝图行，并额外写出 `unassisted_holdout_repair_seed_blueprint.json` 与 `unassisted_holdout_repair_seed_blueprint.txt` 两个 sidecar。前 5 条来自 v1147 的无锚点 prompts：`answer:`、`answer: `、`completion:`、`finish: `、`state compact signal\nanswer:`。这些 prompt 都不包含 `fixed` 或 `loss`，completion 则要求输出 `fixed loss`。这样下一版训练可以对准无锚点 pair 生成，而不是继续依赖 `lo`、`los`、`fi` 之类前缀锚点。

后 4 条是补充蓝图：两个 `fixed_first` 行强化 `fixed` 起始词，一个 `loss_after_model_fixed` 行用于训练 `fixed` 后续接 `loss`，一个 `short_pair` 行提供极短 surface。这里有一个细节：`loss-after-fixed-01` 的 prompt 是 `answer: fixed`，它确实带有 `fixed`，因此本版没有把它放进“评估 prompt target-free”检查范围，而是标记了 `decoder_anchor_boundary=training_only_context_not_eval`。这说明它可以作为训练过渡样本，但不能作为无锚点评估题。这个边界比简单地把所有 target 出现都禁止更实际，也更符合小模型训练修复的需要。

## 输出与归档

CLI 文件是 `scripts/build_unassisted_holdout_repair_plan_v1148.py`。真实运行命令如下：

```powershell
python scripts/build_unassisted_holdout_repair_plan_v1148.py --out-dir output/unassisted-holdout-repair-plan-v1148 --require-plan-ready --force
```

真实输出是 `status=pass`、`decision=unassisted_holdout_repair_plan_ready`、`work_item_count=6`、`acceptance_gate_count=5`、`blocked_action_count=4`、`seed_blueprint_count=9`、`new_training_allowed=True`、`promotion_ready=False`。报告归档在 `f/1148/解释/unassisted-holdout-repair-plan-v1148`，截图归档在 `f/1148/图片/unassisted-holdout-repair-plan-v1148.png`。

输出 writer 使用 `write_readability_outputs` 生成 JSON、CSV、TXT、Markdown 和 HTML，同时额外写 seed blueprint JSON/TXT。这个设计比只把 seed rows 塞进主 JSON 更好，因为下一版脚本可以直接读取 `unassisted_holdout_repair_seed_blueprint.json`，人工复核也可以直接打开 `.txt` 看 prompt/completion 对。

## 测试覆盖

测试文件是 `tests/test_unassisted_holdout_repair_plan_v1148.py`。第一组测试构造 v1147 loss-only gap，确认 plan ready、work item 数、acceptance gate 数、seed blueprint 数、`new_training_allowed=True` 和 `promotion_ready=False`。第二组测试把 v1147 next step 改错，确认 `v1147_next_step_matches_plan` 会失败。第三组测试模拟无锚点 full pair 已经恢复的情况，确认 `unassisted_pair_absent` 会失败。这个失败语义很重要：如果 full pair 已经恢复，就不该继续走 repair plan，而应切换到更强的 replay 或 promotion-bound 检查。第四组测试覆盖输出 writer 和 CLI，确认传目录可定位 v1147 JSON，并且 sidecar seed blueprint 文件真实写出。

本版验证还包括 py_compile、聚焦 pytest、真实 CLI、Playwright MCP HTML 截图、source encoding、diff check 和全量 pytest。测试不是只证明代码能跑，而是在保护 v1148 的关键边界：只有 v1147 证据确实说明“loss-only partial signal + fixed/full-pair gap”时，才允许进入 unassisted repair plan。

## 一句话总结

v1148 把 v1147 的无锚点失败形态收束成了可执行修复蓝图：下一步可以做小规模 unassisted repair training，但必须保持评估 target-free、保护已有 loss signal、恢复 fixed/loss full pair，并继续把 promotion 关在更后面的 holdout 证据之后。
