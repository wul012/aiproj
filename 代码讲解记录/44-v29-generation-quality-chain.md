# 第二十九版讲解：generation quality evidence chain

本版目标是把 v28 生成的 `generation_quality.json` 接入 MiniGPT 的正式证据链。

v28 已经能从 `eval_suite.json` 或 `sample_lab.json` 里分析生成样本，判断是否存在空输出、过短输出、低多样性、重复字符、重复 n-gram 和 prompt echo。v29 不再新增新的生成算法，也不重新训练模型，不修改 Transformer，不改变 eval suite 的生成逻辑。它只做一件事：让生成质量报告被 registry、model card 和 project audit 消费，让“生成质量是否通过”可以进入 release-style review。

本版来自上一版路线：

```text
v28 generation_quality.json
 -> v29 registry consumes generation quality
 -> model_card summarizes generation quality coverage
 -> project_audit checks generation quality readiness
 -> later release bundle / release gate can inherit audit result
```

## 关键文件

本版主要修改：

```text
src/minigpt/registry.py
src/minigpt/model_card.py
src/minigpt/project_audit.py
scripts/register_runs.py
tests/test_registry.py
tests/test_model_card.py
tests/test_project_audit.py
README.md
代码讲解记录/README.md
a/29/解释/说明.md
```

没有新增单独的核心模块。原因是 v28 已经有 `generation_quality.py`，v29 的重点是把它的输出接入现有证据链，而不是再做一个新的分析器。

## registry 读取规则

`registry.py` 现在会在每个 run 目录下寻找两种 generation quality 路径：

```text
generation-quality/generation_quality.json
eval_suite/generation-quality/generation_quality.json
```

第一个路径是推荐的 run 级产物位置，第二个路径兼容 v28 默认输出，也就是从 `eval_suite/eval_suite.json` 旁边直接生成的情况。

读取函数是：

```python
def _read_generation_quality(root: Path) -> dict[str, Any]:
```

它会返回完整 JSON 对象，并额外写入：

```text
generation_quality_path
```

这个字段不是模型指标，而是证据来源路径，方便后续定位报告来自哪里。

## RegisteredRun 新字段

`RegisteredRun` 新增这些字段：

```text
generation_quality_status
generation_quality_cases
generation_quality_pass_count
generation_quality_warn_count
generation_quality_fail_count
generation_quality_avg_unique_ratio
```

它们来自 `generation_quality.json` 的：

```text
summary.overall_status
summary.case_count
summary.pass_count
summary.warn_count
summary.fail_count
summary.avg_unique_ratio
```

字段语义是：

```text
overall_status=pass   这一批生成样本没有触发 warn/fail
overall_status=warn   有低多样性、重复、prompt echo 等风险
overall_status=fail   有空续写、过短续写等更硬的问题
case_count            本次生成质量报告覆盖了多少条样本
```

这些字段不会替代 `best_val_loss`。loss 仍然是训练目标上的指标；generation quality 是生成样本层面的轻量证据。

## registry 输出变化

`build_run_registry` 新增：

```text
generation_quality_counts
```

例如：

```json
{
  "pass": 2
}
```

这让 registry 可以快速回答：

```text
有多少 run 已经通过生成质量分析？
有没有 warn/fail 的生成质量报告？
```

CSV 新增 generation quality 列，HTML 新增 `Gen Quality` 列，链接区也会出现：

```text
gen quality
```

这个链接指向 `generation_quality.html`。它是只读证据入口，不会触发重新分析，也不会写入训练产物。

## model card 汇总规则

`model_card.py` 新增：

```text
generation_quality_counts
coverage.generation_quality_runs
coverage.generation_quality_pass_runs
```

run 表里也会显示：

```text
generation_quality_status
generation_quality_cases
```

状态推导也更严格了。`_derive_status` 现在在 dataset quality 和 eval suite 之后继续检查 generation quality：

```text
没有 generation quality -> needs-generation-quality
generation quality 不是 pass -> review
generation quality pass -> 可以继续成为 ready
```

注意：如果 experiment card 已经显式给出 `summary.status`，model card 会尊重 card 里的状态。这是为了保留单 run 人工 review 的入口，不让 registry 自动推导覆盖人工标记。

## project audit 门禁

`project_audit.py` 新增两条检查：

```text
generation_quality
non_pass_generation_quality
```

第一条检查覆盖率：

```text
每个 registered run 是否都有 generation quality 证据
```

第二条检查质量状态：

```text
已经分析过的 generation quality 是否都是 pass
```

如果缺失，会建议：

```text
Run generation quality analysis for all registered eval suite or sampling outputs.
```

如果有 warn/fail，会建议：

```text
Review runs with non-pass generation quality before release-style handoff.
```

这让 audit 不再只看数据质量、eval suite 和 dashboard，也开始把生成样本质量纳入发布前证据。

## register_runs 输出

`scripts/register_runs.py` 增加打印：

```text
generation_quality_counts={...}
```

这是命令行 smoke 里的快速证据。它不是新的 JSON 源，只是把 registry 已经计算好的摘要打印出来，方便本地和 CI 日志检查。

## 测试覆盖

本版更新了三组测试。

`tests/test_registry.py` 在 fake run 里加入：

```text
generation-quality/generation_quality.json
generation-quality/generation_quality.html
```

关键断言包括：

```text
run.generation_quality_status == "pass"
registry["generation_quality_counts"] == {"pass": 2}
registry.csv 包含 generation_quality_status
registry.html 包含 Gen Quality 列和 gen quality 链接
```

这些断言保护 registry 的读取、汇总、CSV 导出和 HTML 证据入口不会静默漂移。

`tests/test_model_card.py` 在 registry fixture 里加入 pass/warn 两种 generation quality 状态。

关键断言包括：

```text
coverage.generation_quality_runs == 2
generation_quality_counts == {"pass": 1, "warn": 1}
recommendations 包含 non-pass generation quality
```

这些断言保护 model card 能识别覆盖率，也能提醒非 pass 生成质量。

`tests/test_project_audit.py` 的完整项目 fixture 加入 pass 状态 generation quality。

关键断言仍然要求：

```text
overall_status == "pass"
fail_count == 0
warn_count == 0
```

这说明当 generation quality 证据完整且 pass 时，新增门禁不会误伤完整项目。

## smoke 证据

v29 的 smoke 构造了两个临时 run：

```text
run-a best_val_loss=0.72 generation_quality=pass
run-b best_val_loss=0.91 generation_quality=pass
```

然后真实运行：

```text
register_runs.py
build_model_card.py
audit_project.py
```

输出链路显示：

```text
registry generation_quality_counts={"pass": 2}
model card generation_quality_runs=2
project audit checks=13 pass/0 warn/0 fail
```

结构检查进一步确认：

```text
registry JSON 有 generation_quality_counts
registry HTML 有 Gen Quality 列和 gen quality 链接
model_card JSON 有 generation_quality_counts 和 generation_quality_runs
project_audit JSON 有 generation_quality / non_pass_generation_quality 两个 check
project_audit Markdown 写出 Generation quality
```

这些是本版归档截图里的主要证据。

## 边界说明

本版不把 generation quality 变成训练目标。

本版不判断中文语义是否正确。

本版不引入外部大模型评分器。

本版不让 release gate 直接读取 `generation_quality.json`。目前 release gate 通过 project audit 的 overall status 间接继承这条检查。后续如果要更严格，可以把 release gate 增加成显式检查 audit 中的 generation quality check。

## 一句话总结

v29 把 v28 的生成质量报告从独立分析产物推进成 registry、model card 和 project audit 都能消费的只读证据链，让 MiniGPT 的发布审查开始同时看训练指标、数据质量和生成样本质量。
