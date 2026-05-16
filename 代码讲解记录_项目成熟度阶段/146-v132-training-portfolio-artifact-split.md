# v132 training portfolio artifact split 代码讲解

## 本版目标

v132 的目标是把 `training_portfolio.py` 里“训练组合流水线计划/执行”和“证据文件发布”两类职责分开。拆分后，`training_portfolio.py` 继续负责构建 pipeline plan、执行 dry-run 或真实步骤、统计 artifact 是否存在，并给出后续建议；`training_portfolio_artifacts.py` 负责把 report dict 写成 JSON、Markdown、HTML。

本版明确不做：

- 不改变 training portfolio 的 JSON schema。
- 不改变 `training_portfolio.json`、`training_portfolio.md`、`training_portfolio.html` 文件名。
- 不改变 `scripts/run_training_portfolio.py` 的 CLI 参数和 dry-run 行为。
- 不把 artifact split 解释成模型能力提升；它只提升维护边界。

## 前置路线

v132 接在 v131 之后，继续沿用 v110 以来的 pressure-guided cleanup 路线：

```text
v110 module pressure audit
 -> v129 training portfolio batch artifact split
 -> v130 experiment card artifact split
 -> v131 project audit artifact split
 -> v132 training portfolio artifact split
```

v131 收口后，维护 smoke 显示最大模块变成 `training_portfolio.py`，且 module pressure 仍为 pass。因此 v132 不是大重构，而是在清晰边界存在时做一个小拆分：把输出层迁出，同时保留旧 facade。

## 关键文件

- `src/minigpt/training_portfolio.py`: 保留 `build_training_portfolio_plan()`、`run_training_portfolio_plan()`、步骤执行、artifact availability 检查和 recommendations。
- `src/minigpt/training_portfolio_artifacts.py`: 新增 artifact 层，负责 JSON/Markdown/HTML 写出、HTML section 渲染、Markdown table 渲染和 escaping helper。
- `tests/test_training_portfolio.py`: 增加 facade identity 断言，保护旧导入路径继续指向新 artifact 实现。
- `README.md`: 更新当前版本、能力矩阵、v132 focus、tag 列表和截图归档说明。
- `c/132/解释/说明.md`: 说明本版运行证据、截图含义和能力边界。

## training portfolio 的核心数据结构

`build_training_portfolio_plan()` 产出 plan dict，核心字段包括：

```text
schema_version
title
project_root
out_root
run_name
dataset_name
dataset_version
suite_path
request_log_path
artifacts
steps
```

`artifacts` 是后续证据链的路径索引，例如 prepared corpus、checkpoint、run manifest、eval suite、generation quality、benchmark scorecard、registry 和 maturity narrative。`steps` 是 pipeline step 列表，每个 step 包含：

```text
key
title
command
expected_outputs
```

`run_training_portfolio_plan()` 在 dry-run 时不执行 command，只根据 artifacts 路径生成可审阅报告；在 `execute=True` 时逐步运行命令，记录 return code、stdout/stderr 和失败步骤。最终 report dict 会增加：

```text
generated_at
execution
step_results
artifact_rows
recommendations
```

这些字段是 artifact 层唯一需要读取的数据。

## 拆分前的问题

拆分前，`training_portfolio.py` 同时承担两类职责：

```text
1. 规划和执行训练 portfolio pipeline
2. 把 pipeline report 发布成 JSON/Markdown/HTML
```

第二类职责包括：

```text
write_training_portfolio_json
render_training_portfolio_markdown
write_training_portfolio_markdown
render_training_portfolio_html
write_training_portfolio_html
write_training_portfolio_outputs
```

这些函数本身不参与训练，也不决定 pipeline 是否成功。它们只是把 report dict 换成可读证据文件。放在核心模块里会让后续调整 pipeline 步骤时同时面对 HTML/CSS/Markdown 细节。

## 新 artifact 模块的职责

`training_portfolio_artifacts.py` 只做证据发布：

- JSON: 机器可消费的完整 training portfolio report。
- Markdown: 适合代码讲解、README 和人工审阅的文本证据。
- HTML: 适合浏览器打开的 run-level entry point。

这些产物是只读证据，不会反向修改数据集、checkpoint、registry 或 maturity narrative。它们也不替代真实训练结果，只负责把本地 pipeline 状态解释清楚。

## facade 为什么保留

旧调用仍然有效：

```python
from minigpt.training_portfolio import build_training_portfolio_plan, write_training_portfolio_outputs
```

拆分后，`build_training_portfolio_plan()` 仍来自 `training_portfolio.py`，而 `write_training_portfolio_outputs()` 的真实实现来自 `training_portfolio_artifacts.py`。测试里的 identity 断言保护这一点：

```text
training_portfolio.write_training_portfolio_outputs
is training_portfolio_artifacts.write_training_portfolio_outputs
```

这避免了后续维护中出现“旧 facade 里残留一份 wrapper、新模块里又有一份实现”的分叉。

## 测试覆盖

`tests/test_training_portfolio.py` 覆盖了几条关键链路：

- plan step 顺序仍包含 prepare dataset、train、eval suite、generation quality、benchmark scorecard、dataset card、registry、maturity summary 和 maturity narrative。
- dry-run report 仍标记为 `planned`，不会误报 completed。
- execute 模式能记录成功步骤、stdout tail 和 artifact availability。
- `write_training_portfolio_outputs()` 仍生成 JSON/Markdown/HTML。
- HTML title escaping 仍保护特殊字符。
- 旧 facade 导出和新 artifact 模块保持同一函数身份。

另外，compile check、dry-run CLI smoke、maintenance smoke、source encoding hygiene、full unittest discovery 和 Playwright HTML 截图一起证明：拆分后导入可用、脚本可运行、页面可打开、编码边界干净。

## 证据意义

v132 不是模型训练能力的一次跃迁，而是维护结构的一次收口。它让 training portfolio 的核心模块更专注于“pipeline 是什么、是否执行、产物是否存在”，让 artifact 模块更专注于“如何发布证据”。这符合当前项目从功能堆叠转向可维护 AI 工程治理的方向。

真正的能力边界是：

```text
training_portfolio.py 负责计划与状态
training_portfolio_artifacts.py 负责证据发布
tests 负责锁住旧契约
c/132 负责保存运行证据
```

## 一句话总结

v132 把 training portfolio 从“厚模块同时规划流水线和发布页面”推进到“pipeline 计划/状态 + artifact 发布层”的结构，维护边界更清楚，但模型质量声明保持克制不变。
