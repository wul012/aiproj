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

e/487/图片
e/487/解释/说明.md
 -> v487 model capability required-term balanced corpus 的运行截图和解释

e/488/图片
e/488/解释/说明.md
 -> v488 model capability required-term balanced training 的运行截图和解释

e/489/图片
e/489/解释/说明.md
 -> v489 model capability required-term prompt-leading corpus 的运行截图和解释

e/490/图片
e/490/解释/说明.md
 -> v490 model capability required-term prompt-leading training 的运行截图和解释

e/491/图片
e/491/解释/说明.md
 -> v491 model capability required-term direct prompt training 的运行截图和解释

e/492/图片
e/492/解释/说明.md
 -> v492 model capability required-term one-term isolation 的运行截图和解释

e/493/图片
e/493/解释/说明.md
 -> v493 model capability required-term one-term seed stability 的运行截图和解释

e/494/图片
e/494/解释/说明.md
 -> v494 model capability required-term pair curriculum 的运行截图和解释

e/495/图片
e/495/解释/说明.md
 -> v495 model capability required-term pair rebalance 的运行截图和解释

e/496/图片
e/496/解释/说明.md
 -> v496 model capability required-term pair rebalance seed stability 的运行截图和解释

e/497/图片
e/497/解释/说明.md
 -> v497 model capability required-term pair capacity sweep 的运行截图和解释

e/498/图片
e/498/解释/说明.md
 -> v498 model capability required-term pair decoding sweep 的运行截图和解释

e/499/图片
e/499/解释/说明.md
 -> v499 model capability required-term pair prompt separation audit 的运行截图和解释

e/500/图片
e/500/解释/说明.md
 -> v500 model capability required-term pair contrast-free training 的运行截图和解释

e/501/图片
e/501/解释/说明.md
 -> v501 model capability required-term pair loss-branch sweep 的运行截图和解释

e/502/图片
e/502/解释/说明.md
 -> v502 model capability required-term pair branch-retention sweep 的运行截图和解释

e/503/图片
e/503/解释/说明.md
 -> v503 model capability required-term pair forced-choice diagnostic 的运行截图和解释

e/504/图片
e/504/解释/说明.md
 -> v504 model capability required-term pair generation-gap audit 的运行截图和解释

e/505/图片
e/505/解释/说明.md
 -> v505 model capability required-term pair decoding-gap probe 的运行截图和解释

e/506/图片
e/506/解释/说明.md
 -> v506 model capability required-term pair decoding-path trace 的运行截图和解释

e/507/图片
e/507/解释/说明.md
 -> v507 model capability required-term pair first-token repair 的运行截图和解释

e/508/图片
e/508/解释/说明.md
 -> v508 model capability required-term pair prefix-completion sweep 的运行截图和解释

e/509/图片
e/509/解释/说明.md
 -> v509 model capability required-term pair diagnostic rollup 的运行截图和解释

e/510/图片
e/510/解释/说明.md
 -> v510 model capability required-term pair continuation-span objective 的运行截图和解释

e/511/图片
e/511/解释/说明.md
 -> v511 model capability required-term pair continuation-span stability 的运行截图和解释

e/512/图片
e/512/解释/说明.md
 -> v512 model capability required-term pair continuation-span heldout 的运行截图和解释

e/513/图片
e/513/解释/说明.md
 -> v513 model capability required-term pair continuation-span alias matrix 的运行截图和解释

e/514/图片
e/514/解释/说明.md
 -> v514 model capability required-term pair loss-alias objective 的运行截图和解释

e/515/图片
e/515/解释/说明.md
 -> v515 model capability required-term pair loss-alias stability 的运行截图和解释

e/516/图片
e/516/解释/说明.md
 -> v516 model capability required-term pair loss-alias focus 的运行截图和解释

e/517/图片
e/517/解释/说明.md
 -> v517 model capability required-term pair loss-alias normalized audit 的运行截图和解释

e/518/图片
e/518/解释/说明.md
 -> v518 model capability required-term pair loss-alias focus metrics 的运行截图和解释

e/519/图片
e/519/解释/说明.md
 -> v519 model capability required-term pair loss-alias stability metrics 的运行截图和解释

e/520/图片
e/520/解释/说明.md
 -> v520 model capability required-term pair loss-alias metric contrast 的运行截图和解释

e/521/图片
e/521/解释/说明.md
 -> v521 model capability required-term pair loss-alias segment audit 的运行截图和解释

e/522/图片
e/522/解释/说明.md
 -> v522 model capability required-term pair loss-alias decode cleanup 的运行截图和解释

e/523/图片
e/523/解释/说明.md
 -> v523 model capability required-term pair loss-alias focus newline cleanup metrics 的运行截图和解释

e/524/图片
e/524/解释/说明.md
 -> v524 model capability required-term pair loss-alias newline suppression probe 的运行截图和解释

e/525/图片
e/525/解释/说明.md
 -> v525 model capability required-term pair loss-alias newline suppression repeat 的运行截图和解释

e/526/图片
e/526/解释/说明.md
 -> v526 generator blocked-token profile 的运行截图和解释
```

写入规则：

- `图片/` 保存 Playwright/Chrome 截图、真实命令输出截图、模型能力报告截图和文档检查截图。
- `解释/说明.md` 写清楚本版主题、真实训练配置、能力指标变化、每张截图证明什么，以及 tag 含义。
- 临时日志、测试缓存和一次性调试文件不放进 `e/`；完成后按 AGENTS 清理门禁删除。
- README、代码讲解和版本说明里引用 v473 及后续归档时，默认引用 `e/<version>`。

一句话总览：`e/` 从 v473 开始承接模型能力阶段证据，让训练治理阶段的 `d/` 成为稳定历史归档。
