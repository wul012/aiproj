# Completion Cleanup Gate

## Four-Project Research Rules

For cross-project research, quality evaluation, and planning, use `[MODE: RESEARCH]`.
Prefer read-only inspection, evidence-backed summaries, and clear separation between facts, judgments, and recommendations.

Developer capability baseline across Node/Java/mini-kv/aiproj:

| Dimension | Rating |
|---|---|
| Architecture design | A- |
| Multi-language engineering | A |
| Test engineering | B+ |
| Output speed | S |
| Refactoring and debt management | B |
| Security and compliance awareness | A |
| Engineering discipline and restraint | C+ |

Core judgment: high-output, strong-design, multi-stack developer with good safety awareness; main growth area is knowing when to stop, refactor, and trade about 30% speed for restraint.

Evaluation rules:
- Praise speed, architecture, multi-language execution, and safety awareness, but do not overstate production readiness.
- Distinguish contract/evidence chain from live runtime integration.
- Treat large files, long names, repeated report renderers, string-based fixture checks, and delayed refactoring as real debt signals.
- Separate latest committed version from dirty working tree changes.
- Until real integration exists, describe the state as `single-project validation + cross-project contract alignment`.

aiproj-specific focus:
- aiproj is AI engineering governance, not just training scripts.
- Evaluate data cards, experiment cards, model cards, audits, release bundles, gates, promotion, and report utilities as the core engineering value.
- Model quality is educational unless stronger eval evidence exists; do not present governance tooling as proof of production model quality.

Refactoring rhythm:
- After 3-4 feature versions, prefer 1 version of contract-preserving refactor, deduplication, or test hardening.
- Split report builders, renderers, styles, artifact helpers, and validators when modules keep growing past roughly 500-800 lines.
- 写代码时不要制造难于维护的巨型代码文件；当单文件职责持续变宽、增长接近约 500-800 行、或已经影响阅读和测试定位时，要做必要拆分。

## Collaboration Rule

能完成的自己做；不能做的、权限不足的、或有疑惑需要用户确认的事项，明确说明原因并让用户配合。

完成一个版本后，如果测试、CI、清理和工作区状态都已经收口，且下一步方向能从现有证据中明确推导出来，就自动继续推进下一个最有价值版本；不要等待用户反复发送“推进”。持续推进时，默认目标是连续推进 10 个中等或较大版本；不要把很小的文档、格式、索引、单点样板改动单独算作一版，除非它修复 CI、阻断风险或完成明确交付闭环。每版应尽量把功能增量、必要拆分、去重、测试硬化和证据归档合并成正常工作量的版本，以资深工程师的判断选择当前最优路线。上下文长度本身不作为停止推进的理由；遇到 CI 失败、需求不清、风险过高、工作区无法收口、外部工具不可用或需要用户取舍时，停止新增修改并说明原因。

Before sending the final response for any task, perform a cleanup pass for files and processes created during that task.

## Code Explanation Rule

后续新增或更新 `代码讲解记录/*.md` 或 `代码讲解记录_*/*.md` 时，讲解风格要向 `D:\C\mini-kv\代码讲解记录\111-restart-recovery-evidence-v55.md` 靠齐。
当讲解内容更偏发布治理、验证清单、manifest、证据链和只读样本时，也要参考 `D:\javaproj\advanced-order-platform\代码讲解记录_生产雏形阶段\58-version-54-release-verification-manifest.md` 的写法：先交代本版目标和边界，再讲输入输出、静态证据、测试覆盖与链路角色。
当讲解内容偏生产就绪度、只读报告、上游证据聚合、路由/CLI 入口、响应模型或治理 readiness summary 时，还要参考 `D:\nodeproj\orderops-node\代码讲解记录\107-production-readiness-summary-v3-v103.md`：先写清本版目标与“不做什么”，再按入口、响应/输出模型、上游证据、核心流程、关键检查、测试与链路角色展开。
不是每个版本都必须新增代码讲解；如果只是轻量文档整理、规则分流或索引维护，可以不写版本讲解。但一旦新增或更新讲解，就必须按上述参考模式写到足够可读，不能只列文件清单。

代码讲解目录按阶段拆分：

- `代码讲解记录/` 保留 v1-v30 的历史讲解，45 篇不需要迁移；后续只做必要修正，不再继续堆新版本。
- 从 v31 开始，新讲解写入 `代码讲解记录_发布治理阶段/`，文件编号继续全局递增，例如 `46-v31-主题.md`。
- `代码讲解记录_项目成熟度阶段/` 保留 v48-v302 的成熟度、训练规模、自动化交接和 CI 回归治理讲解；目录内容已较密，后续只做必要修正，不再继续堆新版本。
- 从 v303 开始，训练治理、文档分流和后续相关讲解写入 `代码讲解记录_训练治理阶段/`，编号继续全局递增，例如 `317-v303-主题.md`。
- `代码讲解记录_训练治理阶段/` 保留 v303-v472 的训练治理、promoted seed、receipt contract 和 CI 回归治理讲解；后续只做必要修正，不再继续堆新版本。
- 从 v473 开始，模型能力、真实 tiny 训练对比、baseline/candidate 能力评估和后续能力提升相关讲解写入 `代码讲解记录_模型能力阶段/`，编号继续全局递增，例如 `487-v473-主题.md`。
- `代码讲解记录_模型能力阶段/` 保留 v473-v1097 的模型能力、baseline/candidate 和 publication receipt 讲解；目录已经过密，后续只做必要修正，不再继续堆新版本。
- 从 v1098 开始，模型治理、receipt/index/review/contract-check、文档分流、能力治理收束和后续相关讲解写入 `代码讲解记录_模型治理阶段/`，编号继续全局递增，例如 `1112-v1098-主题.md`。
- 如果项目进入新的大阶段，再新建同级目录 `代码讲解记录_阶段名称/`，不要回头移动旧阶段文件。
- 文档部分如果某个目录内容明显变多、主题开始分叉、或继续写入会降低检索效率，可以新建同级目录承接后续内容；旧目录保留历史，不回头搬迁，README 只补索引和分流说明。

具体要求：

- 开头先说明本版目标、它解决什么问题，以及明确不做什么。
- 写清楚本版来自哪条路线或前置能力，能关联计划文档、上一版能力或上下游产物时要写出来。
- 列出关键新增/修改文件，并解释每个文件在链路里的角色。
- 不只写功能清单，要解释核心数据结构、核心函数、字段语义、输入输出格式和运行流程。
- 对 JSON/HTML/SVG/fixture/report 等产物，要说明它们是不是最终证据、是否只读、是否用于后续模块消费。
- 测试部分要写清楚测试如何真实覆盖链路、关键断言保护了什么，而不是只写“测试通过”。
- README、脚本、截图、归档如果参与本版闭环，也要说明它们承担的证明作用。
- 末尾保留“一句话总结”，用来说明这一版把项目能力推进到了哪一层。
- 可以根据 MiniGPT 的实际内容调整章节名，但整体深度、证据链意识和边界说明要接近参考文档。

## Verification Archive Rule

Current update from v69 onward:

- `a/` keeps v1-v31 runtime screenshots and explanations.
- `b/` keeps v32-v68 runtime screenshots and explanations.
- `c/` keeps v69-v302 runtime screenshots and explanations.
- From v303 onward, new runtime screenshots and explanations go to `d/`.
- `d/` keeps v303-v472 runtime screenshots and explanations.
- From v473 onward, model-capability-stage runtime screenshots and explanations go to `e/`.
- `e/` keeps v473-v1097 runtime screenshots and explanations.
- From v1098 onward, model-governance-stage runtime screenshots and explanations go to `f/`.
- The current structure is `f/<version>/图片/` and `f/<version>/解释/说明.md`.
- README, code explanations, archive notes, and tag notes should cite `f/<version>` for v1098 and later evidence.
- Do not migrate old `a/` or `b/` evidence unless the user explicitly asks.

运行截图和解释目录按阶段拆分：

- `a/` 保留 v1-v31 的历史运行截图和解释，不迁移旧版本。
- 从 v32 开始，新的运行截图和解释写入与 `a/` 同级的 `b/`。
- 目录结构继续使用 `b/<version>/图片/` 和 `b/<version>/解释/说明.md`。
- README、代码讲解、归档说明、tag 说明里提到新版本证据时，后续默认引用 `b/<version>`。
- `c/` 保留 v69-v302 的运行截图和解释，不迁移旧版本。
- 从 v303 开始，新的运行截图和解释写入与 `a/`、`b/`、`c/` 同级的 `d/`。
- 目录结构继续使用 `d/<version>/图片/` 和 `d/<version>/解释/说明.md`。
- README、代码讲解、归档说明、tag 说明里提到 v303-v472 证据时，默认引用 `d/<version>`。
- `d/` 保留 v303-v472 的历史运行截图和解释，不迁移旧版本。
- 从 v473 开始，模型能力阶段新的运行截图和解释写入与 `a/`、`b/`、`c/`、`d/` 同级的 `e/`。
- 目录结构继续使用 `e/<version>/图片/` 和 `e/<version>/解释/说明.md`。
- README、代码讲解、归档说明、tag 说明里提到 v473 及后续证据时，默认引用 `e/<version>`。
- `e/` 保留 v473-v1097 的历史运行截图和解释，不迁移旧版本。
- 从 v1098 开始，模型治理阶段新的运行截图和解释写入与 `a/`、`b/`、`c/`、`d/`、`e/` 同级的 `f/`。
- 目录结构继续使用 `f/<version>/图片/` 和 `f/<version>/解释/说明.md`。
- README、代码讲解、归档说明、tag 说明里提到 v1098 及后续证据时，默认引用 `f/<version>`。

## Temporary Files

Delete files and folders created only for intermediate editing, conversion, rendering, testing, debugging, or validation.

Common examples to remove:

- `tmp/`, `.tmp/`, `output/tmp/`
- `test-output/`, `playwright-report/`
- `__pycache__/`, `.pytest_cache/`
- temporary render PNG/PDF files
- helper scripts created only for the task
- intermediate document files such as `*_edit.docx`, `*_editing.docx`, `*_temp.docx`, `*_converted.docx`, `*_rendered*`
- document names containing edit/temp/convert/preview words in any language, when they are clearly intermediate files

Do not delete user-provided source files, final deliverables, source code changes requested by the user, logs still needed for debugging, `.git`, Codex session/state files, or files not created during the current task.

## Background Processes

When starting any long-running process, record what it is for and, when practical, its PID, port, or terminal session.

Before final response, stop background processes started during the task unless the user explicitly needs them running.

Common examples to stop:

- training/dev preview servers
- `python -m http.server`
- Playwright browsers and test servers
- Node, Python, or MCP/debug subprocesses started only for this task

If a process must remain running, state its name, port/PID if known, and why it was kept.

## Final Response Requirement

Include a short cleanup summary when meaningful:

- files deleted
- files kept
- processes stopped
- processes intentionally left running
