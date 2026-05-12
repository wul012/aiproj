# 29. v14 Run Manifest

这一版新增 `src/minigpt/manifest.py`，目标是让每次训练都留下一个可复现的实验快照：当时用的代码版本、环境、数据来源、模型配置、训练结果和产物清单都保存到 run 目录。

## 文件角色

`manifest.py` 负责生成两类产物：

- `run_manifest.json`：给程序读取的完整元数据。
- `run_manifest.svg`：给人快速查看的摘要图。

`scripts/train.py` 负责在训练结束后调用 manifest 写入函数。

`dashboard.py` 和 `playground.py` 负责把 manifest 当作普通实验产物展示出来。

## 核心流程

```text
train.py 完成训练
 -> 保存 checkpoint/tokenizer/train_config/history/sample
 -> build_run_manifest
 -> collect_git_metadata
 -> collect_run_artifacts
 -> write_run_manifest_json
 -> write_run_manifest_svg
 -> dashboard/playground 显示 manifest 链接与摘要
```

## 关键代码

`build_run_manifest` 把训练时已经知道的信息合成一个字典，包括：

- `git`：commit、branch、tag、dirty 状态。
- `environment`：Python、platform、torch、numpy。
- `data`：数据来源、总 token 数、训练/验证 token 数、dataset report 摘要。
- `model`：模型配置和参数量。
- `training`：训练参数、tokenizer、device、起止 step。
- `results`：最后 loss 和 `history_summary`。
- `artifacts`：run 目录里的 checkpoint、tokenizer、metrics、dataset report、dashboard、playground 等产物。

`collect_run_artifacts` 不只记录文件是否存在和大小，还会对较小文件计算 `sha256`。这一步是后面做 dataset fingerprint、artifact integrity check 的基础。

`write_run_manifest_svg` 会把最关键的信息画成摘要卡片，例如 commit、dirty、token 数、参数量、best val、artifact 数量和训练耗时。

## 训练脚本变化

`train.py` 在训练开始时记录 `started_at`，在保存主要训练产物后记录 `finished_at`，再写 manifest。

这样 manifest 可以覆盖本次 run 的完整结果，而不是只记录训练前配置。

训练结束后会多打印一行：

```text
manifest=runs/minigpt/run_manifest.json
```

## 验证范围

v14 新增 `tests/test_manifest.py`，覆盖：

- 小文件 sha256。
- run artifact inventory。
- manifest 关键字段。
- JSON/SVG 写出。

同时 dashboard 和 playground 测试也增加了 manifest 链接检查，确保 UI 层没有漏接。

## 一句话总结

v14 把一次训练从“目录里有一堆文件”升级成“有一张可复现的实验身份证”。
