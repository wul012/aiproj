# v714 pair-readiness structured-template contract

## 本版目标和边界

v714 的目标是把 v713 的负面结论转成下一条训练路线的 contract。

v713 已经确认 loss-retention prefix repair 回归：

```text
decision=pair_readiness_loss_retention_patch_regressed
default_hit_delta=-1
```

所以 v714 不继续加 `loss=lo`、`loss=los` 之类单边 prefix 权重，也不训练模型。它只做一件事：生成一个结构化模板 contract，让后续 materialize/train 继续复用已有链路。

## 前置链路

```text
v704 split plan
 -> v705 split contract
 -> v706 corpus materialization
 -> v707 real tiny training
 -> v708 failure diagnostic
 -> v709 loss-retention plan
 -> v710 contract patch
 -> v711 patched materialization
 -> v712 patched training
 -> v713 repair comparison: patch regressed
 -> v714 structured-template contract
```

v714 的输入是 `e/713/解释/model-capability-required-term-pair-readiness-repair-comparison/model_capability_required_term_pair_readiness_repair_comparison.json`。

## 关键新增和修改文件

- `src/minigpt/model_capability_required_term_pair_readiness_structured_template_contract.py`
  - 新 contract builder。
  - 读取 v713 comparison。
  - 校验 source comparison 是否为 pass、decision 是否为 `pair_readiness_loss_retention_patch_regressed`、default hit delta 是否小于 0。
  - 输出 `contract.training_rows`、`contract.evaluation_probes`、`summary`、`interpretation`。

- `src/minigpt/model_capability_required_term_pair_readiness_structured_template_contract_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 报告展示 structured rows、checks、source delta 和 next action。

- `scripts/run_model_capability_required_term_pair_readiness_structured_template_contract.py`
  - CLI 入口。
  - 输入 v713 comparison JSON 或目录。
  - 输出到指定 `--out-dir`，支持 `--require-pass` 与 `--force`。

- `src/minigpt/model_capability_required_term_pair_readiness_corpus_materialization.py`
  - 扩展 ready contract decision 白名单。
  - 让既有 materializer 接受 `pair_readiness_structured_template_contract_ready`。
  - 这是窄改动，不复制 materialize 逻辑。

- `tests/test_model_capability_required_term_pair_readiness_structured_template_contract.py`
  - 覆盖 contract ready、可被 materializer 消费、错误 source 阻断、eval prompt 不重叠、输出格式。

## 核心数据结构

v714 的 contract 使用 14 条结构化模板训练行，例如：

```text
task: complete required term | prompt: fixed= | answer: fixed
task: complete required term | prompt: loss= | answer: loss
case=fixed | prompt=fixed= | expected=fixed | answer=fixed
case=loss | prompt=loss= | expected=loss | answer=loss
```

这些行和 v710 的区别在于：

- v710 只是增加 loss 前缀重复行。
- v714 把 prompt、expected、answer 写进同一条结构化样本。
- v714 同时保留 fixed/loss 两边，避免继续单边修补。

heldout probes 仍然是：

```text
fixed=
loss=
fixed=|loss=
```

其中 `fixed=|loss=` 仍是 pair probe，不进入 training rows。

## 校验逻辑

主要 check 包括：

- `source_comparison_passed`
  - v713 comparison 必须是 pass。

- `source_comparison_decision`
  - 必须明确是 `pair_readiness_loss_retention_patch_regressed`。

- `prior_route_regressed`
  - v713 summary 必须确认 candidate 回归。

- `prior_default_delta_negative`
  - `default_hit_delta` 必须小于 0。

- `no_exact_eval_row_overlap`
  - training rows 不能与 eval prompts 精确重叠。

- `heldout_pair_absent`
  - `fixed=|loss=` 不能出现在 training rows。

这些 check 的作用是让 v714 只在“上一条 repair 路线已经被真实对比关闭”的前提下生成新 contract，避免随意扩展训练语料。

## 输出和证据

运行证据在：

- `e/714/解释/model-capability-required-term-pair-readiness-structured-template-contract/`
- `e/714/图片/v714-pair-readiness-structured-template-contract.png`

关键输出：

```text
status=pass
decision=pair_readiness_structured_template_contract_ready
failed_count=0
contract_ready=True
structured_training_row_count=14
source_default_hit_delta=-1
model_quality_claim=contract_only
```

`model_quality_claim=contract_only` 很重要：它说明这版只是准备更合理的训练输入，不证明模型已经学会 pair readiness。

## 测试覆盖

测试覆盖了五个边界：

- 正常 v713 comparison 能生成 ready contract。
- 新 contract 能被现有 corpus materializer materialize。
- source decision 不是 regression 时会 fail。
- training rows 与 eval prompts 没有精确重叠。
- JSON/CSV/TXT/Markdown/HTML 都能输出。

这组测试保护的重点不是 UI，而是 contract 能否安全进入既有训练链。

## 一句话总结

v714 把 v713 的失败修复路线转成结构化模板训练 contract，让项目从单边 prefix weighting 转向更可复核的 prompt-answer 目标。
