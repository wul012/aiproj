# v1178 MiniGPT PTQ policy sensitivity 代码讲解

## 本版目标与边界

v1178 接在 v1177 之后。v1177 已经把 v1175 的 post-training quantization 多 seed 测量结果转换成一个可复核的 deployment candidate selector：给定一组质量预算，选择预算内 effective bits 最低的候选。默认预算下，v1177 选出了 `group32:3b`，并拒绝了更低 effective bits 的 `per_channel_row:3b`，因为后者 exact-match drop 超过默认 `0.10`。

v1178 要补的是 v1177 留下的一个工程问题：这个候选是否稳定？如果质量预算稍微严格一点或宽松一点，选择是否还会是 `group32:3b`？如果答案是否定的，那么项目在讲解 v1177 时就不能说“group32:3b 是唯一正确候选”，而要说“在 balanced/default 质量预算下它是当前候选”。这一区别看起来细，但对于工程判断很关键：候选选择不是客观真理，而是质量容忍度、压缩收益和风险边界共同决定的结果。

因此 v1178 新增 `ptq_policy_sensitivity_v1178.py` 和 `run_ptq_policy_sensitivity_v1178.py`，用三档 policy profile 复用 v1177 selector：

```text
strict_quality
balanced_default
aggressive_compression
```

这不是新治理链，也不是再造一套 PTQ 逻辑。它只是在 v1177 已经实现的候选选择器外面套一层 profile sweep，观察不同质量预算下选择如何变化。本版仍然只消费 v1175 的真实 PTQ JSON，不重跑训练，不声称 int kernel 加速，不制造新的模型质量结论。

## 为什么要做 policy sensitivity

在 v1177 里，默认预算是：

```text
dCE <= 0.08
exact-match drop <= 0.10
KL <= 0.10
```

这组预算下 `group32:3b` 通过，而 `per_channel_row:3b` 失败。这个结论本身很有用，但也有一个潜在风险：如果默认阈值是人为选出来的，那么别人可以问“你是不是为了选 group32:3b 才设了这些阈值”。v1178 用 profile sweep 来回应这个问题。它不假装阈值没有主观性，而是把阈值主观性显式化：严格预算、默认预算、激进预算分别会选什么。

真实 v1175 artifact 上，三档结果是：

```text
strict_quality          -> per_tensor:4b
balanced_default        -> group32:3b
aggressive_compression  -> per_channel_row:3b
```

这个结果恰恰说明候选选择是预算敏感的。严格质量下不能接受 3b 带来的可见准确率风险，所以回到 `per_tensor:4b`。默认预算下，`group32:3b` 在 dCE、KL 和 EM drop 三项都不过界，因此成为折中候选。激进预算下，项目允许更大的 exact-match loss，才会放行 `per_channel_row:3b`。

这样比单独给出一个候选更透明。它告诉使用者：如果你更在意可见输出准确率，就用 strict；如果你愿意以更大 accuracy loss 换 compression，就用 aggressive；如果没有明确产品容忍度，就采用 balanced_default，不把更大损失伪装成免费收益。

## 新增数据结构 `PtqPolicyProfile`

核心模块是 `src/minigpt/ptq_policy_sensitivity_v1178.py`。它先定义：

```python
@dataclass(frozen=True)
class PtqPolicyProfile:
    profile_id: str
    label: str
    policy: PtqCandidatePolicy
```

这里没有重新定义阈值字段，而是直接复用 v1177 的 `PtqCandidatePolicy`。这是本版最重要的维护决策：v1178 不应该复制 `max_dce_nats`、`max_exact_match_drop`、`max_kl_nats` 的含义，也不应该重新写候选通过/失败规则。它只把若干个 `PtqCandidatePolicy` 命名为 profile，然后交给 v1177 的 `build_ptq_candidate_report` 去计算。

`profile_id` 是机器可读标识，例如 `strict_quality`。`label` 是人可读说明，用来解释这个 profile 的使用场景。`policy` 是真正的阈值对象。`as_row()` 会把三者合并成输出表里的基础字段：

```python
{
    "profile_id": ...,
    "label": ...,
    "max_dce_nats": ...,
    "max_exact_match_drop": ...,
    "max_kl_nats": ...,
}
```

这样 CSV/Markdown/HTML 里每一行都能看到该 profile 的阈值，而不是只看到 profile 名字。

## 默认三档 profile

`DEFAULT_POLICY_PROFILES` 是本版的默认分析集合。

第一档是 `strict_quality`：

```python
PtqCandidatePolicy(max_dce_nats=0.02, max_exact_match_drop=0.04, max_kl_nats=0.04)
```

它偏保守。dCE 只能增加 0.02，EM drop 不能超过 0.04，KL 不能超过 0.04。在真实 v1175 曲线上，这会选 `per_tensor:4b`。原因是 3b 系列的损失都太高，而 `per_tensor:4b` 的 effective bits 虽然不是最低，但质量损失足够小。

第二档是 `balanced_default`：

```python
PtqCandidatePolicy(max_dce_nats=0.08, max_exact_match_drop=0.10, max_kl_nats=0.10)
```

它就是 v1177 默认预算。真实 artifact 上选择 `group32:3b`。这是项目默认建议，因为它在质量损失不越界的前提下，把 effective bits 降到了 3.5。

第三档是 `aggressive_compression`：

```python
PtqCandidatePolicy(max_dce_nats=0.10, max_exact_match_drop=0.14, max_kl_nats=0.11)
```

它允许更大可见准确率下降，因此会放行 `per_channel_row:3b`。这个 profile 不是默认推荐，而是用来表明：如果外部产品场景明确接受更大 EM drop，那么更激进的 candidate 是存在的。但如果没有这种明确容忍度，不能把 aggressive 结果作为默认。

## 主流程 `build_ptq_policy_sensitivity_report`

主函数支持两类输入：

```python
ptq_report_or_path: dict[str, Any] | str | Path
```

和 v1177 一样，路径输入可以是 JSON 文件，也可以是目录。目录会通过 v1177 的 `locate_ptq_report` 定位到 `ptq_v1175.json`。如果传入 dict，测试可以直接用内存 fixture。

函数读取 source PTQ report 后，核心逻辑是：

```python
profile_reports = [
    build_ptq_candidate_report(ptq_report, policy=profile.policy, ...)
    for profile in profiles
]
rows = [_profile_row(profile, report) for profile, report in zip(profiles, profile_reports)]
```

也就是说，每个 profile 都跑一次 v1177 candidate selector。本版没有自己的候选排序逻辑，没有自己的拒绝原因逻辑，也没有重新解释 S1 行。这一点保护了 v1177 和 v1178 的一致性：如果将来 v1177 的候选选择规则修正了，v1178 会自然继承，而不是出现两套“类似但不完全一致”的判断。

`_profile_row` 把每个 profile 的结果压成一行：

```text
profile_id
status
decision
selected_candidate_id
selected_eff_bits
selected_dce_mean
selected_kl_mean
selected_em_drop
viable_candidate_count
max_dce_nats
max_exact_match_drop
max_kl_nats
```

这些字段足够回答两个问题：第一，这个 profile 是否能选出候选；第二，它选出的候选质量损失和 effective bits 是什么。

## 稳定性判断

v1178 的 summary 会计算：

```python
selected_ids = [row["selected_candidate_id"] for row in rows if row["selected_candidate_id"]]
unique_selected = sorted(set(selected_ids))
stable = len(unique_selected) <= 1 and bool(unique_selected)
```

如果三档 profile 都选同一个 candidate，那么 `selection_stable_across_profiles=True`，说明候选对当前测试预算不敏感。真实结果不是这样。真实结果中 `unique_selected_candidate_count=3`，所以：

```text
selection_stable_across_profiles=False
sensitivity_verdict=candidate_choice_changes_with_quality_budget
```

这个 verdict 比“group32:3b 最好”更诚实。它说明：`group32:3b` 是 balanced/default 预算下的最佳折中，但 strict 会更保守，aggressive 会更激进。项目不能把默认预算的结论扩大成跨预算不变的结论。

## 输出报告结构

报告输出仍然走 readability artifact 体系：

```text
schema_version
title
generated_at
status
decision
summary
rows
profile_reports
recommendations
csv_fieldnames
```

其中 `rows` 是主要消费对象，适合 CSV、Markdown 和 HTML 展示。`profile_reports` 保存每个 profile 调用 v1177 后的完整子报告，便于后续排查某个 profile 为什么选中或没选中某个候选。`summary` 则保存整体结论，例如：

```text
policy_sensitivity_ready=True
source_status=pass
source_verdict=per_channel_advantage_not_separable
profile_count=3
passing_profile_count=3
unique_selected_candidate_count=3
selection_stable_across_profiles=False
default_profile_candidate=group32:3b
default_profile_eff_bits=3.5
default_profile_dce_mean=0.064286
default_profile_em_drop=0.090555
boundary=policy_sensitivity_only_reuses_v1175_quality_cost_evidence
```

`boundary` 再次强调本版只复用 v1175 质量成本证据。它不是 runtime benchmark，也不是生产部署许可。

## CLI 入口

脚本是 `scripts/run_ptq_policy_sensitivity_v1178.py`。运行示例：

```powershell
python scripts\run_ptq_policy_sensitivity_v1178.py f\1175\解释\ptq_v1175 --out-dir f\1178\解释\ptq_policy_sensitivity_v1178 --require-pass --force
```

参数保持简单：

```text
ptq_report
--out-dir
--require-pass
--force
```

这里没有暴露自定义 profile 的 CLI 参数，是有意克制。v1178 的目标是给项目建立一个固定、可比较、可截图的三档分析；如果把每档阈值都放到命令行里，后续 artifact 之间会很难比较。真正需要自定义 profile 时，可以在 Python 调用 `build_ptq_policy_sensitivity_report(..., profiles=...)`，而不是让版本级证据失去固定含义。

脚本输出五件套：

```text
ptq_policy_sensitivity_v1178.json
ptq_policy_sensitivity_v1178.csv
ptq_policy_sensitivity_v1178.txt
ptq_policy_sensitivity_v1178.md
ptq_policy_sensitivity_v1178.html
```

HTML 又通过 Playwright MCP 截图，保存到：

```text
f/1178/图片/ptq-policy-sensitivity-v1178.png
```

## 测试覆盖

新增测试文件是 `tests/test_ptq_policy_sensitivity_v1178.py`。

第一个测试 `test_profiles_show_candidate_choice_is_budget_sensitive` 使用简化版 v1175 PTQ fixture，断言三档 profile 的选择分别是：

```text
strict_quality -> per_tensor:4b
balanced_default -> group32:3b
aggressive_compression -> per_channel_row:3b
```

同时断言 `selection_stable_across_profiles=False` 和 `unique_selected_candidate_count=3`。这个测试保护本版核心结论：候选选择是预算敏感的。

第二个测试 `test_source_failure_blocks_all_profiles` 把 source status 改成 `review`。因为每个 profile 都复用 v1177 selector，而 v1177 会拒绝未通过的 source report，所以 v1178 整体 status 也必须是 `fail`。这保护了上游证据链。

第三个测试 `test_outputs_and_cli_are_wired` 验证目录输入、输出五件套和 CLI 入口。它把 fixture 写成临时 `ptq_v1175.json`，让 CLI 用目录输入生成报告，再断言 exit code 为 0。

focused 验证：

```powershell
python -m py_compile src\minigpt\ptq_policy_sensitivity_v1178.py scripts\run_ptq_policy_sensitivity_v1178.py tests\test_ptq_policy_sensitivity_v1178.py
python -m pytest tests\test_ptq_policy_sensitivity_v1178.py tests\test_ptq_candidate_v1177.py -q -o cache_dir=runs\pytest-cache-v1178-focused
```

结果是 `8 passed`。

## 和 v1177 的关系

v1177 是单次选择：给一个 policy，输出一个 candidate。v1178 是敏感性分析：给一组 profiles，多次调用 v1177，然后比较结果是否稳定。

这个层次划分比较干净。v1177 负责“候选通过/失败、拒绝原因、排序、selected_candidate”。v1178 负责“不同 policy 选出来是否相同、默认 profile 是否只是折中、strict/aggressive 的取舍是什么”。如果把这两层写在同一个模块里，`ptq_candidate_v1177.py` 会开始承担 profile 管理、稳定性统计、推荐语生成，职责会变宽。现在拆成两个 200 行以内的模块，后续维护更清楚。

## 一句话总结

v1178 证明 PTQ candidate selection 不是跨预算不变的唯一答案，而是随质量容忍度变化；项目默认保留 `balanced_default -> group32:3b`，同时把 strict 与 aggressive 的选择差异显式暴露出来，避免把阈值敏感的工程取舍包装成绝对结论。
