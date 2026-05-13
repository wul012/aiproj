# 第四十八版代码讲解：project maturity summary

## 本版目标、来源和边界

v43-v47 已经把 pair batch、pair trend、dashboard/playground 链接、registry pair report links 和 pair delta leaders 做成了一条完整证据链。继续细拆链接或表格列，收益会越来越低。v48 的目标是收口：把 v1-v48 的能力按项目成熟度维度汇总成一个可阅读、可导出、可截图的 maturity summary。

本版不训练模型，不改变 registry/pair batch 的已有格式，不新增 release gate 规则，也不继续拆 pair/report 小功能。它只读取项目已有证据，输出能力矩阵和下一阶段建议。

## 所在链路

```text
model core
 -> data / reproducibility
 -> evaluation benchmark
 -> local inference
 -> registry / reporting
 -> release governance
 -> project maturity summary
```

这一层回答的问题是：这个学习型 AI 工程到底成熟到哪一层，下一步该补真实 benchmark scoring、数据规模，还是服务化硬化。

## 关键文件

- `src/minigpt/maturity.py`：构建 maturity summary，渲染 JSON/CSV/Markdown/HTML。
- `scripts/build_maturity_summary.py`：命令行入口。
- `tests/test_maturity.py`：覆盖版本发现、registry context、输出文件和 HTML 转义。
- `README.md`：记录 v48 当前能力、tag、截图、学习地图和下一步。
- `代码讲解记录_项目成熟度阶段/README.md`：开启新的项目成熟度阶段。
- `b/48/解释/说明.md`：保存本版运行截图解释和 tag 含义。

## 输入数据来源

`build_maturity_summary(project_root)` 会读取四类本地证据：

- `README.md` 中的 `vN.0.0` 版本记录，用来判断当前版本和 published version count。
- `a/<version>`、`b/<version>` 目录，用来判断运行截图归档覆盖。
- `代码讲解记录*/*.md`，用来判断代码讲解覆盖。
- 可选 `runs/registry/registry.json`，用来读取 run count、quality counts、pair report counts 和 pair delta summary。

如果没有 registry，summary 仍然能生成，只是 `registry_context.available=false`，并给出生成 registry 的建议。

## 能力矩阵

`CAPABILITY_SPECS` 把项目分成八个能力区：

- `Model Core`
- `Data And Reproducibility`
- `Evaluation Benchmarks`
- `Local Inference And Playground`
- `Registry And Reporting`
- `Release Governance`
- `Documentation And Evidence`
- `Project Synthesis`

每个能力区有目标版本列表、目标成熟度、证据说明和下一步建议。构建时会计算：

- `covered_versions`
- `missing_versions`
- `score_percent`
- `maturity_level`
- `status`

这样 v48 不是靠主观文字说“项目不错”，而是把已有 tag 和归档证据映射成明确的 capability matrix。

## 输出文件

`write_maturity_summary_outputs` 会写出：

```text
maturity_summary.json
maturity_summary.csv
maturity_summary.md
maturity_summary.html
```

其中 JSON 是机器可读总览；CSV 是能力矩阵表；Markdown 适合代码讲解和 README 复述；HTML 适合浏览器截图和作品展示。

## HTML 读法

`maturity_summary.html` 有四块：

- Overview stats：当前版本、版本数量、归档数量、代码讲解数量、成熟度均值、状态、registry runs、pair deltas。
- Capability Matrix：每个能力区的状态、等级、覆盖版本、证据和下一步。
- Phase Timeline：v1-v12、v13-v24、v25-v34、v35-v47、v48 的阶段覆盖。
- Registry Context / Recommendations：把当前 registry 证据和下一步建议放在同一页。

这让项目能从“长 README 流水账”收束成一个评审者能快速扫描的成熟度报告。

## 测试和证据

本版测试覆盖：

- 版本发现：`README.md` 的 v1-v48 能被识别。
- 归档发现：`a/` 和 `b/` 的版本目录能被统计。
- registry context：`pair_delta_summary` 能进入 maturity summary。
- 输出文件：JSON/CSV/Markdown/HTML 都能写出。
- HTML 安全：标题里的 `<...>` 会被转义。

运行证据保存在 `b/48/图片`，包括全量测试、maturity smoke、结构检查、Playwright Chrome 截图和文档检查。

## 一句话总结

v48 把 MiniGPT 从“持续追加证据链功能”推进到“能解释自身成熟度、短板和下一阶段路线”的阶段。
