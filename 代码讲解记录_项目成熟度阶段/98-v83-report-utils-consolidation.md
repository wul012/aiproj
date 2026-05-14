# v83 report utils consolidation 代码讲解

## 本版目标

v83 的目标不是继续给 `promoted/training-scale` 链路再拆一个新报告，而是先处理最近几版暴露出来的代码质量问题：很多模块都在重复写一批很小但很关键的 helper，例如：

```text
artifact row 检查
JSON/CSV 写出
命令展示
Markdown 表格单元格转义
HTML 转义
list/dict 防御式归一化
```

这些 helper 单独看都不复杂，但它们被复制到多个 evidence-chain 模块以后，会带来三个风险：

- 后续字段语义很容易漂移，例如某个模块的 artifact row 有 `count`，另一个模块忘记写。
- 输出转义策略可能不一致，HTML/Markdown 报告的边界测试需要重复写。
- 每一版都增加私有 helper，会让代码量继续膨胀，而不是真正提升 MiniGPT 的模型能力或工程质量。

所以 v83 明确做的是一次小范围收口：新增 `report_utils.py`，并只迁移最新的 v82 `promoted_training_scale_seed_handoff.py`。这样既能验证公共层，也不会一次性改动几十个历史模块。

本版明确不做：

- 不改训练逻辑。
- 不改模型结构、tokenizer 或数据集处理。
- 不重写所有历史报告模块。
- 不改变 v82 handoff 的 JSON/CSV/Markdown/HTML 外部格式。
- 不新增新的治理报告层，只做公共基础设施整理。

## 前置路线

v83 接在 v80-v82 的 promoted training scale 链路之后：

```text
v80 promoted training scale baseline decision
 -> v81 promoted training scale next-cycle seed
 -> v82 promoted training scale seed handoff
 -> v83 shared report utility consolidation
```

v82 已经证明 seed handoff 能把下一轮 `plan_training_scale.py` 命令落成 plan 产物，并暴露后续 batch command。v83 的判断是：这条链路已经足够长，继续堆新节点之前，应该先把重复的底层报告工具收口。否则后续 v84、v85 再推进时，每个新模块都会继续复制同样的 `_artifact`、`_e`、`_md`、`_dict` 和 CSV 写出逻辑。

## 关键文件

```text
src/minigpt/report_utils.py
src/minigpt/promoted_training_scale_seed_handoff.py
tests/test_report_utils.py
tests/test_promoted_training_scale_seed_handoff.py
c/83/图片
c/83/解释/说明.md
```

`src/minigpt/report_utils.py` 是本版新增的公共工具模块。它不负责理解某一种业务报告，只提供多个报告模块都会用到的稳定小原语。

`src/minigpt/promoted_training_scale_seed_handoff.py` 是迁移验证点。v83 没有改变它的外部职责，仍然负责读取 v81 seed、校验或执行 plan 命令、检查 plan artifact、读取 next batch command，只是把私有 helper 改为复用公共工具。

`tests/test_report_utils.py` 是公共层的直接单测。它不依赖训练、不依赖真实 checkpoint，只验证 helper 自身的语义。

`tests/test_promoted_training_scale_seed_handoff.py` 是回归保护。它证明 v82 handoff 迁移以后，planned、blocked、execute、failed、输出和 HTML escaping 仍然保持一致。

`c/83` 保存运行截图与解释，用来证明这次不是只改 README，而是完成了代码、测试、归档、浏览器检查和文档闭环。

## 核心公共函数

`write_json_payload(payload, path)` 负责写 JSON 文件：

```text
输入：任意 payload、输出路径
行为：自动创建父目录，以 UTF-8 写出 ensure_ascii=False、indent=2 的 JSON
输出：磁盘上的 JSON 文件
```

它替代了多个模块里反复出现的：

```text
out_path = Path(path)
out_path.parent.mkdir(...)
out_path.write_text(json.dumps(...))
```

`write_csv_row(row, path, fieldnames)` 负责写单行 CSV。当前很多 evidence report 的 summary CSV 都是“一份报告一行摘要”，所以先把这个常见模式公共化。字段顺序由 `fieldnames` 控制，缺失字段会写成空值。

`csv_cell(value)` 负责把 CSV 单元格稳定化：

- `None` 写成空字符串。
- `dict/list/tuple` 写成 JSON 字符串，避免 Python repr 在不同上下文里难以消费。
- 普通标量直接写入。

`make_artifact_row(key, path, exists=None, count=None)` 是 artifact row 的基础结构：

```json
{
  "key": "training_scale_plan_json",
  "path": "runs/.../training_scale_plan.json",
  "exists": true,
  "count": 1
}
```

字段语义是：

- `key`：证据产物的稳定名称，供 summary、Markdown、HTML 和后续模块引用。
- `path`：产物路径，保持字符串形式，便于 JSON/CSV/HTML 输出。
- `exists`：产物是否存在。
- `count`：产物数量；普通文件存在时是 `1`，不存在是 `0`，目录聚合类产物可以显式传入数量。

`make_artifact_rows(items)` 是批量版本，输入是 `(key, path)` 列表，输出 artifact row 列表。

`count_available_artifacts(rows)` 只计算 `exists` 为真的 artifact 数量，让 summary 里的 `available_artifact_count` 不再手写 `sum(...)`。

`as_dict`、`list_of_dicts`、`list_of_strs`、`string_list` 是防御式归一化函数。它们的目标不是类型系统炫技，而是让报告读取外部 JSON 时更稳：上游字段缺失、类型不对时返回空结构，而不是让渲染函数直接崩掉。

`display_command(value)` 把命令列表转成人能复制阅读的命令字符串。它会给含空格或双引号的参数加引号，避免 README、Markdown 和 HTML 里的 command text 变得含混。

`markdown_cell(value)` 处理 Markdown 表格单元格：把 `|` 转义，把换行压成空格。

`html_escape(value)` 统一 HTML 转义，避免每个报告模块自己包一层 `html.escape(...)`。

## v82 handoff 的迁移方式

迁移前，`promoted_training_scale_seed_handoff.py` 自己维护这些私有函数：

```text
_artifact
_dict
_list_of_dicts
_list_of_strs
_string_list
_display_command
_quote_command_part
_md
_e
utc_now
```

迁移后，它从 `minigpt.report_utils` 引入公共工具，并保留原模块的业务函数名称：

```text
build_promoted_training_scale_seed_handoff
write_promoted_training_scale_seed_handoff_outputs
render_promoted_training_scale_seed_handoff_markdown
render_promoted_training_scale_seed_handoff_html
```

这种迁移方式刻意保守：外部 CLI、测试和下游调用不用改，只是模块内部的重复 helper 消失了。

`_artifact_rows(project_root, next_plan)` 仍然只负责 handoff 的业务判断：它知道本层应该检查哪些 plan 产物：

```text
training_scale_plan.json
training_scale_variants.json
training_scale_plan.csv
training_scale_plan.md
training_scale_plan.html
```

但“如何构造 artifact row”的通用结构交给 `make_artifact_rows`。这就是 v83 想要的边界：业务模块决定检查什么，公共工具决定行结构怎么稳定表达。

`write_promoted_training_scale_seed_handoff_json` 改为调用 `write_json_payload`。这说明 JSON 写出格式以后可以集中维护。

`write_promoted_training_scale_seed_handoff_csv` 改为调用 `write_csv_row`。字段含义仍属于 handoff 模块，CSV 写出机制属于公共层。

`_summary` 里的 `available_artifact_count` 改为调用 `count_available_artifacts`。这个变化很小，但它让 artifact availability 的含义和公共 artifact row 绑定起来。

## 输入输出格式

`report_utils.py` 自己不定义完整报告 schema，它只定义可复用的小结构。

最重要的小结构是 artifact row：

```json
{
  "key": "artifact_name",
  "path": "artifact/path",
  "exists": false,
  "count": 0
}
```

这个结构会出现在后续多类报告中，用来表达“某个证据产物是否真的存在”。它既是 JSON 证据的一部分，也会被 Markdown/HTML summary 渲染消费。

CSV 写出的输入是：

```text
row: dict[str, Any]
fieldnames: list[str]
```

输出是带 header 的单行 CSV。它不是训练数据，也不是模型输入，只是 evidence summary 的机器可读索引。

命令展示函数的输入可以是：

```text
["python", "scripts/plan_training_scale.py", "--out-dir", "runs/next plan"]
```

输出会变成：

```text
python scripts/plan_training_scale.py --out-dir "runs/next plan"
```

这类字符串用于 README、Markdown、HTML 和 CLI 打印，不会反向作为执行命令重新解析。真正执行命令时仍使用原始 list，避免 shell quoting 风险。

## 测试覆盖

`tests/test_report_utils.py` 覆盖了公共层本身：

- artifact row 能记录文件存在、缺失和数量。
- 聚合类 artifact 能显式传入 `count`。
- command display 能处理空格和双引号。
- Markdown cell 会转义竖线并压平换行。
- HTML escape 会转义 `<tag>`。
- JSON/CSV 写出会自动创建父目录。
- list/dict 归一化会过滤非法元素。

这些断言保护的是公共层的“基础合同”。一旦以后更多模块迁移到 `report_utils.py`，这些合同就会同时保护更多链路。

`tests/test_promoted_training_scale_seed_handoff.py` 没有因为 v83 被删减，反而继续作为迁移回归测试：

- ready seed 不执行时仍是 `planned`。
- review seed 在 `allow_review=False` 时仍被阻断。
- `--execute` 路径仍能真实运行 plan 命令并检测 5 个 plan artifact。
- 失败命令仍返回 `failed` 和非零 return code。
- 输出渲染仍会转义 HTML。

这说明公共化没有改变 v82 handoff 的行为。

## 截图归档

v83 的运行截图放在：

```text
c/83/图片
c/83/解释/说明.md
```

截图承担的证明作用是：

- `01-unit-tests.png` 证明 focused tests、compile check 和全量回归测试通过。
- `02-report-utils-smoke.png` 证明公共工具能独立写 JSON/CSV、检查 artifact row、展示命令。
- `03-promoted-handoff-refactor-smoke.png` 证明迁移后的 v82 handoff 仍能写出完整产物。
- `04-report-utils-structure-check.png` 证明新增源码、测试、文档、归档结构齐全。
- `05-playwright-promoted-handoff-html.png` 证明迁移后的 HTML 报告仍能被浏览器打开。
- `06-docs-check.png` 证明 README、代码讲解索引和 c archive 索引已经同步。

这些截图不是模型训练成果，它们是工程收口证据：证明这次重构有测试、有产物、有浏览器检查、有文档说明。

## 后续使用原则

v83 之后，如果新模块需要：

```text
artifact row
JSON/CSV summary output
HTML escaping
Markdown table cell escaping
command text display
list/dict defensive normalization
```

应该优先复用 `report_utils.py`，而不是继续复制私有 helper。

但这不意味着立刻把所有历史模块都重构。更合理的节奏是：

- 新增模块默认使用公共工具。
- 旧模块只有在被修改、扩展或出现 bug 时顺手迁移。
- 涉及输出格式的历史模块迁移时必须保留回归测试，避免改变已有证据格式。

## 一句话总结

v83 把 MiniGPT 的推进方式从“继续堆一层新报告”拉回到“先沉淀可复用的报告基础设施”，让后续 evidence-chain 代码可以少复制 helper、多复用稳定公共层。
