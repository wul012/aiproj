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

e/527/图片
e/527/解释/说明.md
 -> v527 model capability required-term pair loss-alias blocked-token fresh compare 的运行截图和解释

e/528/图片
e/528/解释/说明.md
 -> v528 model capability required-term pair loss-alias fresh seed sweep 的运行截图和解释

e/529/图片
e/529/解释/说明.md
 -> v529 generation profile playground/API/CLI surface 的运行截图和解释

e/530/图片
e/530/解释/说明.md
 -> v530 generation profiles endpoint and runtime playground registry 的运行截图和解释

e/531/图片
e/531/解释/说明.md
 -> v531 generation profile contract check 的运行截图和解释

e/532/图片
e/532/解释/说明.md
 -> v532 required-term pair generation profile replay 的运行截图和解释

e/533/图片
e/533/解释/说明.md
 -> v533 required-term pair coexistence refresh 的运行截图和解释

e/534/图片
e/534/解释/说明.md
 -> v534 required-term pair first-token preference 的运行截图和解释

e/535/图片
e/535/解释/说明.md
 -> v535 required-term pair colon-immediate refresh 的运行截图和解释

e/536/图片
e/536/解释/说明.md
 -> v536 required-term pair colon-immediate stability 的运行截图和解释

e/537/图片
e/537/解释/说明.md
 -> v537 required-term pair colon-immediate missed-seed diagnostic 的运行截图和解释

e/538/图片
e/538/解释/说明.md
 -> v538 required-term pair first-token boost stability 的运行截图和解释

e/539/图片
e/539/解释/说明.md
 -> v539 required-term pair isolated prompt stability 的运行截图和解释

e/540/图片
e/540/解释/说明.md
 -> v540 required-term pair direct-budget stability 的运行截图和解释

e/541/图片
e/541/解释/说明.md
 -> v541 required-term pair decode boundary check 的运行截图和解释

e/542/图片
e/542/解释/说明.md
 -> v542 required-term pair top-k2 stability 的运行截图和解释

e/543/图片
e/543/解释/说明.md
 -> v543 required-term pair temperature boundary check 的运行截图和解释

e/544/图片
e/544/解释/说明.md
 -> v544 required-term pair top-k2 t0.8 stability 的运行截图和解释

e/545/图片
e/545/解释/说明.md
 -> v545 required-term pair first-token boost top-k2 t0.8 stability 的运行截图和解释

e/546/图片
e/546/解释/说明.md
 -> v546 required-term pair loss-calibrated top-k2 t0.8 stability 的运行截图和解释

e/547/图片
e/547/解释/说明.md
 -> v547 required-term pair seed coverage tradeoff 的运行截图和解释

e/548/图片
e/548/解释/说明.md
 -> v548 required-term pair seed config selection 的运行截图和解释

e/549/图片
e/549/解释/说明.md
 -> v549 required-term pair seed config replay 的运行截图和解释

e/550/图片
e/550/解释/说明.md
 -> v550 required-term pair seed config held-out replay 的运行截图和解释

e/551/图片
e/551/解释/说明.md
 -> v551 required-term pair seed config held-out gap diagnostic 的运行截图和解释

e/552/图片
e/552/解释/说明.md
 -> v552 required-term pair equals-surface fixed repair 的运行截图和解释

e/553/图片
e/553/解释/说明.md
 -> v553 required-term pair coexistence corpus split 的运行截图和解释

e/554/图片
e/554/解释/说明.md
 -> v554 required-term pair equals-surface balanced repair 的运行截图和解释

e/555/图片
e/555/解释/说明.md
 -> v555 required-term pair equals-surface repair comparison 的运行截图和解释

e/556/图片
e/556/解释/说明.md
 -> v556 required-term pair equals-surface tied repair 的运行截图和解释

e/557/图片
e/557/解释/说明.md
 -> v557 required-term pair refresh forced-choice 的运行截图和解释

e/558/图片
e/558/解释/说明.md
 -> v558 required-term pair constrained decode feasibility 的运行截图和解释

e/559/图片
e/559/解释/说明.md
 -> v559 required-term pair equals-surface tied wider embedding 的运行截图和解释

e/560/图片
e/560/解释/说明.md
 -> v560 required-term pair equals-surface no-pair-id repair 的运行截图和解释

e/561/图片
e/561/解释/说明.md
 -> v561 required-term pair equals-surface no-pair-id loss-balanced repair 的运行截图和解释

e/562/图片
e/562/解释/说明.md
 -> v562 required-term pair equals-surface no-pair-id loss-balanced stability 的运行截图和解释

e/563/图片
e/563/解释/说明.md
 -> v563 required-term pair no-pair-id loss-balanced missed-seed diagnostic 的运行截图和解释

e/564/图片
e/564/解释/说明.md
 -> v564 required-term pair no-pair-id loss-balanced first-token stability 的运行截图和解释

e/565/图片
e/565/解释/说明.md
 -> v565 required-term pair no-pair-id first-token migration comparison 的运行截图和解释

e/566/图片
e/566/解释/说明.md
 -> v566 required-term pair no-pair-id loss-balanced light-first-token stability 的运行截图和解释

e/567/图片
e/567/解释/说明.md
 -> v567 required-term pair no-pair-id first-token density comparison 的运行截图和解释

e/568/图片
e/568/解释/说明.md
 -> v568 required-term pair first-token route decision 的运行截图和解释

e/569/图片
e/569/解释/说明.md
 -> v569 required-term pair route held-out replay 的运行截图和解释

e/570/图片
e/570/解释/说明.md
 -> v570 required-term pair route held-out expanded suite 的运行截图和解释

e/571/图片
e/571/解释/说明.md
 -> v571 required-term pair route fresh seed 3535 的运行截图和解释

e/572/图片
e/572/解释/说明.md
 -> v572 required-term pair route fresh seed 3535 missed diagnostic 的运行截图和解释

e/573/图片
e/573/解释/说明.md
 -> v573 required-term pair route fresh seed 3535 first-token repair 的运行截图和解释

e/574/图片
e/574/解释/说明.md
 -> v574 required-term pair route fresh seed 3535 repair comparison 的运行截图和解释

e/575/图片
e/575/解释/说明.md
 -> v575 required-term pair route fresh seed 3535 wider embedding 的运行截图和解释

e/576/图片
e/576/解释/说明.md
 -> v576 required-term pair route fresh seed 3535 variable comparison 的运行截图和解释

e/577/图片
e/577/解释/说明.md
 -> v577 required-term pair fresh seed route decision 的运行截图和解释

e/578/图片
e/578/解释/说明.md
 -> v578 required-term pair route closeout summary 的运行截图和解释

e/579/图片
e/579/解释/说明.md
 -> v579 required-term pair branch binding seed 3535 的运行截图和解释
```

写入规则：

- `图片/` 保存 Playwright/Chrome 截图、真实命令输出截图、模型能力报告截图和文档检查截图。
- `解释/说明.md` 写清楚本版主题、真实训练配置、能力指标变化、每张截图证明什么，以及 tag 含义。
- 临时日志、测试缓存和一次性调试文件不放进 `e/`；完成后按 AGENTS 清理门禁删除。
- README、代码讲解和版本说明里引用 v473 及后续归档时，默认引用 `e/<version>`。

一句话总览：`e/` 从 v473 开始承接模型能力阶段证据，让训练治理阶段的 `d/` 成为稳定历史归档。
