# v1270：CI workflow hygiene 职责拆分与严格类型扩面

## 1. 本版目标、背景与明确不做

v1268 给 CI hygiene 增加 execution economy 检查后，`src/minigpt/ci_workflow_hygiene.py` 已经增长到 523 行。它同时保存 61 个 summary 字段的 TypedDict、GitHub Action 与 YAML 文本解析、63 条原子检查构造、十余组 gate readiness 派生、recommendation 决策、最终 report 编排以及历史 artifact writer 再导出。文件尚未达到 800 行硬上限，却已经越过 500 行 warning 线，并且每增加一个 CI gate 都需要在同一文件多个相距很远的区域修改。

这类文件的风险不只来自行数。类型定义、文本解析、检查策略与摘要投影拥有不同变化原因：新增字段会改类型和 summary；新增 action 解析规则会改 checks；新增 writer 不应触碰判定；公共入口则应长期稳定。把它们捆在一起，会扩大 merge 冲突半径，也让评审者难以判断某次修改是在改变“检查事实”还是“解释事实”。

v1270 的目标是按变化原因拆分，保留一个很薄的兼容入口。明确不做：不新增 CI gate，不调整 v1268 execution economy 策略，不更改 check ID、summary key、decision 或 recommendation 文本，不更改 JSON/CSV/Markdown/HTML writer，不降低 ruff/mypy/file-size 门，不触碰科学线训练、checkpoint、缓存证据、`decide()` 与 promotion verdict。

## 2. 拆分前的机械基线

为避免“测试看起来通过但报告悄悄变化”，拆分前先对真实 `.github/workflows/ci.yml` 调用公开 builder，固定 `generated_at=2026-01-01T00:00:00Z`，再对 `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=False)` 的 UTF-8 字节计算 SHA-256。基线为 `298db00f23faa43be167566fb46e9f6851962364777b1693a29ad631cb72f126`，同时记录 `checks=63`、`summary_keys=61`。

固定时间非常关键。若使用实时 `utc_now()`，每次运行都会因时间字段不同而得到新 hash，无法区分结构漂移与正常时间变化。排序 key 与紧凑 separators 则让 hash 只取决于数据模型，不取决于字典插入顺序或缩进风格。这份 hash 是一次性重构 parity 证据，不被写成永久 golden 测试，因为 CI 策略未来仍可能经过有意评审后扩展；永久锁死整个 report 会让合理演进变得笨重。

## 3. 四层结构及职责

拆分后的第一层是 `ci_workflow_hygiene_types.py`，96 行。它只定义 `CheckStatus`、`CiWorkflowCheck`、`CiWorkflowAction`、`CiWorkflowSummary` 与 `CiWorkflowReport`。61 个 summary 字段集中在这里，使字段契约可以被 mypy 独立验证，也让检查算法无需夹着一百行类型声明阅读。类型模块不读文件、不执行正则、不做判定。

第二层是 `ci_workflow_hygiene_checks.py`，175 行。它拥有三条正则：action `uses`、Python version 与 action major；拥有 `collect_actions()`、`build_checks()`、`check_passed()`、`forbidden_env_hits()` 和 `python_version()`。这个层回答“workflow 文本里客观存在什么”：使用了哪个 action、是否存在 forbidden env、哪些命令与顺序存在、tag trigger 是否出现。每个结果都是原子 `CiWorkflowCheck`，不在这里决定整个 workflow 是否 ready。

第三层是 `ci_workflow_hygiene_summary.py`，239 行。它接收 text、actions 与 checks，不重新解析 YAML 文本。`build_summary()` 计算失败数、execution policy 状态与各 gate 的 present/order/ready 三元组；`build_recommendations()` 只根据 summary 生成维护建议。新增 `_gate_state()` 将过去重复的“present check + 若干 order checks + conjunction”收敛成一个局部模式。它不生成文件，也不知道 report 的标题或输出路径。

第四层是保留原路径的 `ci_workflow_hygiene.py`，现在 80 行。它读取 workflow 文本，依次调用 `collect_actions()`、`build_checks()`、`build_summary()`，组装 policy 与 report，再调用 recommendation builder。历史使用者仍从相同模块导入 `build_ci_workflow_hygiene_report` 和各 writer；`__all__` 与 writer identity 保持不变。这个入口是 compatibility facade，也是唯一知道完整流水线顺序的地方。

## 4. `_gate_state()` 为什么是合适抽象

拆分前，tiny scorecard、boundary check、boundary plan、archived path、receipt failure、docs readability、static analysis、type analysis、file-size、A-track closeout 和 normalization guard 都重复同一种代码：先查 command check 是否通过，再查一到三个 order check，最后把二者相与得到 ready。重复并非完全相同，因为每组 order ID 数量不同，但语义一致。

`_gate_state(checks, present_check_id, *order_check_ids)` 返回 `(present, order_ready, ready)`。可变参数允许一个 gate 只有一个顺序条件，也允许 docs readability 有三个条件；`all()` 在这些 ID 上调用 `check_passed()`。调用点仍明确列出每个稳定 ID，评审者能看到依赖关系，没有把策略藏进字符串拼接或大型配置字典。

这个抽象没有用动态字段名修改 TypedDict。`build_summary()` 仍显式写出 61 个字段，因此 mypy 能检查每个 key，报告输出顺序也与旧实现一致。它消除的是 readiness 算法重复，不牺牲静态可见性。这是比“把所有 gate 塞进一个 dict 再循环 update”更保守的折中。

## 5. 输入、处理与输出链路

公开入口输入是 workflow 文件路径，可选 project root、title 与 generated_at。入口读取 UTF-8 文本后，checks 层先把 action 行转成结构化 action，再生成 action version、forbidden env、execution policy、required command、required order 和 Python version 检查。summary 层从检查 ID 派生组合状态；入口将 policy 常量、summary、actions、checks 和 recommendations 装入 `CiWorkflowReport`。

之后现有 artifacts 模块把同一 report 投影成 JSON、CSV、Markdown 和 HTML。v1270 没有移动 artifacts，因为 writer 已经是独立职责，继续拆它没有收益。CLI `scripts/check_ci_workflow_hygiene.py` 也没有改参数或输出字段。换句话说，外部可见链路仍是“workflow -> public builder -> report -> writers/CLI”，内部只是从单文件函数调用变为清晰组件调用。

## 6. parity 证明与组件测试

拆分后用完全相同命令重算 canonical report，SHA-256 仍为 `298db00f23faa43be167566fb46e9f6851962364777b1693a29ad631cb72f126`，check count 仍为 63，summary key count 仍为 61。hash 相同意味着不仅字段值相同，actions/checks/recommendations 数组内容、policy、detail 文本与布尔派生结果也相同。证据记录在 `f/1270/解释/ci-workflow-hygiene-refactor-parity.json`。

`tests/test_ci_workflow.py` 新增组件重组测试。它读取真实 workflow，分别调用 `collect_actions`、`build_checks`、`build_summary` 和 `build_recommendations`，再与公开 builder 返回的四个部分逐项相等比较。这项测试不像固定 hash 那样阻止未来有意扩展，但能保证 public facade 只是组件的忠实编排，防止入口额外修改某个字段或漏掉 recommendation。

现有测试继续覆盖老 action 版本、缺失命令、顺序错误、tag trigger、cache 缺失、artifact writer identity、CLI exit code 与四格式输出。聚焦批次共 `23 passed`。测试中曾出现一次插入位置导致的 indentation error；该失败发生在 collection 阶段，修复后从 py_compile 重新开始，并使用 PowerShell 的显式 exit-code 检查避免后续命令成功掩盖前序失败。

## 7. 严格范围与维护指标

三个新模块全部加入 `scripts/check_static_analysis.py` 的 `DEFAULT_STRICT_PATHS` 与 committed ruff baseline 的 `strict_paths`。它们必须零 lint 且通过 `ruff format --check`，不能因为是拆分产物就落回 271 条历史 baseline。mypy manifest 同时加入 checks、summary 与 types，`scope_floor` 从 16 收紧到 19；`ci_governance_gate` group 现在覆盖 public builder、checks、artifacts、policy、summary 与 types 六个承重文件。正式结果为 `target_count=19`、`diagnostic_count=0`、`scope_issue_count=0`。

file-size ratchet 扫描文件数从 2776 变为 2779，因为新增三个模块；`over_warning_count` 从 22 降到 21，原 523 行入口不再占 warning。新文件分别是 80、175、239 与 96 行，没有制造新的 warning。四个文件合计行数高于原单文件，这是显式类型和模块边界的成本；本版不把“总 LOC 减少”作为成功指标。真正收益是单文件认知负担、变化耦合和冲突半径下降。

## 8. 浏览器证据与规则升级

正式归档保留 CI hygiene 与 type analysis 的四格式报告。file-size ratchet 的全仓逐文件 JSON 接近四万行，而本版只使用其中 `over_warning_count=21`，因此没有把整份重复数据复制进 `f/1270`；计数写入 parity JSON，完整命令仍可复现。这是 evidence economy 的主动约束。Playwright 打开 type-analysis HTML 时第一次发现 favicon 404。v1269 的 static-analysis HTML 已出现并修过同类问题；这是第二次，因此按“同一失误第二次出现要升格为规则”处理：`AGENTS.md` 新增独立 HTML evidence 必须使用内联空 favicon、浏览器验证不得带 console error 的约定，`check_type_analysis.py` renderer 同时加入 `data:,` favicon。

重新生成后，浏览器页面无 console error，可访问性快照显示 Status pass、Targets 19、Scope floor 19、Diagnostics 0、Scope issues 0，并列出三个新组件。截图保存为 `f/1270/图片/ci-hygiene-type-scope-v1270.png`。截图用于证明展示层与目标清单可读，最终类型判定仍来自 JSON 与 mypy return code。

## 9. 最强质疑与回应

最强质疑是：“523 行并不算巨型文件，拆成四个文件是否过度设计？”若只是平均切片，质疑成立。本版不是按行数均分，而是按独立变化原因分层：类型契约、事实检查、状态派生和公共编排。每层都有明确输入输出，组件重组测试与 canonical hash 证明边界没有引入行为漂移。入口从 523 到 80、warning count 减一只是结果，主要收益是未来新增 check 时不再同时穿越类型、正则、summary 和 compatibility facade 的长文件。

## 10. 一句话总结

v1270 在 report 字节契约完全不变的前提下，把 CI hygiene 从 523 行多职责文件重构为四个可独立理解、严格 lint、严格 mypy、低冲突的工程组件。
