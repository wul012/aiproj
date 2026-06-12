# v1140 report loader dedup 代码讲解

## 本版目标和不做什么

v1140 是一次契约保持型重构。它的直接背景是 v1135 到 v1139 连续完成了一条模型能力回归准备链路：v1135 生成 plan，v1136 做 evidence inventory，v1137 生成 suite manifest，v1138 做 suite readiness，v1139 做 follow-up closeout。五个版本的功能边界很清楚，但代码层面留下了一个典型的高速迭代痕迹：每个模块都复制了一段几乎相同的 report loader 样板，包括“如果输入是目录就拼默认 JSON 文件名”和“用 `utf-8-sig` 读取 JSON，并要求 payload 必须是 dict”。这类重复本身不复杂，却会在后续版本里持续扩大，因为每新增一个报告模块就会再复制一次。

本版的目标就是把这段重复收进共享 helper，让最新的五个 regression 模块先成为第一批消费者。它不改变任何报告的 JSON、CSV、text、Markdown、HTML 输出语义，不改已有 CLI 参数，不改 public function 名字，不批量迁移历史几百个模块。这个“不做什么”比“做什么”同样重要。全仓库里 `read_json_report` 这种样板已经出现很多次，如果一口气全部替换，风险会很高：旧模块可能有细微差异，错误信息可能被测试或下游脚本依赖，某些模块可能读取的不是同一类 JSON。v1140 只处理刚刚形成的 v1135-v1139 链路，属于有上下文、有测试、有真实产物的一小块区域。

## 为什么这版应该先做重构

Claude 给出的队列里提到 AGENTS.md 的节奏规则：连续三到四个功能版本后，应该做一次 contract-preserving refactor、去重或测试硬化。这个判断是合理的。v1135-v1139 虽然不是大规模模型训练版本，但它们已经连续五版围绕同一条治理链推进，积累了相同 loader 模式。继续直接做 v1141 trend report 当然也能做，但 trend report 还会继续读取上游 JSON，如果不先收掉 loader 样板，就会把重复继续复制到新版本。

v1140 的收益有三层。第一层是减少重复代码，最新五个模块不再各自维护 `json.loads(Path(path).read_text(encoding="utf-8-sig"))` 和非 dict 判断。第二层是统一行为，后续如果需要调整 BOM 读取、错误消息格式或目录输入策略，只需要改一个 helper。第三层是测试硬化，本版给 helper 自己补了测试，确保目录输入、文件输入、BOM JSON 和错误消息都被覆盖。对于一个报告治理项目来说，这种小型基础设施比继续堆更多报告更有长期价值。

## 共享 helper

本版在 `src/minigpt/report_utils.py` 里新增两个函数：`locate_upstream_report` 和 `read_json_object`。`report_utils.py` 当前只有一百多行，职责本来就包括 JSON 写出、CSV cell 格式化、dict/list 规范化、路径引用解析等基础工具，所以把两个小型读取 helper 放在这里是合适的，没有必要为了它们新建一个额外大模块。

`locate_upstream_report(path, default_name)` 的逻辑很简单：如果 `path` 是目录，就返回 `path / default_name`；否则直接返回 `path`。这正是 v1135-v1139 五个模块里重复出现的 locate 函数。保留这个行为可以保证 CLI 仍然支持两种输入方式：用户可以传具体 JSON，也可以传某个报告输出目录。

`read_json_object(path, *, description)` 负责读取 JSON object。它使用 `utf-8-sig`，所以能兼容带 BOM 的 JSON 文件。读取后如果 payload 不是 dict，就抛出 `ValueError(f"{description} must be a JSON object")`。这里特意把 description 做成参数，是为了保留各模块原有错误消息，比如 `model capability cadence report must be a JSON object`、`model capability regression plan must be a JSON object`。错误消息是契约的一部分，不能为了去重把所有报错都改成一个泛泛的 “report must be a JSON object”。

## 五个模块如何迁移

v1135 的 `model_capability_regression_plan.py` 保留 `locate_cadence_report` 和 `read_json_report`。前者现在返回 `locate_upstream_report(path, CADENCE_JSON)`，后者返回 `read_json_object(path, description="model capability cadence report")`。模块外部看不到变化，CLI 和测试仍然按旧函数名调用。

v1136 的 `model_capability_regression_inventory.py` 同样保留 `locate_regression_plan` 和 `read_json_report`，只是内部委托给共享 helper。它的 description 是 `model capability regression plan`，和原有错误消息一致。v1137 的 `model_capability_regression_suite_manifest.py` 迁移 `locate_inventory_report` 和 inventory JSON 读取。v1138 的 `model_capability_regression_suite_readiness.py` 迁移 suite manifest JSON 读取。v1139 的 `model_capability_regression_followup_closeout.py` 迁移 readiness JSON 读取。

这五个模块都删除了私有 `json` import，因为它们不再自己调用 `json.loads`。它们仍然保留 `Path` 和 `Any`，因为其他检查函数、路径存在性判断和类型注解还在使用这些对象。迁移后，模块的职责更集中：它们负责各自的业务检查和报告结构，通用文件定位和 JSON object 读取交给共享层。

## 新增测试

`tests/test_report_loading.py` 是 helper 的直接测试。它覆盖四个关键场景：目录输入会拼默认文件名，文件输入会原样返回，`utf-8-sig` 可以读取 BOM JSON，非 dict payload 会按传入 description 抛出精确错误消息。这些测试看起来小，但正好保护了本版最容易被悄悄改坏的契约。

`tests/test_report_loader_dedup.py` 是 v1140 自己的报告测试。它构造临时项目结构，写入五个目标模块的模拟文件。第一条测试确认当五个模块都导入共享 helper 且没有私有 loader 复制时，dedup report 是 `pass`。第二条测试故意让一个目标模块保留 `json.loads(Path(path).read_text(encoding="utf-8-sig"))`，确认报告会失败，并且 issue 里出现 `no_target_private_loader_copy`。第三条测试覆盖 artifact writer 和 CLI，确保 JSON、CSV、text、Markdown、HTML 五种输出都能生成。

此外，本版还跑了 v1135-v1139 五个已有模块的原测试。这个动作很关键，因为 v1140 的目标是 contract-preserving refactor，而不是新功能覆盖。原测试不用改断言还能通过，才说明 public wrapper 和输出语义没有被破坏。

## v1140 dedup report

本版新增 `src/minigpt/report_loader_dedup.py` 和 `scripts/generate_report_loader_dedup_v1140.py`。这不是新治理链，而是重构证据报告。模块会扫描 `src/minigpt`，统计 `read_json_report` 定义数量、私有 loader copy 数量，列出五个迁移模块，并检查它们是否存在、是否导入 `locate_upstream_report`、是否导入 `read_json_object`、是否仍然保留私有 `json.loads` loader。

真实运行命令是：

```powershell
python -B scripts\generate_report_loader_dedup_v1140.py --out-dir f\1140\解释\report-loader-dedup-v1140 --require-dedup-ready --force
```

真实输出为 `status=pass`、`decision=report_loader_dedup_ready`、`dedup_ready=True`、`read_json_report_definition_count=431`、`private_loader_copy_count=439`、`migrated_module_count=5`、`next_step=build_model_capability_regression_trend_report_v1141`。这里的全项目计数不是说 v1140 迁移了 431 个函数或 439 个 copy，而是说明历史重复仍然很大，本版只做了最新五个目标模块的有界迁移。报告中的 `boundary` 是 `contract_preserving_thin_wrappers_only`，强调这不是批量改名，也不是输出格式升级。

Playwright MCP 打开 HTML 后，页面标题是 `MiniGPT report loader dedup v1140`，快照中可以看到 `Migrated Report Loaders` 表格和 `Recommendations` 区域。截图保存为 `f/1140/图片/v1140-report-loader-dedup.png`。这张截图证明 HTML 产物可读，也让后续查看版本证据时不必只依赖命令行输出。

## 维护意义

v1140 的维护意义是把“重复但低风险”的样板抽出来，同时没有把项目拖进大范围历史迁移。很多项目在后期会遇到两种极端：一种是永远不重构，导致每个新功能继续复制旧样板；另一种是突然做一次超大规模清理，结果改动面过宽，测试和审查成本暴涨。v1140 选择中间路线：只改最近同一条链路的五个模块，补 helper 测试，再用 report 证明迁移结果。

这版也给后续迁移建立了范式。以后如果某个历史模块需要维护，可以顺手把它的 loader 改成 `locate_upstream_report` 和 `read_json_object`，不需要一次性迁移全仓库。这样做符合 AGENTS.md 的节奏：功能推进和维护优化要交替出现，但每次优化都要有边界、有测试、有证据。

另一个收益是 v1141 trend report 可以直接复用共享 helper。v1141 需要读取 v1135-v1139 的多个 JSON 产物，如果继续复制 loader，就会把同一问题带到下一条报告链里。v1140 先把基础层铺好，v1141 再做趋势报告会更干净。

## 一句话总结

v1140 在不改变 public API 和报告产物语义的前提下，把 v1135-v1139 五个 regression 模块的 loader 样板收进共享 helper，并用测试、报告和截图证明这次重构是有边界、可复查的维护优化。
