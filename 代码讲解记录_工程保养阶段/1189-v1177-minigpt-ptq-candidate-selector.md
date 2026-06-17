# v1177 MiniGPT PTQ candidate selector 代码讲解

## 本版目标与边界

v1177 接在两个紧密相关的版本之后：v1175 做了 post-training weight quantization，也就是把已经训练好的 MiniGPT 权重做 fake quantization，再用 held-out completion-token cross entropy、exact-match、logit KL 和 weight relative error 衡量质量损失；v1176 则把 PTQ 和 distillation 共同需要的 completion-mask X/Y 构造逻辑抽成 `completion_masking.build_completion_xy`，避免训练/评估合同分裂。v1177 不再重跑训练，也不再增加新的量化算法，而是把 v1175 的真实测量结果变成一个可复核的“候选选择”。

这个边界很重要。v1175 的结论是质量测量，不是部署承诺：它 fake-quantize 权重后仍然在 fp32 runtime 中前向推理，没有 int kernel，没有实际显存或吞吐收益。v1177 延续这个诚实边界，只回答一个更窄的问题：如果我们接受一组明确质量预算，那么 v1175 的 S1 quality-vs-bits 曲线里，哪一个候选是“在预算内 effective bits 最低”的选择。也就是说，本版做的是 quality-cost selection，而不是 runtime acceleration。

本版明确不做三件事。第一，不声称 `group32:3b` 已经可以生产部署，因为没有真实 int kernel 验证。第二，不用新的训练或新的随机种子覆盖 v1175 的测量，而是直接消费 v1175 已经通过 CI 和 tag 的 JSON artifact。第三，不把候选选择写成口头建议，而是输出 JSON/CSV/text/Markdown/HTML，使后续脚本、人工审阅和截图证据都能读取同一份事实。

## 为什么需要 v1177

v1175 的报告足够严谨，但它仍然偏“测量报告”：15 条 S1 行告诉我们 per-tensor、per-channel-row、group32 在 8/6/4/3/2 bit 下的 `ce_mean`、`dce_mean`、`kl_mean`、`em_mean` 和 effective bits。人可以读这些行，然后说“我觉得 group32 3b 还可以”。但如果没有明确预算，这个判断就会漂移：有人看 CE，会喜欢 group32 3b；有人看 effective bits，会想选 per_channel_row 3b；有人只看 nominal bit，会误以为所有 3b 都差不多。

v1177 的价值是把“我觉得”变成“预算 + 排序 + 拒绝原因”。默认策略是：

```text
dCE <= 0.08
exact-match drop <= 0.10
KL <= 0.10
```

在这组规则下，`per_channel_row:3b` 虽然 effective bits 为 3.1878，比 `group32:3b` 的 3.5 更低，但它的 exact-match drop 是 0.123333，超过 0.10，所以不能选。`group32:3b` 的 dCE 是 0.064286、KL 是 0.07137、EM drop 是 0.090555，三项都在预算内，因此成为最低 effective bits 的候选。这个结果很具体，也很容易复核。

这样做还有一个工程层面的收益：后续如果用户或另一个模型提出“为什么不选 per-channel 3b”“为什么不保守选 per-tensor 4b”，项目不需要重新争论，只要看 v1177 的 rows：候选通过还是失败、失败原因是什么、viable_rank 是多少，都在 artifact 里。

## 新增模块 `ptq_candidate_v1177.py`

核心实现放在 `src/minigpt/ptq_candidate_v1177.py`。这个模块没有依赖 PyTorch，不训练模型，也不触碰 checkpoint。它只读 v1175 JSON，提取 S1 全模型量化行，然后按策略筛选。

模块里最先定义的是两个常量：

```python
PTQ_CANDIDATE_STEM = "ptq_candidate_v1177"
PTQ_SOURCE_DEFAULT_NAME = "ptq_v1175.json"
```

第一个常量控制输出文件名，确保 JSON/CSV/text/Markdown/HTML 的 stem 统一。第二个常量让 CLI 支持两种输入：可以传 `ptq_v1175.json` 文件，也可以传包含该 JSON 的目录。目录输入会通过 `locate_upstream_report(path, "ptq_v1175.json")` 变成具体文件，这和项目里许多 contract check / report loader 的习惯一致。

策略对象是 `PtqCandidatePolicy`：

```python
@dataclass(frozen=True)
class PtqCandidatePolicy:
    max_dce_nats: float = 0.08
    max_exact_match_drop: float = 0.10
    max_kl_nats: float = 0.10
```

这里把阈值写成 dataclass，而不是散落在函数参数里，是为了让输出报告可以原样记录 `policy.as_dict()`。这样 artifact 本身就包含“用什么预算选出来的候选”。如果未来要做更保守或更激进的选择，只需要 CLI 传入不同阈值，输出报告就会保留当时的阈值上下文。

## 输入定位与 JSON 读取

模块暴露两个轻量函数：

```python
def locate_ptq_report(path: str | Path) -> Path:
    return locate_upstream_report(path, PTQ_SOURCE_DEFAULT_NAME)

def read_json_report(path: str | Path) -> dict[str, Any]:
    return read_json_object(path, description="PTQ source report")
```

它们看起来很小，但承担的是入口合同。`locate_ptq_report` 让脚本既能消费目录，也能消费文件；`read_json_report` 统一使用 `report_utils.read_json_object`，支持 `utf-8-sig`，并保证输入必须是 JSON object。这个选择沿用了 v1140 以后 report loader dedup 的方向：公共的 JSON 读取、路径定位和输出写入都尽量集中在 shared helpers，避免每个版本自己手写 `json.loads(Path(...).read_text(...))`。

## 主流程 `build_ptq_candidate_report`

`build_ptq_candidate_report` 是本版的核心函数。它支持传入两类输入：

```python
ptq_report_or_path: dict[str, Any] | str | Path
```

如果调用方传的是路径，函数会定位并读取 v1175 JSON；如果传的是 dict，测试可以直接构造内存 fixture，不必落盘。这个设计让单测更快，也让 CLI 和库函数共享同一套逻辑。

函数首先读取 v1175 summary：

```python
summary = as_dict(ptq_report.get("summary"))
fp32_ce = number_or_default(summary.get("fp32_ce"), 0.0)
fp32_em = number_or_default(summary.get("fp32_exact_match"), 0.0)
source_status = str(ptq_report.get("status", "unknown"))
source_decision = str(ptq_report.get("decision", "unknown"))
source_verdict = str(summary.get("verdict", "unknown"))
```

这里有两个关键点。第一，v1177 不自己发明 baseline，它使用 v1175 的 `fp32_ce` 和 `fp32_exact_match` 作为质量损失的参照。第二，v1177 会检查 source report 的状态。即使某个候选行看起来满足阈值，只要 v1175 source status 不是 `pass`，v1177 就不能给出可用候选，因为上游测量本身没有通过。

随后函数筛出 S1 行：

```python
if row.get("sweep") == "S1" and row.get("component") == "all"
```

只使用 S1 是有意的。v1175 的 S2 是 component sensitivity，S3 是 c_attn axis/scheme robustness，它们回答的是“哪个组件敏感”和“attention claim 是否稳健”；v1177 要做的是全模型部署候选选择，所以只消费 S1 的全模型质量-vs-bits 曲线。这样输入语义清楚，不会把局部组件实验误当成完整模型配置。

每一行会变成 candidate row，字段包括：

```text
candidate_id
granularity
bits
eff_bits
ce_mean
dce_mean
kl_mean
em_mean
em_drop
quality_budget_pass
reject_reasons
viable_rank
```

`candidate_id` 形如 `group32:3b`，方便人读和 CSV 检索。`eff_bits` 保留 v1175 已经计算好的 effective bits，包括 scale metadata 成本，而不是只看 nominal bit。`em_drop` 是 v1177 新计算的字段，等于 `fp32_exact_match - em_mean`，它保护 exact-match 不被 CE 单指标掩盖。对于这个玩具任务，CE 更连续、更适合作为主指标，但 exact-match 仍然是用户能直观看懂的能力表面。如果 CE 预算通过但 exact-match 大幅掉落，候选也不应该轻易通过。

## 拒绝原因如何工作

拒绝逻辑集中在 `_reject_reasons`：

```python
if dce_mean > policy.max_dce_nats:
    reasons.append("dce_above_budget")
if em_drop > policy.max_exact_match_drop:
    reasons.append("exact_match_drop_above_budget")
if kl_mean > policy.max_kl_nats:
    reasons.append("kl_above_budget")
```

这三个原因分别保护三种不同失败模式：

`dce_above_budget` 表示 completion-token cross entropy 损失太大。它是连续指标，能比 exact-match 更早看到模型退化。v1175 已经说明 EM 是阶跃指标，容易错放量化 cliff，所以 v1177 仍然把 dCE 放在第一位。

`exact_match_drop_above_budget` 表示生成结果表面正确率下降太多。`per_channel_row:3b` 就是这种情况的典型例子：它的 dCE 是 0.086742，只比默认 0.08 略高，但更明显的问题是 EM 从 0.883333 掉到 0.760，drop 达 0.123333，超过默认 0.10。这个拒绝原因让“更低 effective bits”的诱惑不能压过可见能力下降。

`kl_above_budget` 表示量化后 logits 分布相对 fp32 偏离太大。KL 不是直接用户指标，但它能捕捉输出分布的形状变化。2b 系列通常 CE 和 KL 一起爆炸，说明不是小幅压缩损失，而是模型行为整体塌掉。

候选通过时，`quality_budget_pass=True`，`reject_reasons` 为空字符串。候选失败时，`reject_reasons` 会把多个原因用逗号连接，便于 CSV 直接查看。

## 排序与最终选择

所有通过预算的候选会按如下顺序排序：

```python
viable.sort(key=lambda row: (row["eff_bits"], row["ce_mean"], row["granularity"], row["bits"]))
```

第一排序键是 effective bits，体现本版目标：在质量预算内尽量压低位宽成本。第二排序键是 CE，处理 effective bits 相同或接近时谁质量更好。后面的 granularity 和 bits 只是稳定排序，避免输出随 Python dict 或输入顺序漂移。

在真实 v1175 artifact 上，默认策略选出：

```text
selected_candidate_id = group32:3b
selected_eff_bits = 3.5
selected_ce_mean = 0.145139
selected_dce_mean = 0.064286
selected_kl_mean = 0.07137
selected_em_mean = 0.792778
selected_em_drop = 0.090555
```

这个结果比 per-tensor 4b 更激进，因为它把 effective bits 从约 4.0 降到 3.5；同时它比 per_channel_row 3b 更保守，因为它没有让 exact-match drop 超出 0.10。也就是说，v1177 不是无脑选最低 bit，而是在质量预算里选最低 effective bits。

## 输出报告结构

`build_ptq_candidate_report` 输出一个普通 dict，结构延续项目 readability reports：

```text
schema_version
title
generated_at
status
decision
summary
rows
selected_candidate
rejected_candidates
recommendations
csv_fieldnames
```

`summary` 是最重要的 machine-readable 概览，包含 `candidate_ready`、source report 状态、policy、fp32 baseline、候选数量、viable 数量、最终候选字段和边界说明。`boundary` 固定写成：

```text
quality_cost_selection_only_no_int_kernel_speed_or_memory_claim
```

这个字段是防误读的。它提醒读者：v1177 只是质量成本候选，不是 runtime deployment proof。`next_step` 也写得很克制：

```text
measure_selected_ptq_candidate_with_real_runtime_or_keep_as_quality_cost_reference
```

意思是，如果将来真的要谈部署收益，需要真实量化 runtime；如果没有 runtime，本报告就保留为 offline quality-cost reference。

`rows` 保存所有 S1 候选行和拒绝原因，`selected_candidate` 保存最终选择的简版字段，`rejected_candidates` 只保留失败候选，方便人工快速看为什么某些低 bit 配置没有入选。

## CLI `select_ptq_candidate_v1177.py`

脚本入口是 `scripts/select_ptq_candidate_v1177.py`，命令示例：

```powershell
python scripts\select_ptq_candidate_v1177.py f\1175\解释\ptq_v1175 --out-dir f\1177\解释\ptq_candidate_v1177 --require-pass --force
```

它支持几个参数：

```text
ptq_report
--out-dir
--max-dce-nats
--max-exact-match-drop
--max-kl-nats
--require-pass
--force
```

`ptq_report` 可以是目录或 JSON 文件。`--force` 用于替换已有输出目录，避免旧 artifact 混入本次结果。`--require-pass` 是 CI 友好的开关：当报告 status 不是 pass 时，返回 1。这里的 fail/review 语义来自报告本身，不靠脚本再写一套判断。

脚本输出使用 `write_readability_outputs`，生成五种格式：

```text
ptq_candidate_v1177.json
ptq_candidate_v1177.csv
ptq_candidate_v1177.txt
ptq_candidate_v1177.md
ptq_candidate_v1177.html
```

这和 v1175 的 artifact 形态一致，也便于 Playwright 截 HTML。

## 测试覆盖

新增测试文件是 `tests/test_ptq_candidate_v1177.py`，一共有 5 个测试。

第一个测试 `test_selects_lowest_effective_bits_inside_quality_budget` 构造一个简化的 v1175 PTQ fixture。它断言默认策略选择 `group32:3b`，同时确认 `per_channel_row:3b` 被拒绝，并且拒绝原因包含 `exact_match_drop_above_budget`。这保护了本版最核心的业务判断：不能因为 effective bits 更低就忽略 EM drop。

第二个测试 `test_tighter_policy_can_reject_all_low_bit_candidates` 把预算调紧到 `dCE<=0.011`、`EM drop<=0.02`、`KL<=0.02`。在这个策略下 3b 系列不再通过，最终选择变成 `per_channel_row:4b`。这个测试说明策略不是写死的，CLI 调阈值会真实改变选择结果。

第三个测试 `test_source_failure_blocks_candidate` 把 source PTQ report 的 status 改成 `review`。即使 rows 里还有可用数据，v1177 也必须输出 `status=fail` 和 `decision=repair_source_ptq_report`。这保护了上游证据链：候选选择不能建立在未通过的测量报告上。

第四个测试 `test_path_directory_input_outputs_and_cli_are_wired` 验证目录输入、输出五件套和 CLI 入口都能工作。它把 `ptq_v1175.json` 写到临时目录，再让 CLI 用目录作为输入，最后断言 exit code 为 0。

第五个测试 `test_cli_require_pass_returns_one_when_no_candidate` 验证 `--require-pass` 的失败路径。source status 被设置为 review，CLI 返回 1。这是给 CI 用的合同。

focused 验证结果：

```powershell
python -m py_compile src\minigpt\ptq_candidate_v1177.py scripts\select_ptq_candidate_v1177.py tests\test_ptq_candidate_v1177.py
python -m pytest tests\test_ptq_candidate_v1177.py -q -o cache_dir=runs\pytest-cache-v1177-focused
```

测试结果是 `5 passed`。

## 运行证据

本版用真实 v1175 artifact 生成证据：

```powershell
python scripts\select_ptq_candidate_v1177.py f\1175\解释\ptq_v1175 --out-dir f\1177\解释\ptq_candidate_v1177 --require-pass --force
```

输出摘要显示：

```text
status=pass
decision=ptq_deployment_candidate_selected
candidate_ready=True
source_status=pass
source_verdict=per_channel_advantage_not_separable
selected_candidate_id=group32:3b
selected_eff_bits=3.5
selected_dce_mean=0.064286
selected_kl_mean=0.07137
selected_em_drop=0.090555
boundary=quality_cost_selection_only_no_int_kernel_speed_or_memory_claim
```

HTML 报告通过 Playwright MCP 打开并截图，截图保存在：

```text
f/1177/图片/ptq-candidate-v1177.png
```

截图不是装饰，它证明本版 HTML artifact 可被浏览器读取，页面里有标题、summary 卡片、候选表和 recommendations。

## 在项目链路里的位置

从 v1161 开始，MiniGPT 有一条 inference-efficiency 线：KV-cache、speculative decoding、PTQ 都在回答“推理成本能不能下降”。这条线的特点是很诚实：KV-cache 看 cache 是否正确，speculative decoding 承认 toy scale wall-clock 更慢，PTQ 承认 fake quantization 只测质量损失。v1177 继续这种风格，把 v1175 的质量损失曲线转换成部署候选，但仍然不越界声称 runtime 收益。

从工程维护角度看，v1177 也接住了 v1176 的成果。v1176 把 completion-mask 合同统一后，PTQ 的 held-out CE 测量更容易和 distillation、SFT 共享理解；v1177 则把 PTQ 的输出变成后续可消费的决策 artifact。一个是输入评估合同的统一，一个是输出决策合同的固化。

如果后续继续推进，合理方向不是继续堆更多口头总结，而是做两件事之一：要么实现真实 int runtime 或更贴近 runtime 的内存核算，再验证 `group32:3b` 是否有实际收益；要么把同样的 candidate-selector 思路推广到 distillation、spec decode 或 SFT 曲线，形成统一的“质量预算内最优候选”选择模式。

## 一句话总结

v1177 把 v1175 的 PTQ 多 seed 测量从“读报告后人工判断”推进为“有预算、有排序、有拒绝原因、有浏览器证据的候选选择器”，让 MiniGPT 的推理成本实验更接近真实工程决策，但仍然守住不声明 runtime 加速的边界。
