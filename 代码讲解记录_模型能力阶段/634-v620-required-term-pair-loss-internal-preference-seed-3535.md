# v620 required-term pair loss-internal-preference seed 3535

## 本版目标和边界

v620 是 v619 新 objective 的第一条真实训练验证。它使用 `equals_surface_no_pair_id_loss_internal_preference_repair`，把 forced-choice 偏好行写进训练语料，然后训练 tiny checkpoint 并运行固定 replay。

本版不新增代码结构，不扩大模型规模；它只验证第一种 objective 是否产生 pair-full。

## 输入和输出

输入是 v619 注册的新 corpus mode。输出写入：

```text
e/620/解释/model-capability-required-term-pair-loss-internal-preference-seed-3535/
e/620/图片/v620-loss-internal-preference-seed-3535.png
```

核心 JSON 仍使用现有 `model_capability_required_term_pair_coexistence_refresh.json`，因为本版复用的是通用 fixed/loss coexistence refresh 链路。

## 训练链路

`scripts/run_model_capability_required_term_pair_coexistence_refresh.py` 做了三件事：

1. 用新 corpus mode 生成训练文本。
2. 调用 `scripts/train.py` 训练 char tokenizer tiny GPT。
3. 对 `fixed=` 和 `loss=` 运行默认 replay 与 newline suppression replay。

## 运行结果

```text
training_status=pass
checkpoint_exists=True
pair_full_observed=False
default_pair_full_variant_count=0
suppression_pair_full_variant_count=0
```

具体 replay 显示：

```text
fixed= -> fixed= fixe
loss=  -> fixed=fixed=
```

这说明模型保留了 fixed 分支，但 `loss=` 仍然被吸到 fixed 分支；v620 不能作为能力提升证据。

## 测试和验证

本版依赖 v619 的 corpus tests，以及真实训练命令的返回状态、checkpoint/tokenizer/metrics/train_config 存在性和 replay JSON。

HTML 报告截图证明这些字段能够被后续版本读取和复核。

## 一句话总结

v620 证明“描述内部偏好”不足以让 tiny GPT 学会 `loss=`，下一版需要转向更直接的 first-token 修复。
