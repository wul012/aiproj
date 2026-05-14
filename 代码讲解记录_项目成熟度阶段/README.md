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
72-v57-request-history-view.md
73-v58-request-history-filters-export.md
74-v59-request-history-detail-json.md
75-v60-request-history-summary-context.md
76-v61-request-history-audit-gates.md
77-v62-release-readiness-dashboard.md
78-v63-release-readiness-comparison.md
79-v64-registry-release-readiness-tracking.md
80-v65-maturity-release-readiness-trend.md
81-v66-maturity-narrative.md
82-v67-training-portfolio-pipeline.md
83-v68-training-portfolio-comparison.md
84-v69-training-portfolio-batch.md
85-v70-training-scale-plan.md
86-v71-training-scale-gate.md
87-v72-gated-training-scale-run.md
88-v73-training-scale-run-comparison.md
89-v74-training-scale-run-decision.md
90-v75-training-scale-workflow.md
91-v76-training-scale-handoff.md
92-v77-training-scale-promotion.md
93-v78-training-scale-promotion-index.md
94-v79-promoted-training-scale-comparison.md
95-v80-promoted-training-scale-decision.md
96-v81-promoted-training-scale-seed.md
97-v82-promoted-training-scale-seed-handoff.md
98-v83-report-utils-consolidation.md
99-v84-controlled-handoff-report-utils.md
100-v85-promoted-seed-report-utils.md
101-v86-promoted-decision-report-utils.md
102-v87-run-decision-report-utils.md
103-v88-run-comparison-report-utils.md
104-v89-gated-run-report-utils.md
105-v90-training-scale-gate-report-utils.md
106-v91-training-scale-plan-report-utils.md
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

截至 v91，项目已经具备从 MiniGPT 模型学习、数据治理、实验复现、评估基准、pair/report 证据链、registry 多 run 索引、发布治理、项目成熟度总结、benchmark scorecard drilldown、rubric-style correctness scoring、registry-level rubric tracking、cross-run scorecard comparison、dataset cards、本地流式推理、流式超时与取消控制、本地推理请求历史视图、请求历史过滤和 CSV 导出、请求历史单条详情 JSON、请求历史稳定性摘要和成熟度上下文集成、请求历史审计门禁和 release evidence 集成，到发布就绪总览 dashboard、跨版本 release readiness comparison、registry-level release readiness tracking、maturity release readiness trend context、release-quality maturity narrative、training portfolio pipeline、training portfolio comparison、training portfolio batch matrix、training scale planner、training scale gate、gated training scale run、training scale run comparison、training scale run decision、consolidated training scale workflow、controlled training scale handoff、training scale promotion acceptance、training scale promotion index、promoted training scale comparison、promoted training scale baseline decision、promoted training scale next-cycle seed、promoted training scale seed handoff、shared report utility consolidation、controlled handoff report-utils migration、promoted seed report-utils migration、promoted decision report-utils migration、run decision report-utils migration、run comparison report-utils migration、gated run report-utils migration、training scale gate report-utils migration 与 training scale plan report-utils migration 的完整学习型 AI 工程链路。

v48 的关键变化是：不继续拆 `links/trends/dashboard`，而是把 v1-v48 汇总为 capability matrix、phase timeline、registry context 和 recommendations。

v49 的关键变化是：把 eval suite、generation quality、pair consistency、pair delta stability、evidence completeness 和 registry context 汇总为一个可评分、可导出、可截图的 benchmark scorecard。

v50 的关键变化是：不只给 run 一个总分，还按 task type 和 difficulty 输出 drilldown 分数、最弱分组和独立 CSV，让 benchmark 短板能定位到任务切片。

v51 的关键变化是：给每个 prompt 增加 rubric-style correctness scoring，记录 required/forbidden terms、长度、任务形态、最弱 case 和 rubric CSV，让 benchmark 不只看输出形状，也能表达基本正确性。

v52 的关键变化是：把 v51 的 rubric 正确性分数带入 run registry，输出 rubric leaderboard、regression summary、CSV 字段、HTML Rubric 列和 scorecard 链接。

v53 的关键变化是：读取多个 benchmark scorecard，对照 baseline 解释 overall/rubric 分数变化、case 级 rubric 退化、task type 和 difficulty 分组变化。

v54 的关键变化是：读取 dataset version、dataset report 和 dataset quality，生成面向人的 dataset card，说明数据身份、来源、预期用途、限制、质量状态、证据产物和建议。

v55 的关键变化是：把 MiniGPT 的生成循环拆出 `sample_next`，新增 `/api/generate-stream` SSE 端点，并让 playground 通过 `Stream Generate` 按钮逐 token 更新输出。

v56 的关键变化是：给流式生成增加 `max_stream_seconds` 超时边界、`timeout` SSE 事件、超时/取消日志字段，并在 playground 里加入 `Stop` 取消按钮。

v57 的关键变化是：读取 `inference_requests.jsonl`，新增 `/api/request-history`，把普通生成、流式生成、超时、取消和 pair 请求归一成最近请求列表，并在 playground 里加入 Request History 表格。

v58 的关键变化是：给 `/api/request-history` 增加 `status`、`endpoint`、`checkpoint` 过滤和 `format=csv` 导出，并在 playground 里加入筛选控件和 Export CSV 链接。
v59 的关键变化是：给每条有效请求日志分配可见 `log_index`，新增 `/api/request-history-detail?log_index=N`，并在 playground 的 Request History 表格里加入 Details 按钮和 JSON 链接。
v60 的关键变化是：新增 request history summary 产物，把 JSONL 请求日志聚合成状态/端点/checkpoint 计数、timeout/bad_request/error rate、最近请求和建议，并让 maturity summary 读取这份上下文。
v61 的关键变化是：让 project audit 读取 request history summary，release bundle 把它列为证据 artifact，standard/review/strict release gate 默认要求 `request_history_summary` 审计检查，legacy profile 继续兼容旧 bundle。
v62 的关键变化是：新增 release readiness dashboard，把 registry、release bundle、project audit、release gate、request history summary 和 maturity summary 汇总为一个 JSON/Markdown/HTML 就绪总览。
v63 的关键变化是：读取多个 `release_readiness.json`，以默认首个输入或 `--baseline` 指定文件作为基线，输出 JSON/CSV/delta CSV/Markdown/HTML 比较报告，解释 readiness 状态、panel、audit score 和缺失 artifact 的跨版本变化。
v64 的关键变化是：让 run registry 读取每个 run 下的 `release-readiness-comparison/release_readiness_comparison.json`，记录 improved/regressed/panel-changed 计数、delta summary、delta leaderboard、CSV 字段和 HTML Release Readiness Deltas 面板。
v65 的关键变化是：让 project maturity summary 读取 registry 的 release readiness trend context，输出 Release Readiness Trend Context，并在发现 release readiness regression 时把 maturity overall status 降为 `warn`。
v66 的关键变化是：新增 release-quality maturity narrative，读取 maturity summary、registry、request history summary、benchmark scorecard 和 dataset card，把分散证据合成一份面向 portfolio/答辩/交接的 JSON/Markdown/HTML 叙事报告。
v67 的关键变化是：新增 training portfolio pipeline，把 prepare dataset、train、eval suite、generation quality、benchmark scorecard、dataset card、registry、maturity summary 和 maturity narrative 串成可 dry-run 或 execute 的端到端训练组合跑。
v68 的关键变化是：新增 training portfolio comparison，读取多份 `training_portfolio.json` 及其链接的 scorecard、dataset card、manifest、eval suite、generation quality 和 maturity narrative，输出相对 baseline 的 JSON/CSV/Markdown/HTML 对比证据。
v69 的关键变化是：新增 training portfolio batch matrix，把多个训练 variant 组织成批量计划/执行入口，每个 variant 生成自己的 portfolio 报告，并自动接入 v68 的 portfolio comparison。
v70 的关键变化是：新增 training scale planner，在执行更大语料训练前先扫描语料规模、质量状态和 token budget，生成可直接交给 v69 batch runner 的 `training_scale_variants.json`。
v71 的关键变化是：新增 training scale gate，读取 v70 `training_scale_plan.json`，用 review/standard/strict profile 检查语料规模、质量警告、baseline、variant、token budget 和 corpus pass 是否适合执行。
v72 的关键变化是：新增 gated training scale run，把 v70 scale plan、v71 gate 和 v69 batch runner 串成受控启动链路，gate 未允许时不会写 batch 产物。
v73 的关键变化是：新增 training scale run comparison，比较多份 `training_scale_run.json`，解释哪些 run 被 gate 放行、阻止、警告或成功进入 batch。
v74 的关键变化是：新增 training scale run decision，读取 v73 comparison，选择下一次最适合进入 `--execute` 的 run，并记录被拒绝候选和原因。
v75 的关键变化是：新增 consolidated training scale workflow，把 v70-v74 的 plan、profile run、comparison 和 decision 收口为一个入口与一组总览产物。
v76 的关键变化是：新增 controlled training scale handoff，读取 v75 workflow decision，默认验证 handoff，显式 `--execute` 时才运行选中的训练命令并记录真实执行证据；同时修正 tiny corpus 训练规模计划的 `block_size`，避免默认 90/10 split 后验证集 token 数不足。
v77 的关键变化是：新增 training scale promotion acceptance，读取完成的 handoff、gated scale run、batch 和 per-variant portfolio 产物，判断本次训练结果是 `promoted`、`review` 还是 `blocked`。
v78 的关键变化是：新增 training scale promotion index，读取一个或多个 promotion 报告，筛出可比较的 promoted 结果，并生成后续 compare 脚本可直接消费的输入列表与命令。
v79 的关键变化是：新增 promoted training scale comparison，读取 v78 index，只比较 promoted 结果，并在 promoted 输入不足或 baseline 不合法时输出 blocked 报告。
v80 的关键变化是：新增 promoted training scale baseline decision，读取 v79 promoted comparison，选择下一阶段稳定 baseline，并在上游比较不完整或候选不合格时输出 blocked/review。
v81 的关键变化是：新增 promoted training scale next-cycle seed，读取 v80 baseline decision 和下一轮语料来源，输出下一阶段的 training-scale plan 命令，并在 baseline decision 或 corpus 输入不完整时保持 blocked。
v82 的关键变化是：新增 promoted training scale seed handoff，读取 v81 seed，默认验证下一轮 plan 命令，显式 `--execute` 时生成 training scale plan 产物，并暴露后续 batch command。
v83 的关键变化是：不继续新拆一层报告，而是新增 shared report utility，把 artifact row、JSON/CSV 写出、命令展示、Markdown/HTML 转义和 list/dict 归一化收口，并先迁移 v82 handoff 验证这条公共层。
v84 的关键变化是：把原始 controlled training scale handoff 迁移为 `report_utils` 的第二个消费者，证明公共层不仅能服务 promoted seed handoff，也能服务 workflow execution handoff。
v85 的关键变化是：把 promoted training scale next-cycle seed 迁移为 `report_utils` 的第三个消费者，让 seed、seed handoff 和 execution handoff 共用同一套报告基础工具。
v86 的关键变化是：把 promoted training scale baseline decision 迁移为 `report_utils` 的第四个消费者，让 baseline decision、seed、seed handoff 和 controlled execution handoff 形成连续的公共报告基础层。
v87 的关键变化是：把 training scale run decision 迁移到 `report_utils`，让 v74 的 execute-candidate selector 也复用公共输出、命令展示和转义工具。
v88 的关键变化是：把 training scale run comparison 迁移到 `report_utils`，让 v73 的 gated-run comparison 也复用公共输出、Markdown/HTML 转义和 list/dict 归一化工具。
v89 的关键变化是：把 gated training scale run 迁移到 `report_utils`，让 v72 的 gate-to-batch handoff report 也复用公共 JSON/CSV 写出和渲染基础工具。
v90 的关键变化是：把 training scale gate 迁移到 `report_utils`，让 v71 的 profile gate 也复用公共 JSON 写出、CSV cell、命令展示和转义工具。
v91 的关键变化是：把 training scale planner 迁移到 `report_utils`，让 v70 的 corpus-scale planning evidence 也复用公共 JSON 写出、命令展示、Markdown/HTML 转义和 list/dict 归一化工具。

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
72-v57-request-history-view.md
 -> 第五十七版代码讲解：把本地推理 JSONL 日志整理成 `/api/request-history` 和 playground 请求历史视图
73-v58-request-history-filters-export.md
 -> 第五十八版代码讲解：给本地推理请求历史增加过滤、匹配计数和 CSV 导出
74-v59-request-history-detail-json.md
 -> 第五十九版代码讲解：给请求历史增加可追溯行号、单条详情 API、raw/normalized JSON 和 playground 行级详情动作
75-v60-request-history-summary-context.md
 -> 第六十版代码讲解：把请求历史从单条追溯推进到稳定性摘要产物，并接入项目成熟度上下文
76-v61-request-history-audit-gates.md
 -> 第六十一版代码讲解：把请求历史稳定性摘要接入 project audit、release bundle 和 release gate policy
77-v62-release-readiness-dashboard.md
 -> 第六十二版代码讲解：把分散的 registry、audit、bundle、gate、request history 和 maturity 证据汇总为发布就绪 dashboard
78-v63-release-readiness-comparison.md
 -> 第六十三版代码讲解：比较多个 release readiness dashboard，解释相对 baseline 的改善、退化和 panel 变化
79-v64-registry-release-readiness-tracking.md
 -> 第六十四版代码讲解：把 release readiness comparison 接入 registry，让发布质量趋势和实验质量证据一起索引
80-v65-maturity-release-readiness-trend.md
 -> 第六十五版代码讲解：把 registry 中的 release readiness trend 接入 maturity summary，让发布质量历史参与成熟度评审
81-v66-maturity-narrative.md
 -> 第六十六版代码讲解：把成熟度、发布趋势、请求历史、benchmark scorecard 和 dataset card 合成为 release-quality maturity narrative
82-v67-training-portfolio-pipeline.md
 -> 第六十七版代码讲解：把数据准备、真实训练、评估、质量分析、scorecard、数据卡和成熟度叙事串成可执行训练组合跑
83-v68-training-portfolio-comparison.md
 -> 第六十八版代码讲解：比较多份 training portfolio，解释相对 baseline 的模型分数、验证损失、产物覆盖、数据警告和成熟度变化
84-v69-training-portfolio-batch.md
 -> 第六十九版代码讲解：把多组训练参数组织成 batch matrix，生成每个 portfolio 并自动接入基线对比
85-v70-training-scale-plan.md
 -> 第七十版代码讲解：训练前扫描语料规模和质量，输出 batch 兼容的训练规模规划和 variants JSON
86-v71-training-scale-gate.md
 -> 第七十一版代码讲解：在执行 batch 前对训练规模规划做准入检查，输出 pass/warn/fail gate 证据
87-v72-gated-training-scale-run.md
 -> 第七十二版代码讲解：把 scale plan 先过 gate，再在允许时交给 batch runner 生成 dry-run 或执行产物
88-v73-training-scale-run-comparison.md
 -> 第七十三版代码讲解：比较多次 gated scale run，解释 allowed/blocked、gate 状态和 batch 是否启动的差异
89-v74-training-scale-run-decision.md
 -> 第七十四版代码讲解：从 comparison 中选择可执行候选，输出 rejected reasons 和下一步 `--execute` 命令
90-v75-training-scale-workflow.md
 -> 第七十五版代码讲解：把 v70-v74 训练规模治理链收口为统一 workflow 入口和总览报告
91-v76-training-scale-handoff.md
 -> 第七十六版代码讲解：把 workflow 选中的执行命令变成可验证、可执行、可记录产物状态的 handoff
92-v77-training-scale-promotion.md
 -> 第七十七版代码讲解：把完成的 handoff 结果验收为 promoted/review/blocked，承接后续 registry、maturity 和对比链路
93-v78-training-scale-promotion-index.md
 -> 第七十八版代码讲解：把多个 promotion 报告收口成 compare-ready 索引，只让 promoted 结果进入后续训练规模对比
94-v79-promoted-training-scale-comparison.md
 -> 第七十九版代码讲解：读取 promotion index 并复用 training scale run comparison，只比较 promoted 运行
95-v80-promoted-training-scale-decision.md
 -> 第八十版代码讲解：读取 promoted comparison，选出下一阶段稳定 promoted baseline，并保留 blocked/review 边界
96-v81-promoted-training-scale-seed.md
 -> 第八十一版代码讲解：读取 promoted baseline decision 和下一轮语料来源，生成下一阶段 training-scale plan 命令并保留阻断边界
97-v82-promoted-training-scale-seed-handoff.md
 -> 第八十二版代码讲解：读取 next-cycle seed，验证或执行 plan 命令，记录 plan 产物和后续 batch command
98-v83-report-utils-consolidation.md
 -> 第八十三版代码讲解：把近期重复的报告小工具收口为 report_utils，并迁移 promoted seed handoff 作为低风险验证点
99-v84-controlled-handoff-report-utils.md
 -> 第八十四版代码讲解：把 controlled training scale handoff 迁移到 report_utils，减少私有 helper 并保持执行证据格式不变
100-v85-promoted-seed-report-utils.md
 -> 第八十五版代码讲解：把 promoted next-cycle seed 迁移到 report_utils，让 seed generation 与两个 handoff 模块共享报告基础层
101-v86-promoted-decision-report-utils.md
 -> 第八十六版代码讲解：把 promoted baseline decision 迁移到 report_utils，让 baseline selector 也复用公共输出和转义工具
102-v87-run-decision-report-utils.md
 -> 第八十七版代码讲解：把 training scale run decision 迁移到 report_utils，让原始训练规模执行候选决策也复用公共报告基础层
103-v88-run-comparison-report-utils.md
 -> 第八十八版代码讲解：把 training scale run comparison 迁移到 report_utils，让 comparison evidence 和 decision evidence 共用报告基础层
104-v89-gated-run-report-utils.md
 -> 第八十九版代码讲解：把 gated training scale run 迁移到 report_utils，让 run、comparison、decision 三层训练规模证据共用报告基础层
105-v90-training-scale-gate-report-utils.md
 -> 第九十版代码讲解：把 training scale gate 迁移到 report_utils，让 gate、run、comparison、decision 四层训练规模证据共用报告基础层
106-v91-training-scale-plan-report-utils.md
 -> 第九十一版代码讲解：把 training scale planner 迁移到 report_utils，让 plan、gate、run、comparison、decision 五层训练规模证据共用报告基础层
```

后续继续推进时，在这里追加 `107-v92-主题.md`，或者在新的能力线目录继续拆分。

## 一句话总览

本目录记录 MiniGPT 从“证据链越来越完整”转向“能解释项目成熟度、短板、benchmark 分数、分组弱项、prompt 正确性、多 run 正确性退化、跨 run scorecard 变化原因、数据卡、本地流式推理、流式推理硬化、请求历史可追溯、请求历史可筛选导出、请求历史单条详情 JSON、请求历史稳定性摘要、请求历史审计门禁、发布就绪 dashboard、release-quality maturity narrative、training portfolio pipeline、training portfolio comparison、training portfolio batch matrix、training scale planner、training scale gate、gated training scale run、training scale run comparison、training scale run decision、consolidated training scale workflow、controlled training scale handoff、training scale promotion acceptance、training scale promotion index、promoted training scale comparison、promoted training scale baseline decision 和下一阶段路线”的过程。
v81 起还会把 promoted baseline 再往前推进到 next-cycle seed，让下一轮训练规模规划能直接消费上一步的决策结果。
v82 起会把 seed 里的 plan 命令落成可审计的 plan 产物，让下一轮 batch command 也能作为证据继续传递。
v83 起开始把重复报告基础设施收口为公共工具，后续版本要优先复用公共层，而不是继续复制私有 helper。
v84 起公共工具不再只是新模块的实验点，而开始回收早期 handoff 模块的重复实现。
v85 起 promoted seed generation 也接入公共工具，说明这条收口线已经覆盖“生成 seed -> 执行 seed handoff -> controlled execution handoff”的连续链路。
v86 起 baseline decision 也接入公共工具，说明这条收口线已经向 seed 上游继续延伸。
v87 起原始 training scale run decision 也接入公共工具，说明收口线开始回到 promoted 链路之前的基础训练规模决策层。
v88 起原始 training scale run comparison 也接入公共工具，说明 comparison evidence 到 decision evidence 的相邻两层已经共享同一套报告基础设施。
v89 起 gated training scale run 也接入公共工具，说明 run -> comparison -> decision 三层训练规模证据已经共享同一套报告基础设施。
v90 起 training scale gate 也接入公共工具，说明 gate -> run -> comparison -> decision 四层训练规模证据已经共享同一套报告基础设施。
v91 起 training scale planner 也接入公共工具，说明 plan -> gate -> run -> comparison -> decision 五层训练规模证据已经共享同一套报告基础设施。
