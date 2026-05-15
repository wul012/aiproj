# MiniGPT 运行截图和解释归档 c

本目录从 v69 开始保存新的运行截图和解释，和历史目录 `a/`、`b/` 同级。

- `a/` 保留 v1-v31 的历史运行证据，不迁移。
- `b/` 保留 v32-v68 的历史运行证据，不迁移。
- 从 v69 开始，新的运行截图和解释写入 `c/`。

目录结构继续沿用旧格式：

```text
c/<version>/图片
c/<version>/解释/说明.md
```

## 当前索引

```text
c/69/图片
c/69/解释/说明.md
 -> v69 training portfolio batch matrix 的运行截图和解释
c/70/图片
c/70/解释/说明.md
 -> v70 training scale planner 的运行截图和解释
c/71/图片
c/71/解释/说明.md
 -> v71 training scale gate 的运行截图和解释
c/72/图片
c/72/解释/说明.md
 -> v72 gated training scale run 的运行截图和解释
c/73/图片
c/73/解释/说明.md
 -> v73 gated training scale run comparison 的运行截图和解释
c/74/图片
c/74/解释/说明.md
 -> v74 training scale run decision 的运行截图和解释
c/75/图片
c/75/解释/说明.md
 -> v75 consolidated training scale workflow 的运行截图和解释
c/76/图片
c/76/解释/说明.md
 -> v76 controlled training scale handoff 的运行截图和解释
c/77/图片
c/77/解释/说明.md
 -> v77 training scale promotion acceptance 的运行截图和解释
c/78/图片
c/78/解释/说明.md
 -> v78 training scale promotion index 的运行截图和解释
c/79/图片
c/79/解释/说明.md
 -> v79 promoted training scale comparison 的运行截图和解释
c/80/图片
c/80/解释/说明.md
 -> v80 promoted training scale baseline decision 的运行截图和解释
c/81/图片
c/81/解释/说明.md
 -> v81 promoted training scale next-cycle seed 的运行截图和解释
c/82/图片
c/82/解释/说明.md
 -> v82 promoted training scale seed handoff 的运行截图和解释
c/83/图片
c/83/解释/说明.md
 -> v83 report utility consolidation 的运行截图和解释
c/84/图片
c/84/解释/说明.md
 -> v84 controlled handoff report utility migration 的运行截图和解释
c/85/图片
c/85/解释/说明.md
 -> v85 promoted seed report utility migration 的运行截图和解释
c/86/图片
c/86/解释/说明.md
 -> v86 promoted decision report utility migration 的运行截图和解释
c/87/图片
c/87/解释/说明.md
 -> v87 run decision report utility migration 的运行截图和解释
c/88/图片
c/88/解释/说明.md
 -> v88 run comparison report utility migration 的运行截图和解释
c/89/图片
c/89/解释/说明.md
 -> v89 gated run report utility migration 的运行截图和解释
c/90/图片
c/90/解释/说明.md
 -> v90 training scale gate report utility migration 的运行截图和解释
c/91/图片
c/91/解释/说明.md
 -> v91 training scale plan report utility migration 的运行截图和解释
c/92/图片
c/92/解释/说明.md
 -> v92 training scale workflow report utility migration 的运行截图和解释
c/93/图片
c/93/解释/说明.md
 -> v93 training scale promotion report utility migration 的运行截图和解释
c/94/图片
c/94/解释/说明.md
 -> v94 training scale promotion index report utility migration 的运行截图和解释
c/95/图片
c/95/解释/说明.md
 -> v95 promoted training scale comparison report utility migration 的运行截图和解释
c/96/图片
c/96/解释/说明.md
 -> v96 generation quality report utility migration 的运行截图和解释
c/97/图片
c/97/解释/说明.md
 -> v97 release bundle report utility migration 的运行截图和解释
c/98/图片
c/98/解释/说明.md
 -> v98 README maturity summary cleanup 的运行截图和解释
c/99/图片
c/99/解释/说明.md
 -> v99 project audit report utility migration 的运行截图和解释
c/100/图片
c/100/解释/说明.md
 -> v100 model card report utility migration 的运行截图和解释
c/101/图片
c/101/解释/说明.md
 -> v101 experiment card report utility migration 的运行截图和解释
c/102/图片
c/102/解释/说明.md
 -> v102 dataset card report utility migration 的运行截图和解释
c/103/图片
c/103/解释/说明.md
 -> v103 run manifest report utility migration 的运行截图和解释
c/104/图片
c/104/解释/说明.md
 -> v104 data preparation report utility migration 的运行截图和解释
c/105/图片
c/105/解释/说明.md
 -> v105 data quality report utility migration 的运行截图和解释
c/106/图片
c/106/解释/说明.md
 -> v106 release readiness report utility migration 的运行截图和解释
c/107/图片
c/107/解释/说明.md
 -> v107 release readiness comparison report utility migration 的运行截图和解释
c/108/图片
c/108/解释/说明.md
 -> v108 batched release governance report utility migration 的运行截图和解释
```

写入规则：

- `图片/` 保存真实命令输出截图、Playwright/Chrome 截图、结构检查截图和文档检查截图。
- `解释/说明.md` 写清楚本版主题、关键改动、每张截图证明什么，以及 tag 含义。
- 临时日志、临时 fixture、测试缓存不放进 `c/`，完成后按 AGENTS 清理门禁删除。
- README、代码讲解和版本说明里引用 v69 及后续归档时，默认引用 `c/<version>`。

一句话总览：`c/` 从 v69 开始承接后续版本的运行截图和解释，让 `a/`、`b/` 都成为稳定的历史阶段归档。
