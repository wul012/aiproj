# v1151 unassisted holdout repair replay comparison：把训练产物送回固定 holdout 验证

## 本版目标与边界

v1151 的目标是把 v1150 训练出的 checkpoint 真正送回 v1149 固定下来的 target-free holdout prompts 上做 replay comparison。v1150 已经证明修复语料可以完成一次 bounded CPU training，并且 train/val loss 都有下降；但 loss 下降只是训练信号，不等价于模型在无锚点提示下真的会输出 `fixed loss`。因此 v1151 要做的是能力验证：同一批无目标词 prompt，不改题、不加 decoder anchor、不换 checkpoint，用真实 `MiniGPTGenerator` 生成 continuation，然后统计 `fixed`、`loss` 和完整 pair 的命中情况。

本版边界同样清楚：`status=pass` 只表示 replay comparison 执行成功，输入完整，5 个 holdout prompt 都产生了 generation row。它不代表模型能力恢复。能力恢复需要看 `all_full_pair_hit` 和 `full_pair_case_count`。真实结果是 `fixed_hit_case_count=4`、`loss_hit_case_count=0`、`full_pair_case_count=0`，所以结论只能是 `bounded_holdout_replay_partial_signal`。这比 v1147 的 unassisted full-pair 0 有进展，因为现在多数 prompt 能输出 `fixed`；但还不是完整 `fixed loss`。

这个边界对项目很重要。早期项目已经有很多治理产物、manifest、handoff、gate 和 receipt，如果把 v1150 的 loss 下降直接写成能力提升，就会再次把治理链误当成模型质量。v1151 把这个风险关住：它承认训练有效，但要求真实生成证明；它承认 partial signal，但拒绝 promotion。

## 前置链路

v1151 接在 v1147-v1150 之后。v1147 对比 decoder-anchor 与无锚点 replay，发现 anchor-assisted 路径能命中更多 fragment，但无锚点完整 pair 仍为 0。v1148 根据这个缺口生成修复计划和 seed blueprint。v1149 把 blueprint 物化成训练 corpus 与 target-free holdout prompts。v1150 运行 bounded training，产出 checkpoint、tokenizer、metrics 和 handoff。v1151 读取这个 handoff，使用 v1149 的 holdout prompts 进行真实 replay。

这样的顺序保证了评估题没有在训练后被临时改动。v1149 先固定 prompts，v1150 训练，v1151 replay。训练之前就确定的 holdout prompts，比训练之后手写的 prompt 更可信。它减少了人为调参和选择性展示的空间。

## 新增模块结构

核心模块是 `src/minigpt/unassisted_holdout_repair_replay_comparison_v1151.py`。模块采用短名版本化，不再沿用旧 route-promotion 的长文件名。它的职责分成五块：定位 handoff、读取 JSON、解析 checkpoint/tokenizer/holdout prompts、运行生成并打分、写 readable report 和 generation rows sidecar。

`default_v1150_training_handoff_path` 返回默认归档路径：

```text
f/1150/解释/unassisted-holdout-repair-training-run-v1150/unassisted_holdout_repair_training_handoff_v1150.json
```

`locate_v1150_training_handoff` 支持文件或目录输入。如果传目录，就自动拼接 `TRAINING_HANDOFF_NAME`。这和 v1149、v1150 的 CLI 风格保持一致。

`read_json_report` 和 `read_json_rows` 负责输入解析。前者读取 handoff，后者读取 holdout prompts 或预计算 generation rows。`read_json_rows` 要求顶层是 list，这样可以避免把错误的 report JSON 当成 rows 消费。

## handoff 回退机制

v1151 里最值得注意的工程修复是 `_resolve_handoff_artifact`。真实 v1150 handoff 是在 `output/unassisted-holdout-repair-training-run-v1150` 下生成后复制到 `f/1150` 的，因此 handoff 中的 checkpoint/tokenizer 路径仍然是训练时的 `output/.../run/checkpoint.pt` 和 `output/.../run/tokenizer.json`。按照清理规则，临时 `output` 目录会被删除，所以如果 v1151 只信 handoff 里的原始路径，就会在归档后失效。

为了解决这个问题，v1151 不修改历史 v1150 tag，而是在消费端增加兼容回退：如果 handoff 记录的路径存在，就直接使用；如果不存在，并且当前知道 handoff 文件路径，就尝试从 handoff 同目录的 `run/checkpoint.pt` 和 `run/tokenizer.json` 读取。v1150 的归档目录正好保存了完整 `run/`，所以这个回退能让归档 handoff 长期可用。

这个设计比回头重写 v1150 更稳。v1150 已经提交、打 tag、CI 通过；v1151 作为后续消费者，应当具备处理“handoff 指向运行时路径、归档里有同名 artifact”的能力。测试里也专门覆盖了这个场景：handoff 里写一个已经删除的 output 路径，但同目录 `run/` 下存在真实文件，builder 应该通过并把 checkpoint 解析到 archived sibling run。

## 生成与打分

`build_unassisted_holdout_repair_replay_comparison_v1151` 是主函数。它先解析 checkpoint、tokenizer 和 holdout prompts，再运行 `_preflight_checks`。preflight 检查包括 handoff 是否 pass、next step 是否为 replay comparison、checkpoint/tokenizer 是否存在、holdout prompts 是否存在且数量不少于 4、prompt 是否 target-free，以及 promotion boundary 是否保持关闭。

`holdout_prompts_target_free` 是关键检查。它会检查每个 prompt 是否包含 expected terms。因为本版要验证无锚点能力，如果 prompt 自己已经包含 `fixed` 或 `loss`，生成命中就没有意义。真实 v1149 的 holdout prompts 都通过这个检查。

preflight 通过后，模块调用 `_generation_rows`。真实运行时，它使用 `_generate_case`，也就是 `MiniGPTGenerator(checkpoint, tokenizer, device).generate(GenerationRequest(...))`。每个 prompt 使用自己的 `max_new_tokens`、`temperature`、`top_k`，没有 seed 时用 `115100 + index`，保证 replay 可复现。测试和离线复核可以传 `precomputed_generations`，这样 CLI 不必加载真实 PyTorch checkpoint 也能测试输出链路。

生成后 `_scored_generation` 会只看 continuation 部分，统计 expected terms。默认 expected terms 是 `fixed` 和 `loss`。每行输出包含 `fixed_hit`、`loss_hit`、`full_pair_hit` 和 row `status`。如果两个词都命中，status 是 `pass`；只命中一个是 `partial`；都没命中是 `fail`。本版真实 rows 里，4 行是 partial，1 行 fail。

## comparison 与 summary

`_comparison` 汇总所有 generation rows。它统计 `case_count`、`fixed_hit_case_count`、`loss_hit_case_count`、`full_pair_case_count`、`any_hit_case_count`、`full_pair_rate`、`all_full_pair_hit` 和 `partial_signal_visible`。这些字段让报告能区分三种情况：完全恢复、部分信号、完全失败。

真实 v1151 是第二种：`fixed_hit_case_count=4`，`loss_hit_case_count=0`，`full_pair_case_count=0`。因此 `_decision` 返回 `unassisted_holdout_repair_replay_partial_signal`，`_model_quality_claim` 返回 `bounded_holdout_replay_partial_signal`，`_next_step` 返回 `diagnose_unassisted_holdout_repair_partial_signal`。

如果未来某个 checkpoint 让 5 个 holdout prompt 全部命中 `fixed` 和 `loss`，v1151 会返回 `unassisted_holdout_repair_replay_full_pair_recovered_candidate`。这里仍然叫 candidate，不直接叫 promotion，因为单 seed、单小语料、单次 replay 还不够。下一步应跨 seed 重复，再考虑 promotion。

## CLI 与真实运行

CLI 文件是 `scripts/run_unassisted_holdout_repair_replay_comparison_v1151.py`。真实命令如下：

```powershell
python scripts/run_unassisted_holdout_repair_replay_comparison_v1151.py --out-dir output/unassisted-holdout-repair-replay-comparison-v1151 --require-comparison-ready --force
```

真实输出是 `status=pass`、`decision=unassisted_holdout_repair_replay_partial_signal`、`case_count=5`、`fixed_hit_case_count=4`、`loss_hit_case_count=0`、`full_pair_case_count=0`、`failed_check_count=0`。这说明输入链路、归档回退、生成执行和报告输出都成立。

生成 rows 写入 `unassisted_holdout_repair_replay_generation_rows_v1151.json`。其中 `answer:`、`finish:`、`state compact signal\nanswer:` 和 `signal:` 都生成了 `fixed`，`completion:` 生成了类似 `fios` 的噪声。所有 case 都没有生成 `loss`。这提供了下一版诊断方向：当前训练让模型学会了第一目标词，但没有把 `loss_after_fixed` 的训练-only context 转化为无锚点 continuation。

## 测试覆盖

`tests/test_unassisted_holdout_repair_replay_comparison_v1151.py` 覆盖五组场景。第一组是 partial signal：fake runner 让 4 个 case 中部分命中 `fixed`，断言 report pass、decision 是 partial、full pair 为 0、require full pair 会返回 1。第二组是 full pair candidate：fake runner 全部返回 `fixed loss`，断言 `all_full_pair_hit=True`，并且 `require_full_pair` 返回 0。第三组把 prompt 改成 `answer fixed:`，确认 target-free preflight 会失败，且不运行 generation rows。第四组验证 archived handoff fallback：handoff 写入失效 output 路径，但同目录 `run/` 有 artifact，builder 应该成功解析。第五组验证 writer 和 CLI 支持 `--precomputed-generations`，确保离线 rows 也能生成报告和 sidecar。

这些测试保护了本版最重要的两条边界：第一，comparison ready 和 full pair success 是两回事；第二，归档 handoff 必须在临时 output 删除后仍可消费。

## 运行证据与文档

v1151 运行证据归档在 `f/1151/解释/unassisted-holdout-repair-replay-comparison-v1151`，截图在 `f/1151/图片/unassisted-holdout-repair-replay-comparison-v1151.png`。截图通过 Playwright MCP 打开归档 HTML 后生成。README、`f/README.md` 和工程保养阶段 README 会同步更新，保证首页和索引都指向本版。

本版的文档不只是记录文件清单，而是把 partial signal 的含义写清楚：v1150 训练不是空转，因为 `fixed` 命中明显增加；但 `loss` 仍然为 0，说明完整目标没有恢复。这个结论比“成功/失败”二分更有价值，因为它给下一版提供了具体诊断点。

## 一句话总结

v1151 用真实 replay 证明 v1150 checkpoint 已经出现无锚点 `fixed` partial signal，但完整 `fixed loss` 仍未恢复，因此项目下一步应诊断 `loss` 缺失，而不是提前声明模型能力提升。
