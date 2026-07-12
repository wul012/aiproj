# v1273 优雅门 E-A1：名称预算机械门

## Family 设计说明（先于实现）

1. 抽象名：`Name Budget Gate`，负责 Python 名称预算，不承载 ruff 行为。
2. 数据边界：baseline 只保存稳定 violation digest、预算和计数；不复制巨型长名文本。
3. 行为边界：AST scanner 发现文件名与公开定义，checker 做 shrink-only 集合比较。
4. 报告边界：输出当前计数、类别分布、new violations 与 top offenders，供 E-A2 决策。
5. 集成边界：独立短名 CLI 接入 CI、engineering health、ruff strict paths 与 mypy scope。
6. 明确不做：E-A1 不重命名历史路径，不碰 schema/artifact/cache/`decide()` 科学合同。

## 一、本版目标、问题与明确边界

v1273 是 `docs/elegance-hotspot-program-aiproj.md` 的 E-A1，也是 aiproj 在“代码要坚固”之后为“代码要优雅”购买的第一道机械约束。此前仓库已经有 ruff baseline、mypy scope、文件大小 ratchet、coverage floor、schema guard 和 honest-measurement gate，它们能发现语法、类型、体积、覆盖与声明边界问题，却不能阻止一个最直观的可读性退化：继续创造一百多个字符的文件名、函数名和常量名。AGENTS 中的名称预算原本只是书面规则；如果没有会失败的检查，忙碌版本仍可能绕过它，评审也只能事后人工指出。

本版把规则定义为可执行合同：`src/` 与 `scripts/` 中，新文件名和公开标识符不得超过 40 个字符；历史违规进入一次性 committed baseline，之后只能减少，不能增加。这里的“公开标识符”不是 Python `__all__` 的严格同义词，而是机械扫描可以稳定识别、对模块读者可见的模块级或类级定义，包括公开函数、异步函数、类、模块变量和类字段。以下划线开头的私有名称、函数体里的局部变量和 import alias 不进入名称预算，避免把实现细节误判成公共概念债。

边界同样重要。v1273 不批量重命名历史 publication/receipt 文件，不修改缓存 artifact 路径，不改 schema registry，不碰科学线训练代码、checkpoint、实验 verdict 或 `decide()`。本版也不宣称 7,515 条历史违规已经修复；它只冻结事实、阻止继续变坏，并为 E-A2 的 top-N 判断提供可复核输入。规则文档、Claude 在 production-excellence brief 中留下的评审结论，以及本 E-track 计划书一并纳入版本，避免规则与实现分处未提交状态。

## 二、入口、输入与输出

维护者入口是 `scripts/check_name_budget.py`。默认命令为：

```powershell
python -B scripts/check_name_budget.py --out-dir runs/name-budget
```

它把仓库根目录、baseline 路径和输出目录交给 `src/minigpt/name_budget.py`。正常 CI 绝不传 `--update-baseline`；只有首次采用或确认存量违规已经减少时，维护者才显式执行更新。CLI 没有暴露 `--max-length`，这是刻意设计：40 是仓库政策，不是调用者可以为了让构建变绿而放宽的运行参数。`--no-fail` 仅用于需要保留失败报告的诊断场景，CI 默认按报告状态返回 0 或 1。

核心输入有三项。第一项是 `project_root`，所有目标与 baseline 都必须解析在仓库内部，越界路径直接抛错。第二项是固定目标 `src` 与 `scripts`。第三项是 `docs/elegance/name-baseline.json`，其中只保存 schema、政策名、40 字符预算、目标列表、违规总数、分类计数和稳定 SHA-256 digest。baseline 不复制 7,515 个超长原文，因此不会再制造一份难读的“长名字大全”；具体原文只在每次运行的 top offenders 与 new violations 中按需出现。

输出为 JSON、CSV、Markdown 和 HTML 四件套。JSON 是后续自动消费的权威报告；CSV 合并新违规和 top offenders，便于表格筛选；Markdown 适合代码评审；HTML 用于人眼核验，并内嵌空 favicon，浏览器打开时不会产生无关 404。报告核心字段包括 `status`、`decision`、`summary`、`kind_counts`、`blockers`、`scan_errors`、`new_violations` 和 `top_offenders`。本版普通运行得到 `status=pass`、`decision=continue_with_name_budget`、`new_violation_count=0`，说明 committed baseline 与当前树一致，而不是说明历史存量为零。

## 三、AST 扫描如何工作

`scan_names()` 先解析目标路径，去重并排序所有 Python 文件。文件名直接按 `Path.name` 计算，因此 `.py` 后缀也占预算；这符合“仓库导航时实际看到的名字”这一维护视角。源码使用 `utf-8-sig` 读取，使扫描器能够给 source-encoding gate 留出独立职责，同时 AST 解析失败仍会进入 `scan_errors` 并令本门失败，不会静默跳过坏文件。

AST 遍历只进入模块体和类体。遇到公开 `FunctionDef`、`AsyncFunctionDef` 或 `ClassDef` 时记录对应类别；类体继续递归，以识别方法、嵌套类和字段。遇到模块级或类级 `Assign`、`AnnAssign` 时，只接收简单 `Name` target。属性赋值、tuple unpacking、import alias 与函数体局部赋值均不计入。这套边界使结果既足够严格，又不会把每一个临时变量都变成 API 治理问题。

每条违规形成 `NameItem`：`kind` 表示 filename/function/class/variable/field，`path` 是仓库相对 POSIX 路径，`qualname` 表示类作用域，`name` 与 `length` 用于人读，`line` 用于定位，`digest` 用于 baseline 比较。digest 的输入是 kind、path、qualname 与 name，不包含行号。这样在函数前增加注释、格式化代码或把定义移动几行，不会被误报为“旧违规消失、新违规出现”；真正重命名、移动文件或改变作用域才会改变身份。该选择由 `test_line_moves_keep_digest` 直接保护。

## 四、shrink-only 状态机

baseline 更新不是简单覆盖。`build_name_report()` 先得到当前 digest 集合，再与旧集合做差：`current - old` 是新增违规，`old - current` 是已解决违规。普通模式要求 baseline 存在、配置有效、扫描无错误且新增集合为空。首次采用时，只有显式 `--update-baseline` 才允许把当前事实写入 baseline；这是 v1273 唯一一次全量登记。

已有 baseline 的更新更严格：当前集合必须是旧集合的子集。只要出现一个新 digest，`baseline_update_allowed` 就是 false，报告加入 `baseline_update_blocked` 与 `new_name_violations`，原 baseline 不写入一字节。测试先保存 baseline 原始 bytes，再制造超长模块变量并请求更新，最后断言退出失败且 bytes 完全相等。这证明开发者不能通过“更新一下 baseline”把新债合法化。

相反，如果历史超长名字被安全删除或缩短，当前集合成为真子集，更新才会写入更小的 digest 列表。`test_subset_update_shrinks` 从一条违规降到零，断言 `resolved_violation_count=1`、baseline `violation_count=0`。这就是 ratchet 的含义：它不要求一次清空数千条冻结历史，但每次真实改善都可以永久收紧，任何反向增长都会失败。

baseline 自身也有防篡改检查。schema 必须为 1，policy 必须是 `aiproj_name_budget`，预算必须精确等于 40，targets 必须精确匹配，digests 必须是无重复字符串列表，`violation_count` 必须与列表长度一致。测试把预算从 40 改成 41 后，报告以 `baseline_budget_invalid` 失败；因此不能修改 baseline 元数据来偷放宽规则。

## 五、CI 与工程健康链路

`.github/workflows/ci.yml` 在 static analysis 后、scoped type analysis 前运行名称预算门。这个位置有明确语义：ruff 先保证新门自身的静态质量，名称门再保护概念命名，mypy 随后检查类型合同。`ci_workflow_hygiene_policy.py` 同时登记命令存在性和顺序：static 必须早于 name budget，name budget 必须早于 type 与 coverage，原有 static 早于 type 的兼容检查仍保留。删除步骤、交换顺序或把门挪到 coverage 后都会让 CI hygiene 失败。

本地 `check_engineering_health.py` 通过 `HEALTH_ENGINEERING_ENTRYPOINTS` 获得相同入口，并把报告写入独立 `name-budget` 子目录。由此维护者不需要记第二套命令。新 CLI 与核心模块也加入 staged ruff strict paths 和 mypy scope；scope floor 从 20 收紧到 22，不能在后续版本把它们悄悄移出类型检查。整个接线没有降低 ruff baseline、coverage floor、文件大小上限或任何既有门槛。

## 六、测试如何保护真实契约

`tests/test_name_budget.py` 包含九个定向测试。扫描测试在同一临时模块中放入长文件名、模块变量、函数、类与类字段，并同时放入私有名称、长 import alias 和函数局部长变量，断言前五者被发现、后三者被排除。这样扫描范围的“公开”含义不是文档自述，而是可执行边界。

其余测试覆盖行移动稳定性、新违规失败、更新请求的 fail-closed 行为、真实收紧、首次 CLI 采用、非法预算、非法 digest 结构与 HTML 空 favicon。CI workflow 与 engineering-health 的既有测试也同步更新：手写 workflow fixture 必须包含新步骤，步骤序列必须出现 `static_analysis → name_budget → type_analysis`。定向合集最终为 38 项通过，证明新增能力、malformed baseline fail-closed 与旧门编排兼容。工程健康总入口随后验证 source encoding 2,785/2,785、CI hygiene 67/67、ruff 新增 0、名称新增 0、mypy 22 目标 0 诊断、normalization 136 项通过；最终树全量 pytest 为 `3759 passed in 1254.87s`。这组结果把局部反例、编排合同和全仓行为回归连成同一证据链。

## 七、真实 census 与 E-A2 含义

首次扫描覆盖 2,049 个 Python 文件，共发现 7,515 条历史超预算名称：函数 3,201、变量 2,671、文件名 1,610、类字段 33，扫描错误为 0。普通模式在 baseline 写入后再次运行，baseline/current 都为 7,515，new 为 0，状态为 pass。

Top offenders 长度达到 204–210 字符，主要集中在 v980-v1014 的 randomized-holdout publication receipt/index/review 链。这一事实很关键：最显眼的不一定是最适合改的。它们很可能出现在 publication receipts、缓存 artifact、registry 或历史导入路径中，而 E-track 明确把这些 pinned 合同列为禁区。E-A2 必须先逐项查 registry、receipt、缓存与调用引用；如果 top 5 都受保护，就应诚实跳过，而不是为了完成“五个重命名”破坏历史可复现性。

另一个重要结论是新门本身遵守自己的预算。核心文件叫 `name_budget.py`，CLI 叫 `check_name_budget.py`，公开类型和函数都在 40 字符以内。新增源码与接线总计 399 行，低于工程版本 400 行生成上限；核心模块 327 行、CLI 50 行，没有把 453 行的旧 static-analysis 脚本继续推向大文件。设计说明先于两个新 family 文件落盘，也满足“三次规则”和 family note 要求。

## 八、运行证据与链路角色

最终报告归档在 `f/1273/解释/name-budget/`，包含 `name_budget.json`、CSV、Markdown 与 HTML。`f/1273/解释/说明.md` 保存需求—证据矩阵、命令与边界；截图只证明 HTML 可读、状态与关键数字可见，不替代 JSON 和测试。`docs/elegance/name-baseline.json` 是 CI 使用的 committed ratchet 数据，不是模型实验 artifact，也不构成模型质量证据。

v1273 在整个 E-track 中承担“建立测量尺”的角色。E-A2 是否进行、改哪些名称，都必须由这把尺和 pin 检查决定；E-A3 则会复跑 census、确认 baseline 未放宽并形成一页 closeout。当前版本只完成 E-A1，不提前宣布整个 program 完成。

## 一句话总结

v1273 把“新增名称不得超过 40 字符、历史债只能减少”从人工约定变成了 AST census、shrink-only baseline、CI 顺序保护、类型与静态检查共同守护的机械合同，同时用真实的 7,515 条存量数据为后续谨慎而非冒进的 top-N 决策建立了依据。
