# v25 Project Audit 代码讲解

## 这一版解决什么问题

v24 已经能生成 `model_card`，说明整个实验系列。
但模型卡偏“展示”，还缺一个更硬的质量门禁：

```text
registry 里有没有 run？
有没有 best run？
每个 run 是否有 loss？
experiment card 是否齐全？
dataset quality 是否齐全？
eval suite 是否齐全？
checkpoint / dashboard 是否齐全？
model card 是否存在？
有没有 ready run？
有没有非 pass 数据质量 run？
```

v25 新增 `project_audit`，把这些问题变成结构化检查：

```text
registry.json + model_card.json
 -> checks: pass / warn / fail
 -> score_percent
 -> recommendations
 -> project_audit.json
 -> project_audit.md
 -> project_audit.html
```

## 核心文件

```text
src/minigpt/project_audit.py
scripts/audit_project.py
tests/test_project_audit.py
```

## build_project_audit 的输入

主函数是：

```python
build_project_audit(registry_path, model_card_path=None)
```

`registry_path` 是必需的。
`model_card_path` 是可选的。如果不传，代码会尝试在 registry 周边寻找：

```text
registry/model_card.json
registry/model-card/model_card.json
../model-card/model_card.json
```

找不到也不会崩溃，但 `model_card` 检查会变成 `warn`。

## Run 行如何构造

`_build_run_rows` 会从 registry 的 `runs` 中提取每个 run 的核心字段：

```text
name
path
status
best_val_loss_rank
best_val_loss
dataset_quality
eval_suite_cases
checkpoint_exists
dashboard_exists
experiment_card_exists
tags
note
```

如果 model card 里有对应 run，则优先使用 model card 里的：

```text
status
experiment_card_exists
tags
note
```

如果没有 model card，则用 registry 字段推断状态。

## 审计检查

`_build_checks` 当前包含 11 项：

```text
registry_runs
best_run
comparable_loss
experiment_cards
dataset_quality
eval_suite
checkpoints
dashboards
model_card
ready_run
non_pass_quality
```

每项检查都有：

```text
id
title
status
detail
evidence
```

`status` 只会是：

```text
pass
warn
fail
```

## 覆盖率检查

很多检查本质是覆盖率，比如：

```text
experiment cards: 2/2
dataset quality: 2/2
eval suite: 2/2
```

这些检查由 `_coverage_check` 统一处理：

```text
0/total -> fail
部分覆盖 -> warn
全部覆盖 -> pass
```

这让门禁规则很直观。

## 分数和总状态

每个检查有权重：

```text
pass = 1.0
warn = 0.5
fail = 0.0
```

总分：

```text
score_percent = 平均权重 * 100
```

总状态：

```text
有 fail -> fail
没有 fail 但有 warn -> warn
全部 pass -> pass
```

所以 v25 的 smoke 中，11 项全 pass，分数就是：

```text
100.0
```

## Recommendations

`_build_recommendations` 会根据失败或警告项生成行动建议。

例如：

```text
缺 experiment cards -> 先给每个 run 生成 experiment card
缺 dataset quality -> 跑数据质量检查
缺 eval suite -> 跑固定 prompt 评估
缺 model card -> 生成 model_card.json
有非 pass 数据质量 -> 先复查数据
```

如果全部通过，则输出：

```text
All audit checks passed; keep the audit with the model card as release evidence.
```

## CLI 脚本

新增脚本：

```powershell
python scripts/audit_project.py --registry runs/registry/registry.json --model-card runs/model-card/model_card.json --out-dir runs/audit
```

输出：

```text
project_audit.json
project_audit.md
project_audit.html
```

脚本还支持：

```powershell
--fail-on-warn
```

这适合以后放进 CI：只要审计出现 warn 或 fail，就让流程失败。

## 一句话总结

v25 把 MiniGPT 的实验资料从“能展示”推进到“能自检”，开始形成面向发布、答辩和复盘的质量门禁。
