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
```

写入规则：

- `图片/` 保存真实命令输出截图、Playwright/Chrome 截图、结构检查截图和文档检查截图。
- `解释/说明.md` 写清楚本版主题、关键改动、每张截图证明什么，以及 tag 含义。
- 临时日志、临时 fixture、测试缓存不放进 `c/`，完成后按 AGENTS 清理门禁删除。
- README、代码讲解和版本说明里引用 v69 及后续归档时，默认引用 `c/<version>`。

一句话总览：`c/` 从 v69 开始承接后续版本的运行截图和解释，让 `a/`、`b/` 都成为稳定的历史阶段归档。
