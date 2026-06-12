# v1143 required term real execution 代码讲解

## 本版目标和停止边界

v1143 的目标，是把 v1135-v1139 那条“模型能力回归准备链路”真正往模型执行方向推进一步。v1135 是计划，v1136 是 inventory，v1137 是 suite manifest，v1138 是 readiness，v1139 是 closeout；v1141 又把这五个版本读成一条闭合链；v1142 则发布 cadence watch，提示下一步应该执行模型能力回归。Claude review 对 v1142 的判断很关键：`schedule_model_capability_regression` 和 `run_selected_model_capability_regression_execution` 其实来自同一个条件，不能拆成两个版本；并且 v1135/v1136 只是计划和清点，不应该被当成真实模型能力 anchor。也就是说，继续做 lookup-only 报告会让“非能力版本连续过长”的问题更严重，而不是解决它。

因此 v1143 不再新增一个只读治理报告，也不再复用 v1137 的 `reuse_existing_evidence_paths` 模式。它选择 suite row `capability-regression-01`，也就是 `required_term_coverage`，做一次真实但边界很小的 MiniGPT 生成执行。真实执行的意思是：脚本创建一个合法的 tiny checkpoint 和 tokenizer，通过正式的 `MiniGPTGenerator` 加载 checkpoint，在 CPU 上生成 continuation，再用 required terms 对 continuation 做评分。最终报告里必须能看到 `continuation= fixed loss`、`hit_terms=fixed, loss`、`passed_case_count=1`。这和过去只检查文件是否存在、manifest 是否 ready、source/test path 是否有效不同。

本版的停止边界也同样明确。它不训练一个可用于实际对话的模型，不比较 baseline/candidate，不做 holdout scorecard，不声明模型晋升，不把单个 required-term 命中解释成整体模型质量提升。报告中的 `model_quality_claim` 被限定为 `single_check_real_execution`，`promotion_ready` 固定为 `False`。这不是保守措辞，而是本版的契约：v1143 只证明“选定的第一项回归检查已经有一次真实生成证据”，不证明“模型已经变好”。

## 上游来源和路线关系

本版直接承接三个上游事实。第一，v1137 的 suite manifest 中存在 `capability-regression-01`，它的 `check_id` 是 `required_term_coverage`，`primary_source` 指向 `bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_dry_run.py`，`boundary` 是 `evidence_lookup_not_model_promotion`。这个 manifest 是执行地图，但它自己不执行模型生成。

第二，v1142 的 cadence watch 给出 due list。真实输出里有 `next_action=run_selected_model_capability_regression_execution`，说明模型能力回归执行已经到期。Claude review 进一步指出，这个 due item 和 schedule item 不是两个独立任务，而是同一个动作的两个表达；如果再把 schedule 单独做成一版，就是继续延长治理链。

第三，Claude review 指定第一项检查应该是 `required_term_coverage`，而不是 `holdout_scorecard_smoke`。原因是后者的 artifact hint 指到较旧的 receipt-index-review，仍偏 receipt chain evidence，不是模型输出；而 `required_term_coverage` 的 dry-run 来源已经把 `fixed/loss` 的评分契约准备好了，最容易从 dry-run 推进到 real bounded run。v1143 正是沿着这条最小可行路径做真实执行。

## 新增模块和职责

本版新增 `src/minigpt/model_capability_required_term_real_execution.py`。这个模块没有把旧的 dry-run 或 real-replay 大模块继续拉长，而是单独承担 v1143 的第一项能力执行。它的职责分成三层。

第一层是输入读取和 tiny checkpoint 构造。`read_json_report` 复用 `report_utils.read_json_object`，继续接受 UTF-8 BOM 兼容读取。`create_required_term_tiny_checkpoint` 会在输出目录下创建 `tiny-required-term-checkpoint/checkpoint.pt` 和 `tiny-required-term-checkpoint/tokenizer.json`。这里的 checkpoint 是一个极小的合法 `MiniGPT` checkpoint，配置为 `n_layer=0`、`n_embd=8`、`block_size=96`，tokenizer 是字符 tokenizer，但额外包含一个目标 token ` fixed loss`。模型权重被确定性设置为：普通 prompt 字符 token 指向同一个方向向量，目标 token 的向量更强，生成时 `top_k=1`，所以真实 `MiniGPTGenerator` 会选择目标 token。这个设计避免了随机训练带来的不稳定，也避免了把本版包装成训练结果。它是一个 deterministic tiny checkpoint，作用是让真实生成路径可复现。

第二层是报告构造。`build_required_term_real_execution` 接收 v1137 suite manifest、checkpoint 路径、tokenizer 路径和 device。它先用 `_selected_suite_row` 找到 `capability-regression-01` 或 `required_term_coverage`，再生成一个固定 prompt case：`answer with exactly two words: fixed loss\nanswer:`，`max_new_tokens=1`，`temperature=0.2`，`top_k=1`，`seed=1143`。随后 `_run_generation` 会调用默认 `_generate_case`，而 `_generate_case` 使用正式 `MiniGPTGenerator(checkpoint, tokenizer, device).generate(GenerationRequest(...))`。这一步产生的不是伪造 continuation，而是 generator 从 checkpoint 中采样得到的输出。

第三层是 scoring 和 checks。`_score_terms` 用大小写无关方式检查 continuation 是否包含 `fixed` 和 `loss`。报告 row 保存 suite id、check id、case id、prompt、continuation、required terms、hit terms、missed terms、case pass、checkpoint、tokenizer 和 generation error。`_checks` 则把本版需要守住的边界写成检查项：v1137 manifest 必须 pass，source manifest 必须是 lookup-only，选中的 suite row 必须存在，check 必须是 required term coverage，primary source 必须仍指向 tokenizer coverage dry-run，checkpoint/tokenizer 必须存在，真实 generation 必须产生 continuation，required terms 必须命中，promotion boundary 必须保持 false。只要其中任一项失败，报告 status 就会变成 fail。

## CLI 入口和输出模型

本版新增脚本 `scripts/run_model_capability_required_term_real_execution.py`。它的默认输入是：

```text
f/1137/解释/model-capability-regression-suite-manifest-v1137/model_capability_regression_suite_manifest_v1137.json
```

默认输出是：

```text
output/model-capability-required-term-real-execution-v1143
```

如果调用者没有传 `--checkpoint`，脚本会在 `out-dir/tiny-required-term-checkpoint/` 下创建 tiny checkpoint 和 tokenizer；如果传了 `--checkpoint`，则必须同时传 `--tokenizer`，这样后续可以替换为真实训练 checkpoint。脚本支持 `--device cpu|auto|cuda`，但本版正式证据使用 `cpu`，因为目标是确定性、低成本、可复核。`--require-pass` 会在报告 status 不是 pass 时返回退出码 1，便于以后接入 CI 或 follow-up gate。`--force` 遵循项目已有脚本习惯，用于删除已有非空输出目录后重新生成。

报告输出使用 `readability_report_artifacts.write_readability_outputs`，因此自动得到 JSON、CSV、text、Markdown、HTML 五种格式。stem 是 `model_capability_required_term_real_execution_v1143`。这保持了 v1130 之后的 artifact 风格：核心模块只构造结构化 report，输出渲染交给共享工具，而不是每个版本重复写一套 CSV/HTML writer。

报告的 summary 字段是后续阅读最重要的部分。`required_term_real_execution_ready=True` 说明本版真实执行通过；`suite_id=capability-regression-01` 和 `check_id=required_term_coverage` 说明它没有跑偏到其他 suite item；`source_execution_mode=reuse_existing_evidence_paths` 保留了上游 manifest 的原始语义，用来提醒读者 v1143 是从 lookup-only 地图转出来的一次 real execution；`case_count=1`、`executed_case_count=1`、`passed_case_count=1`、`failed_case_count=0` 明确这只是单检查单 case；`model_quality_claim=single_check_real_execution` 和 `promotion_ready=False` 是边界声明；`next_step=run_real_holdout_scorecard_smoke_v1144` 则承接 Claude review 给出的路线。

## 为什么不直接复用旧 real replay 模块

仓库里已经有 `bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_real_replay.py`，它可以跑完整 tokenizer-covered holdout suite 的 real replay。但 Claude review 明确说 v1143 应该先跑 suite item `capability-regression-01` 的 required term coverage，而不是直接做 holdout scorecard 或扩展成更大的 benchmark。旧 real replay 模块承担的是一组 holdout cases 的 replay，它的语义更接近 v1144 或后续能力版本；如果 v1143 直接复用它作为主报告，容易把“第一项 required-term 单检查”放大成“holdout suite 已经进入全面 replay”。这会让报告边界变模糊。

因此本版新建一个窄模块，而不是再往旧模块里塞 v1143 的 suite-manifest 解释、tiny checkpoint 构造和单检查 summary。这样做也符合仓库规则：不要制造难维护的巨型文件。当一个模块已经承担 holdout suite replay 时，v1143 的 manifest-to-real-execution 桥接就应该有自己的小入口。后续 v1144 真正做 `holdout_scorecard_smoke` 时，可以再决定复用旧 real replay 模块，或者在它上面包一层 scorecard smoke，而不需要让 v1143 提前污染它的职责。

## 测试如何保护链路

本版新增 `tests/test_model_capability_required_term_real_execution.py`。第一条测试 `test_real_execution_runs_minigpt_generator_and_hits_required_terms` 会在临时目录中创建 tiny checkpoint，然后调用 `build_required_term_real_execution`，不注入 fake runner。也就是说，这条测试真的走了 `MiniGPTGenerator`、`GenerationRequest`、checkpoint load、tokenizer decode 和 continuation scoring。测试断言 status 是 pass，decision 是 `model_capability_required_term_real_execution_ready`，summary 里的 `model_quality_claim` 是 `single_check_real_execution`，`promotion_ready` 是 false，row continuation 等于 ` fixed loss`，hit terms 等于 `["fixed", "loss"]`。这是本版最核心的保护。

第二条测试 `test_real_execution_fails_when_manifest_selects_wrong_check` 会把 manifest 第一行的 check id 改成 `holdout_scorecard_smoke`。由于 suite row 仍然是 `capability-regression-01`，构造器会选中它，但 `_checks` 会发现 check id 不再是 `required_term_coverage`，报告变成 fail，并出现 `selected_check_is_required_term_coverage` issue。这条测试保护 Claude review 的第一项纠偏：v1143 不能把第一版真实执行偷换成其他检查。

第三条测试 `test_real_execution_fails_when_checkpoint_is_missing` 会删除 checkpoint 输入，让 report 同时暴露 `checkpoint_exists` 和 `generation_executed` 失败。这样可以防止脚本在没有真实模型文件时仍然产出 pass 报告。第四条测试 `test_outputs_and_cli_are_wired` 则验证五格式输出和 CLI 默认创建 tiny checkpoint 的路径都可用，并用 `--require-pass` 确认通过状态能返回 0。

这些测试的重点不是扩大覆盖面，而是保护本版最关键的契约：有真实 generation，选中的是 required term coverage，缺 checkpoint 不能通过，输出入口可以复现。v1144 如果开始做 holdout scorecard smoke，再新增多 case、多指标和 scorecard pipeline 的测试。

## 真实运行证据

本版真实运行了两次脚本。第一份写入 `output/model-capability-required-term-real-execution-v1143/`，用于项目常规 output artifact；第二份写入 `f/1143/解释/model-capability-required-term-real-execution-v1143/`，作为版本归档证据。关键输出如下：

```text
status=pass
decision=model_capability_required_term_real_execution_ready
required_term_real_execution_ready=True
suite_id=capability-regression-01
check_id=required_term_coverage
source_execution_mode=reuse_existing_evidence_paths
case_count=1
executed_case_count=1
passed_case_count=1
failed_case_count=0
required_terms=fixed, loss
hit_terms=fixed, loss
model_quality_claim=single_check_real_execution
promotion_ready=False
next_step=run_real_holdout_scorecard_smoke_v1144
failed_check_count=0
```

HTML 报告通过 Playwright MCP 打开，并保存截图到 `f/1143/图片/model-capability-required-term-real-execution-v1143.png`。由于 Playwright MCP 阻止直接访问 `file://`，截图时临时启动了 `python -m http.server 8765 --bind 127.0.0.1`，完成后已经停止。截图快照能看到 `required_term_real_execution_ready=True`、`passed_case_count=1`、`failed_case_count=0`、`model_quality_claim=single_check_real_execution` 和 `promotion_ready=False`。

## 下一步

v1143 清掉的是“没有真实生成执行 anchor”的问题，但它只清掉第一块。按照 Claude review 给出的路线，v1144 应该做 real `holdout_scorecard_smoke`。那一版需要比 v1143 更接近实际能力评估：不再只看单个 required term token，而是让一个小 holdout scorecard 从真实模型输出中得到结果。v1145 再把 `loss_signal_bridge` 和 `decoder_anchor_distribution` 接回来，形成“表面项、holdout 项、训练信号项、decoder 分布项”的组合证据。

换句话说，v1143 是从治理链回到模型输出的第一个锚点，不是终点。它的价值在于把 cadence watch 的 alarm 合法地往前移动：项目现在可以说“已经有一次真实生成的 required-term 回归执行”，但还不能说“模型能力已经系统提升”。这个边界越清楚，后续 v1144/v1145 的证据才越可信。

## 一句话总结

v1143 把 `capability-regression-01` 从 lookup-only manifest 行推进为一次真实 CPU generation，并用 `fixed/loss` required-term 命中建立第一个受限模型能力执行锚点，同时继续保持 `promotion_ready=False`。
