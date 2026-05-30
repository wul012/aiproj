# v522 required-term pair loss-alias decode cleanup 代码讲解

## 本版目标与边界

v522 的目标是验证 v521 发现的 newline segmentation 是否可以通过有边界的 decode cleanup 恢复 strict surface hit。它不是改模型，也不是把 normalized hit 当作 strict hit，而是比较清理策略对同一批 v518 continuation 的影响。

本版不训练、不生成、不改 checkpoint。它只读取 v518 focus metrics，输出 cleanup strategy audit。

## 前置链路

前置版本：

- v521：确认 4/4 normalization gains 全部来自 newline split。
- v520：确认 focus 阶段相对 source 阶段新增 normalized full signal。
- v518：提供真实 focus generation rows。

v522 顺着 v521 的 next action，测试 remove-newlines 是否足以解释 strict miss。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_loss_alias_decode_cleanup.py`
  - 新增 cleanup audit builder。
  - 定义 `raw`、`strip`、`remove_newlines`、`collapse_whitespace`、`remove_all_whitespace`、`alnum_only` 六种策略。
  - 计算每个 case 的 strategy hits 和 minimal recovery strategy。
- `src/minigpt/model_capability_required_term_pair_loss_alias_decode_cleanup_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
  - HTML 表格展示 raw 与 cleanup 策略对比。
- `scripts/run_model_capability_required_term_pair_loss_alias_decode_cleanup.py`
  - CLI 接收 v518 focus JSON 或目录。
- `tests/test_model_capability_required_term_pair_loss_alias_decode_cleanup.py`
  - 用 fake newline-split continuation 验证 remove-newlines full recovery。

## 核心数据结构

case row 字段：

- `raw_hit`
- `normalized_hit`
- `normalization_gain`
- `remove_newlines_hit`
- `collapse_whitespace_hit`
- `remove_all_whitespace_hit`
- `alnum_only_hit`
- `minimal_recovery_strategy`
- `continuation_preview`
- `remove_newlines_preview`

summary 字段：

- `decode_cleanup_decision`
- `raw_hit_count`
- `remove_newlines_hit_count`
- `collapse_whitespace_hit_count`
- `remove_all_whitespace_hit_count`
- `alnum_only_hit_count`
- `remove_newlines_full_coverage`
- `minimal_recovery_strategy`

这些字段让报告能区分“需要很宽泛 normalization”与“只需 newline cleanup”。

## 核心流程

1. CLI 定位 v518 focus JSON。
2. Builder 校验 source focus report。
3. `_cleanup_rows()` 遍历 generation rows。
4. `_strategy_hits()` 对每条 continuation 应用多个 cleanup 策略。
5. `_summary()` 汇总每种策略恢复了多少 case。
6. artifact writer 输出可审计证据。

流程全程只读，不会修改原始 generation rows。

## 真实结果解释

v522 真实运行结果：

```text
raw_hit_count=0
remove_newlines_hit_count=4
collapse_whitespace_hit_count=0
remove_all_whitespace_hit_count=4
alnum_only_hit_count=4
minimal_recovery_strategy=remove_newlines
```

这说明恢复 strict surface 不需要删除所有非字母数字字符；仅移除 newline 就够。换句话说，当前问题更像 generation 输出中的换行边界，而不是语义记忆失败。

## 测试覆盖

测试覆盖：

- newline split continuation 经 `remove_newlines` 后 2/2 恢复。
- artifact writer 输出五类文件。
- 缺少 seed reports 时结构失败。

这些断言保护本版边界：cleanup audit 是后处理假设检验，不会改变模型真实输出。

## 运行证据

运行证据归档在：

```text
e/522/解释/model-capability-required-term-pair-loss-alias-decode-cleanup/
e/522/图片/
```

截图：

```text
e/522/图片/01-model-capability-required-term-pair-loss-alias-decode-cleanup.png
```

## 一句话总结

v522 把 newline segmentation 进一步验证为可由 remove-newlines 恢复的 strict surface 问题，下一步应做 bounded cleanup evaluation。
