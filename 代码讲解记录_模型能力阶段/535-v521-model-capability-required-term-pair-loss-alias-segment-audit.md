# v521 required-term pair loss-alias segment audit 代码讲解

## 本版目标与边界

v521 的目标是解释 v518/v520 里的 normalized full signal 为什么不是 strict full。v520 已经确认 focused repair 后出现了 normalized full；本版进一步分析 continuation，把 strict miss 拆成具体的 separator/token 形态。

本版不训练、不生成、不修改 checkpoint 或 tokenizer。它只读取 v518 focus report 的 `generation_rows`，并在可能时加载对应 tokenizer，输出只读审计报告。

## 前置链路

前置版本：

- v518：focus report 显示 strict support `0/4`，normalized support `4/4`。
- v520：source/focus contrast 显示 normalized gain delta 为 `4`。

v521 接在 v520 后面，目标是定位这个 gain 的文本形态来源。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_loss_alias_segment_audit.py`
  - 新增只读 segment audit builder。
  - 从 focus seed reports 中读取 generation rows。
  - 使用 `normalize_for_required_term()` 复用 v518 的 normalization 规则。
  - 尝试用 `load_tokenizer()` 加载 seed tokenizer，记录 token pieces preview。
- `src/minigpt/model_capability_required_term_pair_loss_alias_segment_audit_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
  - HTML 表格展示 case、strict、normalized、gain、separator、tokens 和 token pieces。
- `scripts/run_model_capability_required_term_pair_loss_alias_segment_audit.py`
  - CLI 接收 v518 focus JSON 或目录。
- `tests/test_model_capability_required_term_pair_loss_alias_segment_audit.py`
  - 用 fake `lo\ns\ns` continuation 验证 newline split 分类。

## 核心数据结构

case row 字段：

- `strict_hit`
- `normalized_hit`
- `normalization_gain`
- `separator_kind`
- `separator_text`
- `alnum_segment_count`
- `normalized_continuation`
- `normalized_expected_index`
- `tokenizer_loaded`
- `tokenizer_name`
- `token_count`
- `token_pieces_preview`

summary 字段：

- `segment_audit_decision`
- `strict_miss_normalized_hit_count`
- `normalization_gain_count`
- `newline_gain_count`
- `space_gain_count`
- `mixed_gain_count`
- `tokenizer_loaded_count`
- `dominant_separator_kind`

这些字段把 normalized hit 从“统计现象”转成“输出形态证据”。

## 核心流程

1. CLI 定位 v518 focus JSON。
2. Builder 校验 source report 为 `status=pass` 且存在 seed reports。
3. `_audit_rows()` 遍历每个 generation row。
4. `_segment_shape()` 查找 expected term 的字符是否被非字母数字分隔。
5. `_token_shape()` 尝试加载 tokenizer 并输出 token pieces preview。
6. `_summary()` 汇总 gain 的 separator 分布。

整个流程不改变上游产物，只产生新的解释性证据。

## 真实结果解释

v521 真实运行结果：

```text
strict_miss_normalized_hit_count=4
normalization_gain_count=4
newline_gain_count=4
space_gain_count=0
mixed_gain_count=0
tokenizer_loaded_count=4
dominant_separator_kind=newline
```

四个 strict miss 都是 normalized hit，而且四个 gain 都来自 newline split。CSV 中的 token pieces 也显示 char tokenizer 把 continuation 拆成类似 `l|o|s|\n|s` 的形态。这说明问题更接近 decoding/stop-token/换行控制，而不是模型完全不知道 `loss`。

## 测试覆盖

测试覆盖：

- fake `lo\ns\ns` 能被识别为 `loss_alias_segment_newline_split`。
- tokenizer 能被加载并记录 token row。
- artifact writer 输出五类文件。
- 缺少 seed reports 时结构失败。

这些断言保护本版边界：segment audit 是解释 strict/normalized 差异，不是替代训练评估。

## 运行证据

运行证据归档在：

```text
e/521/解释/model-capability-required-term-pair-loss-alias-segment-audit/
e/521/图片/
```

截图：

```text
e/521/图片/01-model-capability-required-term-pair-loss-alias-segment-audit.png
```

## 一句话总结

v521 把 loss-alias normalized full 的原因定位为 newline segmentation，为下一步 decoding cleanup 实验提供了直接依据。
