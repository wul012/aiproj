# v707 pair-readiness training run

## 本版目标和边界

v707 的目标是基于 v706 的 materialized corpus 做真实训练，并用 heldout direct probes 检查结果。

本版不直接做 promotion，不使用 heldout pair probe；它只回答一个问题：训练在明确 split 后，是否至少能同时命中 `fixed=` 和 `loss=` 两个 direct probes。

## 前置链路

v706 生成：

```text
pair_readiness_training_corpus.txt
pair_readiness_heldout_eval_fixture.json
```

v707 读取 materialization report，通过其中的 corpus path 启动训练，并从 fixture 中取 direct probes。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_readiness_training_run.py`
  - 训练 run builder。
  - 复用现有 training subprocess wrapper。
  - 复用 generation profile replay。
  - 生成 summary 和 interpretation。

- `src/minigpt/model_capability_required_term_pair_readiness_training_run_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 展示 replay variants。

- `scripts/run_model_capability_required_term_pair_readiness_training_run.py`
  - CLI。
  - 输入 v706 materialization JSON 或目录。

- `tests/test_model_capability_required_term_pair_readiness_training_run.py`
  - 使用 fake train/fake generate 覆盖 pair-full、no pair-full、corpus missing 和输出格式。

## 运行流程

流程：

```text
读取 v706 materialization
确认 training corpus 存在
调用 scripts/train.py 训练 tiny checkpoint
构造 heldout direct source report
调用 generation profile replay
汇总 pair_full_observed
```

direct probes：

```text
fixed=
loss=
```

## 真实结果

输出：

```text
decision=pair_readiness_training_no_pair_full
checkpoint_exists=True
pair_full_observed=False
default_continuation_hit_count=1
```

生成样本：

```text
fixed= -> fixed=fixed=fixed=
loss=  -> loss=fixed=fixed=
```

因此 v707 是一次真实负结果：训练成功，但 loss direct probe 被 fixed 分支吸附。

## 为什么这版仍有价值

和 v696-v702 不同，v707 的训练输入已经来自 checked contract，heldout direct probes 也从 fixture 中读取。失败不能再简单归因于“报告不规范”或“训练/评估混在一起”。

这说明后续方向应该检查 fixed 分支为什么支配 loss，而不是继续增加同类训练行。

## 一句话总结

v707 在明确 train/eval split 后做了真实训练，结果仍是 fixed-only，为下一步 heldout failure diagnostic 提供了干净负样本。
