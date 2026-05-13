# MiniGPT 代码讲解记录_项目成熟度阶段

本目录从 v48 开始记录 MiniGPT 的“项目成熟度阶段”。前一阶段 `代码讲解记录_评估基准阶段` 已经把 v35-v47 的 benchmark、dataset version、baseline comparison、本地推理边界、checkpoint/pair generation、pair batch/trend、dashboard/playground、registry links 和 pair delta leaders 收口。

从 v48 开始，重点不再是继续拆细某一种 report/link，而是回答更高一层的问题：

```text
这个 MiniGPT 学习工程目前成熟到哪一层？
哪些能力已经有证据链？
哪些能力只是教学展示，还不是生产能力？
下一步应该补 benchmark scoring、数据规模，还是服务化硬化？
已有 benchmark、generation quality、pair batch 和 registry 证据，能否合成一个 run 级评分入口？
合成总分之后，能否继续解释到 task type 和 difficulty 这两层？
分组以后，能否再解释每个 prompt 是否满足基本正确性 rubric？
单个 run 有 rubric 分之后，能否进入 registry，比较多次实验的正确性退化？
registry 能显示多 run 正确性排名之后，能否进一步解释分数为什么变了、具体退化在哪个 case？
已有 dataset version 和 quality report 之后，能否给人一张说明用途、来源、限制和质量状态的数据卡？
本地 playground 已经能同步生成之后，能否把真实 autoregressive 采样拆成可流式消费的 token 事件？
流式生成可用之后，能否补上超时边界、取消控制和可追溯日志，避免本地推理体验停在演示层？
```

## 写入规则

本阶段文档继续沿用全局编号：

```text
63-v48-maturity-summary.md
64-v49-benchmark-scorecard.md
65-v50-benchmark-scorecard-drilldowns.md
66-v51-benchmark-rubric-scoring.md
67-v52-registry-benchmark-rubric-tracking.md
68-v53-benchmark-scorecard-comparison.md
69-v54-dataset-cards.md
70-v55-streaming-generation.md
71-v56-streaming-cancel-timeout.md
```

说明文档继续向参考文档靠齐：

```text
D:\C\mini-kv\代码讲解记录\111-restart-recovery-evidence-v55.md
```

每篇要写清楚：

- 本版目标、来源、边界和不做什么。
- 本版如何总结前面阶段，而不是继续堆小功能。
- 关键文件、输入输出、字段含义和运行流程。
- JSON、CSV、Markdown、HTML、截图和归档为什么能作为证据。
- 测试覆盖哪些判断，以及失败时能拦住什么。
- 一句话总结项目成熟度推进到了哪一层。

## 当前项目进度基线

截至 v56，项目已经具备从 MiniGPT 模型学习、数据治理、实验复现、评估基准、pair/report 证据链、registry 多 run 索引、发布治理、项目成熟度总结、benchmark scorecard drilldown、rubric-style correctness scoring、registry-level rubric tracking、cross-run scorecard comparison、dataset cards、本地流式推理，到流式超时与取消控制的完整学习型 AI 工程链路。

v48 的关键变化是：不继续拆 `links/trends/dashboard`，而是把 v1-v48 汇总为 capability matrix、phase timeline、registry context 和 recommendations。

v49 的关键变化是：把 eval suite、generation quality、pair consistency、pair delta stability、evidence completeness 和 registry context 汇总为一个可评分、可导出、可截图的 benchmark scorecard。

v50 的关键变化是：不只给 run 一个总分，还按 task type 和 difficulty 输出 drilldown 分数、最弱分组和独立 CSV，让 benchmark 短板能定位到任务切片。

v51 的关键变化是：给每个 prompt 增加 rubric-style correctness scoring，记录 required/forbidden terms、长度、任务形态、最弱 case 和 rubric CSV，让 benchmark 不只看输出形状，也能表达基本正确性。

v52 的关键变化是：把 v51 的 rubric 正确性分数带入 run registry，输出 rubric leaderboard、regression summary、CSV 字段、HTML Rubric 列和 scorecard 链接。

v53 的关键变化是：读取多个 benchmark scorecard，对照 baseline 解释 overall/rubric 分数变化、case 级 rubric 退化、task type 和 difficulty 分组变化。

v54 的关键变化是：读取 dataset version、dataset report 和 dataset quality，生成面向人的 dataset card，说明数据身份、来源、预期用途、限制、质量状态、证据产物和建议。

v55 的关键变化是：把 MiniGPT 的生成循环拆出 `sample_next`，新增 `/api/generate-stream` SSE 端点，并让 playground 通过 `Stream Generate` 按钮逐 token 更新输出。

v56 的关键变化是：给流式生成增加 `max_stream_seconds` 超时边界、`timeout` SSE 事件、超时/取消日志字段，并在 playground 里加入 `Stop` 取消按钮。

## 后续讲解索引

```text
63-v48-maturity-summary.md
 -> 第四十八版代码讲解：生成项目成熟度总览，把 v1-v48 汇总为能力矩阵、阶段时间线、registry 上下文和下一步建议
64-v49-benchmark-scorecard.md
 -> 第四十九版代码讲解：生成统一 benchmark scorecard，把 run 级评估覆盖、生成质量、pair 稳定性和 registry 上下文合成一个评分报告
65-v50-benchmark-scorecard-drilldowns.md
 -> 第五十版代码讲解：给 benchmark scorecard 增加 task type / difficulty drilldown，解释总分背后的弱项分组
66-v51-benchmark-rubric-scoring.md
 -> 第五十一版代码讲解：给 benchmark scorecard 增加 per-prompt rubric scoring，把正确性检查写入 case、drilldown、summary 和导出文件
67-v52-registry-benchmark-rubric-tracking.md
 -> 第五十二版代码讲解：让 registry 读取 benchmark scorecard rubric 分数，比较多 run 正确性表现和退化
68-v53-benchmark-scorecard-comparison.md
 -> 第五十三版代码讲解：比较多个 benchmark scorecard，解释 correctness 分数变化来自哪个 run、哪个 case、哪个任务分组
69-v54-dataset-cards.md
 -> 第五十四版代码讲解：把 dataset version、quality 和 provenance 收口成数据卡，说明用途、限制、质量状态和证据产物
70-v55-streaming-generation.md
 -> 第五十五版代码讲解：把本地 playground 生成从一次性 JSON 返回推进到 Server-Sent Events 流式 token 输出
71-v56-streaming-cancel-timeout.md
 -> 第五十六版代码讲解：给流式生成增加服务端超时边界和浏览器端取消控制
```

后续继续推进时，在这里追加 `72-v57-主题.md`，或者在新的能力线目录继续拆分。

## 一句话总览

本目录记录 MiniGPT 从“证据链越来越完整”转向“能解释项目成熟度、短板、benchmark 分数、分组弱项、prompt 正确性、多 run 正确性退化、跨 run scorecard 变化原因、数据卡、本地流式推理、流式推理硬化和下一阶段路线”的过程。
