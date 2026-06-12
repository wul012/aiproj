# v1147 decoder-anchor 与 unassisted holdout 对照：把局部锚点信号和无锚点能力分开

## 本版目标与边界

v1147 的目标是接住 v1146 报告里的 `next_step=compare_decoder_anchor_probe_with_unassisted_holdout_replay`，把上一版已经观察到的 decoder-anchor fragment signal 放到一个更严格的对照环境里看。v1146 的真实运行已经证明：同一个 v1145 checkpoint 在 `fixed `、`lo`、`los`、`fi` 这类短前缀提示下，可以稳定产生 `loss` 或 `fixed` 的局部片段，真实指标是 `fragment_hit_count=5`、`anchor_assisted_loss_hit_count=4`。这个结果有价值，但它只说明模型在带有明显前缀锚点时存在局部补全信号，不能直接说明模型已经具备无锚点问答或 holdout 任务能力。

因此 v1147 做的不是新训练，也不是模型晋升，而是一个对照诊断：复用 v1145 的真实训练 checkpoint，在同一个模型、同一个 tokenizer、同一套生成参数风格下，另外跑五个不含 `fixed`、`loss` 目标词的 unassisted holdout-style prompts。然后把这五个无锚点输出与 v1146 的五个锚点输出并排比较。它要回答的问题很窄：v1145 checkpoint 的信号到底更像“前缀锚点触发的 fragment completion”，还是已经自然扩展成“没有前缀锚点也能完整给出 fixed/loss pair”的能力。

本版明确不做三件事。第一，不重新训练 checkpoint，因为 v1147 的变量应只落在 decoding prompt 是否带锚点，而不是训练数据或训练步数变化。第二，不把 `loss` 片段命中视为完整能力恢复，因为无锚点场景真正需要的是 `fixed` 和 `loss` 同时出现。第三，不设置 `promotion_ready=True`，即便报告 `status=pass`，也只代表对照诊断成立，不代表模型可以进入晋升或发布。

## 上游链路位置

这一版属于 v1143-v1147 的真实能力链路。v1143 先把 `capability-regression-01 / required_term_coverage` 从 lookup-only manifest 变成一个真实 MiniGPT generation check。v1144 把 holdout scorecard smoke 也改为真实生成证据，并把输出喂给既有 scorecard builder。v1145 进一步做了小规模真实训练：用 loss-signal bridge 和 decoder-anchor distribution 语料训练一个 tiny checkpoint，训练指标显示 train loss 与 val loss 均下降。v1146 则使用这个 checkpoint 跑短 prompt 的 decoder-anchor fragment probe，观察到局部片段信号。

v1147 的角色是在 v1146 和下一步修复之间加一层“能力解释闸门”。如果 v1147 发现 unassisted prompts 也能完整恢复 `fixed/loss` pair，那么后续应该改成晋升边界的 replay check；如果 v1147 发现 unassisted 只能零散出现 `loss`，而无法同时恢复 `fixed`，那么后续更合理的动作就是做 unassisted holdout repair plan 或针对性训练补丁。真实结果属于后者：unassisted 出现 3 个 `loss` 片段，但 `fixed` 命中数是 0，完整 pair 命中数也是 0。

## 新增模块

核心模块是 `src/minigpt/decoder_anchor_holdout_comparison_v1147.py`。这个文件把 v1147 的逻辑分成四层：定位上游报告与 checkpoint、运行 unassisted cases、构造对照 rows、生成 checks 与 summary。这样做的原因是当前项目已经经历了大量治理版本，真正难维护的地方通常不是单个判断，而是路径解析、报告读取、运行证据和边界字段混在一起。v1147 把这些职责拆开，避免继续制造大而散的报告文件。

`locate_v1146_report` 支持传入 JSON 文件或输出目录。如果用户传目录，函数会自动补上 `model_capability_decoder_anchor_probe_v1146.json`。这个设计沿用项目里很多 report CLI 的习惯，降低手工复跑成本。

`locate_v1145_report_from_v1146` 是路径兜底函数。v1146 的 JSON 里保留了源 v1145 报告路径，但早期归档时某些路径在不同终端编码下显示会不稳定；同时 v1145 报告本身记录的 checkpoint 路径仍指向已清理的 `output/...`。v1147 不回写历史 tag，也不修改已归档 JSON，而是从当前 v1146 报告位置向上找到仓库根目录，再构造 `f/1145/解释/model-capability-loss-signal-bridge-decoder-anchor-distribution-v1145/model_capability_loss_signal_bridge_decoder_anchor_distribution_v1145.json`。这里的 `解释` 用模块常量 `EXPLAIN_DIR_NAME="\u89e3\u91ca"` 表达，避免命令行编码差异污染源码。

`resolve_comparison_paths` 是本版最重要的工程辅助函数。它先尝试使用显式传入的 checkpoint/tokenizer，再尝试 v1146 报告里的路径；如果这些路径不存在，就读取 v1145 loss-signal report，并复用 v1146 模块里的 `resolve_v1145_checkpoint_paths`。这样本版能兼容两类场景：本地 `output` 尚未清理时可以直接读取原路径；只保留归档证据时也能从 `f/1145/.../real-loss-signal-training-run` 找到真实 checkpoint。报告会把 `reported_checkpoint_exists`、`checkpoint_exists`、`used_v1145_archive_resolution` 等字段写入 `path_resolution`，让路径漂移不再是隐藏事实。

主函数 `build_decoder_anchor_holdout_comparison_v1147` 接收 v1146 report、checkpoint、tokenizer、device 和可选 generator runner。生产路径下 runner 是 `_generate_case`，它用 `MiniGPTGenerator` 和 `GenerationRequest` 真实加载 checkpoint；测试路径可以注入 fake runner，验证 builder 的契约而不依赖 torch 输出。这个注入点不是偷懒，而是为了把单元测试和真实运行分层：单测证明规则和结构，CLI 证明真实模型能执行。

## Unassisted cases 的设计

本版的五个 unassisted prompts 分别是 `answer:`、`answer: `、`completion:`、`finish: `、`state compact signal\nanswer:`。它们刻意不包含 `fixed` 或 `loss`。这是一个关键边界：如果 prompt 自身含有 `loss`，那么 generated 或 combined 文本里出现 `loss` 并不能说明模型主动生成了目标词，只可能是 prompt 泄漏。v1146 的锚点组可以使用 `lo`、`los`、`fixed `，因为它测的就是前缀锚点补全；v1147 的 unassisted 组必须避免这种提示泄漏，才有资格作为对照。

每个 case 的 `expected_terms` 都是 `["fixed", "loss"]`。评分只看 continuation，不看完整 generated。原因也很明确：MiniGPTGenerator 在 prompt 超过 block size 或被截断时，`generated` 可能不再以原 prompt 开头，如果把 generated 当作命中来源，会把提示文本、截断上下文和模型新增 token 混在一起。v1147 关注的是模型实际补出来的内容，因此 `_unassisted_row` 只对 `continuation` 做 term hit。它输出 `hit_terms`、`missed_terms`、`any_term_hit` 和 `full_pair_hit`，其中 `full_pair_hit` 才是无锚点能力恢复的核心字段。

真实运行结果很有解释价值：五个 unassisted cases 中有三个命中了 `loss`，但没有一个命中 `fixed`，也没有一个形成完整 `fixed/loss` pair。这说明 v1145 的训练确实让 `loss` 更容易从若干答题面冒出来，但还没有学成稳定的双词答案结构。换句话说，模型不是完全没有变化；它已经有了局部 loss suffix 信号，但它仍然没有无锚点 pair coexistence 能力。

## 对照 rows 与 summary

`_comparison_rows` 把 v1146 的 anchor rows 和 v1147 的 unassisted rows 按顺序配对，生成面向阅读的对照表。每一行包含 anchor 的 `prompt`、`combined`、`fragment_hit`、`anchor_loss_hit`，也包含 unassisted 的 `prompt`、`continuation`、`hit_terms`、`full_pair_hit`。这张表的意义不是做统计花活，而是让读者一眼看到：带 `lo/los/fixed` 前缀时，模型更容易补出目标片段；换成 `answer:`、`completion:` 这类无锚点提示时，它最多冒出 `loss`，但无法把 `fixed` 一起带出来。

summary 则把这件事量化：`anchor_fragment_hit_count=5`、`anchor_loss_hit_count=4`、`unassisted_any_term_hit_count=3`、`unassisted_fixed_hit_count=0`、`unassisted_loss_hit_count=3`、`unassisted_full_pair_count=0`。最关键的是 `anchor_over_unassisted_hit_delta=2` 和 `unassisted_full_pair_count=0`。前者说明 anchor-assisted fragment signal 确实强于无锚点任一 term 命中，后者说明完整 pair 能力尚未恢复。

`model_quality_claim` 被设置为 `anchor_assisted_signal_exceeds_unassisted_holdout_replay`。这个名字刻意很长，但它准确表达了边界：本版只声明锚点辅助信号超过无锚点 replay，而不是声明模型整体质量提升。`promotion_ready=False` 和 `unassisted_success_claim=False` 继续保留，防止读者把 pass 状态误读为模型晋升。

## 检查规则

`_checks` 覆盖十个点。前两个检查 v1146 是否通过、v1146 的 next step 是否确实指向本版对照。中间检查 checkpoint/tokenizer 是否存在、anchor rows 是否是五行、unassisted rows 是否执行五行、生成过程是否没有错误。最后三项是解释边界：anchor fragment hit 必须多于 unassisted any-term hit，unassisted 完整 pair 不能已经恢复，promotion boundary 必须保留。

这里最值得注意的是 `unassisted_pair_not_recovered`。如果未来某个 checkpoint 在无锚点提示下已经能完整输出 `fixed` 和 `loss`，这个检查会失败。这不是坏事，而是提示我们不应继续沿用“anchor 强于 unassisted”的诊断报告，而应该切换到更强的晋升边界检查。也就是说，v1147 的失败不一定意味着模型坏了；它可能意味着模型已经突破了本版假设，需要换更严格的报告类型。

## CLI 与运行证据

CLI 文件是 `scripts/run_decoder_anchor_holdout_comparison_v1147.py`。它默认读取 `f/1146/解释/model-capability-decoder-anchor-probe-v1146/model_capability_decoder_anchor_probe_v1146.json`，默认输出到 `output/decoder-anchor-holdout-comparison-v1147`。参数支持 `--decoder-anchor-probe`、`--loss-signal-distribution`、`--checkpoint`、`--tokenizer`、`--device`、`--require-pass` 和 `--force`。这让它既能在当前仓库归档路径中直接复跑，也能在测试或后续迁移时显式传入别的 checkpoint。

真实命令是：

```powershell
python scripts/run_decoder_anchor_holdout_comparison_v1147.py --out-dir output/decoder-anchor-holdout-comparison-v1147 --require-pass --force
```

真实输出为 `status=pass`、`decision=decoder_anchor_signal_exceeds_unassisted_holdout_replay`、`anchor_fragment_hit_count=5`、`unassisted_any_term_hit_count=3`、`unassisted_full_pair_count=0`。输出文件包括 JSON、CSV、TXT、Markdown 和 HTML，并归档到 `f/1147/解释/decoder-anchor-holdout-comparison-v1147`。HTML 通过 Playwright MCP 打开并截图，截图保存在 `f/1147/图片/decoder-anchor-holdout-comparison-v1147.png`。这张截图证明页面可渲染、summary cards 和 comparison rows 可见。

## 测试覆盖

测试文件是 `tests/test_decoder_anchor_holdout_comparison_v1147.py`。第一组测试用 fake runner 构造一个成功对照：anchor 五行全命中，unassisted 只有两个任一 term 命中，完整 pair 为零。它保护的是主 builder 的成功路径、summary 字段和 promotion boundary。第二组测试把 v1146 的 next step 改错，确认报告必须失败并给出 `v1146_next_step_matches_comparison` issue。第三组测试传入缺失 checkpoint，确认 `checkpoint_exists` 会阻断。第四组测试模拟 v1145 归档路径：源报告里记录 stale `output/...`，但同级 `real-loss-signal-training-run` 下有 checkpoint/tokenizer，resolver 必须 fallback 成功。第五组测试覆盖输出和 CLI：传目录而不是 JSON，创建 tiny checkpoint，确认 CLI 能写出 v1147 JSON。

这些测试不是为了追求数量，而是保护本版最容易出错的地方：上游 next_step 对齐、归档路径解析、无锚点对照规则、CLI 目录输入和输出格式。它们也延续了最近几版的分层验证方式：单测确保报告契约，真实 CLI 确保 MiniGPTGenerator 能加载真实 checkpoint，Playwright 截图确保 HTML 报告能作为人工复核材料。

## 与后续路线的关系

v1147 给出的下一步是 `build_unassisted_holdout_repair_plan`。这个建议来自真实对照结果，而不是凭空推进治理链。现在项目已经知道：v1145 checkpoint 的 `loss` 信号存在，前缀锚点能放大这个信号，但无锚点完整 pair 还没有恢复。因此后续更有价值的是针对 `fixed` 和 `loss` 的无锚点共现做小规模训练补丁或样本设计，而不是继续堆新的 wrapper 报告。

这也回应了前面用户反复提醒的方向：功能推进时要兼顾必要拆分和维护，不要只做很小的报告版本。v1147 同时做了真实模型输出对照、路径 resolver 收束、CLI、测试、归档和讲解；它没有新训练，但它把 v1145-v1146 的能力解释往前推进了一层，让下一步训练或 repair plan 更有依据。

## 一句话总结

v1147 把 v1146 的锚点片段命中从“看起来有效”推进成了“与无锚点 holdout replay 对照后仍然更强”的真实诊断，同时明确证明当前 checkpoint 还没有恢复无锚点 `fixed/loss` pair 能力，因此下一步应该修复 unassisted holdout，而不是宣布模型晋升。
