# v28 Generation Quality 代码讲解

v28 增加的是生成质量分析层。前面的 eval suite 能固定 prompt 跑生成结果，sampling lab 能比较采样参数，但它们主要保存“生成了什么”。本版继续往后做一步：检查这些生成结果是否太短、太重复、字符多样性太低，或者像是在复读 prompt。

核心文件：

```text
src/minigpt/generation_quality.py
scripts/analyze_generation_quality.py
tests/test_generation_quality.py
```

## 角色

`generation_quality.py` 读取两类已有产物：

```text
eval_suite.json
sample_lab.json
```

然后输出：

```text
generation_quality.json
generation_quality.csv
generation_quality.md
generation_quality.svg
generation_quality.html
```

它不替代 loss，也不替代人工评估，而是给 MiniGPT 增加一组轻量的生成质量信号。

## 核心入口

入口函数是：

```python
def build_generation_quality_report(
    source_path: str | Path,
    *,
    source_type: str = "auto",
    min_continuation_chars: int = 8,
    min_unique_ratio: float = 0.25,
    max_repeat_run: int = 8,
    max_repeated_ngram_ratio: float = 0.65,
    ngram_size: int = 2,
    title: str = "MiniGPT generation quality report",
    generated_at: str | None = None,
) -> dict[str, Any]:
```

它的流程是：

```text
读取 JSON
 -> 自动判断 source_type
 -> 遍历 results
 -> 计算每个 case 的 metrics
 -> 根据阈值生成 flags
 -> 汇总 pass / warn / fail
 -> 输出完整 report
```

## Source Type

`_infer_source_type` 会根据字段判断来源：

```text
有 case_count 和 avg_continuation_chars -> eval_suite
有 prompt 和 max_new_tokens -> sample_lab
否则 -> generic_results
```

这样脚本既能接 eval suite，也能接 sampling lab，后续接别的生成结果也比较自然。

## Metrics

每个生成样本会计算这些指标：

```text
char_count
stripped_char_count
unique_char_count
unique_ratio
repeated_ngram_ratio
longest_repeat_run
continuation_preview
```

其中：

- `unique_ratio` 表示非空白字符中有多少比例是不重复字符。
- `repeated_ngram_ratio` 表示 n-gram 重复程度，默认看 bigram。
- `longest_repeat_run` 表示最长连续重复字符长度。

这些指标都很朴素，但对小模型很有用，因为小模型常见问题就是空输出、复读、低多样性和循环。

## Flags

`_flags` 会把指标转成问题标记：

```text
empty_continuation -> fail
too_short -> fail
low_diversity -> warn
long_repeat_run -> warn
high_ngram_repetition -> warn
prompt_echo -> warn
```

每个 flag 都包含：

```json
{
  "id": "low_diversity",
  "level": "warn",
  "detail": "Unique ratio 10.0% is below 25.0%."
}
```

这样既方便人读，也方便后续 model card、audit、release gate 继续消费。

## Status 汇总

每个 case 的状态由 flags 决定：

```text
有 fail flag -> fail
没有 fail 但有 warn flag -> warn
没有 flags -> pass
```

整体状态也类似：

```text
有失败 case -> overall_status = fail
没有失败但有 warning case -> overall_status = warn
全部通过 -> overall_status = pass
```

这让报告能快速告诉你：这批生成样本只是“有点需要看”，还是“不能作为候选结果”。

## CLI 脚本

命令行入口是：

```powershell
python scripts/analyze_generation_quality.py --input runs/minigpt/eval_suite/eval_suite.json --out-dir runs/minigpt/generation-quality
```

它会打印：

```text
source_type=eval_suite
overall_status=fail
cases=4
checks=2 pass/1 warn/1 fail
outputs={...}
```

阈值可以通过参数调整，例如：

```powershell
--min-continuation-chars 8
--min-unique-ratio 0.25
--max-repeat-run 8
--max-repeated-ngram-ratio 0.65
```

## 输出格式

JSON 是主格式，保留完整结构。

CSV 方便表格分析。

Markdown 方便粘贴到报告。

SVG 画出 unique ratio 和 repeated n-gram ratio 的简图。

HTML 用于浏览器审阅，每个 case 会展示状态、长度、多样性、重复率、最长重复和 flags。

## 测试覆盖

`tests/test_generation_quality.py` 覆盖：

- eval suite 输入能产生 pass/warn/fail。
- sample lab 输入可以从 `generated` 自动截出 continuation。
- JSON/CSV/Markdown/SVG/HTML 输出存在。
- HTML 会转义 `<script>`。
- 非法阈值会报错。

## 一句话总结

v28 把 MiniGPT 的评估从“固定 prompt 生成文本”推进到“对生成文本做轻量质量诊断”：它开始回答模型生成是否太短、太重复、太缺少多样性。
