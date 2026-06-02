# v748 fixed-preserving transfer corpus materialization 代码讲解

## 本版目标和边界

v748 的目标是把 v747 生成的 fixed-preserving transfer contract patch 变成真实训练输入。

v747 解决的是“合同是否可检查、是否保留 fixed/loss direct rows、是否控制 transfer row budget”；v748 解决的是“这个合同能否被统一 materializer 消费，并产出训练 corpus 与 heldout eval fixture”。

本版不训练模型，不判断 `fixed` 或 `loss` 是否学会，也不更新模型 checkpoint。它的证据边界是数据物化：训练文本行数、eval probe 数、heldout 未泄漏、输出路径可供后续训练消费。

## 前置路线

- v745 判断 v742-v744 的 broad pair-transfer route 出现回退，应关闭该路线。
- v746 规划更轻量的 fixed-preserving transfer route，限制新增 transfer rows 为 4。
- v747 将计划落成 checked contract patch，并把新 decision 注册到 materializer。
- v748 使用已有 corpus materialization 能力读取 v747 输出目录，完成训练前数据准备。

这条路线的重点是先控制训练输入，再观察训练输出，避免在没有干净数据证据时直接解释模型行为。

## 关键复用文件

- `src/minigpt/model_capability_required_term_pair_readiness_corpus_materialization.py`
  - v748 继续复用这个通用 materializer。
  - 它定位 contract JSON，校验 source contract 状态和 decision，再写出 corpus 与 heldout fixture。
  - v747 已新增 `pair_readiness_fixed_preserving_transfer_contract_patch_ready`，所以本版无需新建 materializer。

- `scripts/run_model_capability_required_term_pair_readiness_corpus_materialization.py`
  - CLI 入口。
  - 第一个参数接收 v747 输出目录。
  - `--repeat 320` 控制每条 training row 的重复次数。
  - `--require-pass` 确保 materialization 失败会返回非零退出码。

- `e/748/解释/model-capability-required-term-pair-readiness-fixed-preserving-transfer-corpus-materialization/`
  - 保存 JSON/CSV/TXT/Markdown/HTML 报告。
  - 保存 `pair_readiness_training_corpus.txt` 和 `pair_readiness_heldout_eval_fixture.json`。
  - 这是下一版训练的直接输入。

## 输入输出结构

输入是 v747 的 contract patch：

```text
e/747/解释/model-capability-required-term-pair-readiness-fixed-preserving-transfer-contract-patch
```

核心输入字段包括：

- `status=pass`
- `decision=pair_readiness_fixed_preserving_transfer_contract_patch_ready`
- `contract.training_rows`
- `contract.evaluation_probes`
- `contract.heldout_pair_probe`

输出是 v748 的 materialization report：

```text
status=pass
decision=pair_readiness_corpus_materialized
training_line_count=6400
evaluation_probe_count=3
model_quality_claim=data_artifact_only
```

`training_line_count=6400` 的来源是：

```text
20 training rows * repeat 320 = 6400 lines
```

## 核心检查

v748 继承 materializer 的 checks：

- `contract_passed`
  - source contract 必须是 pass。

- `contract_decision`
  - source contract decision 必须属于 materializer 允许的 ready decisions。
  - v747 新增的 fixed-preserving decision 在这里被真正使用。

- `repeat_positive`
  - repeat 必须大于 0。

- `training_rows_present`
  - contract 必须有训练 rows。

- `heldout_not_in_training_rows`
  - exact heldout pair probe 不能作为训练 row。

- `heldout_not_in_corpus`
  - exact heldout pair probe 不能出现在物化后的 corpus 行中。

这些检查保护的是训练输入边界，不是模型效果。只有下一版训练和 heldout probe replay 才能评价模型行为。

## 运行证据

运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_corpus_materialization.py e\747\解释\model-capability-required-term-pair-readiness-fixed-preserving-transfer-contract-patch --out-dir e\748\解释\model-capability-required-term-pair-readiness-fixed-preserving-transfer-corpus-materialization --repeat 320 --require-pass --force
```

Playwright 快照确认 HTML 中可见：

- `Status pass`
- `Decision pair_readiness_corpus_materialized`
- `Train lines 6400`
- `Eval probes 3`
- `contract_decision pair_readiness_fixed_preserving_transfer_contract_patch_ready`

截图位于：

```text
e/748/图片/v748-fixed-preserving-transfer-corpus-materialization.png
```

## 证据链角色

v748 是 v747 contract patch 与 v749 training run 之间的数据闸口。它不扩大功能面，而是把训练输入固定下来，让后续训练失败或成功都能追溯到明确 corpus。

一句话总结：v748 把 fixed-preserving transfer route 从可检查 contract 推进到可训练 corpus，为下一版模型训练提供干净输入证据。
