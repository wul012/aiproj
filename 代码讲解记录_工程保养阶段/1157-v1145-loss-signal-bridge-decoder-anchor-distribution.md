# v1145 loss signal bridge 与 decoder anchor distribution 真实证据

## 本版目标与边界

v1145 的目标是接住 v1143、v1144 之后的路线，把“模型能力回归治理”从只读 artifact 与单点生成 smoke，推进到一次更接近真实训练链路的 bounded evidence。v1143 已经完成 `required_term_coverage` 的真实生成执行，证明 `capability-regression-01` 不再只是 manifest 里的一条 lookup；v1144 又把 `holdout_scorecard_smoke` 落成了五个真实 MiniGPT generation case，并通过已有 `benchmark_scorecard` 生成 nested scorecard。到 v1145，如果继续堆一层 review、index、readiness，就会回到治理链自我循环。所以本版选择做两件更贴近模型能力本身的事：第一，materialize 一份小型 `loss_signal_bridge` 语料，并用 `scripts/train.py` 跑真实 CPU training；第二，复用已有 decoder-anchor distribution audit，检查这份训练语料里的 carry-forward、direct answer、decoder bridge 三类样本是否均衡。

本版边界必须说清楚。v1145 不做模型 promotion，不宣称 MiniGPT 已有通用泛化能力，也不把一次 40 step 的小训练当成生产级模型评估。它只回答一个有限问题：在 v1144 之后，项目能否从“真实生成 smoke”继续走到“真实训练产生 loss 信号，并且训练语料的 decoder anchor 分布可解释”。因此报告里的 `model_quality_claim` 被命名为 `loss_signal_bridge_and_decoder_anchor_distribution_real_execution`，而 `promotion_ready` 明确保持 `False`。这两个字段一起表达了本版的姿态：它比普通治理报告更实，但仍是 bounded evidence，不是最终模型质量结论。

## 前置链路

v1145 的前置是 `f/1144/解释/model-capability-holdout-scorecard-smoke-v1144/model_capability_holdout_scorecard_smoke_v1144.json`。CLI 默认读取这份报告，并在 check rows 里校验两个条件：`status=pass`，以及 `summary.holdout_scorecard_smoke_ready=True`。这样做的原因是，v1145 不是凭空开始一条新路线，而是沿着 Claude review 给出的三步路线走：v1143 做真实 required-term execution，v1144 做真实 holdout scorecard smoke，v1145 做 loss signal bridge 加 decoder anchor distribution。前置校验使报告链条具备顺序性，避免后续有人直接拿 v1145 的训练结果跳过 v1144。

本版还复用了一条较早存在的 decoder-anchor 逻辑：`model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit`。这条旧能力本来服务于 route promotion bounded real replay 的 decoder-anchor 种子审计，它已经有 bucket 规则、risk 判断、Markdown/HTML 输出和测试覆盖。v1145 没有重新发明一套分布审计，而是把新 materialize 的 seed revision 和 diagnostic report 喂给旧 builder，让旧规则继续发挥作用。这是本版比较关键的工程判断：新增能力应该组合已有成熟部件，而不是因为版本推进就复制一份相似逻辑。

## 新增模块

核心文件是 `src/minigpt/model_capability_loss_signal_bridge_decoder_anchor_distribution.py`。它是一个短名模块，避免回到此前过长文件名和过长能力链命名的问题。模块暴露的主要函数包括：

- `materialize_loss_signal_bridge_inputs`
- `run_loss_signal_bridge_training`
- `build_loss_signal_bridge_decoder_anchor_distribution`
- `write_loss_signal_bridge_decoder_anchor_distribution_outputs`
- `resolve_exit_code`

`default_decoder_anchor_examples` 定义了九条样本，分成三组：三条 `carry_forward_*`，三条 `unanchored_direct_answer`，三条 `prefix_decoder_bridge`。这三个 revision type 并不是随便取名，它们对应旧 distribution audit 的 bucket 规则：`carry_forward` 前缀会落入 carry-forward bucket，`unanchored_direct_answer` 会落入 direct-answer bucket，`prefix_` 前缀会落入 decoder-bridge bucket。每组各三条，所以最终分布是 `0.3333 / 0.3333 / 0.3333`。这使 v1145 的分布结论可以由代码规则推导，而不是报告里手写一个“均衡”结论。

`materialize_loss_signal_bridge_inputs` 负责把这些内存样本写成四类输入：语料 TXT、examples JSONL、seed revision JSON、failure diagnostic JSON。语料 TXT 由 prompt 和 completion 拼接而成，用于真实训练；examples JSONL 是可读的逐行样本；seed revision JSON 是喂给旧 distribution audit 的结构化输入；failure diagnostic JSON 提供 `case_count` 和 `zero_hit_case_count`，用于旧审计里的风险判断。这里的 diagnostic 是一个轻量占位，但它不是凭空结论，而是表达本版的前提：v1145 先做均衡语料和 loss signal，不在本版重新判定 decoder 失败路径。真正的 decoder probe 被放到下一步。

`run_loss_signal_bridge_training` 是本版“真实”的核心入口。它调用仓库已有 `scripts/train.py`，而不是自己手写一套训练循环。训练参数被刻意压小：`max_iters=40`，`batch_size=8`，`block_size=16`，`n_layer=1`，`n_head=1`，`n_embd=16`，`dropout=0.0`，设备默认 CPU。这样既能产生 `metrics.jsonl`、`checkpoint.pt`、`tokenizer.json`、`run_manifest.json` 等真实训练产物，又不会把版本验证拖成大训练任务。函数返回 command、returncode、stdout/stderr tail 和 run_dir，最终进入主报告的 `training_command` 字段。这个字段很重要，因为它把“训练真的执行过”与“训练输出在哪里”放进报告，而不是只保留结果摘要。

`build_loss_signal_bridge_decoder_anchor_distribution` 负责汇总。它先读取 training run 的 `metrics.jsonl`，通过 `history.load_records` 解析成 `TrainingRecord`，然后计算 first/last train loss、first/last val loss，以及 delta。loss signal 的 pass 条件是至少两条 metric，并且 `train_loss_delta < 0`。本轮真实运行得到 `first_train_loss=3.307331`、`last_train_loss=2.307431`、`train_loss_delta=-0.999899`，同时 val loss 也从 `3.320089` 降到 `2.825226`。注意，builder 当前把 train loss 下降作为硬门槛，val loss 下降作为摘要证据展示；这样能降低小样本训练偶然波动导致的误判，但仍保留 val loss 给后续判断。

同一个 builder 还会调用旧的 distribution audit，并把 nested audit 输出写到 `decoder-anchor-distribution-audit/`。主报告里保留了完整 `decoder_anchor_distribution` 对象和 `decoder_anchor_distribution_outputs` 路径。这样，读者既可以看 v1145 的总报告，也可以下钻到旧审计的 bucket rows、risk rows、Markdown 和 HTML。主报告摘要只摘出最重要的字段：`decoder_anchor_distribution_ready=True`、`decoder_anchor_example_count=9`、`carry_forward_share=0.3333`、`direct_answer_share=0.3333`、`decoder_bridge_share=0.3333`、`rebalanced_seed_needed=False`。

## CLI 入口

CLI 文件是 `scripts/run_model_capability_loss_signal_bridge_decoder_anchor_distribution_v1145.py`。它默认读取 v1144 归档报告，默认输出到 `output/model-capability-loss-signal-bridge-decoder-anchor-distribution-v1145`。执行流程是固定的：

1. 清理或创建输出目录。
2. 调用 `materialize_loss_signal_bridge_inputs` 写入本版语料和输入 JSON。
3. 如果没有传 `--training-run-dir`，调用 `scripts/train.py` 跑真实训练。
4. 如果传了 `--training-run-dir`，复用已有训练目录，这主要用于测试和调试。
5. 调用 builder 生成主报告。
6. 用 `write_readability_outputs` 写 JSON、CSV、TXT、Markdown、HTML。
7. 在 `--require-pass` 下，主报告失败就返回 1。

这个 CLI 的测试友好性来自 `--training-run-dir`。单测不需要真的跑训练，只要准备一个带 `metrics.jsonl`、`checkpoint.pt`、`tokenizer.json`、`run_manifest.json`、`train_config.json` 的 fixture 目录，就能覆盖 builder、output writer 和 CLI wiring。真实证据则通过不传 `--training-run-dir` 的路径产生，归档在 `f/1145`。这让本版同时满足“单测快”和“版本证据真实”两个目标。

## 检查与字段语义

主报告的 `check_rows` 有十四条检查。前两条检查 v1144 前置：`v1144_holdout_scorecard_passed` 和 `v1144_holdout_scorecard_ready`。接下来检查 seed revision 是否 pass、样本数量是否达到九条、corpus 是否存在。训练部分检查 training subprocess 是否成功、metrics 是否至少两条、train loss 是否下降、checkpoint/tokenizer 是否存在。分布部分检查 nested distribution audit 是否 pass、是否不需要 rebalanced seed、分布输出是否写出。最后一条 `promotion_boundary_kept` 明确保护边界，防止本版被误读成 promotion。

`summary.loss_signal_bridge_decoder_anchor_distribution_ready` 是总 ready 字段，只有所有 check 通过才为 true。`loss_signal_ready` 表示训练 loss 信号是否成立。`decoder_anchor_distribution_ready` 表示旧分布审计是否成功。`rebalanced_seed_needed=False` 是本版的重要结果，因为它说明这份九条语料至少没有触发旧规则中的 direct-answer underweighted、carry-forward dominates、bridge underweighted 等风险。`next_step=run_decoder_anchor_probe_against_v1145_checkpoint` 则把下一版方向收束得很清楚：既然现在有真实 checkpoint 和均衡 seed，下一步应该拿 checkpoint 做 decoder-anchor probe，而不是继续写更多解释性报告。

`rows` 里只有两行：`loss_signal_bridge` 和 `decoder_anchor_distribution`。这不是信息不足，而是刻意保持主表可读。详细训练字段放在 summary 和 `training_signal`；详细分布字段放在 nested `decoder_anchor_distribution`。主表只承担扫描入口，帮助读者快速知道本版两个核心维度是否通过。

## 测试覆盖

新增测试文件是 `tests/test_model_capability_loss_signal_bridge_decoder_anchor_distribution.py`。它覆盖四个场景。

第一个测试构造通过场景：materialize 输入、写一个 train loss 从 `1.2` 降到 `0.7` 的 fixture training run，然后调用 builder。断言包括 status、decision、总 ready、loss signal ready、train loss delta 小于零、`rebalanced_seed_needed=False`、model quality claim、promotion boundary 和 exit code。这个测试保护的是主链路。

第二个测试把 train loss 改成从 `1.0` 升到 `1.1`，报告必须失败，并且 issues 里必须包含 `train_loss_decreased`。这个测试保护 loss signal 的硬门槛，防止未来有人只检查 metrics 文件存在、不检查 loss 方向。

第三个测试把 v1144 前置的 `holdout_scorecard_smoke_ready` 改为 False，报告必须失败，并指出 `v1144_holdout_scorecard_ready`。这个测试保护版本顺序，防止 v1145 被单独拿出来作为无前置的训练证据。

第四个测试覆盖输出和 CLI。它写一个 holdout JSON、复用 fixture training run，通过 CLI 的 `--training-run-dir` 走完整输出路径，并确认主 JSON 与 nested `decoder-anchor-distribution-audit` 目录存在。这个测试保护脚本入口，确保命令行不只是 import 能过，而是真的能写出版本证据结构。

## 运行证据

真实命令如下：

```powershell
python scripts/run_model_capability_loss_signal_bridge_decoder_anchor_distribution_v1145.py --out-dir output/model-capability-loss-signal-bridge-decoder-anchor-distribution-v1145 --require-pass --force
```

真实输出显示 `status=pass`，`failed_check_count=0`。训练记录数为 5，train loss 从 `3.307331` 降到 `2.307431`，val loss 从 `3.320089` 降到 `2.825226`。decoder anchor 分布三类各占三分之一，nested audit 给出 `rebalanced_seed_needed=False`。随后输出被复制到 `f/1145/解释/model-capability-loss-signal-bridge-decoder-anchor-distribution-v1145`，Playwright MCP 通过本地 HTTP server 打开 HTML，并截图保存到 `f/1145/图片/model-capability-loss-signal-bridge-decoder-anchor-distribution-v1145.png`。

## 工程取舍

本版没有把真实训练逻辑塞进单测，也没有把 `scripts/train.py` 的训练循环复制到新模块里。这是为了保持维护边界：训练还是由项目既有训练入口负责，v1145 模块负责组织输入、调用训练、读取 metrics 和生成报告。以后如果训练参数、manifest 或 tokenizer 行为需要统一调整，仍然应该改 `scripts/train.py` 或训练核心依赖，而不是在每个治理版本里维护一份分叉训练实现。

本版也没有继续沿用超长旧命名。旧的 `bounded_objective_loss_signal_bridge_target_only_memory_...` 系列已经证明过一个问题：名字越长，越容易让版本看起来很多，但维护者很难快速判断当前能力到底做了什么。v1145 用 `model_capability_loss_signal_bridge_decoder_anchor_distribution` 这个相对短的名字，把真实主题放在前面：loss signal bridge 和 decoder anchor distribution。它不是一次命名洁癖，而是为了后续 v1146 的 decoder-anchor probe 能有清晰接点。

## 一句话总结

v1145 把模型能力回归路线从真实 generation smoke 推进到真实 bounded training evidence：loss 确实下降，decoder anchor 语料分布通过审计，但项目仍保持 promotion 边界，下一步才适合用本版 checkpoint 做 decoder-anchor probe。
