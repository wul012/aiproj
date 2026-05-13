# MiniGPT 代码讲解记录_评估基准阶段

本目录从 v35 开始记录 MiniGPT 的“评估基准阶段”。上一阶段 `代码讲解记录_发布治理阶段` 已经把 v31-v34 的 release gate profiles、profile comparison、profile deltas 和 configurable baseline 收口；v35-v47 开始，项目重点从“发布治理继续细分”转向“模型能力如何被固定任务集、稳定数据版本、baseline model comparison、本地推理安全边界、checkpoint 选择、checkpoint 快速比较入口、side-by-side 生成、可留档 pair artifacts、固定 prompt pair batch、pair batch trend、dashboard/playground 报告入口、registry 多 run 索引和跨 run pair delta 聚合表达出来”。

## 写入规则

新版本如果主要围绕 benchmark、标准评估集、模型能力横向比较、数据版本和推理服务评估，就写入本目录。编号继续沿用全局顺序：

```text
50-v35-benchmark-eval-suite.md
51-v36-dataset-versioning.md
52-v37-baseline-model-comparison.md
53-v38-inference-safety-profile.md
54-v39-checkpoint-selector.md
55-v40-checkpoint-comparison-shortcuts.md
56-v41-side-by-side-generation.md
57-v42-pair-generation-artifacts.md
58-v43-pair-batch-comparison.md
59-v44-pair-batch-trends.md
60-v45-pair-batch-dashboard-links.md
61-v46-registry-pair-report-links.md
62-v47-registry-pair-delta-leaders.md
```

说明文档继续向参考文档靠齐：

```text
D:\C\mini-kv\代码讲解记录\111-restart-recovery-evidence-v55.md
```

也就是每篇要写清楚：

- 本版目标、来源、边界和不做什么。
- 本版位于模型能力评估链路的哪一环。
- 关键文件、字段语义、输入输出和运行流程。
- JSON、CSV、SVG、HTML、截图和归档为什么能作为证据。
- 测试覆盖链路、关键断言和失败时能拦住什么。
- 一句话总结项目成熟度推进到了哪一层。

## 当前项目进度基线

截至 v47，项目已经具备从训练、数据治理、数据版本、实验记录、发布治理、benchmark prompt suite、baseline model comparison、本地推理 API 安全画像、playground checkpoint selector、checkpoint comparison shortcuts、side-by-side checkpoint generation、persisted pair generation artifacts、fixed prompt pair batch comparison、pair batch trend comparison、pair batch dashboard/playground links、registry pair report links 到 registry pair delta leaders 的完整学习型 AI 工程链路。发布治理已经能解释 profile 分歧；评估基准阶段开始回答更直接的问题：

```text
同一个 checkpoint 在固定任务集上表现如何？
同一个 checkpoint 到底用了哪个 dataset version？
不同 checkpoint、tokenizer、模型大小和训练步数以后能否横向比较？
本地 playground 当前选择的是哪个 checkpoint？
多个候选 checkpoint 的文件、tokenizer、参数量和数据版本差异是什么？
同一个 prompt 用两个 checkpoint 生成时，输出是否相同、长度差异是多少？
这次左右 checkpoint 生成对比是否能保存成可复查的本地 JSON/HTML 证据？
同一套固定 prompts 能否批量跑左右 checkpoint，并形成可横向扫描的 JSON/CSV/Markdown/HTML 对比报告？
多个已保存 pair batch 报告之间，哪些 case 的相等状态或长度 delta 变化最大？
pair batch 和 trend 报告能否从 dashboard/playground 一处打开？
多个 run 的 pair batch 和 trend 报告能否从 registry 一处扫描和打开？
多个 run 里哪些 prompt case 的左右 checkpoint 生成长度差异最大？
```

当前评估主线：

```text
eval prompts
 -> benchmark prompt metadata
 -> dataset version manifest
 -> eval suite JSON/CSV/SVG/HTML
 -> generation quality analysis
 -> registry / dashboard / playground artifact links
 -> baseline model comparison
 -> local inference safety profile
 -> checkpoint selector
 -> checkpoint comparison shortcuts
 -> side-by-side generation
 -> pair generation artifacts
 -> fixed prompt pair batch comparison
 -> pair batch trend comparison
 -> pair batch dashboard/playground links
 -> registry pair report links
 -> registry pair delta leaders
```

## 后续讲解索引

```text
50-v35-benchmark-eval-suite.md
 -> 第三十五版代码讲解：把 fixed prompt eval suite 升级成带任务类型、难度、预期行为和 HTML 报告的 benchmark prompt suite
51-v36-dataset-versioning.md
 -> 第三十六版代码讲解：给 prepared corpus 增加 dataset id、version manifest、HTML 报告和下游 artifact 链路
52-v37-baseline-model-comparison.md
 -> 第三十七版代码讲解：给 compare_runs 增加 baseline、模型签名、loss/参数 delta、Markdown/HTML 报告和截图证据
53-v38-inference-safety-profile.md
 -> 第三十八版代码讲解：给本地推理 API 增加安全画像、model-info 端点、请求日志和浏览器验证证据
54-v39-checkpoint-selector.md
 -> 第三十九版代码讲解：给 playground server 增加 checkpoint 发现、选择、model-info 查询、生成路由和请求日志证据
55-v40-checkpoint-comparison-shortcuts.md
 -> 第四十版代码讲解：给 playground server 和页面增加 checkpoint compare endpoint、差异字段、model-info 快捷入口和选择动作
56-v41-side-by-side-generation.md
 -> 第四十一版代码讲解：给 playground server 和页面增加 generate-pair endpoint、左右 checkpoint 路由、输出对比摘要和 pair request 日志
57-v42-pair-generation-artifacts.md
 -> 第四十二版代码讲解：给 side-by-side generation 增加 `/api/generate-pair-artifact`、本地 JSON/HTML 留档、playground 保存入口和日志 artifact 路径
58-v43-pair-batch-comparison.md
 -> 第四十三版代码讲解：用固定 prompt suite 批量比较左右 checkpoint，输出 pair_generation_batch JSON/CSV/Markdown/HTML 报告
59-v44-pair-batch-trends.md
 -> 第四十四版代码讲解：读取多个 pair_generation_batch.json，输出 pair_batch_trend JSON/CSV/Markdown/HTML 趋势比较报告
60-v45-pair-batch-dashboard-links.md
 -> 第四十五版代码讲解：把 pair_generation_batch 和 pair_batch_trend 报告接入 dashboard/playground，一页查看摘要和浏览器链接
61-v46-registry-pair-report-links.md
 -> 第四十六版代码讲解：把 pair batch/trend 摘要、CSV 字段、HTML Pair Reports 列和报告链接接入 run registry
62-v47-registry-pair-delta-leaders.md
 -> 第四十七版代码讲解：把多个 run 的 pair batch case delta 聚合成 pair_delta_summary 和 Pair Delta Leaders 面板
```

v48 已经转入 `代码讲解记录_项目成熟度阶段`，本目录的评估基准阶段到 v47 收口；后续如果继续做 benchmark scoring 再按实际能力线决定是否回到本目录。

## 一句话总览

本目录记录 MiniGPT 从“证据链很完整”转向“模型能力可以被固定任务集、稳定数据版本、baseline、可选择 checkpoint、checkpoint 快速对比入口、同 prompt 双 checkpoint 生成结果比较、本地 pair artifact 留档、固定 prompt pair batch 横向比较、batch trend 跨报告比较、dashboard/playground 一处打开报告、registry 多 run 扫描报告以及跨 run pair delta 聚合”的过程。
