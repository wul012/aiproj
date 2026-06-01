# v684 required-term pair surface policy leakage risk

## 本版目标和边界

v684 的目标是给 v682 选出的 `pair_context_prefix` 增加一层 leakage-risk 解释，把它从“稳定生成策略候选”进一步约束成“上下文解码辅助”。这一步解决的是表述风险：v681 已经证明某些 prompt policy 能让三颗 dual-boundary seed 都生成 fixed/loss pair-full，但 v683 也证明非泄漏 single-label baseline 不稳定。如果不把这层边界写清楚，后续很容易把一个带上下文锚点的解码策略误讲成模型本身的无条件能力。

本版明确不做三件事：

- 不训练新 checkpoint。
- 不修改 v681 真实 generation replay 的结果。
- 不把 `pair_context_prefix` promotion 成模型 baseline。

它只做 contract-preserving 的证据层补充：读取 v682 selector 和 v683 minimality check，生成一个机器可读、可截图、可测试的风险报告。

## 前置链路

本版接在 v679-v683 的 surface policy 分支之后：

- v679 定位剩余问题：seed 2535 在 free generation 中漏掉 `loss`，但内部 forced-choice 仍稳定。
- v680 把这个问题转成 surface policy plan，分出 non-leaking baseline、contextual-anchor policy 和被排除的 target-echo upper bound。
- v681 对四个 replay policy 做真实生成，发现 `dual_boundary_sentence` 与 `pair_context_prefix` 都稳定 pair-full。
- v682 用泄漏等级、模板长度和训练边界复用程度选择 `pair_context_prefix`。
- v683 证明 selected policy 仍然依赖 contextual anchor，不能 promotion。

v684 的位置就是把 v683 的判断落成正式风险证据。

## 关键文件

### `src/minigpt/model_capability_required_term_pair_surface_policy_leakage_risk.py`

这是本版核心模块。它提供四类能力：

- `locate_selector_source()` 和 `locate_minimality_source()`：支持输入目录或 JSON 文件，目录输入时自动补齐对应报告文件名。
- `read_json_report()`：读取 UTF-8/UTF-8-BOM JSON，并确保输入是对象。
- `build_surface_policy_leakage_risk()`：合并 selector/minimality 两份报告，生成主 JSON 结构。
- `write_surface_policy_leakage_risk_outputs()`：写出 JSON、CSV、text、Markdown、HTML 五种产物。

核心输出字段：

- `status`：输入报告和 selected policy 是否可用。
- `decision`：本版结论，当前真实运行是 `required_term_pair_surface_policy_contextual_risk_documented`。
- `selected_policy`：完整保留 v682 选出的 policy 行，包含模板、泄漏等级、命中统计和选择理由。
- `risk_rows`：风险明细。当前包含 `contextual_anchor` 与 `minimal_prompt_not_stable`。
- `summary.promotion_allowed`：固定为 `False`，避免后续误晋升。
- `interpretation.model_quality_claim`：当前为 `contextual_decode_policy_only`。

这里的 `risk_rows` 不是安全审计意义上的漏洞清单，而是模型能力声明边界。`contextual_anchor` 表示 prompt 里提供了另一个目标词作为锚点，`minimal_prompt_not_stable` 表示非泄漏 single-label baseline 在 v683 中没有稳定 pair-full。

### `scripts/run_model_capability_required_term_pair_surface_policy_leakage_risk.py`

这是 CLI 入口。它接收两个位置参数：

```text
selector minimality
```

二者都可以是目录，也可以直接是 JSON 文件。脚本会解析输入路径、按需清理输出目录、读取报告、生成风险报告、写出五种产物，并在 `--require-pass` 下根据 `status` 决定退出码。

### `tests/test_model_capability_required_term_pair_surface_policy_leakage_risk.py`

测试覆盖三层边界：

- 正常 selector + minimality 输入会生成 `status=pass`，并记录 `medium` 风险。
- 当 selector 不是 pass 时，报告变成 `fail`，`--require-pass` 语义会返回失败退出码。
- 输出渲染覆盖 JSON/CSV/text/Markdown/HTML，保护五件套证据不被后续改坏。

这些测试没有重新训练模型，但覆盖了本版真正新增的契约：selected policy 风险能被稳定计算和渲染。

## 真实运行证据

正式运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_surface_policy_leakage_risk.py e\682\解释\model-capability-required-term-pair-surface-policy-selector e\683\解释\model-capability-required-term-pair-surface-policy-minimality-check --out-dir e\684\解释\model-capability-required-term-pair-surface-policy-leakage-risk --require-pass --force
```

实际结果：

- `status=pass`
- `decision=required_term_pair_surface_policy_contextual_risk_documented`
- `selected_policy_id=pair_context_prefix`
- `risk_level=medium`
- `promotion_allowed=False`
- `model_quality_claim=contextual_decode_policy_only`
- `next_action=run budget and surface-variant checks without treating the policy as model baseline`

截图归档：

- `e/684/图片/v684-surface-policy-leakage-risk.png`

说明归档：

- `e/684/解释/说明.md`

## 为什么本版有必要

如果只停在 v681，结论会显得很诱人：两个策略都能跨三 seed pair-full。v682 和 v683 已经把策略选择和最小性边界往前推了一步，但还缺一份单独的风险文档，把“prompt 给了另一个 term”这件事变成明确字段。v684 补的就是这层治理口径。

它对后续版本的作用是：

- budget sweep 只能在 `contextual_decode_policy_only` 口径下进行。
- surface variant replay 需要判断策略是否对模板形式过敏。
- closeout 不能把 selected policy 写成 promoted model quality。

## 验证

本版完成后运行：

```powershell
python -m py_compile src\minigpt\model_capability_required_term_pair_surface_policy_leakage_risk.py scripts\run_model_capability_required_term_pair_surface_policy_leakage_risk.py tests\test_model_capability_required_term_pair_surface_policy_leakage_risk.py
python -m pytest tests\test_model_capability_required_term_pair_surface_policy_leakage_risk.py -q -o cache_dir=runs\pytest-cache-v684
```

结果：

- `py_compile` 通过。
- `3 passed in 0.10s`。

## 一句话总结

v684 把 `pair_context_prefix` 从“生成上可行的 policy”约束为“带上下文锚点风险的 decode aid”，让后续评估继续推进但不越过模型能力声明边界。
