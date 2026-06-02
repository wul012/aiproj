# v715 structured-template corpus materialization

## 本版目标和边界

v715 的目标是把 v714 的 structured-template contract 变成真实可训练文件。

本版不训练模型，不解释模型输出，也不修改训练器。它只确认：

- v714 contract 能被 materializer 读取。
- training corpus 能写入磁盘。
- heldout eval fixture 能写入磁盘。
- pair probe 不泄漏到 corpus。

## 前置链路

```text
v713 repair comparison -> loss-retention prefix route regressed
v714 structured-template contract -> prompt-answer rows, contract_only
v715 corpus materialization -> pair_readiness_training_corpus.txt + heldout fixture
```

v715 的输入目录是：

```text
e/714/解释/model-capability-required-term-pair-readiness-structured-template-contract
```

## 关键修改

`src/minigpt/model_capability_required_term_pair_readiness_corpus_materialization.py` 做了一个小但必要的维护性修复：

```text
PAIR_READINESS_CONTRACT_JSON_FILENAMES = (
    split contract json,
    loss-retention contract patch json,
    structured-template contract json,
)
```

之前 CLI 输入目录时只默认查找 split contract 文件。v715 扩展为按已知 contract 文件名探测，让 materializer 可以直接接受 v710 或 v714 这类后续 contract 输出目录。

这里特意没有 import v710/v714 builder 模块，因为它们会间接拉起 training run，再回到 materializer，形成循环依赖。文件名表用字符串维护，是为了让 locator 轻量、稳定、无副作用。

## 运行产物

v715 输出目录：

```text
e/715/解释/model-capability-required-term-pair-readiness-structured-template-corpus-materialization/
```

核心文件：

- `pair_readiness_training_corpus.txt`
  - 真实训练 corpus。
  - 14 条 structured rows 重复 320 次，共 4480 行。

- `pair_readiness_heldout_eval_fixture.json`
  - heldout replay fixture。
  - 保留 `fixed=`、`loss=`、`fixed=|loss=` 三个 probes。

- `model_capability_required_term_pair_readiness_corpus_materialization.json`
  - materialization report。
  - 记录 source contract、settings、paths、checks 和 summary。

## 校验逻辑

v715 继承 materializer 的关键 check：

- `contract_passed`
  - v714 contract 必须 pass。

- `contract_decision`
  - v714 decision 必须在 ready contract 白名单里。

- `repeat_positive`
  - repeat 必须大于 0。

- `training_rows_present`
  - contract 必须提供足够 training rows。

- `heldout_not_in_training_rows`
  - `fixed=|loss=` 不能是 training row。

- `heldout_not_in_corpus`
  - `fixed=|loss=` 也不能作为重复后的 corpus line。

## 测试覆盖

新增测试覆盖了 structured-template 输出目录定位：

```text
locate_pair_readiness_corpus_materialization_source(root)
 -> model_capability_required_term_pair_readiness_structured_template_contract.json
```

同时重跑了 structured-template contract 与 corpus materialization focused tests，确认 locator 修复没有引入循环依赖。

## 运行证据

运行截图：

- `e/715/图片/v715-structured-template-corpus-materialization.png`

关键输出：

```text
status=pass
decision=pair_readiness_corpus_materialized
training_line_count=4480
evaluation_probe_count=3
model_quality_claim=data_artifact_only
```

`model_quality_claim=data_artifact_only` 表示这版只证明训练输入存在且无泄漏，不代表模型能力提升。

## 一句话总结

v715 把 structured-template contract 落成真实训练 corpus，并顺手修复 materializer 目录输入定位，让后续训练链路更顺滑可维护。
