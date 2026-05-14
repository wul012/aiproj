# 第一百版代码讲解：Model Card 接入 report_utils

## 本版目标

v100 的目标是把 `model_card.py` 接入 `report_utils`，继续收束报告基础设施。

它解决的问题是：model card 是 project audit 的上游输入，v99 已经把 project audit 接到公共工具，但 model card 自己仍保留 UTC 时间、JSON 写出、HTML 转义和 dict/list 归一化逻辑。v100 让模型说明层也复用同一套基础工具。

本版明确不做：

- 不改变 model card 的字段结构。
- 不改变 ready/review run 统计。
- 不改变 intended use、limitations、coverage、recommendations 的生成策略。
- 不改变 HTML/Markdown 布局。
- 不改 project audit、release bundle 或 release gate。
- 不拆分 `model_card.py` 的大结构。

## 路线来源

v100 延续的是 report-utils consolidation 路线。

相关链路可以理解为：

```text
experiment cards / registry
 -> model card
 -> project audit
 -> release bundle
 -> release gate
```

v97 已经迁移 release bundle。
v99 已经迁移 project audit。
v100 继续把 project audit 的上游 model card 迁到公共报告工具。

这样从模型说明、项目审计到发布总包，开始共享同一套 JSON 写出、HTML 转义和数据归一化基础设施。

## 关键文件

- `src/minigpt/model_card.py`
  - 删除本地 `utc_now`。
  - 删除本地 `_dict`。
  - 删除本地 `_list_of_dicts`。
  - 删除本地 `_e`。
  - 删除 `datetime/timezone` 和 `html` 直接导入。
  - 引入 `report_utils.utc_now`、`write_json_payload`、`html_escape`、`as_dict`、`list_of_dicts`。

- `tests/test_model_card.py`
  - 本版不改测试文件。
  - 原有测试继续覆盖 registry + experiment cards、missing experiment cards、输出产物和 HTML escaping。

- `README.md`
  - 当前版本更新到 v100。
  - 当前能力矩阵中的 shared report infrastructure 更新到 model card migration。
  - 增加 v100 tag 和 `c/100` 截图说明。

- `代码讲解记录_项目成熟度阶段/README.md`
  - 增加 `115-v100-model-card-report-utils.md` 索引。
  - 当前阶段基线更新到 v100。

- `c/100/解释/说明.md`
  - 解释本版六张截图分别证明什么。

## 核心迁移点

迁移前，model card 自己实现：

```python
utc_now()
write_model_card_json()
_dict()
_list_of_dicts()
_e()
```

迁移后，通用语义来自：

```python
from minigpt.report_utils import (
    as_dict as _dict,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    utc_now,
    write_json_payload,
)
```

`write_model_card_json()` 变成：

```python
def write_model_card_json(card: dict[str, Any], path: str | Path) -> None:
    write_json_payload(card, path)
```

这让 model card 的 JSON 输出和 project audit、release bundle 等模块保持一致。

## 保留本地 helper 的原因

本版没有把所有 helper 都迁到 `report_utils`。

这些 helper 保留在 `model_card.py`：

- `_string_list`
- `_as_str_list`
- `_md`
- `_fmt`
- `_fmt_delta`
- `_fmt_any`
- `_rank_label`
- `_path_link`
- `_tag_chips`
- `_generation_quality_label`

原因是它们表达的是 model card 自己的展示规则。

例如：

- `_as_str_list` 需要兼容字符串、逗号分隔字符串和 list，用来处理 tags。
- `_path_link` 根据 HTML 的 `base_dir` 生成相对链接。
- `_tag_chips` 把 tag 渲染成 HTML chip。
- `_fmt_any` 对 dict/list 有 model card 风格的显示规则。

这些不适合变成公共工具，否则 `report_utils` 会混入 model-card-specific UI 语义。

## 数据结构和字段语义

model card 的主要输出仍然包括：

- `summary`
  - `run_count`、`best_run_name`、`best_val_loss`、`ready_runs`、`review_runs`。

- `intended_use`
  - 说明这个 MiniGPT 项目适合教学、比较本地小模型实验和展示学习过程。

- `limitations`
  - 明确它不是生产级助手，validation loss 不等于生成质量。

- `coverage`
  - 统计 experiment card 覆盖率、质量检查 run、eval suite run、generation quality run。

- `top_runs`
  - 按 registry 排名筛出的候选 run。

- `runs`
  - 每个 run 的状态、loss、dataset quality、eval/generation quality、tags 和 note。

- `recommendations`
  - 根据 missing cards、review runs、non-pass generation quality 等情况生成建议。

v100 没有改变这些字段，只改变它们使用的通用写出和转义工具。

## 运行流程

model card 的流程仍然是：

```text
registry.json
 -> optional experiment_card.json files
 -> build_model_card()
 -> model_card.json
 -> model_card.md
 -> model_card.html
```

v100 只改变底层工具：

- `generated_at` 使用公共 `utc_now`。
- JSON 写出使用公共 `write_json_payload`。
- HTML 转义使用公共 `html_escape`。
- dict/list 归一化使用公共 `as_dict` 和 `list_of_dicts`。

## 测试覆盖

本版使用 `tests.test_model_card` 做行为回归。

关键断言包括：

- registry + experiment cards 能生成两个 run 的模型卡。
- best run、ready/review run、coverage 和 generation quality 统计保持不变。
- missing experiment cards 仍然会产生推荐动作。
- 输出函数仍然生成 JSON、Markdown、HTML 三类产物。
- HTML 标题和 run 名称仍然正确 escaping。

同时跑 `tests.test_report_utils`，确保公共工具行为稳定。

## 证据闭环

v100 的证据放在 `c/100`：

- `01-unit-tests.png` 证明聚焦测试、compileall 和全量 unittest 通过。
- `02-model-card-complete-smoke.png` 证明完整 registry + experiment cards 能生成正确模型卡。
- `03-model-card-missing-cards-smoke.png` 证明缺 experiment cards 的 warning/recommendation 边界仍然存在。
- `04-model-card-structure-check.png` 证明通用 helper 已迁移，model-card-specific helper 保留。
- `05-playwright-model-card-html.png` 证明 HTML 能被真实 Chrome 打开。
- `06-docs-check.png` 证明 README、`c/README.md`、讲解索引和 v100 讲解文件互相对齐。

## 一句话总结

v100 把 model card 接入公共报告基础设施，让模型说明、项目审计和发布总包这条治理链共享同一套基础工具，同时保留模型卡自己的展示语义。
