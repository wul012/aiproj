# v1149 unassisted holdout repair seed corpus：把修复蓝图变成训练前输入

## 本版目标与边界

v1149 的目标是把 v1148 生成的 `repair_seed_blueprint_rows` 物化成下一版训练可以直接消费的文件。v1148 已经完成了计划层的收束：确认当前能力缺口是无锚点 `fixed` 和完整 `fixed/loss` pair 缺失，确认下一步允许做 bounded repair training，并生成了 9 条 seed blueprint。v1149 接着做更落地的一步：把这些 blueprint 行写成训练 corpus、JSONL 样本、target-free holdout prompts 和 train command hint。

本版仍然不训练模型，也不声明模型能力提升。它的 `model_quality_claim` 是 `seed_corpus_only`，`promotion_ready=False`。这两个字段说明：v1149 只是准备训练输入和复测提示，不能被当成 checkpoint 改善证据。它的价值在于降低 v1150 训练版本的不确定性，让下一版不需要再猜 prompt/completion 怎么组织，也不需要重新讨论哪些提示能进评估、哪些只能作为训练上下文。

这个边界很重要。当前项目已经从早期“治理链很完整”转向“模型能力需要真实提升”。真实提升不是靠多写一个报告得来的，而是要逐步把证据链落到训练数据、训练运行和复测上。v1149 就是这个转换里的训练输入层：它把 v1148 计划中的蓝图变成文件，准备给 `scripts/train.py --prepared-data` 使用。

## 输入来源

v1149 默认读取 `f/1148/解释/unassisted-holdout-repair-plan-v1148/unassisted_holdout_repair_plan_v1148.json`。如果同目录下存在 `unassisted_holdout_repair_seed_blueprint.json`，就优先读取这个 sidecar；如果 sidecar 不存在，就从主计划 JSON 的 `repair_seed_blueprint_rows` 读取。这个设计让它既能消费正式归档产物，也能在测试或迁移时只依赖主 JSON。

输入里的核心字段是 v1148 summary：`unassisted_holdout_repair_plan_ready=True`、`next_step=materialize_unassisted_holdout_repair_seed_corpus`、`promotion_ready=False`。这些字段保证 v1149 不会被提前运行。如果 v1148 计划没有 ready，或者 next step 不是 seed corpus materialization，v1149 应该失败，而不是自己替上游作决定。

seed blueprint 本身有 9 条。前 5 条来自 v1147 的无锚点提示面，例如 `answer:`、`completion:`、`finish:`、`state compact signal\nanswer:`，completion 要求 `fixed loss`。后 4 条是 v1148 增补的修复样本，包括 fixed-first、loss-after-fixed 和 short-pair。v1149 会保留这些样本，但会对它们的评估边界做分类。

## 新增模块结构

核心模块是 `src/minigpt/unassisted_holdout_repair_seed_corpus_v1149.py`。它延续最近几版的短名风格，没有把历史 route-promotion 长命名继续扩散。模块内部主要分成五块：定位输入、加载 blueprint、构建 materialization report、写 sidecar 输出、生成检查与 summary。

`locate_v1148_plan` 支持 JSON 或目录输入。如果传入目录，就拼接 `unassisted_holdout_repair_plan_v1148.json`。`default_v1148_plan_path` 用 `EXPLAIN_DIR_NAME` 构造默认归档路径，避免中文目录在不同终端编码下造成源码污染。

`load_seed_blueprint` 是本版的输入兼容层。它先看 CLI 是否传了 `--seed-blueprint`，再看 v1148 plan 同目录的 sidecar，最后回退到 plan JSON 内嵌的 `repair_seed_blueprint_rows`。这种顺序保证正式归档中的 sidecar 是首选，因为它就是 v1148 专门给后续版本消费的文件；同时也保证测试 fixture 不必复制整个目录结构。

`build_unassisted_holdout_repair_seed_corpus_v1149` 是主 builder。它接收 plan report 和 seed rows，生成 `examples`、`holdout_prompt_rows`、`corpus_text`、`train_command_hint`、`check_rows`、`materialization` 和 `summary`。这比只写一个 corpus 文件更稳，因为后续版本需要知道 corpus 是从哪里来的、哪些 prompt 能评估、哪些样本只是 training-only context。

## 样本物化逻辑

`_example_rows` 把每条 blueprint 转成训练样本行。每行保留 `example_id`、`kind`、`prompt`、`completion`、`text`、`target_terms`、`decoder_anchor`、`decoder_anchor_boundary`、`training_only_context`、`prompt_contains_target_terms`、`source` 和 `variant_index`。其中 `text` 是真正进入 corpus 的字符串，由 `_join_prompt_completion` 负责拼接。

这里有两个边界字段值得注意。`decoder_anchor` 必须为 False。v1149 是无锚点修复，不允许把 `lo`、`los`、`fixed ` 这类 decoder anchor 当成样本类型混进去。`training_only_context` 则用于处理 `loss-after-fixed-01` 这种样本。它的 prompt 是 `answer: fixed`，这确实包含目标词 `fixed`，因此不能进入无锚点评估 prompts；但它可以作为训练上下文，用来教模型在已经出现 fixed 后继续生成 loss。v1149 用 `decoder_anchor_boundary=training_only_context_not_eval` 把这类样本明确隔离出来。

`_holdout_prompt_rows` 只从 target-free、非 training-only、未重复的 prompt 中生成 holdout prompts。每个 holdout prompt 都带 `expected_terms=["fixed","loss"]`、`max_new_tokens=8`、`temperature=0.2`、`top_k=5`。真实输出里 `target_free_holdout_prompt_count=5`，说明它保留了足够的无锚点评估面。这个文件后续可以给 v1150 或 v1151 的 replay 使用，避免训练后临时改题。

## 输出文件

v1149 输出不仅有通用 readable report，还额外写四个 sidecar：

- `unassisted_holdout_repair_seed_corpus.txt`
- `unassisted_holdout_repair_seed_corpus.jsonl`
- `unassisted_holdout_repair_holdout_prompts.json`
- `unassisted_holdout_repair_train_command_hint.json`

`seed_corpus.txt` 是最直接的训练输入，可以传给 `scripts/train.py --prepared-data`。`seed_corpus.jsonl` 保留结构化样本，方便排查每行来自哪种修复目的。`holdout_prompts.json` 是后续复测输入，专门保持 target-free。`train_command_hint.json` 则写出建议的训练参数，例如 char tokenizer、batch size 8、block size 24、max iters 50、learning rate 0.01、CPU device 等。它不是强制配置，但能让 v1150 训练版本少做一次人为猜测。

真实 v1149 运行生成的 summary 是：`example_count=9`、`unique_prompt_count=6`、`pair_example_count=7`、`target_free_holdout_prompt_count=5`、`training_only_context_count=1`、`decoder_anchor_example_count=0`、`corpus_char_count=198`。这些数字说明 corpus 很小，适合做 bounded repair training；同时它保留了足够 target-free holdout prompts，用于训练后复测。

## 检查规则

`_checks` 覆盖十个关键条件。首先检查 v1148 plan 是否 pass、plan ready 是否为 True、next step 是否指向 seed corpus materialization。然后检查 seed blueprint 至少有 8 行，所有 blueprint 行都被 materialized 成 examples，pair examples 至少 5 条，decoder anchor 数量必须为 0，target-free holdout prompts 至少 4 个，corpus 字符数要大于 120，最后确认上游 promotion boundary 没有被打开。

这些检查既保护前置链路，也保护训练输入质量。比如 `decoder_anchor_free` 防止本来要修的无锚点能力又被锚点样本污染；`target_free_holdout_prompts_present` 防止训练版本没有干净复测题；`promotion_boundary_kept` 防止有人把 seed corpus 当作质量证明。

如果未来 v1148 的 blueprint 被改坏，例如加入了 `decoder_anchor=True` 的行，v1149 会失败。如果 v1148 plan 还没 ready，v1149 也会失败。这样的失败比默默生成 corpus 更好，因为训练输入一旦错了，后续 checkpoint 结果也会变得不可解释。

## CLI 与真实运行

CLI 文件是 `scripts/materialize_unassisted_holdout_repair_seed_corpus_v1149.py`。真实命令如下：

```powershell
python scripts/materialize_unassisted_holdout_repair_seed_corpus_v1149.py --out-dir output/unassisted-holdout-repair-seed-corpus-v1149 --require-seed-ready --force
```

真实输出为 `status=pass`、`decision=unassisted_holdout_repair_seed_corpus_ready`。输出归档在 `f/1149/解释/unassisted-holdout-repair-seed-corpus-v1149`，截图归档在 `f/1149/图片/unassisted-holdout-repair-seed-corpus-v1149.png`。截图通过 Playwright MCP 打开 HTML 报告后生成，页面里能看到 summary cards 和 seed corpus examples 表。

## 测试覆盖

测试文件是 `tests/test_unassisted_holdout_repair_seed_corpus_v1149.py`。第一组测试验证正常物化路径：9 条样本、至少 4 个 target-free holdout prompts、0 个 decoder anchor、`model_quality_claim=seed_corpus_only`。第二组测试把 plan ready 改成 False，确认 `v1148_plan_ready` issue 会阻断。第三组测试把第一条 seed row 改成 `decoder_anchor=True`，确认 `decoder_anchor_free` 会失败。第四组测试覆盖 writer 和 CLI，确认传目录可以定位 v1148 plan，sidecar blueprint 能加载，最终能写出 corpus 与 holdout prompts。

这些测试保护的是 v1149 的真实职责：不是训练模型，而是正确准备训练输入，并且保留复测题的干净边界。

## 一句话总结

v1149 把 v1148 的无锚点修复蓝图落实成了可训练 corpus、结构化样本、target-free holdout prompts 和训练参数提示，为 v1150 的 bounded repair training 铺好了输入层，同时继续避免把种子语料误读成模型能力提升。
