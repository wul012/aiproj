# v1144 holdout scorecard smoke 代码讲解

## 本版目标和停止边界

v1144 的目标，是在 v1143 已经完成 `capability-regression-01 / required_term_coverage` 的真实生成执行之后，把 Claude review 路线里的第二项 `holdout_scorecard_smoke` 落到真实模型输出上。v1143 只有一个 prompt、一个 continuation、一个 required-term scoring；它足以证明项目从 lookup-only 治理链回到了真实 `MiniGPTGenerator`，但还不能证明 scorecard 管线能消费真实生成结果。v1144 就补这个缺口：运行 5 个小型 holdout smoke case，收集真实 continuation，把它们整理成 `benchmark_scorecard.py` 已经支持的 run_dir 结构，再由现有 scorecard builder 计算 nested benchmark scorecard。

本版不做完整 benchmark，不比较 baseline/candidate，不训练模型，不声明模型晋升，也不把 scorecard smoke 解释成生产质量。输出里的 `model_quality_claim` 是 `holdout_scorecard_smoke_real_execution`，`promotion_ready=False`。报告里还明确写出 `pair_same_checkpoint_baseline=True`，意思是 pair 部分只是同 checkpoint baseline，用来证明 scorecard 输入和 pair 指标链路可复现，不证明候选模型比 baseline 更好。这个边界很重要，因为 v1137 的 `holdout_scorecard_smoke` 行带着一个较旧 artifact hint，如果本版只是读取那个 hint，等于继续做 receipt/index 类治理证据；v1144 必须把真实生成放到 scorecard 前面。

## 上游来源

v1144 有两个输入。第一个是 v1137 suite manifest：

```text
f/1137/解释/model-capability-regression-suite-manifest-v1137/model_capability_regression_suite_manifest_v1137.json
```

本版从中选择 `suite_id=capability-regression-04`、`check_id=holdout_scorecard_smoke` 的行。这个行的 `primary_source` 是 `benchmark_scorecard.py`，`primary_test` 是 `test_benchmark_scorecard.py`，`boundary` 仍然是 `evidence_lookup_not_model_promotion`。它说明 scorecard smoke 在准备链路中被列为可执行项，但它自己不是执行结果。

第二个输入是 v1143 real required-term execution：

```text
f/1143/解释/model-capability-required-term-real-execution-v1143/model_capability_required_term_real_execution_v1143.json
```

v1144 会检查其中 `summary.required_term_real_execution_ready=True`。这不是为了把 v1143 当作模型质量证明，而是为了保证路线顺序正确：先证明单项 required-term real execution，再推进到 holdout scorecard smoke。如果 v1143 前置不 ready，v1144 报告会 fail，避免跳过第一块能力证据。

## 新增模块结构

本版新增 `src/minigpt/model_capability_holdout_scorecard_smoke.py`。模块保持 400 行以内，没有去改 `benchmark_scorecard.py`，也没有复制它的评分逻辑。它的核心职责是桥接：把真实生成 case 转成 scorecard 所需的 `eval_suite`、`generation_quality` 和 `pair_batch` 三组文件，然后调用既有 `build_benchmark_scorecard`。

`create_holdout_scorecard_tiny_checkpoint` 复用 v1143 的 `create_required_term_tiny_checkpoint`。不同点在于 v1143 的 prompt corpus 只有一个 prompt，而 v1144 会把 5 个 holdout prompt 拼成 corpus，确保 tokenizer 覆盖所有 prompt 字符。生成目标仍是 ` fixed loss` 这个 token。这样做的目的不是制造一个“更强模型”，而是让每个 smoke case 都通过真实生成器走一遍确定性 continuation，消除随机训练带来的不稳定。

`_holdout_cases` 定义 5 个小 case，覆盖 `qa`、`summary`、`continuation` 三类 task type，以及 `easy`、`medium`、`hard` 三类 difficulty。每个 case 都带 prompt、seed、max_new_tokens、temperature、top_k 和 required terms。它们不是正式评测集，而是 scorecard smoke 集：数量足够让 `benchmark_scorecard` 的 coverage component 不再因为 case 太少而降分，同时规模又足够小，适合 CI 和本地快速复核。

`_run_cases` 会逐个调用 `_generate_case`。`_generate_case` 使用正式 `MiniGPTGenerator(checkpoint, tokenizer, device).generate(GenerationRequest(...))`，所以 rows 中的 `generated`、`continuation`、`seed`、`temperature` 都来自真实生成响应。随后 `_score_terms` 检查 continuation 是否包含 `fixed` 和 `loss`。本版真实输出里 5 个 continuation 都是 ` fixed loss`，因此 `passed_case_count=5`。

## 如何接入 benchmark scorecard

`_write_scorecard_inputs` 是本版最关键的桥。它把真实 generation rows 写成三组输入。

第一组是 `real-holdout-scorecard-run/eval_suite/eval_suite.json`。这里每个 result 包含 name、task_type、difficulty、prompt、generated、continuation、expected_behavior、tags、rubric、char_count 和 unique_char_count。rubric 明确要求 `must_include=["fixed", "loss"]`，并限制 continuation 长度。这样 `benchmark_scorecard_scoring.rubric_case_score` 能用既有逻辑计算 must_include、length bounds、task shape 等检查。

第二组是 `real-holdout-scorecard-run/generation_quality/generation_quality.json`。v1144 的 smoke continuation 都命中 required terms，所以 generation quality summary 写成 `overall_status=pass`、`case_count=5`、`pass_count=5`、`fail_count=0`、`total_flags=0`。这不是通用生成质量评估，只是把 smoke case 的基本质量状态提供给 scorecard component。

第三组是 `real-holdout-scorecard-run/pair_batch/pair_generation_batch.json`。它把 left/right 都设置成同一个 checkpoint，结果里 `same_checkpoint=True`、`generated_equal=True`、delta 为 0。这样 `benchmark_scorecard.py` 会识别 `pair_same_checkpoint_baseline=True`，并把 pair component 分数 capped 到 90。这个设计刻意保守：pair 指标参与 scorecard smoke，但报告不声称跨 checkpoint 提升。

写完三组输入后，模块调用 `build_benchmark_scorecard(run_dir)`，再调用 `write_benchmark_scorecard_outputs(scorecard, run_dir / "scorecard")`。因此 v1144 的证据里既有 wrapper report，也有 nested `benchmark_scorecard.json/csv/md/html`。这让后续 v1145 或更高版本可以直接读取真实 scorecard 结果，而不必重新推导。

## 输出模型和检查项

v1144 wrapper report 的 summary 包含 `holdout_scorecard_smoke_ready`、case count、scorecard overall status、overall score、rubric average、generation quality status、pair baseline 标记、model quality claim、promotion boundary 和 next step。真实运行结果是：

```text
holdout_scorecard_smoke_ready=True
case_count=5
executed_case_count=5
passed_case_count=5
scorecard_overall_status=pass
scorecard_overall_score=97.0
rubric_avg_score=100.0
generation_quality_status=pass
pair_same_checkpoint_baseline=True
model_quality_claim=holdout_scorecard_smoke_real_execution
promotion_ready=False
next_step=run_loss_signal_bridge_and_decoder_anchor_distribution_v1145
```

`_checks` 保护本版边界。它检查 v1137 manifest 是否 pass，是否选中 `capability-regression-04`，check id 是否为 `holdout_scorecard_smoke`，v1137 的 artifact hint 是否只作为上下文，v1143 前置是否 ready，checkpoint/tokenizer 是否存在，是否执行了 5 个 case，是否没有 generation error，是否 5 个 case 都命中 required terms，nested scorecard 是否 overall pass，scorecard outputs 是否全部写出，promotion boundary 是否保持 false。这里的 `artifact_hint_not_used_as_result` 很重要：它明确回应 Claude review 对 stale v1100 receipt-index-review 的提醒。本版报告里保留 artifact hint，但不会把它当作模型输出证据。

## CLI 和真实运行

新增脚本 `scripts/run_model_capability_holdout_scorecard_smoke_v1144.py`。默认读取 v1137 manifest 和 v1143 real execution，默认输出到：

```text
output/model-capability-holdout-scorecard-smoke-v1144
```

如果不传 `--checkpoint`，脚本会创建 `tiny-holdout-scorecard-checkpoint/checkpoint.pt` 和 `tokenizer.json`。如果传入外部 checkpoint，则必须传 `--tokenizer`。这保留了向真实训练 checkpoint 迁移的入口。`--require-pass` 用于让失败报告返回 1，方便 CI 或下一阶段 gate 使用。正式归档运行把输出写入：

```text
f/1144/解释/model-capability-holdout-scorecard-smoke-v1144
```

HTML 通过 Playwright MCP 截图，保存到：

```text
f/1144/图片/model-capability-holdout-scorecard-smoke-v1144.png
```

截图中可以看到 `case_count=5`、`passed_case_count=5`、`scorecard_overall_score=97.0`、`model_quality_claim=holdout_scorecard_smoke_real_execution`、`promotion_ready=False`。

## 测试覆盖

新增 `tests/test_model_capability_holdout_scorecard_smoke.py`。第一条测试真实创建 tiny checkpoint，并调用默认 generator path，不注入 fake runner。它断言 report pass、case_count 为 5、passed_case_count 为 5、nested scorecard overall_status 为 pass、model_quality_claim 正确、promotion_ready 为 false，并确认所有 continuation 都是 ` fixed loss`。这条测试保护 v1144 的真实执行属性。

第二条测试把 manifest 的 check id 改成 `required_term_coverage`，断言报告 fail，并出现 `selected_check_is_holdout_scorecard_smoke`。这防止 v1144 跑回 v1143 的第一项检查。第三条测试把 v1143 prerequisite 改成 not ready，断言 `required_term_real_execution_ready` issue 出现，保护版本顺序。第四条测试覆盖 wrapper 五格式输出、CLI `--require-pass` 和 nested `benchmark_scorecard.json` 是否真实落盘。

这些测试比 v1143 更重一点，因为它们不仅验证生成，还验证 scorecard 输入和 nested scorecard 输出。它仍然是 smoke，而不是全量 benchmark；但它已经能说明项目具备“真实生成 -> 评估输入 -> scorecard 汇总 -> 证据归档”的闭环。

## 下一步

v1144 之后，Claude review 给出的路线还剩 v1145：`loss_signal_bridge + decoder_anchor_distribution`。现在已经有 required-term 单检查和 holdout scorecard smoke 两个真实执行锚点，下一步应该把训练信号和 decoder 分布也接入真实证据，而不是继续扩展 receipt 或 manifest。v1145 应该继续保持边界：可以说“真实 loss/decoder 证据已接入”，但除非出现更强 baseline/candidate 比较，否则仍不应设置 `promotion_ready=True`。

## 一句话总结

v1144 把 5 个真实 MiniGPT generation case 接入既有 benchmark scorecard，形成第一个 real holdout scorecard smoke，同时明确这只是同 checkpoint smoke baseline，不是模型晋升证明。
