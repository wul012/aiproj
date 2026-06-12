# v1150 unassisted holdout repair training run：把修复语料推进成真实训练产物

## 本版目标与边界

v1150 的目标是把 v1149 生成的无锚点修复语料真正交给 MiniGPT 的训练入口执行一次 bounded tiny training，并把训练后的 checkpoint、tokenizer、metrics、manifest、sample、loss curve 与 handoff 汇总成可复核报告。v1149 已经把 v1148 的 repair seed blueprint 物化成 `unassisted_holdout_repair_seed_corpus.txt`、JSONL 样本、target-free holdout prompts 和 train command hint；但 v1149 仍然只是输入准备层，没有训练模型。v1150 接着把这条路线往前推进一格：确认这份 corpus 能被 `scripts/train.py --prepared-data` 消费，确认训练能完成到 `max_iters=50`，确认训练产物齐全，并确认 loss 指标出现下降。

本版明确不做模型能力提升结论。报告里的 `model_quality_claim` 是 `training_artifact_only`，`promotion_ready=False`。这不是保守措辞，而是当前证据链必须遵守的边界：loss 下降说明模型在这份小语料上学到了局部模式，不能直接说明它在未见过的 target-free holdout prompt 上已经稳定输出 `fixed loss`。尤其本轮 sample 只命中 `fixed`，没有命中 `loss`，更说明不能把训练运行本身包装成能力成功。因此 v1150 的真实价值是把“有一个可用 checkpoint 可供 replay”固定下来，让 v1151 能用同一批 holdout prompts 做复测。

这条边界也回应了之前 Claude review 对项目路线的提醒：不能继续只做 lookup 或 governance report，而要执行一个真正的模型生成相关检查。v1143 开始项目已经从 required term coverage 的真实执行进入模型能力方向；v1147 证明 decoder-anchor evidence 强于 unassisted replay，但 unassisted full-pair 仍为 0；v1148 产出修复计划；v1149 产出修复语料；v1150 就是这条修复路线的训练执行版。它不是新治理链，而是把已有修复路线落到真实训练产物。

## 新增文件与职责

本版新增核心模块 `src/minigpt/unassisted_holdout_repair_training_run_v1150.py`。这个模块不直接训练模型，而是负责读取 v1149 seed corpus report 和一个训练 run directory，检查 run directory 是否满足 v1150 的训练证据契约，然后输出结构化报告。把训练执行和报告构建分开，是为了让测试可以用 fake run 覆盖契约，不必每个单测都启动 PyTorch；真实 CLI 则可以在需要时先运行训练，再调用同一个 builder 生成报告。

新增 CLI 是 `scripts/run_unassisted_holdout_repair_training_v1150.py`。它支持两种模式：默认模式只检查已有 run directory；传入 `--run-training` 时，会调用 `scripts/train.py` 先训练，再生成 v1150 报告。本版真实归档使用的是 `--run-training`，因此 `f/1150` 中的 checkpoint 和 metrics 不是测试 fixture，也不是手工拼出的 JSON，而是由项目原训练入口产生的实际文件。

新增测试文件是 `tests/test_unassisted_holdout_repair_training_run_v1150.py`。测试不跑真实 PyTorch，而是构造一个具有 checkpoint、tokenizer、metrics、manifest、sample 和 prepared corpus 的 fake run，用来验证 v1150 builder 的契约：正常 run 应该通过；缺少 checkpoint 应该失败；训练使用了不同 corpus 应该失败；writer 和 CLI 应该能输出 JSON/CSV/TXT/Markdown/HTML 以及 handoff sidecar。这个测试策略让训练逻辑和证据检查逻辑各自归位：训练入口本身已有项目内覆盖，v1150 重点保护的是“训练产物是否可被治理链正确识别”。

本版还新增归档说明 `f/1150/解释/说明.md`，并把正式 HTML 报告截图保存到 `f/1150/图片/unassisted-holdout-repair-training-run-v1150.png`。README、`f/README.md` 和工程保养阶段 README 也会更新，用来让项目首页、运行证据目录和代码讲解目录都能定位到 v1150。

## 输入来源

v1150 默认输入是：

```text
f/1149/解释/unassisted-holdout-repair-seed-corpus-v1149/unassisted_holdout_repair_seed_corpus_v1149.json
```

对应的训练文本是同目录下的：

```text
unassisted_holdout_repair_seed_corpus.txt
```

这个路径由 `default_v1149_seed_corpus_path` 和 `seed_corpus_text_path` 共同决定。`locate_v1149_seed_corpus` 支持传入 JSON 文件或输出目录：如果用户传目录，就自动拼接 `unassisted_holdout_repair_seed_corpus_v1149.json`。这延续了最近几版的输入习惯，让脚本既能直接消费归档目录，也能在测试中消费临时目录。

v1149 report 的关键字段是 `summary.unassisted_holdout_repair_seed_corpus_ready=True`、`summary.next_step=run_unassisted_holdout_repair_training`、`summary.promotion_ready=False` 和 `corpus_text`。v1150 的检查会确认这些字段仍然成立。如果 seed corpus 没 ready，v1150 不能训练；如果 v1149 的 next step 不指向 training，说明链路顺序错了；如果 promotion_ready 被提前打开，说明有人把 seed corpus 或训练前输入误标成能力证据。

## 训练执行

真实 v1150 命令如下：

```powershell
python scripts/run_unassisted_holdout_repair_training_v1150.py --out-dir output/unassisted-holdout-repair-training-run-v1150 --run-training --require-training-ready --force
```

CLI 在 `--run-training` 模式下调用 `scripts/train.py`，参数保持轻量且可复现：char tokenizer、batch size 8、block size 24、max iters 50、eval interval 10、eval iters 2、learning rate 0.01、train ratio 0.85、1 layer、1 head、embedding 16、dropout 0、seed 1150、CPU device。这里没有扩大模型，也没有换复杂 tokenizer，因为本轮目标不是追求大规模训练效果，而是验证 v1149 修复语料能否产生一个完整 checkpoint，并给下一版 replay 提供输入。

`scripts/train.py` 完成训练后会生成 `checkpoint.pt`、`tokenizer.json`、`metrics.jsonl`、`train_config.json`、`run_manifest.json`、`history_summary.json`、`loss_curve.svg`、`sample.txt` 和 `prepared_corpus.txt`。v1150 builder 会把这些文件统一作为 artifact rows 写入报告。真实运行中，训练一共记录了 6 条 metrics：step 1、10、20、30、40、50。train loss 从 `3.0307888984680176` 降到 `1.2284066677093506`，val loss 从 `2.9943225383758545` 降到 `1.499302864074707`。报告汇总为 `train_loss_delta=-1.802382`、`val_loss_delta=-1.49502`。

这些数字证明了训练运行有效，但不是能力证明。因为训练 corpus 极小，loss 下降可能只是局部记忆和短模式吸收。要证明模型能力，必须用 v1149 固定下来的 target-free holdout prompts 生成输出，再检查 `fixed` 与 `loss` 的命中情况。v1150 因此把下一步固定为 `run_unassisted_holdout_repair_replay_comparison`。

## 核心 builder 流程

`build_unassisted_holdout_repair_training_run_v1150` 是本版主函数。它接收 `seed_corpus_report` 和 `run_dir`，读取训练产物，然后组装完整报告。函数先解析 `seed_summary`，再通过 `_artifacts` 枚举 run directory 中的关键文件。`_metrics` 读取 `metrics.jsonl`，取第一条和最后一条记录，计算 train/val loss delta。`_read_json` 读取 `train_config.json` 和 `run_manifest.json`，`_read_text` 读取 `prepared_corpus.txt` 和 `sample.txt`。

接着 `_checks` 生成检查行。检查行覆盖上游 ready、next step、checkpoint、tokenizer、metrics、manifest、prepared corpus 一致性、metrics 记录数量、max iters 是否到达、train loss 是否下降、val loss 是否下降，以及 promotion boundary 是否保持关闭。这里最关键的是 `prepared_corpus_matches_seed`。它会拿训练目录里的 `prepared_corpus.txt` 与 v1149 report 的 `corpus_text` 做完全一致比较。这样可以防止训练时误用别的 corpus，或者手工复制时漏行。模型能力路线最怕“训练输入和报告宣称不一致”，所以这个检查必须硬。

`_training` 负责从检查结果和训练产物中提取给后续消费的字段，包括 artifact count、metric record count、final step、final train/val loss、loss delta、max iters、seed、checkpoint path、tokenizer path、prepared data path、source seed corpus path、sample hit 状态和下一步。`sample_fixed_hit` 与 `sample_loss_hit` 只是诊断字段，不参与 pass/fail。真实运行中 sample 命中 fixed 但没有命中 loss，所以它提醒下一版 replay 仍然必要。

`_summary` 把核心指标压缩成报告首页可读的字段。`_interpretation` 则把边界写成机器可读的解释：如果 status 失败，就给出 `not_claimed`；如果 status 通过，也只给出 `training_artifact_only`，并说明能力提升必须通过 unchanged target-free holdout prompts replay 证明。

## 输出与 handoff

`write_unassisted_holdout_repair_training_run_v1150_outputs` 使用 `write_readability_outputs` 写通用的 JSON、CSV、TXT、Markdown 和 HTML。row key 使用 `artifact_rows`，所以 HTML 表格展示的是 checkpoint、tokenizer、metrics、manifest、history summary、loss curve、sample 和 prepared corpus 等训练产物，而不是 seed examples。

本版还额外写出 `unassisted_holdout_repair_training_handoff_v1150.json`。这个 handoff 只保留下一版最需要的内容：status、decision、source seed corpus、run dir、checkpoint、tokenizer、holdout prompts、model quality claim、promotion boundary 和 next step。它的作用是让 v1151 不必重新从大报告里猜路径。v1151 可以读取这个 handoff，拿 checkpoint/tokenizer 运行生成，再拿 v1149 的 holdout prompts 做固定复测。

handoff 中的 `holdout_prompts` 指向 v1149 的：

```text
unassisted_holdout_repair_holdout_prompts.json
```

这点很重要，因为评估题不能在训练后临时修改。v1149 先固定 target-free holdout prompts，v1150 只训练并交接，v1151 再复测，这样链路才有因果顺序。

## 测试覆盖

`tests/test_unassisted_holdout_repair_training_run_v1150.py` 有四组测试。第一组构造通过状态的 seed corpus report 和 fake run，断言 `status=pass`、`decision=unassisted_holdout_repair_training_run_ready`、`final_step=50`、train/val loss delta 都小于 0、`sample_fixed_hit=True`、`sample_loss_hit=False`、`model_quality_claim=training_artifact_only`、`promotion_ready=False`、`next_step=run_unassisted_holdout_repair_replay_comparison`。这组测试保护正常链路。

第二组删除 `checkpoint.pt`，确认报告失败并出现 `checkpoint_exists` issue。第三组把 fake run 的 `prepared_corpus.txt` 改成不同文本，确认出现 `prepared_corpus_matches_seed` issue。这个负例非常关键，因为它保护的是训练输入的来源一致性，而不是简单文件存在性。第四组测试 writer 与 CLI：传入 seed corpus 目录能定位 JSON，输出集合包含通用五件套和 training handoff，CLI 在不跑训练的模式下能消费已有 run directory 并通过 `--require-training-ready`。

真实验证还包含 py_compile、聚焦测试、正式 CLI 训练、Playwright MCP 截图、source encoding、全量 pytest 和 git diff check。这样本版既覆盖了代码契约，也覆盖了真实产物。

## 归档与链路角色

v1150 运行证据归档在 `f/1150`。`f/1150/解释/unassisted-holdout-repair-training-run-v1150` 保存完整报告和训练 run，`f/1150/图片/unassisted-holdout-repair-training-run-v1150.png` 保存 HTML 截图。截图不是为了展示好看，而是证明归档后的 HTML 报告能打开，并且 status、decision、loss delta、sample hit 和 artifact rows 可见。

在整条路线里，v1150 的位置很清楚：v1147 发现 unassisted full pair 失败，v1148 规划修复，v1149 准备训练输入，v1150 执行训练并交接 checkpoint，v1151 应该做 replay comparison。这个顺序避免了过去项目容易出现的问题：先写很多治理报告，再回头发现没有真实 checkpoint 或没有固定评估 prompt。现在每一步都有自己的输入、输出和边界。

## 一句话总结

v1150 把 v1149 的无锚点修复语料变成了真实、可复核、可交接的训练 checkpoint，但仍然把模型能力结论留给下一版 replay comparison，项目因此从“准备训练”推进到“有训练产物可测”。
