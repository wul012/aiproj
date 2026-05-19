# v265 promoted decision artifact writer split

## 本版目标和边界

v265 的目标是完成 promoted decision 模块的第二段收口。v264 已经把 selected handoff review summary/recommendation helper 拆出，但 `src/minigpt/promoted_training_scale_decision.py` 仍然同时承担 baseline selection、summary assembly、recommendations 和 artifact rendering。本版把 JSON/CSV/Markdown/HTML writer 与 HTML helper 移到 `promoted_training_scale_decision_artifacts.py`。

本版不改变：

- promoted baseline 选择规则；
- rejection rules；
- `decision_status`；
- summary 字段；
- recommendations；
- `promoted_training_scale_decision.json/csv/md/html` 内容契约；
- CLI 输出。

## 前置链路

v264 先拆 review helper，因为 selected handoff suite/batch-review projection 是业务语义。v265 再拆 artifact writer，因为它是纯输出层。这样 promoted decision 主文件就从“业务 + 输出”回到“业务编排 + 兼容 re-export”。

## 关键文件

### `src/minigpt/promoted_training_scale_decision_artifacts.py`

新增 artifact 模块，负责：

- `write_promoted_training_scale_decision_json()`
- `write_promoted_training_scale_decision_csv()`
- `render_promoted_training_scale_decision_markdown()`
- `write_promoted_training_scale_decision_markdown()`
- `render_promoted_training_scale_decision_html()`
- `write_promoted_training_scale_decision_html()`
- `write_promoted_training_scale_decision_outputs()`

同时承接 `_rejected_table()`、`_list_section()`、`_style()`、`_card()` 这些只服务 HTML/Markdown 输出的 helper。

### `src/minigpt/promoted_training_scale_decision.py`

主文件现在负责：

- 加载 promoted comparison；
- 生成 promotion rows；
- 计算 rejection reasons；
- 选择 selected baseline；
- 生成 summary 和 recommendations；
- 从 artifact 模块 re-export writer/render 函数。

拆分后主文件从 600 行降到 313 行，artifact 文件为 317 行。

### 测试

原 `tests/test_promoted_training_scale_decision.py` 仍然从 `promoted_training_scale_decision` 导入 writer/render 函数，测试通过说明兼容 re-export 没有破坏旧入口。`tests/test_promoted_training_scale_decision_review.py` 继续保护 v264 拆出的 review helper。

## 输入输出

输入仍然是 promoted comparison JSON 或目录。输出仍然是：

- `promoted_training_scale_decision.json`
- `promoted_training_scale_decision.csv`
- `promoted_training_scale_decision.md`
- `promoted_training_scale_decision.html`

本版没有新增字段，只移动 writer/render 的实现位置。

## 测试覆盖

- 聚焦测试运行 promoted decision 主流程和 decision review helper 测试。
- contract smoke 写出 JSON/CSV/Markdown/HTML，并检查 artifact 文件都存在、Markdown/HTML 包含原关键内容、主文件行数降低到 313。
- 全量 unittest 确认其他治理链路未受影响。
- source encoding 检查确认新文件没有 BOM、不可打印字符或语法错误。

## 证据归档

运行截图和解释归档在 `c/265`：

- `c/265/图片/01-focused-tests.png`
- `c/265/图片/02-contract-smoke.png`
- `c/265/图片/03-full-unittest.png`
- `c/265/图片/04-source-encoding.png`
- `c/265/图片/05-docs-check.png`
- `c/265/解释/说明.md`

## 一句话总结

v265 把 promoted decision 的 artifact writer 从 baseline decision builder 拆出，让主文件从 600 行降到 313 行，同时保留旧导入入口和输出契约。
