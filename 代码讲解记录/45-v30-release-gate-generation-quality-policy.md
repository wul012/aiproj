# 第三十版讲解：release gate generation quality policy

本版目标是把 v29 接入 project audit 的生成质量检查，继续推进到 release gate 的显式策略层。

v29 已经做到：

```text
generation_quality.json
 -> registry
 -> model_card
 -> project_audit
```

但是 v29 的 release gate 只会整体读取 audit status 和 audit checks 是否全 clean。也就是说，只要 audit 结果里有 warn/fail，release gate 会受到影响；但 gate policy 本身没有明说“generation quality 是必需证据”。v30 补上的就是这个边界：release gate 默认要求 project audit 里必须存在并通过：

```text
generation_quality
non_pass_generation_quality
```

本版不重新分析生成文本，不修改 `generation_quality.py`，不重新定义模型质量指标，不把 release gate 变成训练或评测执行器。release gate 仍然只读 `release_bundle.json`，它只是更严格地检查 bundle 里的 audit evidence。

## 关键文件

本版修改：

```text
src/minigpt/release_gate.py
scripts/check_release_gate.py
tests/test_release_gate.py
README.md
代码讲解记录/README.md
a/30/解释/说明.md
```

关键点是：`release_gate.py` 消费 v26 的 release bundle、v25/v29 的 project audit 结果；它不直接读取 run 目录，也不直接读取 `generation_quality.json`。

## 策略字段

`build_release_gate` 新增参数：

```python
require_generation_quality: bool = True
```

输出的 `policy` 里新增：

```text
require_generation_quality_audit_checks=true
```

这个字段表达的是 release gate 的放行策略，而不是模型指标本身。含义是：

```text
release_bundle.audit_checks 里必须存在 generation_quality
release_bundle.audit_checks 里必须存在 non_pass_generation_quality
这两个 audit check 都应该是 pass
```

如果是旧版本 release bundle，可以通过 CLI 显式关闭：

```powershell
--allow-missing-generation-quality
```

这个开关只用于 legacy bundle 兼容，不是推荐路径。

## 新增 gate check

`_build_checks` 新增一条检查：

```text
id: generation_quality_audit_checks
title: Generation quality audit checks passed
```

它的判断来自两个 helper：

```python
_generation_quality_audit_result(...)
_generation_quality_audit_detail(...)
```

规则是：

```text
缺少 generation_quality 或 non_pass_generation_quality -> fail
任意一个是 fail -> fail
任意一个是 warn -> warn
两个都是 pass -> pass
策略关闭 -> pass，并说明不要求这两项
```

这让 release gate 对生成质量证据的态度从“隐含在 audit overall 里”变成“有单独 policy line 和 check row”。

## 输入输出边界

输入仍然是：

```text
release_bundle.json
```

release gate 不读取：

```text
registry.json
model_card.json
project_audit.json
generation_quality.json
run directories
checkpoint.pt
```

这是刻意保持的边界。release bundle 已经是 handoff evidence，gate 只检查 handoff evidence 是否满足 policy。这样 gate 可以在 CI 或发布脚本里稳定运行，不需要重新扫描项目目录。

输出仍然是：

```text
gate_report.json
gate_report.md
gate_report.html
```

它们是最终门禁证据，不是中间日志。v30 在这些报告里能看到：

```text
require_generation_quality_audit_checks=true
Generation quality audit checks passed
generation_quality=pass
non_pass_generation_quality=pass
```

## CLI 行为

`scripts/check_release_gate.py` 新增参数：

```powershell
--allow-missing-generation-quality
```

默认行为更严格：

```text
缺少 generation quality audit checks -> exit code 1
generation quality audit checks fail -> exit code 1
generation quality audit checks warn -> gate_status=warn
```

命令输出也会打印：

```text
require_generation_quality=True
```

这行是 smoke 和 CI 日志里的快速证据，说明本次 gate 不是宽松 legacy 模式。

## 测试覆盖

`tests/test_release_gate.py` 更新了 `make_bundle` fixture。默认 bundle 会包含：

```text
ready_run
generation_quality
non_pass_generation_quality
```

新增测试覆盖四个关键场景。

第一，完整 bundle 可以通过：

```text
gate_status=pass
decision=approved
generation_quality_audit_checks 存在
```

第二，缺失 generation quality audit checks 会阻断：

```text
gate_status=fail
decision=blocked
exit_code=1
detail 包含 missing required audit check
```

第三，legacy bundle 可以显式放宽：

```text
require_generation_quality=False
generation_quality_audit_checks=pass
```

这保护旧 bundle 的检查入口，但要求调用者显式选择。

第四，generation quality audit checks 为 warn 时：

```text
gate_status=warn
fail_on_warn=False -> exit 0
fail_on_warn=True -> exit 1
```

这些断言保护了三个边界：默认严格、legacy 可选、warn 可按 CI 策略升级为失败。

## smoke 证据

v30 smoke 构造了一个 release bundle：

```text
release_status=release-ready
audit_status=pass
audit_score_percent=100
ready_runs=2
missing_artifacts=0
generation_quality=pass
non_pass_generation_quality=pass
```

运行：

```powershell
python scripts/check_release_gate.py --bundle ... --out-dir ...
```

得到：

```text
gate_status=pass
decision=approved
checks=11 pass/0 warn/0 fail
require_generation_quality=True
```

结构检查确认：

```text
policy.requires_generation_quality = true
generation_quality_audit_checks 存在且 pass
Markdown / HTML 都写出 Generation quality audit checks passed
```

另外还构造了一个 legacy 缺失场景，删除两个 generation quality audit checks 后重新跑 gate：

```text
gate_status=fail
decision=blocked
exit_code=1
```

这证明 v30 的策略不是只在报告里显示，而是真正影响 release gate 的退出码。

## 边界说明

本版不改变 project audit 的 generation quality 检查规则。那是 v29 的责任。

本版不直接解析 generation quality case 级 flags。release gate 只要求 audit 层给出 pass/warn/fail。

本版不把旧 release bundle 自动视为合格。旧 bundle 要么补 project audit，要么显式使用 `--allow-missing-generation-quality`。

本版不改变 release bundle 格式。它只消费已有的 `audit_checks` 列表。

## 一句话总结

v30 把 generation quality 从 audit 里的普通检查推进成 release gate 的显式发布策略，让 MiniGPT 的最终放行不再只看 audit overall，而是明确要求生成质量证据存在并通过。
