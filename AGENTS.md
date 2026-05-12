# Completion Cleanup Gate

## Collaboration Rule

能完成的自己做；不能做的、权限不足的、或有疑惑需要用户确认的事项，明确说明原因并让用户配合。

Before sending the final response for any task, perform a cleanup pass for files and processes created during that task.

## Code Explanation Rule

后续新增或更新 `代码讲解记录/*.md` 或 `代码讲解记录_*/*.md` 时，讲解风格要向 `D:\C\mini-kv\代码讲解记录\111-restart-recovery-evidence-v55.md` 靠齐。

代码讲解目录按阶段拆分：

- `代码讲解记录/` 保留 v1-v30 的历史讲解，45 篇不需要迁移；后续只做必要修正，不再继续堆新版本。
- 从 v31 开始，新讲解写入 `代码讲解记录_发布治理阶段/`，文件编号继续全局递增，例如 `46-v31-主题.md`。
- 如果项目进入新的大阶段，再新建同级目录 `代码讲解记录_阶段名称/`，不要回头移动旧阶段文件。

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

运行截图和解释目录按阶段拆分：

- `a/` 保留 v1-v31 的历史运行截图和解释，不迁移旧版本。
- 从 v32 开始，新的运行截图和解释写入与 `a/` 同级的 `b/`。
- 目录结构继续使用 `b/<version>/图片/` 和 `b/<version>/解释/说明.md`。
- README、代码讲解、归档说明、tag 说明里提到新版本证据时，后续默认引用 `b/<version>`。

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
