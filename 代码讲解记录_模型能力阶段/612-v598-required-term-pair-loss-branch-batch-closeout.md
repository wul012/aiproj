# v598 required-term pair loss-branch batch closeout

## 本版目标和边界

v598 是 v589-v598 十版批次的收口版本。它新增一个 closeout artifact，把本轮 loss-branch 实验链路合并成单一判断：loss 分支已经稳定可见，但 pair-full 仍然失败，下一步必须转向 fixed-retention objective。

本版不训练模型，不新增语料，也不把治理证据包装成模型质量提升。它只回答一个问题：这一轮 loss-branch 是否还值得继续按原方向推进。

## 前置路线

本版承接以下版本：

```text
v589 corpus modes
v590 targeted seed
v591 dual-anchor seed
v592 micro-span seed
v593 objective comparison
v594 route decision
v595 targeted seed stability
v596 missed-seed diagnostic
v597 fixed-retention readiness
```

这些版本共同说明：`loss` 分支可以被模型命中，但 `fixed` 分支在 first-token 层面仍然掉落。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_loss_branch_batch_closeout.py
src/minigpt/model_capability_required_term_pair_loss_branch_batch_closeout_artifacts.py
scripts/run_model_capability_required_term_pair_loss_branch_batch_closeout.py
tests/test_model_capability_required_term_pair_loss_branch_batch_closeout.py
e/598/解释/model-capability-required-term-pair-loss-branch-batch-closeout/
```

## 核心数据结构

`evidence_rows` 是本版的主证据表，每行包含：

```text
version
label
path
status
decision
key_result
```

它把九个来源统一成一张表，方便人工审阅，也方便后续脚本消费。

`summary` 保留批次级判断字段：

```text
single_seed_pair_full_count
comparison_loss_only_tradeoff_report_count
stability_pair_full_seed_count
diagnostic_first_token_gap_count
readiness_ready_for_design
```

这些字段共同决定 closeout 是否通过。

## 运行流程

CLI 接收九个输入目录或 JSON 文件：

```text
--corpus-contract
--targeted-seed
--dual-anchor-seed
--micro-span-seed
--comparison
--route-decision
--stability
--diagnostic
--readiness
```

每个输入会先通过 `locate_loss_branch_batch_report()` 定位 JSON。如果目录中没有对应文件，或者同名文件不唯一，就会失败，避免 closeout 读错证据。

随后 builder 汇总字段并生成：

```text
status=pass
decision=close_loss_branch_batch_and_start_fixed_retention_objective
```

## 输出产物

本版输出 JSON、CSV、TXT、Markdown、HTML：

```text
model_capability_required_term_pair_loss_branch_batch_closeout.json
model_capability_required_term_pair_loss_branch_batch_closeout.csv
model_capability_required_term_pair_loss_branch_batch_closeout.txt
model_capability_required_term_pair_loss_branch_batch_closeout.md
model_capability_required_term_pair_loss_branch_batch_closeout.html
```

其中 JSON 是后续程序消费的主证据；HTML 和截图用于人工审阅；CSV 用于快速比较 evidence rows。

## 测试覆盖

测试覆盖了：

- 正常 loss-only 到 fixed-retention 路线时 closeout pass。
- stability 如果出现 pair-full，会触发 fail，避免结论与证据不一致。
- JSON/CSV/TXT/Markdown/HTML 全格式输出。
- 嵌套目录定位 JSON。
- CLI 在 `--require-pass` 和坏输入下返回非零。

本地验证还额外跑了本轮相关测试与全量测试：

```text
42 passed
1187 passed
source encoding: status=pass, clean_count=684
```

## 一句话总结

v598 把 v589-v597 的训练和诊断结果收敛为下一步路线：关闭 loss-branch 批次，进入 fixed-retention objective。
