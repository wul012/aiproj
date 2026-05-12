# v26 Release Bundle 代码讲解

## 这一版解决什么问题

v25 的 `project_audit` 已经能告诉我们项目是否满足基本门禁。
但交付时还需要一个更靠外层的报告，把下面这些证据放到同一个入口里：

```text
registry.json / registry.html
model_card.json / model_card.html
project_audit.json / project_audit.html
top runs
release status
recommendations
evidence artifacts
```

v26 新增 `release_bundle`：

```text
registry + model_card + project_audit
 -> release_bundle.json
 -> release_bundle.md
 -> release_bundle.html
```

它是“最终交付证据包”，适合配合 tag、截图归档和 README 一起展示。

## 核心文件

```text
src/minigpt/release_bundle.py
scripts/build_release_bundle.py
tests/test_release_bundle.py
```

## build_release_bundle 的输入

主函数是：

```python
build_release_bundle(registry_path, model_card_path=None, audit_path=None)
```

`registry_path` 是必需的。

`model_card_path` 和 `audit_path` 可以手动传入，也可以自动发现：

```text
registry/model_card.json
registry/model-card/model_card.json
../model-card/model_card.json
registry/project_audit.json
registry/audit/project_audit.json
../audit/project_audit.json
```

## Release status

`release_status` 根据 audit 状态计算：

```text
audit pass -> release-ready
audit warn -> review-needed
audit fail -> blocked
没有 audit -> needs-audit
```

这比单纯显示 audit status 更贴近交付语义。

## Summary

`summary` 汇总：

```text
release_status
audit_status
audit_score_percent
run_count
best_run_name
best_val_loss
ready_runs
available_artifacts
missing_artifacts
```

所以打开 release bundle 的第一屏，就能知道“这一版能不能交付”。

## Evidence artifacts

`_collect_release_artifacts` 会收集证据文件：

```text
registry.json
registry.csv
registry.svg
registry.html
model_card.json
model_card.md
model_card.html
project_audit.json
project_audit.md
project_audit.html
```

每个 artifact 记录：

```text
key
title
path
kind
description
exists
size_bytes
```

这让 release bundle 不只是文字说明，也能检查关键交付物是否真的存在。

## Top runs

`_top_runs` 优先使用 model card 的 `top_runs`。
如果 model card 不存在，就退回 registry 的 `loss_leaderboard`。

这样 release bundle 即使缺少部分上层材料，也能尽量给出可读摘要。

## Recommendations

recommendations 会合并：

```text
project_audit.recommendations
model_card.recommendations
release status 派生建议
```

例如：

```text
release-ready -> 保留这个 bundle 作为 tag 证据
blocked -> 先修复 failed audit checks
needs-audit -> 先生成 project_audit.json
```

## CLI 脚本

新增脚本：

```powershell
python scripts/build_release_bundle.py --registry runs/registry/registry.json --model-card runs/model-card/model_card.json --audit runs/audit/project_audit.json --out-dir runs/release-bundle
```

输出：

```text
release_bundle.json
release_bundle.md
release_bundle.html
```

终端会打印：

```text
release_status
audit_status
best_run
artifacts
outputs
```

## 与前几版的关系

```text
registry: 多 run 索引
experiment_card: 单 run 复盘
model_card: 项目级说明
project_audit: 项目级质量门禁
release_bundle: 最终交付证据包
```

## 一句话总结

v26 把 MiniGPT 的实验材料从“能审计”推进到“能交付”，形成一个可随版本 tag 一起保存的 release evidence bundle。
