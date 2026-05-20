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
```

写入规则：

- `图片/` 保存真实命令输出截图、Playwright/Chrome 截图、结构检查截图和文档检查截图。
- `解释/说明.md` 写清楚本版主题、关键改动、每张截图证明什么，以及 tag 含义。
- 临时日志、临时 fixture、测试缓存不放进 `d/`，完成后按 AGENTS 清理门禁删除。
- README、代码讲解和版本说明里引用 v303 及后续归档时，默认引用 `d/<version>`。

一句话总览：`d/` 从 v303 开始承接后续版本的运行截图和解释，让 `a/`、`b/`、`c/` 都成为稳定的历史阶段归档。
