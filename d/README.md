# MiniGPT 运行截图和解释归档 d

本目录从 v303 开始保存新的运行截图和解释，和历史目录 `a/`、`b/`、`c/` 同级。

- `a/` 保留 v1-v31 的历史运行证据，不迁移。
- `b/` 保留 v32-v68 的历史运行证据，不迁移。
- `c/` 保留 v69-v302 的历史运行证据，不迁移。
- 从 v303 开始，新的运行截图和解释写入 `d/`。

目录结构继续沿用旧格式：

```text
d/<version>/图片
d/<version>/解释/说明.md
```

## 当前索引

```text
d/303/图片
d/303/解释/说明.md
 -> v303 training governance documentation stage split 的运行截图和解释
d/304/图片
d/304/解释/说明.md
 -> v304 training scale run CI regression carryover 的运行截图和解释
d/305/图片
d/305/解释/说明.md
 -> v305 training scale decision CI regression gate 的运行截图和解释
d/306/图片
d/306/解释/说明.md
 -> v306 training scale workflow handoff CI regression carryover 的运行截图和解释
d/307/图片
d/307/解释/说明.md
 -> v307 training scale promotion CI regression carryover 的运行截图和解释
d/308/图片
d/308/解释/说明.md
 -> v308 training scale promotion index CI regression filtering 的运行截图和解释
d/309/图片
d/309/解释/说明.md
 -> v309 promoted training scale comparison CI regression context 的运行截图和解释
d/310/图片
d/310/解释/说明.md
 -> v310 promoted training scale decision CI regression context 的运行截图和解释
d/311/图片
d/311/解释/说明.md
 -> v311 promoted training scale seed CI regression context 的运行截图和解释
d/312/图片
d/312/解释/说明.md
 -> v312 promoted training scale seed handoff CI regression context 的运行截图和解释
d/313/图片
d/313/解释/说明.md
 -> v313 promoted seed handoff receipt CI contract 的运行截图和解释
d/314/图片
d/314/解释/说明.md
 -> v314 promoted seed handoff assurance CI contract summary 的运行截图和解释
d/315/图片
d/315/解释/说明.md
 -> v315 tiny standard benchmark smoke 的运行截图和解释
d/316/图片
d/316/解释/说明.md
 -> v316 tiny standard pair baseline smoke 的运行截图和解释
d/317/图片
d/317/解释/说明.md
 -> v317 tiny scorecard comparison smoke 的运行截图和解释
d/318/图片
d/318/解释/说明.md
 -> v318 tiny scorecard decision smoke 的运行截图和解释
d/319/图片
d/319/解释/说明.md
 -> v319 tiny decision diagnostics smoke 的运行截图和解释
d/320/图片
d/320/解释/说明.md
 -> v320 tiny budget comparison smoke 的运行截图和解释
d/321/图片
d/321/解释/说明.md
 -> v321 promoted seed handoff artifact split 的运行截图和解释
d/322/图片
d/322/解释/说明.md
 -> v322 tiny scorecard decision threshold smoke 的运行截图和解释
d/323/图片
d/323/解释/说明.md
 -> v323 tiny threshold diagnostics smoke 的运行截图和解释
d/324/图片
d/324/解释/说明.md
 -> v324 tiny threshold profile smoke 的运行截图和解释
d/325/图片
d/325/解释/说明.md
 -> v325 decision threshold profile artifact 的运行截图和解释
d/326/图片
d/326/解释/说明.md
 -> v326 decision failure taxonomy 的运行截图和解释
d/327/图片
d/327/解释/说明.md
 -> v327 decision remediation plan 的运行截图和解释
d/328/图片
d/328/解释/说明.md
 -> v328 remediation summary 的运行截图和解释
d/329/图片
d/329/解释/说明.md
 -> v329 remediation metadata 的运行截图和解释
d/330/图片
d/330/解释/说明.md
 -> v330 remediation CSV artifact 的运行截图和解释
d/331/图片
d/331/解释/说明.md
 -> v331 clean remediation gate 的运行截图和解释
d/332/图片
d/332/解释/说明.md
 -> v332 remediation gate issues 的运行截图和解释
d/333/图片
d/333/解释/说明.md
 -> v333 remediation gate issue text 的运行截图和解释
d/334/图片
d/334/解释/说明.md
 -> v334 tiny scorecard smoke checker 的运行截图和解释
```

写入规则：

- `图片/` 保存真实命令输出截图、Playwright/Chrome 截图、结构检查截图和文档检查截图。
- `解释/说明.md` 写清楚本版主题、关键改动、每张截图证明什么，以及 tag 含义。
- 临时日志、临时 fixture、测试缓存不放进 `d/`，完成后按 AGENTS 清理门禁删除。
- README、代码讲解和版本说明里引用 v303 及后续归档时，默认引用 `d/<version>`。

一句话总览：`d/` 从 v303 开始承接后续版本的运行截图和解释，让 `a/`、`b/`、`c/` 都成为稳定的历史阶段归档。
