# v1262：production-excellence A1 有限范围严格类型分析

## 一、本版目标、问题与明确边界

v1261 已经把 ruff 作为可失败的静态分析门接入仓库，但 ruff 主要处理语法级错误、未使用导入、未定义名称和格式一致性。它无法回答更深一层的问题：一个函数声明返回 `dict[str, str]` 时，实际是否可能把未知类型直接返回；一个 `TypedDict` 是否被错误地当成普通 `dict[str, Any]` 传递；从 JSON 取出的值在调用 `.get()` 前是否真的完成了类型收窄；CI gate 的状态字符串是否严格限制在 `pass` 与 `fail`。这些问题不会总在单测样本里立即爆炸，却会逐渐削弱公共报告契约和治理门的可维护性。

本版的目标不是宣布“全仓类型安全”，而是完成 A1 计划要求的有限范围 mypy 接入：选择真正承重、已经具有较完整注解、又不涉及科学实验语义的模块，使用严格模式检查；把检查范围写入版本控制；建立不可静默缩小的范围下限；让 CI、本地工程健康命令和 CI workflow hygiene 同时保护该门；最后生成可供机器和人工复核的证据。

本版明确不做四件事。第一，不对一千多个历史模块开展一次性类型修复，因为那会形成难以审查的机械改动，并违反计划书“full-repo mypy is NOT required”的约束。第二，不进入科学线，不修改训练参数、缓存 checkpoint、模型生成、实验 verdict 或 `decide()` 逻辑。第三，不使用大面积 `ignore_errors` 把错误压下去。第四，不把 mypy 通过解释成模型质量、生产成熟度或 promotion readiness 的提升。它只说明八个工程承重文件在约定配置下通过严格类型检查。

## 二、为什么选择这八个文件

范围清单位于 `docs/static-analysis/mypy-scope.json`。清单不是随手拼出的命令参数，而是把八个文件分成四个职责组。

`shared_report_contract` 组包含 `src/minigpt/report_utils.py`。该模块提供 JSON 写入、输出 bundle、CSV 单元格转换、路径定位、归档引用解析、字典/列表类型收窄、数字转换、Markdown 与 HTML 转义等共享能力。大量报告构建器依赖这里的函数，因此它相当于报告层的基础契约。它的类型边界稳定，能给后续逐批扩展 mypy 范围提供可信起点。

`ci_governance_gate` 组包含 `ci_workflow_hygiene.py`、`ci_workflow_hygiene_artifacts.py` 和 `ci_workflow_hygiene_policy.py`。policy 定义 CI 必须出现的命令与顺序；主模块读取 workflow、构造检查项、计算 summary；artifacts 把报告渲染为 JSON、CSV、Markdown 和 HTML。这三个文件形成完整的“规则 -> 判定 -> 证据”链，是工程治理线最典型的承重切片。

`engineering_orchestration` 组包含 `scripts/_bootstrap.py` 与 `scripts/_engineering_health.py`。前者是当前维护入口的单一清单，后者把清单转换成实际执行步骤并聚合结果。若它们的类型契约漂移，本地工程健康与 CI 可能出现入口不同步、命令元组形状不一致或 writer 返回类型模糊等问题。

`analysis_gates` 组包含 `scripts/check_static_analysis.py` 与本版新增的 `scripts/check_type_analysis.py`。让类型门检查自己并不是形式主义：如果检查器自身的 runner、scope、诊断和输出模型都没有类型保护，门的报告可能先于被检查代码发生漂移。同时把 v1261 的 ruff gate 纳入范围，可以让两种分析门共享更清楚的工程边界。

这八个文件覆盖公共报告工具、治理 policy、判定、渲染、工程入口与分析器自身，又完全避开模型训练和科学实验判定，因此与“两条工作线”的仓库规则一致。

## 三、范围清单如何阻止“接了 mypy 但范围越来越小”

只在 CI 中写 `python -m mypy file_a.py file_b.py` 有一个明显缺点：维护者可以删除一个难修文件，命令仍然返回成功，外部只看到绿色状态，却不知道保护面缩小了。本版把目标写入 `mypy-scope.json`，并增加 `scope_floor=8`。`validate_scope()` 在启动 mypy 之前执行以下检查：schema 版本必须是 1；tool 必须是 mypy；targets 必须是非空列表；目标不得重复；目标数量不得低于 floor；每个目标必须位于项目根目录内、后缀为 `.py` 且真实存在；groups 必须为非空对象；每组至少包含一个目标；组内路径必须已经在 targets 声明；每个 target 都必须归属某个组。

这套机制并不能阻止评审者显式修改 `scope_floor`，也不应该假装能做到。它解决的是“静默缩水”：若有人只从 targets 删除文件而不调整 floor，CI 立即失败；若删除分组或留下无归属目标，也会失败；若确实要降低 floor，就必须产生清楚可见的 policy diff，由评审判断是否合理。后续扩展时，正确动作是增加目标并提高 floor，而不是把新的历史错误加入 baseline。mypy 在本范围内没有历史错误 baseline，八个目标必须保持零诊断。

## 四、`check_type_analysis.py` 的输入、流程和输出

CLI 的默认输入是项目根目录、`docs/static-analysis/mypy-scope.json` 和输出目录 `runs/type-analysis`。`load_scope()` 使用 `utf-8-sig` 读取 JSON，并拒绝非对象顶层结构。`scope_targets()` 把经过读取的目标稳定转换为元组。`build_report()` 先解析绝对 manifest 路径，再调用 `validate_scope()`；只有范围契约通过后，才组装 `python -m mypy --config-file pyproject.toml <targets...>`。

子进程固定使用项目根目录作为 cwd，并以 UTF-8、`errors=replace` 捕获输出，避免 Windows 本地代码页让检查器自己因解码失败而崩溃。`parse_diagnostics()` 同时支持带列号与不带列号的 mypy 输出，把路径、行、列、severity、error code 和 message 转为结构化记录。绝对路径若位于仓库内，会归一化为仓库相对 POSIX 路径，便于 Windows 与 Linux CI 之间比较和阅读。

`_report_payload()` 将运行结果统一为 `status`、`decision`、`return_code`、summary、targets、scope issues 和 diagnostics。范围失败使用 return code 2 形成报告，不会在写证据前直接抛出；mypy 失败保留 mypy 返回码和诊断；只有范围无问题且 mypy 返回 0 时，状态才是 `pass`，决策才是 `continue_with_typed_scope`。

`write_report_outputs()` 生成四种输出。JSON 是最完整的机器消费证据；CSV 把 scope 行和 diagnostic 行放入同一张可筛选表；Markdown 适合代码评审与归档阅读；HTML 提供状态卡、目标列表和诊断表，供浏览器核验与截图。这里的 HTML 不是独立的新治理链，只是同一报告模型的可视化投影。

CLI 的 `--no-fail` 只用于需要观察失败报告但不阻断调用方的调试场景，CI 默认不传，因此范围或类型失败都会返回 1。正常运行打印状态、决策、目标数、诊断数、范围问题数和输出路径，日志无需打开文件也能快速判断结果。

## 五、严格配置与 `follow_imports=skip` 的真实含义

`pyproject.toml` 将 Python 版本设为 3.11，启用 `strict=true`、`warn_unused_configs=true`、错误代码显示和 explicit package bases。严格模式会打开未注解函数、隐式 Optional、无类型返回、泛型缺参等一组检查，确保“被纳入范围”不是宽松扫描。

本版同时设置 `follow_imports=skip`。这并不表示 mypy 不检查八个目标之间的代码；八个目标都作为顶层目标显式传入，都会被严格分析。它表示目标导入的其他历史模块不会被递归拉入本次迁移。第一次试跑若不设置该边界，mypy 会沿着报告导入一路进入 dashboard、model card、dataset card，甚至模型与 RoPE 实现，八个顶层文件最终触发十六个文件中的六十余条错误。这些错误很多真实且值得未来处理，但在 v1262 同时修复会越过工程/科学线边界，也会把“一版有限类型门”变成不可控的全仓迁移。

所以 `follow_imports=skip` 是范围隔离，而不是忽略八个目标的错误。报告明确列出目标与 floor，文档也不声称全仓 clean。未来可以用新增分组逐步把重要依赖显式加入 targets；每增加一批，floor 同步提高，形成单向扩张的类型保护面。

## 六、本版实际修复了哪些类型边界

接入严格检查后，本版修复了几类不改变运行语义、却能改善维护性的边界。

第一类是 JSON/Any 收窄。原先若在三元表达式中重复调用 `report.get("summary")`，mypy 无法证明第二次调用与第一次得到同一对象，因此仍认为它可能为 `None`。现在先保存 `raw_summary` 或 `value`，检查 `isinstance(..., dict)` 后再构造字典。运行结果不变，但控制流和类型事实一致，读者也更容易看懂“先读取、再验证、后消费”。

第二类是 TypedDict 契约。`CiWorkflowSummary` 已经定义完整字段，却被 `_recommendations()` 声明成普通 `dict[str, Any]`，严格检查会拒绝这种不必要的降级。现在函数直接接受 `CiWorkflowSummary`，调用链保留字段约束。构造 action check 时，局部 `status` 明确标注为 `CheckStatus`，避免普通 `str` 被误传给只允许 `Literal["pass", "fail"]` 的 `_check()`。

第三类是 writer 返回值。工程健康与 CI artifact bundle 期望 writer 执行写入并返回 `None`，原来的 lambda 会把内部写函数返回的 `Path` 透传出去。运行时 bundle 并不使用返回值，所以行为没有出错，但类型揭示了契约含混。本版用显式 `write_json()`、`write_markdown()` 包装器丢弃内部返回值，并在跳过导入分析的边界对 bundle 总返回值做明确 `cast(dict[str, str], ...)`。这把“我们知道共享 helper 的契约是什么”写进代码，而不是留给推断猜测。

第四类是子进程与报告字段。ruff gate 写 baseline 时把 `dict[str, Any]` 中的 `generated_at` 直接交给要求字符串的参数；现在显式 `str()`。location 先保存原值再做字典收窄，避免重复 `.get()` 破坏类型事实。mypy runner 使用统一的 `Callable[..., CompletedProcess[str]]`，与现有 ruff gate 的可注入测试方式一致。

这些修改都没有改变任何报告字段含义、CI policy 决策、模型输出或科学 verdict。现有测试继续通过，是 contract-preserving 的必要证据。

## 七、CI、工程健康和 workflow hygiene 如何闭环

仅有脚本并不等于工程门。本版在 `.github/workflows/ci.yml` 中把 `Scoped type analysis gate` 放在 ruff 之后、归档与证据 smokes 之前，最终仍早于 coverage。这样类型错误能快速失败，不必等待完整测试覆盖流程结束。

`scripts/_bootstrap.py` 将 `check_type_analysis.py` 加入 `HEALTH_ENGINEERING_ENTRYPOINTS`，所以本地运行 `check_engineering_health.py` 会自动执行该门。`scripts/_engineering_health.py` 为它分配稳定 step id `type_analysis`，输出到 `runs/engineering-health/type-analysis/`，聚合 summary 会记录其命令、返回码和状态。

CI workflow hygiene policy 新增 `type_analysis_gate` 必需命令，并增加两条顺序关系：必须位于 static analysis 之后，必须位于 coverage 之前。主报告新增 `type_analysis_present`、`type_analysis_order_ready`、`type_analysis_ready`；Markdown、HTML 和 CLI stdout 同步展示。若有人从 workflow 删除 mypy，或把它移到 coverage 后，hygiene 自己先失败。由此形成“类型门检查代码，hygiene 检查类型门是否还存在且位置正确”的双层保护。

## 八、bootstrap 改进为何并入本版而不单独发版

工作区已有未提交的 `scripts/codex-bootstrap.ps1` 和 AGENTS 当前状态表，它们的方向合理：新会话用一个命令显示最近提交、工作区状态、最新 tag、最近 CI 和计划指针，减少重复定位成本。但首次运行暴露出 Windows PowerShell 对无 BOM UTF-8 脚本中字面中文的解码问题，输出路径发生乱码。

本版没有为这个小修单独消耗版本号，而是将脚本输出改为纯 ASCII 指针，同时保留对仓库 AGENTS 和 A-track brief 的指向。`tests/test_session_bootstrap.py` 静态断言四组关键命令和 brief 指针存在，并要求整个脚本 `isascii()`，防止未来重新引入当前 PowerShell 环境无法稳定解析的字符。该测试不会执行 `gh` 或网络调用，因此单测保持快速、确定且无副作用；真实 bootstrap 已在本版开始时运行，能够正常输出状态。

## 九、测试如何证明失败路径真实存在

`tests/test_type_analysis.py` 不只验证成功样例。第一组测试在临时目录创建真实 Python 文件，证明合法 target 与 group 可通过。第二组把 floor 设置为 2 但只提供一个目标，同时让 group 引用未声明路径，断言两条独立问题都被报告。这证明 scope ratchet 不是文档口号。

第三组给诊断解析器同时输入“带列号”和“不带列号”的 mypy 行，断言列号分别为 3 与 0，错误代码保留。第四组注入返回码 1 的 fake runner，让 `build_report()` 产生真实失败状态和结构化 assignment diagnostic。第五组检查四种证据文件全部生成且 Markdown 包含目标路径。

现有 CI workflow tests 增加 type gate 的 required command、顺序 ID 和 summary 三态断言；工程健康测试确认它位于 ruff 后、normalization guard 前，并使用独立输出目录；项目配置测试确认 requirements、mypy strict 配置、CI 命令和 START_HERE 命令同时存在；session bootstrap 测试保护启动脚本。ruff gate也把新 type checker 纳入 strict path，使它必须保持 lint 与 format clean。

最终真实运行不是 mock：`check_type_analysis.py` 返回 `status=pass`、`target_count=8`、`scope_floor=8`、`diagnostic_count=0`、`scope_issue_count=0`；ruff 仍保持 545 条历史 baseline、0 新问题；CI workflow hygiene 45 项全部通过，type analysis 的 present/order/ready 均为 true。Playwright MCP 打开 HTML 后，辅助树与截图均能看到上述指标和八个目标。

## 十、链路角色与后续扩展方式

v1261 解决“新 lint 问题不能继续增长”，v1262 解决“关键工程契约要有严格类型保护且范围不能静默缩小”。两版合起来完成 A1，但没有清偿全部历史静态分析债。下一阶段 A2 应按计划接入或校准 coverage floor，而不是继续无边界增加类型目标。

未来扩展 mypy 时应遵循三个动作：选择一个职责完整的小组；先让组内文件在严格模式下零诊断；将路径加入 manifest 并提高 scope floor。不要递归扫全仓后批量加 ignore，不要降低 floor，不要为了类型通过改变科学实验 verdict。若某个依赖属于科学线，应先停下并取得跨线授权。

## 一句话总结

v1262 把 mypy 从一个可选开发工具变成了“有明确承重范围、有不可静默缩小的下限、有失败证据、有 CI 顺序保护”的严格工程门，同时保持模型实验语义完全不变，至此 production-excellence A1 从语法与格式约束推进到关键契约的类型约束。
