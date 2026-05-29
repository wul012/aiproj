# v492 model capability required-term one-term isolation

## 本版目标和边界

v492 的目标是验证一个更小的问题：tiny GPT 在只有一个 required term 的训练条件下，是否能完成 `prompt -> term` 的短续写。

前几版已经把多 term 路线逐步缩小：

- v489 修正 prompt-leading corpus。
- v490 证明 prompt-leading 训练仍是 `0/9`。
- v491 去掉 metadata 和多模板变体，direct prompt training 仍是 `0/9`。
- v492 把 9 个 term 拆成 9 个独立 checkpoint，隔离“单目标容量”。

本版如果出现命中，也不能直接声称模型具备多任务能力。它只能证明：在没有其他 required term 干扰时，tiny 模型可以学到部分目标词级 continuation。

## 关键文件

- `src/minigpt/model_capability_required_term_one_term_isolation.py`
  - 读取 v491 direct prompt training report。
  - 为每个 term 生成独立 corpus。
  - 为每个 term 训练一个独立 tiny checkpoint。
  - 对每个 checkpoint 运行对应 scaffold prompt。
  - 汇总单目标命中数、checkpoint 数、相对 v491 的 delta。
- `src/minigpt/model_capability_required_term_one_term_isolation_artifacts.py`
  - 写出 JSON、CSV、text、Markdown 和 HTML。
- `scripts/run_model_capability_required_term_one_term_isolation.py`
  - CLI 入口，支持 repeat、训练参数、term-limit、`--force` 和 `--require-pass`。
- `tests/test_model_capability_required_term_one_term_isolation.py`
  - 覆盖 fake capacity observed、no uptake、坏 source、corpus 单目标性、产物写出和定位函数。
- `e/492/`
  - 保存真实 one-term corpora、9 个 one-term checkpoint、报告、CLI 输出和截图。

## 核心数据结构

输入是 v491 的 `model_capability_required_term_direct_prompt_training.json`，主要读取：

- `term_rows`：9 个 required term 的 `case`、`term`、`scaffold_prompt`。
- `summary.training_status`：确保 v491 训练链路本身完成。
- `summary.continuation_hit_count`：作为 previous baseline，真实值为 `0`。

每个 `isolation_row` 表示一次独立训练：

- `one_term_run_id`：例如 `02-fixed`。
- `one_term_corpus_path`：只包含当前 term 的 corpus。
- `training_status`、`checkpoint_exists`：证明独立训练产物是否可用。
- `generated`、`continuation`、`continuation_hit_count`：当前 checkpoint 的 probe 结果。

## 运行流程

1. CLI 定位 v491 report。
2. builder 读取 9 个 term row。
3. 对每个 term 创建独立语料：

```text
fixed:fixed
fixed: fixed
```

4. 调用 `_train_micro_checkpoint`，每个 term 输出一个独立 `checkpoint.pt`。
5. 调用 `_generation_row`，只用当前 term 对应 prompt 测当前 checkpoint。
6. 汇总 `training_pass_count`、`checkpoint_exists_count`、`continuation_hit_count`、`term_with_continuation_hit_count`。
7. 写出 JSON/CSV/text/Markdown/HTML 和截图证据。

## 真实结果

```text
status=pass
decision=required_term_one_term_capacity_observed
one_term_isolation_decision=one_term_isolation_capacity_observed
term_count=9
isolation_count=9
training_pass_count=9
checkpoint_exists_count=9
continuation_hit_count=5
term_with_continuation_hit_count=5
term_success_rate=0.5556
previous_continuation_hit_count=0
continuation_hit_delta=5
single_term_capacity_observed=True
model_quality_claim=one_term_capacity_signal_only
```

命中的 term 是 `fixed`、`text`、`loss`、`four`、`chain`。未命中的 term 是 `because`、`data`、`real`、`while`。

这个结果改变了前几版的判断：v491 的失败不是因为 tiny 模型完全没有记住 prompt-to-term 的能力，而是多个 target term 放在同一训练分布里时，模型还不能稳定按 prompt 条件选择正确目标。

## 测试覆盖

测试保护了几个关键点：

- fake generation 命中时，报告必须输出 `required_term_one_term_capacity_observed`。
- fake generation 不命中时，结构仍然 `pass`，但能力结论必须保持 no-uptake。
- one-term corpus 只能包含当前 target，不能混入其他 term。
- v491 source training 状态异常时，v492 必须 fail。
- JSON/CSV/text/Markdown/HTML 必须全部写出。

这些测试确保 v492 不会把多 term 训练结果误用成单 term 证据，也避免把训练成功误判为能力提升。

## 证据角色

- JSON 是后续 seed stability 或 small-group curriculum 可以消费的主证据。
- CSV 用于逐 term 查看命中和生成预览。
- HTML 与截图用于人工复核 9 个 one-term run。
- `one-term-corpora/` 保存每个 term 的训练输入。
- `one-term-runs/` 保存每个 term 的 checkpoint/tokenizer/metrics/run manifest。

## 一句话总结

v492 首次在 required-term 路线上观察到正向模型能力信号：单目标条件下 tiny GPT 能命中部分 required term，但多目标条件选择仍未解决。
