# MiniGPT 运行截图和解释归档 e

本目录从 v473 开始保存模型能力阶段的运行截图和解释，和历史目录 `a/`、`b/`、`c/`、`d/` 同级。

- `a/` 保留 v1-v31 的历史运行证据，不迁移。
- `b/` 保留 v32-v68 的历史运行证据，不迁移。
- `c/` 保留 v69-v302 的历史运行证据，不迁移。
- `d/` 保留 v303-v472 的训练治理阶段运行证据，不迁移。
- 从 v473 开始，新的模型能力阶段运行截图和解释写入 `e/`。

目录结构继续沿用旧格式：

```text
e/<version>/图片
e/<version>/解释/说明.md
```

## 当前索引

```text
e/473/图片
e/473/解释/说明.md
 -> v473 baseline-candidate tiny model capability delta 的运行截图和解释

e/474/图片
e/474/解释/说明.md
 -> v474 model capability ladder 的运行截图和解释

e/475/图片
e/475/解释/说明.md
 -> v475 model capability ladder stability 的运行截图和解释

e/476/图片
e/476/解释/说明.md
 -> v476 model capability stall diagnostic 的运行截图和解释

e/477/图片
e/477/解释/说明.md
 -> v477 model capability token budget probe 的运行截图和解释

e/478/图片
e/478/解释/说明.md
 -> v478 model capability token budget stability 的运行截图和解释

e/479/图片
e/479/解释/说明.md
 -> v479 model capability rubric signal audit 的运行截图和解释

e/480/图片
e/480/解释/说明.md
 -> v480 model capability required-term coverage audit 的运行截图和解释

e/481/图片
e/481/解释/说明.md
 -> v481 model capability required-term uptake audit 的运行截图和解释

e/482/图片
e/482/解释/说明.md
 -> v482 model capability required-term scaffold probe 的运行截图和解释

e/483/图片
e/483/解释/说明.md
 -> v483 model capability required-term micro-training 的运行截图和解释

e/484/图片
e/484/解释/说明.md
 -> v484 model capability required-term holdout 的运行截图和解释

e/485/图片
e/485/解释/说明.md
 -> v485 model capability required-term split scan 的运行截图和解释

e/486/图片
e/486/解释/说明.md
 -> v486 model capability required-term split seed stability 的运行截图和解释
```

写入规则：

- `图片/` 保存 Playwright/Chrome 截图、真实命令输出截图、模型能力报告截图和文档检查截图。
- `解释/说明.md` 写清楚本版主题、真实训练配置、能力指标变化、每张截图证明什么，以及 tag 含义。
- 临时日志、测试缓存和一次性调试文件不放进 `e/`；完成后按 AGENTS 清理门禁删除。
- README、代码讲解和版本说明里引用 v473 及后续归档时，默认引用 `e/<version>`。

一句话总览：`e/` 从 v473 开始承接模型能力阶段证据，让训练治理阶段的 `d/` 成为稳定历史归档。
