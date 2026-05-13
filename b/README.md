# MiniGPT 运行截图和解释归档

本目录从 v32 开始保存新的运行截图和解释，和历史目录 `a/` 同级。

`a/` 保留 v1-v31 的历史归档，不迁移旧文件。后续新版本默认写入本目录，避免所有运行证据继续堆在同一个历史目录里。

目录结构继续沿用旧格式：

```text
b/<version>/图片
b/<version>/解释/说明.md
```

示例：

```text
b/32/图片
b/32/解释/说明.md
```

## 当前索引

```text
b/32/图片
b/32/解释/说明.md
 -> v32 release gate profile comparison 的运行截图和解释
b/33/图片
b/33/解释/说明.md
 -> v33 release gate profile delta explanations 的运行截图和解释
b/34/图片
b/34/解释/说明.md
 -> v34 configurable release gate delta baseline 的运行截图和解释
b/35/图片
b/35/解释/说明.md
 -> v35 benchmark eval suite metadata 的运行截图和解释
b/36/图片
b/36/解释/说明.md
 -> v36 dataset version manifests 的运行截图和解释
b/37/图片
b/37/解释/说明.md
 -> v37 baseline model comparison 的运行截图和解释
b/38/图片
b/38/解释/说明.md
 -> v38 inference safety profile 的运行截图和解释
b/39/图片
b/39/解释/说明.md
 -> v39 checkpoint selector 的运行截图和解释
b/40/图片
b/40/解释/说明.md
 -> v40 checkpoint comparison shortcuts 的运行截图和解释
b/41/图片
b/41/解释/说明.md
 -> v41 side-by-side checkpoint generation 的运行截图和解释
b/42/图片
b/42/解释/说明.md
 -> v42 persisted pair generation artifacts 的运行截图和解释
b/43/图片
b/43/解释/说明.md
 -> v43 fixed prompt pair generation batches 的运行截图和解释
b/44/图片
b/44/解释/说明.md
 -> v44 pair batch trend comparison 的运行截图和解释
b/45/图片
b/45/解释/说明.md
 -> v45 pair batch dashboard/playground links 的运行截图和解释
b/46/图片
b/46/解释/说明.md
 -> v46 registry pair report links 的运行截图和解释
b/47/图片
b/47/解释/说明.md
 -> v47 registry pair delta leaders 的运行截图和解释
b/48/图片
b/48/解释/说明.md
 -> v48 project maturity summary 的运行截图和解释
b/49/图片
b/49/解释/说明.md
 -> v49 benchmark scorecard 的运行截图和解释
b/50/图片
b/50/解释/说明.md
 -> v50 benchmark scorecard drilldowns 的运行截图和解释
b/51/图片
b/51/解释/说明.md
 -> v51 benchmark rubric scoring 的运行截图和解释
b/52/图片
b/52/解释/说明.md
 -> v52 registry benchmark rubric tracking 的运行截图和解释
b/53/图片
b/53/解释/说明.md
 -> v53 benchmark scorecard comparison 的运行截图和解释
b/54/图片
b/54/解释/说明.md
 -> v54 dataset cards 的运行截图和解释
b/55/图片
b/55/解释/说明.md
 -> v55 streaming playground generation 的运行截图和解释
b/56/图片
b/56/解释/说明.md
 -> v56 streaming timeout and cancellation 的运行截图和解释
```

写入规则：

- `图片/` 保存真实命令输出截图、Playwright/Chrome 截图、结构检查截图和文档检查截图。
- `解释/说明.md` 写清楚本版主题、关键改动、每张截图证明什么，以及 tag 含义。
- 临时日志、临时 fixture、测试缓存不放进 `b/`，完成后按 AGENTS 清理门禁删除。
- README、代码讲解和版本说明里引用后续归档时，默认引用 `b/<version>`。

一句话总览：`a/` 记录 v1-v31 的历史运行证据，`b/` 从 v32 开始继续记录后续版本的运行截图和解释。
