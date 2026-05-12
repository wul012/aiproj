# Completion Cleanup Gate

## Collaboration Rule

能完成的自己做；不能做的、权限不足的、或有疑惑需要用户确认的事项，明确说明原因并让用户配合。

Before sending the final response for any task, perform a cleanup pass for files and processes created during that task.

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
