# v96 generation quality report utility migration

## 本版目标

v96 的目标是把 `generation_quality.py` 中与公共 `report_utils.py` 语义一致的报告基础设施迁移出去，同时保留本模块特有的显示格式化规则。

v83-v95 主要围绕 training scale 和 promoted 链路做收口。v96 开始把公共报告工具层扩展到模型输出质量证据上。generation quality 是评估链路中很关键的一层：它读取 eval suite 或 sample lab 输出，检查 continuation 长度、多样性、重复、prompt echo 等问题，然后给 registry、model card、project audit 和 release gate 提供质量证据。

本版解决的问题是：`generation_quality.py` 原本也保留了私有 `utc_now`、`_list_of_dicts`、`_dict`、`_e` 和 JSON writer。这些与 `report_utils.py` 的语义一致，可以安全迁移。

## 本版明确不做什么

v96 不改变 generation quality 的判定策略。

保持不变的边界包括：

- `min_continuation_chars`、`min_unique_ratio`、`max_repeat_run`、`max_repeated_ngram_ratio`、`ngram_size` 的含义不变。
- empty continuation 仍然 fail。
- too short 仍然 fail。
- low diversity、long repeat run、high ngram repetition、prompt echo 仍然 warn。
- eval_suite、sample_lab、generic_results 的输入解析不变。
- JSON/CSV/Markdown/SVG/HTML 的字段结构不变。
- CLI `scripts/analyze_generation_quality.py` 的参数和输出语义不变。

本版也不强行迁移所有 helper。`_md` 和 `_string_list` 保留在模块内，因为它们有 generation quality 的本地语义：

- `_md` 会把 `None` 显示为 `missing`，并用 `_fmt_any` 处理 float。
- `_string_list` 会过滤空字符串，适合 warnings/recommendations 的 HTML 列表展示。

这两个 helper 和公共 `markdown_cell`、`string_list` 不是完全同义，直接替换会改变报告显示细节。

## 来自哪条路线

v83 新增 `report_utils.py`，后续版本主要迁移 training scale evidence。
v96 则把同一套公共报告基础设施扩展到 generation quality：

```text
eval suite / sample lab
 -> generation quality
 -> registry / model card / project audit / release gate
```

这说明公共工具层开始覆盖“模型输出质量证据”，不再只服务训练规模治理链路。

## 关键文件

`src/minigpt/generation_quality.py`

这是本版核心迁移文件。它继续负责读取生成样本，构造 case rows、flags、summary、recommendations、warnings，并输出 JSON/CSV/Markdown/SVG/HTML。

`src/minigpt/report_utils.py`

这是公共报告工具层。本版复用：

```text
as_dict as _dict
html_escape as _e
list_of_dicts as _list_of_dicts
utc_now
write_json_payload
```

`tests/test_generation_quality.py`

这是 generation quality 业务测试。它保护 pass/warn/fail 分类、sample_lab 输入解析、输出文件、HTML escaping 和阈值校验。

`tests/test_report_utils.py`

继续保护公共工具本身。v96 让 generation quality 成为新的消费者，因此公共层测试也属于本版的回归边界。

`scripts/analyze_generation_quality.py`

这是 CLI 入口。本版不改参数，只用它做 eval_suite 和 sample_lab smoke，证明迁移后两类来源仍然可用。

`c/96/`

保存本版运行截图和解释，包括 tests、smoke、结构检查、Playwright HTML 和文档对齐检查。

## 迁移前的重复点

迁移前，`generation_quality.py` 自己维护：

```text
utc_now
_list_of_dicts
_dict
_e
```

并手写 JSON 输出：

```text
Path(...).write_text(json.dumps(..., ensure_ascii=False, indent=2))
```

SVG 写出中还直接调用 `html.escape`。v96 把这些全部统一到公共 `html_escape` 和 `write_json_payload`。

## 保留的本地 helper

`_md`

它不是普通 Markdown cell。它会先经过 `_fmt_any`，让 `None` 显示为 `missing`，让 float 使用较短格式。这是 generation quality 报告的显示语义。

`_string_list`

它会过滤空字符串。公共 `string_list` 会保留空字符串对应的 `""`，不完全等价。generation quality 的 recommendations/warnings 列表更适合过滤空项。

这些保留不是遗漏，而是为了避免“统一工具”反而改变报告输出。

## 核心数据结构

`cases`

每个 case 表示一个 prompt/generation 的质量检查结果，关键字段包括：

```text
name
prompt
generated
continuation
char_count
unique_char_count
unique_ratio
repeated_ngram_ratio
longest_repeat_run
flags
status
continuation_preview
```

`flags`

每个 flag 由 `id`、`level`、`detail` 组成：

```text
empty_continuation
too_short
low_diversity
long_repeat_run
high_ngram_repetition
prompt_echo
```

其中 `fail` 会把 case status 变成 fail，只有 warn 时 status 为 warn，没有 flags 时 status 为 pass。

`summary`

summary 给 registry、model card、project audit 和 release gate 使用：

```text
overall_status
source_type
case_count
pass_count
warn_count
fail_count
avg_continuation_chars
avg_unique_ratio
avg_repeated_ngram_ratio
max_repeat_run
```

## 输出格式说明

`generation_quality.json`

这是机器可读质量证据。v96 只把写出动作替换为 `write_json_payload`，字段结构不变。

`generation_quality.csv`

这是 case 行级表格，用于快速查看每条样本的 status、flags 和 continuation preview。

`generation_quality.md`

这是人读版，包含 summary、policy、cases、recommendations 和 warnings。v96 保留本地 `_md`，避免 Markdown 中 `missing` 和 float 显示规则变化。

`generation_quality.svg`

这是可视化证据，用彩色条展示 unique ratio，用灰色条展示 repeated ngram ratio。v96 把 SVG 文本转义改为公共 `_e`。

`generation_quality.html`

这是浏览器证据，展示 stats、case table、recommendations 和 warnings。v96 复用公共 `html_escape`。

## 运行流程

主流程保持不变：

```text
build_generation_quality_report
 -> _read_required_json
 -> _infer_source_type
 -> _build_case_rows
 -> _build_summary
 -> _recommendations
 -> _warnings
 -> write_generation_quality_outputs
```

其中 `_build_case_rows` 是质量判定核心，v96 没有改动。

## 测试如何覆盖链路

`test_build_generation_quality_report_marks_pass_warn_fail`

构造 pass、warn、fail 三类 eval suite 结果，断言 overall status 为 fail，并确认 low_diversity 和 empty_continuation flags 存在。

`test_build_generation_quality_report_reads_sample_lab_generated_text`

构造 sample_lab 输出，断言 source_type 为 sample_lab，并确认 continuation preview 仍然从 generated 文本中正确切出。

`test_write_generation_quality_outputs`

确认 JSON、CSV、Markdown、SVG、HTML 都能写出。v96 的 SVG 转义迁移也由这个测试覆盖。

`test_render_generation_quality_html_escapes_text`

用 `<Quality>` 和 `<script>` 输入，确认 HTML 仍然转义。

`test_generation_quality_rejects_bad_thresholds`

确认不合法阈值仍会抛出 `ValueError`。

## 本版证据

v96 证据归档在：

```text
c/96/图片
c/96/解释/说明.md
```

关键截图包括：

- focused tests、compile check 和 full regression。
- eval suite smoke，证明 pass/warn/fail 分类仍然正确。
- sample lab smoke，证明 sample_lab 输入仍然可解析。
- 结构检查，确认公共 helper 已引用、私有同义 helper 已移除、模块特有 helper 被保留。
- Playwright/Chrome 打开生成后的 HTML 报告。
- README、阶段索引和 `c/README.md` 的 v96 文档检查。

## 后续推进原则

后续迁移 generation quality 相邻模块时要保持同样原则：

- 公共 helper 只有语义一致时才替换。
- 模块特有的格式化、筛选、业务判定 helper 不强行迁移。
- 迁移后必须保留至少一条输入 smoke 和一条浏览器证据。

## 一句话总结

v96 把 generation quality 的公共报告基础设施迁移到 `report_utils`，让模型输出质量证据也加入共享报告层，同时保留本模块特有的显示格式化语义。
