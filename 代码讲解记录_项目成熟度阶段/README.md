# MiniGPT 代码讲解记录_项目成熟度阶段

## 最新追加
191-v177-dashboard-section-helper-split.md
 -> v177 code explanation: split dashboard style, stats grid, artifact cards, content sections, links, images, formatting, and escaping helpers into `dashboard_sections.py`, while keeping dashboard payload building, artifact collection, write_dashboard, script usage, legacy render export, and public render entrypoint unchanged.
190-v176-benchmark-scorecard-decision-artifact-split.md
 -> v176 code explanation: split benchmark scorecard decision JSON/CSV/Markdown/HTML artifact writers into `benchmark_scorecard_decision_artifacts.py`, while keeping comparison loading, candidate evaluation, baseline exclusion, rubric threshold checks, generation-quality review items, selected-run ranking, recommendations, script usage, and old facade exports unchanged.
189-v175-promoted-training-scale-comparison-artifact-split.md
 -> v175 code explanation: split promoted training scale comparison JSON/CSV/Markdown/HTML artifact writers into `promoted_training_scale_comparison_artifacts.py`, while keeping promotion index loading, promoted-run filtering, comparison input resolution, baseline handling, blockers, recommendations, script usage, and old facade exports unchanged.
188-v174-training-scale-gate-artifact-split.md
 -> v174 code explanation: split training scale gate JSON/CSV/Markdown/HTML artifact writers into `training_scale_gate_artifacts.py`, while keeping policy profiles, plan loading, gate checks, status summaries, recommendations, workflow usage, and old facade exports unchanged.
187-v173-training-scale-run-decision-artifact-split.md
 -> v173 code explanation: split training scale run decision JSON/CSV/Markdown/HTML artifact writers into `training_scale_run_decision_artifacts.py`, while keeping candidate selection, rejection reasons, readiness thresholds, execute command construction, workflow usage, and old facade exports unchanged.

186-v172-eval-suite-artifact-split.md
 -> v172 code explanation: split eval suite JSON/CSV/SVG/HTML artifact writers into `eval_suite_artifacts.py`, while keeping prompt suite loading, prompt result construction, eval report schema, CLI usage, and old facade exports unchanged.
185-v171-server-get-route-split.md
 -> v171 code explanation: split MiniGPT server GET route dispatch into `server_routes.py`, while keeping health/checkpoints/model-info/request-history/playground/run-file GET semantics, POST generation routes, request logging, and old server facade exports unchanged.
184-v170-release-readiness-comparison-artifact-split.md
 -> v170 code explanation: split release readiness comparison JSON/CSV/delta CSV/Markdown/HTML artifact writers into `release_readiness_comparison_artifacts.py`, while keeping comparison schema, baseline override, delta logic, registry consumption, and old facade exports unchanged.
183-v169-promoted-training-scale-seed-handoff-artifact-split.md
 -> v169 code explanation: split promoted seed handoff JSON/CSV/Markdown/HTML artifact writers into `promoted_training_scale_seed_handoff_artifacts.py`, while keeping handoff schema, command execution, timeout handling, plan artifact detection, and old facade exports unchanged.
182-v168-promoted-training-scale-seed-artifact-split.md
 -> 第一百六十八版代码讲解：把 `promoted_training_scale_seed.py` 的 JSON/CSV/Markdown/HTML artifact 写出和渲染拆到 `promoted_training_scale_seed_artifacts.py`，保持 seed schema、next-plan 命令和旧 facade 导出不变。

181-v167-playground-request-history-script-split.md
 -> 第一百六十七版代码讲解：把 `playground_script.py` 里的 request-history JavaScript 片段拆到 `playground_request_history_script.py`，保持 playground HTML、请求历史查询、详情 JSON 和 CSV 导出契约不变。

180-v166-project-audit-context-split.md
 -> ????????????? `project_audit.py` ? request-history summary ? CI workflow hygiene ??/??????? `project_audit_contexts.py`??? audit schema?artifact ???CLI ? facade ?????

179-v165-training-scale-plan-artifact-split.md
 -> 第一百六十五版代码讲解：把 `training_scale_plan.py` 的 JSON/variants/CSV/Markdown/HTML artifact 写出和渲染拆到 `training_scale_plan_artifacts.py`，保持 scale plan schema、CLI、facade 导出和训练规模链路消费不变。

178-v164-server-request-history-endpoint-split.md
 -> 第一百六十四版代码讲解：把 `server.py` 的 `/api/request-history` 和 `/api/request-history-detail` HTTP endpoint 处理拆到 `server_request_history.py`，保持 request-history JSON/CSV/detail 契约和 `minigpt.server` facade 导出不变。
177-v163-benchmark-scorecard-comparison-delta-split.md
 -> 第一百六十三版代码讲解：把 `benchmark_scorecard_comparison.py` 的 run/case/group delta、summary、recommendation 和 best-run 选择拆到 `benchmark_scorecard_comparison_deltas.py`，保持比较 schema、CLI、artifact facade 和 promotion decision 消费不变。
176-v162-model-card-artifact-split.md
 -> 第一百六十二版代码讲解：把 `model_card.py` 的 JSON/Markdown/HTML artifact 写出和渲染拆到 `model_card_artifacts.py`，保持 model card schema、CLI 和旧导出不变。
175-v161-dataset-card-artifact-split.md
 -> 第一百六十一版代码讲解：把 `dataset_card.py` 的 JSON/Markdown/HTML artifact 写出和渲染拆到 `dataset_card_artifacts.py`，保持 dataset card schema、CLI 和旧导出不变。
174-v160-training-scale-promotion-artifact-split.md
 -> 第一百六十版代码讲解：把 `training_scale_promotion.py` 的 JSON/CSV/Markdown/HTML artifact 写出和渲染拆到 `training_scale_promotion_artifacts.py`，保持 promotion decision schema、CLI 和旧导出不变。
173-v159-server-http-helper-split.md
 -> 第一百五十九版代码讲解：把 `server.py` 的 JSON/text/SSE/file response、request body parsing 和 run file serving helper 拆到 `server_http.py`，保持 `create_handler()`/`run_server()` 路由行为和旧 facade 导出不变。
172-v158-release-gate-comparison-artifact-split.md
 -> 第一百五十八版代码讲解：把 release gate profile comparison 的 JSON/CSV/Markdown/HTML artifact 写出和渲染拆到 `release_gate_comparison_artifacts.py`，保留 `release_gate_comparison.py` 旧导出和比较 schema 不变。
171-v157-registry-leaderboard-split.md
 -> 第一百五十七版代码讲解：把 registry HTML 的 loss、rubric、pair delta 和 release readiness delta leaderboard 渲染拆到 `registry_leaderboards.py`，保持 `render_registry_html()` 和 registry payload 契约不变，继续降低当前最大渲染模块压力。
170-v156-server-checkpoint-split.md
 -> 第一百五十六版代码讲解：把 server contracts 的 checkpoint discovery、health、model-info 和 comparison payload 拆到 `server_checkpoints.py`，保留 `server_contracts.py`/`server.py` facade 兼容，让本地推理 checkpoint 证据链更独立。
169-v155-server-logging-split.md
 -> 第一百五十五版代码讲解：把 server 的 request-history 事件构造拆到 `server_logging.py`，保留 `server.py` facade 兼容，让 HTTP handler 更聚焦路由、响应和 append。
168-v154-release-readiness-artifact-split.md
 -> 第一百五十四版代码讲解：把 release readiness dashboard 的 JSON/Markdown/HTML 渲染写出拆到 `release_readiness_artifacts.py`，保留 `release_readiness.py` facade 兼容，并让 readiness 构建逻辑从展示输出层里解耦。
167-v153-release-bundle-artifact-split.md
 -> 第一百五十三版代码讲解：把 release bundle 的 JSON/Markdown/HTML 渲染写出拆到 `release_bundle_artifacts.py`，保留 `release_bundle.py` facade 兼容，并让 module pressure 回到 pass。

166-v152-ci-workflow-hygiene-typed-schema.md
 -> 第一百五十二版代码讲解：给 CI workflow hygiene 的 check/action/summary/report 补局部 TypedDict，并把 action major 解析从只认 `v6` 扩展到 `v6`、`v6.0.0`、`6`。

165-v151-maturity-ci-workflow-readiness-context.md
 -> 第一百五十一版代码讲解：把 registry 汇总出的 CI workflow readiness regression 接入 maturity summary，形成 maturity review 级别的 `ci-regressed` 趋势、CLI/Markdown/HTML 展示和 `c/` 证据计数对齐。

164-v150-registry-ci-workflow-readiness-regression.md
 -> 第一百五十版代码讲解：把 release readiness comparison 的 CI workflow regression 汇总进 registry，形成 dashboard -> comparison -> registry 的连续治理链。
163-v149-release-readiness-comparison-ci-workflow-deltas.md
 -> 第一百四十九版代码讲解：把 CI workflow hygiene 状态接入 release readiness comparison，比较跨版本 CI 状态、failed check delta 和 regression 建议。
162-v148-release-readiness-ci-workflow-hygiene-panel.md
 -> 第一百四十八版代码讲解：把 CI workflow hygiene evidence 从 release bundle 继续带入 release readiness dashboard，新增独立面板、summary 字段、CLI 参数，并保持 review 而非 hard block 边界。
161-v147-release-bundle-ci-workflow-hygiene-evidence.md
 -> 第一百四十七版代码讲解：把 CI workflow hygiene evidence 从 project audit 继续带入 release bundle，发布总包携带 CI workflow 状态、context 和 JSON/Markdown/HTML artifact。
160-v146-project-audit-ci-workflow-hygiene-context.md
 -> 第一百四十六版代码讲解：把 v145 的 CI workflow hygiene report 接入 project audit，作为项目治理上下文参与审计摘要、check 和输出展示。
159-v145-ci-workflow-hygiene-report.md
 -> 第一百四十五版代码讲解：把 CI workflow 的 Node 24 native action 策略做成可运行 hygiene gate，并接入 GitHub Actions 输出 JSON/CSV/Markdown/HTML 证据。
158-v144-github-actions-node24-native-actions.md
 -> 第一百四十四版代码讲解：把 CI 从 v143 的 Node 24 force flag 修正为 checkout/setup-python v6 原生 node24 action，真正消除 Node 20 target annotation。
157-v143-github-actions-node24-runtime.md
 -> 第一百四十三版代码讲解：把 GitHub Actions 显式切到 Node 24 JavaScript action runtime，并用测试守住 workflow 策略，消除 Node.js 20 deprecation 提醒。
156-v142-source-encoding-target-compatibility.md
 -> 第一百四十二版代码讲解：把 source encoding hygiene 从 BOM/语法检查推进到目标 Python 兼容性门禁，避免本地新版解释器通过而 Python 3.11 CI 失败。
155-v141-maturity-narrative-scorecard-decision.md
 -> 第一百四十一版代码讲解：把 benchmark scorecard promotion decision 接入 maturity narrative，让 selected run、status counts、review/blocker 和 flag delta 进入项目成熟度叙事。

154-v140-benchmark-scorecard-promotion-decision.md
 -> 第一百四十版代码讲解：新增 benchmark scorecard promotion decision，把 scorecard comparison 的 rubric/overall delta、case regression 和 generation-quality flag taxonomy 变化转成 promote/review/blocked 决策证据。
153-v139-benchmark-scorecard-comparison-flag-taxonomy.md
 -> 第一百三十九版代码讲解：把 benchmark scorecard 的 generation-quality flag taxonomy 接入跨 scorecard comparison，比较 total flags delta、dominant flag 变化和 worst generation case 变化，让 promotion review 能看到分数背后的问题类型漂移。
152-v138-benchmark-scorecard-flag-taxonomy.md
 -> 第一百三十八版代码讲解：把 generation quality 的 flag taxonomy 接入 benchmark scorecard，让 run 级评分入口能看到 total flags、dominant flag、worst generation case 和 flag penalty。
151-v137-generation-quality-flag-taxonomy.md
 -> 第一百三十七版代码讲解：给 generation quality 增加 flag taxonomy，汇总问题类型、严重级别、最差样本和 dominant flag，让生成质量证据从粗粒度状态推进到可追踪弱项诊断。
150-v136-generation-quality-artifact-split.md
 -> 第一百三十六版代码讲解：把 generation quality 的 JSON/CSV/Markdown/SVG/HTML 输出写入层拆成 artifact 模块，保留 metrics/flags/summary、旧 facade 和脚本调用方式。
149-v135-release-gate-artifact-split.md
 -> 第一百三十五版代码讲解：把 release gate 的 JSON/Markdown/HTML 输出写入层拆成 artifact 模块，保留 policy/check/summary、旧 facade 和脚本调用方式。
148-v134-maturity-narrative-artifact-split.md
 -> 第一百三十四版代码讲解：把 maturity narrative 的 JSON/Markdown/HTML 输出写入层拆成 artifact 模块，保留 narrative summary/sections/evidence matrix、旧 facade 和脚本调用方式。
147-v133-registry-ranking-split.md
 -> 第一百三十三版代码讲解：把 registry 的 loss/rubric leaderboard、pair delta、release readiness delta 聚合拆成 ranking 模块，保留 registry schema 和 facade。
146-v132-training-portfolio-artifact-split.md
 -> 第一百三十二版代码讲解：把 training portfolio 的输出写入层拆成 artifact 模块，保留 pipeline planning、dry-run/execute 状态、旧 facade 和脚本调用方式。
145-v131-project-audit-artifact-split.md
 -> 第一百三十一版代码讲解：把 project audit 的输出写入层拆成 artifact 模块，保留旧 facade、schema、审计评分和脚本调用方式。
144-v129-v130-artifact-splits.md
 -> 第一百二十九/一百三十版合并代码讲解：把 training portfolio batch 与 experiment card 的输出写入层拆成 artifact 模块，保留旧 facade、schema 和脚本调用方式。
143-v128-registry-artifact-split.md
 -> 第一百二十八版代码讲解：把 registry 输出写入层从 renderer 中拆到独立 artifact 模块，保留旧 facade 和 HTML 交互，但让 registry_render 更专注于渲染逻辑。

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
107-v92-training-scale-workflow-report-utils.md
108-v93-training-scale-promotion-report-utils.md
109-v94-training-scale-promotion-index-report-utils.md
110-v95-promoted-training-scale-comparison-report-utils.md
111-v96-generation-quality-report-utils.md
112-v97-release-bundle-report-utils.md
113-v98-readme-maturity-summary.md
114-v99-project-audit-report-utils.md
115-v100-model-card-report-utils.md
116-v101-experiment-card-report-utils.md
117-v102-dataset-card-report-utils.md
118-v103-run-manifest-report-utils.md
119-v104-data-prep-report-utils.md
120-v105-data-quality-report-utils.md
121-v106-release-readiness-report-utils.md
122-v107-release-readiness-comparison-report-utils.md
123-v108-release-governance-batch-report-utils.md
124-v109-maintenance-batching-policy.md
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

截至 v108，项目已经具备从 MiniGPT 模型学习、数据治理、实验复现、评估基准、pair/report 证据链、registry 多 run 索引、发布治理、项目成熟度总结、benchmark scorecard drilldown、rubric-style correctness scoring、registry-level rubric tracking、cross-run scorecard comparison、dataset cards、本地流式推理、流式超时与取消控制、本地推理请求历史视图、请求历史过滤和 CSV 导出、请求历史单条详情 JSON、请求历史稳定性摘要和成熟度上下文集成、请求历史审计门禁和 release evidence 集成，到发布就绪总览 dashboard、跨版本 release readiness comparison、registry-level release readiness tracking、maturity release readiness trend context、release-quality maturity narrative、training portfolio pipeline、training portfolio comparison、training portfolio batch matrix、training scale planner、training scale gate、gated training scale run、training scale run comparison、training scale run decision、consolidated training scale workflow、controlled training scale handoff、training scale promotion acceptance、training scale promotion index、promoted training scale comparison、promoted training scale baseline decision、promoted training scale next-cycle seed、promoted training scale seed handoff、shared report utility consolidation、controlled handoff report-utils migration、promoted seed report-utils migration、promoted decision report-utils migration、run decision report-utils migration、run comparison report-utils migration、gated run report-utils migration、training scale gate report-utils migration、training scale plan report-utils migration、training scale workflow report-utils migration、training scale promotion report-utils migration、training scale promotion index report-utils migration、promoted training scale comparison report-utils migration、generation quality report-utils migration、release bundle report-utils migration、README maturity summary cleanup、project audit report-utils migration、model card report-utils migration、experiment card report-utils migration、dataset card report-utils migration、run manifest report-utils migration、data preparation report-utils migration、data quality report-utils migration、release readiness report-utils migration、release readiness comparison report-utils migration 与 batched release governance report-utils migration 的完整学习型 AI 工程链路。

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
v92 的关键变化是：把 consolidated training scale workflow 迁移到 `report_utils`，让 v75 的总入口 evidence 也复用公共 JSON 写出、Markdown/HTML 转义和 list/dict 归一化工具。
v93 的关键变化是：把 training scale promotion acceptance 迁移到 `report_utils`，让 v77 的验收层 evidence 也复用公共 JSON 写出、Markdown/HTML 转义和 list/dict 归一化工具。
v94 的关键变化是：把 training scale promotion index 迁移到 `report_utils`，让 v78 的 promoted-only 索引层 evidence 也复用公共 JSON 写出、Markdown/HTML 转义和 list/dict 归一化工具。
v95 的关键变化是：把 promoted training scale comparison 迁移到 `report_utils`，让 v79 的 promoted-only comparison evidence 也复用公共 JSON 写出、Markdown/HTML 转义和 list/dict 归一化工具。
v96 的关键变化是：把 generation quality 迁移到 `report_utils`，但只迁移语义一致的 JSON 写出、UTC 时间、HTML/SVG 转义和 list/dict 归一化工具，保留本模块特有的 Markdown/字符串格式化规则。
v97 的关键变化是：把 release bundle 迁移到 `report_utils`，但只迁移语义一致的 JSON 写出、UTC 时间、HTML 转义和 list/dict 归一化工具，保留发布总包特有的 Markdown/大小/排名格式化规则。
v98 的关键变化是：不继续新增一层报告，而是把 README 开头从冗长功能流水账收束为成熟度矩阵、能力地图和后续压力点，方便从项目成熟度角度快速评估。
v99 的关键变化是：把 project audit 迁移到 `report_utils`，让 release bundle 的上游审计层也复用公共 JSON 写出、UTC 时间、HTML 转义和 list/dict 归一化工具，但不改变审计评分和发布判断。
v100 的关键变化是：把 model card 迁移到 `report_utils`，让 project audit 的上游模型说明层也复用公共 JSON 写出、UTC 时间、HTML 转义和 list/dict 归一化工具，但不改变模型卡内容和展示语义。
v101 的关键变化是：把 experiment card 迁移到 `report_utils`，让 model card 的上游单 run 说明层也复用公共 JSON 写出、UTC 时间、HTML 转义和 dict 归一化工具，但不改变单次实验卡内容和展示语义。
v102 的关键变化是：把 dataset card 迁移到 `report_utils`，让 experiment card 的上游数据说明层也复用公共 JSON 写出、UTC 时间、HTML 转义和 dict 归一化工具，但不改变数据卡内容和展示语义。
v103 的关键变化是：把 run manifest 迁移到 `report_utils`，让训练复现清单也复用公共 JSON 写出、UTC 时间和 HTML 转义工具，但不改变清单字段、artifact digest 和 SVG 展示语义。
v104 的关键变化是：把 data preparation 迁移到 `report_utils`，让 prepared corpus、dataset report、dataset version 这条数据准备链也复用公共 JSON 写出、UTC 时间、HTML 转义和 dict 归一化工具，但不改变文本归一化、source discovery、质量报告交接和展示语义。
v105 的关键变化是：把 data quality 迁移到 `report_utils`，让 dataset_quality JSON/SVG 证据也复用公共 JSON 写出和 HTML 转义工具，但不改变质量判断、issue 字段、重复源检测和重复行检测语义。
v106 的关键变化是：把 release readiness dashboard 迁移到 `report_utils`，让发布就绪总览也复用公共 JSON 写出、UTC 时间、HTML 转义和 dict/list 归一化工具，但不改变 ready/review/blocked/incomplete 判断、panel/action 语义和证据表展示。
v107 的关键变化是：把 release readiness comparison 迁移到 `report_utils`，让跨版本发布就绪对比也复用公共 JSON 写出、UTC 时间、HTML 转义、dict/list 归一化和 CSV cell 工具，但不改变 baseline override、status delta、panel delta 和 recommendation 语义。
v108 的关键变化是：把 release gate、release gate profile comparison 和 request history summary 合并迁移到 `report_utils`，让低风险同类 utils migration 不再一模块一版本，同时保持 gate policy、profile delta 和 request-history summary 语义不变。
v109 的关键变化是：新增 maintenance batching policy，把“utils migration 版本拆得过细”的质量判断落成可运行检查，要求相关低风险维护项合并成批量版本，高风险行为、服务、契约、UI 或大模块变化继续单独收口。

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
107-v92-training-scale-workflow-report-utils.md
 -> 第九十二版代码讲解：把 consolidated training scale workflow 迁移到 report_utils，让 plan、gate、run、comparison、decision、workflow 六层训练规模证据共用报告基础层
108-v93-training-scale-promotion-report-utils.md
 -> 第九十三版代码讲解：把 training scale promotion acceptance 迁移到 report_utils，让执行验收层也进入公共报告基础层
109-v94-training-scale-promotion-index-report-utils.md
 -> 第九十四版代码讲解：把 training scale promotion index 迁移到 report_utils，让 promoted-only 索引层也进入公共报告基础层
110-v95-promoted-training-scale-comparison-report-utils.md
 -> 第九十五版代码讲解：把 promoted training scale comparison 迁移到 report_utils，让 promoted-only 比较层也进入公共报告基础层
111-v96-generation-quality-report-utils.md
 -> 第九十六版代码讲解：把 generation quality 迁移到 report_utils，同时保留模块特有的显示格式化 helper
112-v97-release-bundle-report-utils.md
 -> 第九十七版代码讲解：把 release bundle 迁移到 report_utils，同时保留发布总包特有的显示格式化 helper
113-v98-readme-maturity-summary.md
 -> 第九十八版代码讲解：把 README 当前版本说明从功能流水账收束为成熟度矩阵、能力地图和下一步压力点
114-v99-project-audit-report-utils.md
 -> 第九十九版代码讲解：把 project audit 迁移到 report_utils，同时保留审计层特有的显示格式化和评分语义
115-v100-model-card-report-utils.md
 -> 第一百版代码讲解：把 model card 迁移到 report_utils，同时保留模型卡特有的标签、链接、排名和展示格式化语义
116-v101-experiment-card-report-utils.md
 -> 第一百零一版代码讲解：把 experiment card 迁移到 report_utils，同时保留单 run 卡片特有的 artifact、标签、链接和展示格式化语义
117-v102-dataset-card-report-utils.md
 -> 第一百零二版代码讲解：把 dataset card 迁移到 report_utils，同时保留数据卡特有的 Markdown、列表过滤、缺失值和质量展示语义
118-v103-run-manifest-report-utils.md
 -> 第一百零三版代码讲解：把 run manifest 迁移到 report_utils，同时保留复现清单特有的 artifact digest、git 探测、持续时间和 SVG 展示语义
119-v104-data-prep-report-utils.md
 -> 第一百零四版代码讲解：把 data preparation 迁移到 report_utils，同时保留数据准备特有的 source discovery、文本归一化、fingerprint 和 dataset version 展示语义
120-v105-data-quality-report-utils.md
 -> 第一百零五版代码讲解：把 data quality 迁移到 report_utils，同时保留质量检查特有的 issue schema、阈值、重复源和重复行判断语义
121-v106-release-readiness-report-utils.md
 -> 第一百零六版代码讲解：把 release readiness dashboard 迁移到 report_utils，同时保留发布就绪总览特有的 panel、action、source resolution 和 evidence table 语义
122-v107-release-readiness-comparison-report-utils.md
 -> 第一百零七版代码讲解：把 release readiness comparison 迁移到 report_utils，同时保留跨版本发布就绪对比特有的 baseline、delta、recommendation 和输出布局语义
123-v108-release-governance-batch-report-utils.md
 -> 第一百零八版代码讲解：把 release gate、gate profile comparison 和 request history summary 合并迁移到 report_utils，同时保留发布治理特有的 policy、delta、summary 和输出语义
124-v109-maintenance-batching-policy.md
 -> 第一百零九版代码讲解：把版本粒度批评落成 maintenance batching policy，判断低风险维护是否应该合并成批量版本
125-v110-module-pressure-audit.md
 -> 第一百一十版代码讲解：把代码膨胀批评落成 module pressure audit，用 AST 和行数扫描标出需要计划性拆分的大模块
126-v111-registry-asset-split.md
 -> 第一百一十一版代码讲解：按 v110 压力报告先拆 registry 的 HTML CSS/JS 资产，降低大模块体量但不改变 registry 数据契约
127-v112-pair-artifact-split.md
 -> 第一百一十二版代码讲解：按 v110 压力报告继续拆 server 的 pair artifact 保存边界，降低服务模块体量但不改变 HTTP 推理契约
128-v113-request-history-core-split.md
 -> 第一百一十三版代码讲解：按 v110 压力报告继续拆 server 的 request-history 核心边界，降低服务模块体量但不改变请求历史 API 契约
129-v114-benchmark-scorecard-artifact-split.md
 -> 第一百一十四版代码讲解：按 v110 压力报告拆 benchmark scorecard 的 artifact 输出边界，降低评分模块体量但不改变 scorecard schema
130-v115-playground-asset-split.md
 -> 第一百一十五版代码讲解：按 v110 压力报告拆 playground 的 HTML CSS/JS 资产边界，降低 UI 模块体量但不改变 playground 静态页面和本地 API 契约
131-v116-registry-data-render-split.md
 -> 第一百一十六版代码讲解：按 v110 压力报告回到 registry 主体，把 run 数据汇总和输出渲染拆成独立模块，同时保留 `minigpt.registry` 兼容入口
132-v117-server-contract-split.md
 -> 第一百一十七版代码讲解：按 v110 压力报告继续拆 server，把安全配置、请求解析、checkpoint/model-info/health payload、SSE 和 pair payload 抽成契约模块，同时保留 `minigpt.server` 兼容入口
133-v118-benchmark-comparison-artifact-split.md
 -> 第一百一十八版代码讲解：按 v110 压力报告拆 benchmark scorecard comparison 的 artifact 输出边界，降低比较模块体量但不改变 comparison schema、CLI 和旧导出
134-v119-maintenance-policy-artifact-split.md
 -> 第一百一十九版代码讲解：按 v110 压力报告拆 maintenance policy 的 artifact 输出边界，降低维护策略模块体量但不改变 batching/module-pressure schema、CLI 和旧导出
135-v120-benchmark-scorecard-scoring-split.md
 -> 第一百二十版代码讲解：按 v110 压力报告拆 benchmark scorecard 的 scoring 边界，降低 scorecard 主模块体量但不改变 rubric 权重、drilldown 公式、schema、CLI 和旧导出
136-v121-maturity-artifact-split.md
 -> 第一百二十一版代码讲解：按 v110 压力报告拆 maturity summary 的 artifact 输出边界，降低成熟度模块体量但不改变 maturity schema、CLI 和旧导出
137-v122-training-portfolio-comparison-artifact-split.md
 -> 第一百二十二版代码讲解：按 v110 压力报告拆 training portfolio comparison 的 artifact 输出边界，降低训练组合比较模块体量但不改变 comparison schema、CLI 和旧导出
138-v123-dashboard-render-split.md
 -> 第一百二十三版代码讲解：按 v110 压力报告拆 dashboard 的 HTML 渲染边界，降低 dashboard 主模块体量但不改变 dashboard payload、CLI 和旧导出
139-v124-playground-asset-module-split.md
 -> 第一百二十四版代码讲解：按 v110 压力报告继续拆 playground_assets 的 CSS/JavaScript 资产边界，降低 facade 体量但不改 playground 静态页面、本地 API 名称和旧导出
140-v125-server-generator-split.md
 -> 第一百二十五版代码讲解：按 v110 压力报告拆 server 的 MiniGPTGenerator 推理生成边界，降低 HTTP server 体量但不改路由、SSE、日志和旧导出
```

后续继续推进时，在这里追加新的全局编号文档，或者在新的能力线目录继续拆分。

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
v92 起 consolidated training scale workflow 也接入公共工具，说明 plan -> gate -> run -> comparison -> decision -> workflow 六层训练规模证据已经共享同一套报告基础设施。
v93 起 training scale promotion acceptance 也接入公共工具，说明训练规模执行验收层开始和前置执行链路共享同一套报告基础设施。
v94 起 training scale promotion index 也接入公共工具，说明 promoted-only 索引层开始和训练规模执行验收层共享同一套报告基础设施。
v95 起 promoted training scale comparison 也接入公共工具，说明 promoted-only 索引层到比较层已经共享同一套报告基础设施。
v96 起 generation quality 也接入公共工具，说明公共报告基础层开始覆盖模型输出质量证据，同时保留局部格式化语义。
v97 起 release bundle 也接入公共工具，说明发布证据总包开始共享报告基础设施，同时保留发布层特有的格式化语义。
v98 起 README 开始把成熟度判断放在第一屏，说明项目不只积累功能，也开始主动压缩表达、突出能力边界和下一步工程压力点。
v99 起 project audit 也接入公共工具，说明发布治理链的审计上游和 release bundle 下游开始共享同一套报告基础设施。
v100 起 model card 也接入公共工具，说明从模型说明、项目审计到发布总包的治理链开始共享同一套报告基础设施。
v101 起 experiment card 也接入公共工具，说明从单 run 说明、模型说明、项目审计到发布总包的治理链开始共享同一套报告基础设施。
v102 起 dataset card 也接入公共工具，说明从数据说明、单 run 说明、模型说明、项目审计到发布总包的治理链开始共享同一套报告基础设施。
v103 起 run manifest 也接入公共工具，说明从训练复现清单、数据说明、单 run 说明到发布总包的治理链开始共享同一套报告基础设施。
v104 起 data preparation 也接入公共工具，说明从 prepared corpus、训练复现清单、数据说明、单 run 说明到发布总包的治理链开始共享同一套报告基础设施。
v105 起 data quality 也接入公共工具，说明数据质量证据、数据准备、训练复现清单、数据说明和发布总包开始共享同一套报告基础设施。
v106 起 release readiness dashboard 也接入公共工具，说明发布就绪总览和上游 release bundle、project audit、model/data/experiment/run 证据开始共享同一套报告基础设施。
v107 起 release readiness comparison 也接入公共工具，说明发布就绪总览和跨版本发布质量对比开始共享同一套报告基础设施。
v108 起同类低风险 utils migration 开始合并发布，说明项目维护节奏从“逐模块验证公共工具”转向“批量收束重复 helper，同时用代表性证据控制风险”。
v109 起项目有了 maintenance batching policy，说明后续版本推进不只看功能能否继续拆，还会检查低风险维护是否应该合并，避免版本粒度继续碎片化。
v110 起项目有了 module pressure audit，说明“代码膨胀持续”的判断不再只靠主观印象，而会先扫描模块行数、函数跨度和风险级别，再决定是否做小步、定向的拆分。
v111 起项目开始按 module pressure audit 做第一处小步拆分，把 registry HTML CSS/JS 资产抽到独立模块，证明“代码膨胀治理”可以先从展示资产边界开始，而不是直接改业务主流程。
v112 起项目把 server 里的 pair artifact 保存边界抽成独立模块，说明服务端大文件治理也可以先从证据写入和 HTML 渲染这类稳定边界开始，而不触碰 HTTP 路由和模型推理主流程。v113 起项目把 request-history 的 JSONL 读取、过滤、详情查询、query 解析和 CSV 导出抽成独立核心模块，说明服务端厚模块治理开始从展示证据层推进到本地推理日志证据链的可复用数据处理层。v114 起项目把 benchmark scorecard 的 JSON/CSV/Markdown/HTML 输出层抽成独立模块，说明评估模块也开始区分“评分计算”和“证据发布”。v115 起项目把 playground 的 CSS/JavaScript 资产抽成独立模块，说明 UI 大文件治理也优先从稳定展示资产边界开始，保留本地 API 和静态页面契约不变。v116 起项目回到 registry 主体，把 run discovery、artifact reading、leaderboard summary 和 output rendering 拆开，说明前面只拆资产的治理可以继续推进到真实数据汇总边界，同时用 facade 保留旧入口。v117 起项目继续回到 server 主体，把纯契约、payload 和 checkpoint metadata 逻辑抽成 `server_contracts.py`，说明服务端治理开始把 HTTP handler、真实生成和可复用契约分开。v118 起项目回到 benchmark scorecard comparison，把输出写入和页面渲染抽成 artifact 模块，说明评估比较链路也开始区分“比较计算”和“证据发布”。v119 起项目回到 maintenance policy 本身，把维护批处理和 module pressure 的证据输出抽成 artifact 模块，说明治理工具也开始区分“策略判断”和“证据发布”。v120 起项目继续回到 benchmark scorecard，把 case 合并、rubric 打分和 group drilldown 抽成 scoring 模块，说明评估模块开始区分“运行证据编排”和“评分计算”。v121 起项目回到 maturity summary，把 JSON/CSV/Markdown/HTML 输出和页面渲染抽成 artifact 模块，说明成熟度汇总也开始区分“成熟度/context 计算”和“证据发布”。v122 起项目回到 training portfolio comparison，把组合比较的 JSON/CSV/Markdown/HTML 输出抽成 artifact 模块，说明训练规模证据链也开始区分“比较计算”和“证据发布”。v123 起项目回到 dashboard，把 HTML/CSS 和各区块渲染抽成 render 模块，说明运行证据页面也开始区分“payload 组装”和“页面发布”。

v124 起项目继续回到 playground assets，把 CSS 与 JavaScript 分成专用模块并让 `playground_assets.py` 退为 facade，说明 UI 资产治理开始从“抽出资产”推进到“资产内部边界清晰化”。
v125 起项目回到本地推理 server，把 `MiniGPTGenerator` 抽成 `server_generator.py`，说明服务端治理进一步区分“HTTP 路由/日志/SSE 编排”和“PyTorch checkpoint/tokenizer 加载及 token 生成”。
