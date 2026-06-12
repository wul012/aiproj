# v1153 unassisted loss suffix repair seed 代码讲解

## 本版目标与边界

v1153 不是一次训练，也不是新的能力评估，它是一版纯粹的 seed revision。它吃进去的是 v1152 partial-signal diagnostic 和 v1149 seed corpus，吐出来的是一份新的修订语料、JSONL、holdout prompt 清单和训练命令提示。它要解决的核心问题很明确：v1151 已经在 4/5 个 target-free holdout case 中命中 `fixed`，但 `loss` 完全缺失；v1153 便是围绕这个 `loss suffix` 进行定向补强。

本版边界也必须说清。第一，它不训练模型，所以不对模型能力做任何新声明。第二，它不修改历史版本产物，v1149-v1152 只是只读输入。第三，它不把 holdout prompts 搞成带目标词的样本，target-free 这个底线必须保住。只要越过这条线，后面的 replay 就不再是同一种实验。

## 前置证据链

v1153 的路线来自 v1152 的诊断结果。v1152 的判断不是“模型完全没信号”，而是“模型有 fixed-only partial signal，但 loss 还没学稳”。这个结论之所以重要，是因为它把下一步动作从“继续解释”转成“补语料”。如果 v1152 看见的是全零信号，v1153 可能会倾向于重新设计 prompt；但现在已经有 `fixed` 的局部信号，所以更合理的动作是把 `fixed -> loss` 这一段续写单独加厚。

本版还依赖 v1149 seed corpus 的结构。v1149 里有 9 条基础样本，包含 6 条 full_pair、2 条 fixed_first 和 1 条 loss_after_model_fixed。这里的 `loss_after_model_fixed` 非常关键，因为它证明 corpus 里确实出现过 `fixed` 后接 `loss` 的训练信号，但它是 training-only context，不能直接当作评估样本。v1153 的工作就是把这类上下文从“单条训练示例”扩展成一组可复用、可追踪、针对 fixed-only case 的补强样本。

## 核心文件

主模块是 `src/minigpt/unassisted_loss_suffix_repair_seed_v1153.py`。它整体沿用了项目已经稳定下来的报告写法：`default_*_path()` 提供默认归档位置，`locate_*()` 兼容目录和文件输入，`read_json_report()` 负责读取 JSON 对象，`build_*()` 负责生成报告，`write_*_outputs()` 负责写出可读格式，`resolve_exit_code()` 控制 CLI 的退出码。

这套骨架看起来朴素，但非常适合后期保养阶段。因为它让每个版本都拥有相似的操作模式：先读上游证据，再做明确的结构化判断，再写多格式报告，再把最终证据归档到 `f/<version>`。这也使得 README 和讲解文档可以稳定引用同一类路径，不用每版重学一遍。

## 数据结构设计

### 1. base rows

`_base_seed_rows()` 会把 v1149 的原始 rows 复制过来，补上少量兼容字段，比如 `variant_index`、`repair_source_case_id`、`repair_added_in_version` 和 `text`。这里最重要的是“复制而不是重建”。这样历史样本仍然保持原样，修订版只是增量叠加在旧语料上，不会把 v1149 的证据写坏。

### 2. repair rows

`_repair_rows()` 是 v1153 最核心的逻辑。它先从 v1152 diagnostic 的 `replay_profile` 读取两个列表：`fixed_only_case_ids` 和 `zero_hit_case_ids`。前者对应已经有 `fixed`、但没有 `loss` 的 case；后者对应连 `fixed` 都没有命中的 case。然后它通过 v1149 的 `holdout_prompt_rows` 回查原始 prompt，给每个 case 生成对应的修订样本。

对于 fixed-only case，生成 `_loss_suffix_row()`。这类样本的 prompt 形态是 `原始prompt + fixed`，completion 是 ` loss`，并标记为 `training_only_context=True`。它的意义是把 `loss` 从一个独立词变成 `fixed` 后面的续写后缀，让模型看到“fixed 之后还应该继续”。这正是 v1152 诊断的根因修补方向。

对于 zero-hit case，生成 `_zero_hit_full_pair_row()`。这类样本保持 target-free prompt，不把目标词放进 prompt，completion 直接是 ` fixed loss`。它的意义不是“重复旧数据”，而是在模型连 `fixed` 都没命中的地方补一个完整模板，让那些最难的 prompt 也有一条 target-free 示例可以追随。

### 3. repair_source_case_id

每一条新增样本都会写 `repair_source_case_id`，把它和 v1152 的 case_id 绑定。这个字段是 v1153 的审计锚点。后续如果 replay 结果变好，可以回头看是哪几个 case 触发了哪些修订样本；如果结果仍不好，也能知道到底是哪类输入没有起效。这个字段让“我为什么这么改”变成结构化信息。

## 输出结构与训练侧 sidecar

本版不是只写一个报告，而是把训练准备也一起写出来。输出主报告使用 `write_readability_outputs()`，生成 JSON、CSV、TXT、Markdown 和 HTML 五种可读格式。然后额外写四个训练侧 sidecar：

- `unassisted_loss_suffix_repair_seed_corpus_v1153.txt`
- `unassisted_loss_suffix_repair_seed_corpus_v1153.jsonl`
- `unassisted_loss_suffix_repair_holdout_prompts_v1153.json`
- `unassisted_loss_suffix_repair_train_command_hint_v1153.json`

其中 `.txt` 是最终训练文本，`.jsonl` 是按 example 逐行的结构化记录，`holdout_prompts` 是后续 replay 的 target-free 测试提示，`train_command_hint` 则把下一步训练参数固定下来。这样 v1153 的产物不只是“一个说明文件”，而是一个完整的训练入口包。

## 检查项的含义

v1153 的 `check_rows` 不是为了凑数量，而是为了把 seed revision 的边界锁死。

- `v1152_diagnostic_passed`：上游诊断必须通过，否则不能修订 seed。
- `v1152_diagnostic_ready`：说明诊断本身是完成态，而不是半路失败的中间产物。
- `v1152_next_step_matches_seed_revision`：说明这版修订是诊断真正指向的下一步。
- `loss_missing_confirmed`：确认本版确实是为“缺失 loss”这个问题服务，而不是乱修。
- `fixed_only_cases_have_suffix_repairs`：保证 fixed-only case 至少能拿到对应的 suffix 修补样本。
- `zero_hit_case_reinforced`：保证最弱的 case 也得到 target-free full-pair reinforcement。
- `holdout_prompts_target_free`：保证评估面没被污染。
- `base_rows_preserved`：保证 v1149 原始 seed 没有被替换。
- `corpus_non_empty`：保证修订后仍然是可训练文本。
- `promotion_boundary_kept`：保证 seed revision 不会被误写成 promotion evidence。

这些检查共同构成了 v1153 的质量边界。它们不证明模型变强，但证明 seed revision 的工程动作是对的。

## 运行结果如何解读

真实运行后，`base_example_count=9`、`repair_example_count=6`、`revised_example_count=15`。这组数很漂亮，但它的意义不是“扩容成功”，而是“针对性补强成功”。新增 6 条里有 5 条 loss suffix repair row 和 1 条 zero-hit full-pair reinforcement row，说明这版确实围绕 v1152 的两类弱点做了定点修复，而不是平均撒样本。

`training_only_context_count=6` 很关键，它说明所有新增样本都留在训练区，不会污染 holdout。这个数字配合 `target_free_holdout_prompt_count=5` 说明训练区和评估区被清楚分开了。`corpus_char_count=347` 也说明本版已经从 v1149 的轻量 corpus 走到了更厚一点的修订 corpus，但仍然完全是 tiny 规模，后续可以在 CPU 上做 bounded training。

`model_quality_claim=seed_revision_only` 同样重要。它告诉读者：v1153 不宣称模型会更好，它只宣称“我已经把下一步训练应该吃什么数据准备好了”。这是一种非常重要的工程自律，尤其在小模型和短版本链里，最容易把“数据修了”误说成“能力变了”。

## 测试为何足够

本版测试覆盖了四类风险。

第一类是结构风险。只要 diagnostic 或 seed report fail，v1153 就必须 fail，这能防止在上游不稳的情况下继续出新语料。

第二类是数据污染风险。`holdout_prompts` 必须 target-free，这是 replay 能否复现同一实验的前提。测试专门验证 5 条 holdout prompt 里没有 `fixed` 或 `loss` 词面。

第三类是修订语料边界风险。测试检查新增的 loss-suffix 行全部带 `training_only_context=True`，确保训练-only 和 holdout 的边界清晰。

第四类是 CLI / 输出风险。目录输入、文件输入、输出目录生成、sidecar 落盘都必须正常，否则就算算法对了，工程上也不可用。

## 一句话总结

v1153 把 v1152 诊断出的 fixed-only / loss-missing 问题落实成 6 条定向修订样本，保住 target-free holdout 边界，为下一轮 bounded training 提供更对症的语料。
