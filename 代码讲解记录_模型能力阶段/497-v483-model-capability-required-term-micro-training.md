# v483：model capability required-term micro-training

## 本版目标和边界

v483 的目标是把 v482 的 probe 结论推进一步：v482 证明现有归档 tiny checkpoint 即使看到 `data:` 这样的 required-term scaffold，也不会在 continuation 中稳定复现 required term；v483 不再只读归档，而是构造一个小的定向训练语料，训练新的 tiny checkpoint，再检查 continuation uptake 是否出现。

本版不做大模型训练，不扩大标准 benchmark，不宣称通用能力提升。它只回答一个更小的问题：required term 已经在数据里，并且 scaffold 形式非常短时，tiny 模型能不能学到一点 prompt-to-term 的续写模式。

## 前置能力

本版承接 v480-v482 的链路：

- v480 coverage audit
  - 证明 required terms 存在于 suite 和 tiny corpus，不是数据缺失。
- v481 uptake audit
  - 证明 archived generation 没有把 required terms 写进 continuation。
- v482 scaffold probe
  - 证明只把 required term 放到 prompt 中，归档 checkpoint 仍没有 continuation uptake。

v483 的不同点是它会真实调用 `scripts/train.py` 训练一个新的 tiny checkpoint。

## 关键新增文件

- `src/minigpt/model_capability_required_term_micro_training.py`
  - 核心实验编排。
  - 输入 v482 scaffold probe report，筛选没有截断、没有超过 block size 的 probe rows。
  - 构造 `required_term_micro_corpus.txt`。
  - 调用训练命令生成 `micro-run/checkpoint.pt` 和 `tokenizer.json`。
  - 用 `MiniGPTGenerator` 对同一批 scaffold prompt 做生成。
  - 统计 prompt/full generated/continuation 三类 required-term 命中。
- `src/minigpt/model_capability_required_term_micro_training_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
  - HTML 用于 Playwright MCP 截图，CSV 用于逐行查看哪些 case 命中。
- `scripts/run_model_capability_required_term_micro_training.py`
  - CLI 入口。
  - 支持训练参数、生成参数、`--require-pass` 和 `--force`。
- `tests/test_model_capability_required_term_micro_training.py`
  - 用 fake train/fake generator 覆盖 uptake、no uptake、缺输入、输出产物和路径定位。

## 核心数据结构

最终报告是：

```text
model_capability_required_term_micro_training.json
```

关键字段：

- `settings`
  - 记录训练与生成参数，包括 `max_iters=300`、`block_size=8`、`n_embd=32`、`learning_rate=0.02`、`term_repeat=24`、`max_new_tokens=8`、`top_k=1`。
- `corpus`
  - 记录微训练语料路径、字符数、行数和重复次数。
  - 这个语料是最终证据，不是临时文件，因为它决定了本次 checkpoint 学到什么。
- `training`
  - 记录训练命令、stdout/stderr 日志路径、checkpoint/tokenizer/metrics/train_config 是否存在。
  - 如果训练命令失败，报告结构会变成 `status=fail`。
- `examples`
  - 从 v482 `probe_rows` 派生的一组训练/生成样本。
  - 每行保留 seed、case、task_type、term、scaffold_prompt 和来源 checkpoint/eval-suite。
- `generation_rows`
  - 每个 scaffold prompt 生成后一行。
  - `generated_hit_count` 包含 prompt 本身，不能直接当作续写能力。
  - `continuation_hit_count` 只看 prompt 之后的 continuation，是本版最关键的能力信号。
- `summary`
  - 汇总 example/generation 数量、continuation 命中数、case 命中数、hit rate 和训练产物状态。
  - `micro_training_decision` 区分训练失败、没有样本、仍无 uptake、部分 learned required terms。

## 运行流程

1. 读取 v482 scaffold probe JSON。
2. 过滤掉 `prompt_truncated=True` 或 `prompt_over_block=True` 的行。
3. 对每行选一个 required term，保留 scaffold prompt，例如 `data:`、`loss:`、`because:`。
4. 构造微型语料：

```text
data:data
data: data
qa-training-loop|data:data
```

这些模式重复写入，用来测试模型是否能学习最小的 scaffold-to-term 续写。

5. 调用 `scripts/train.py`，使用 char tokenizer 和 CPU tiny config 训练新的 checkpoint。
6. 用训练出的 checkpoint 对同一批 scaffold prompt 做 greedy-ish 生成。
7. 输出 JSON/CSV/text/Markdown/HTML，并用 Playwright MCP 截 HTML 报告。

## v483 真实运行结果

真实配置：

```text
max_iters=300
eval_iters=2
batch_size=16
block_size=8
n_layer=1
n_head=1
n_embd=32
learning_rate=0.02
term_repeat=24
max_new_tokens=8
temperature=0.2
top_k=1
```

结果：

```text
status=pass
decision=required_term_micro_training_uptake_observed
micro_training_decision=targeted_micro_training_partially_learned_required_terms
example_count=20
generation_count=20
continuation_hit_count=4
case_with_continuation_hit_count=4
continuation_hit_rate=0.2
training_status=pass
checkpoint_exists=True
tokenizer_exists=True
model_quality_claim=targeted_micro_training_signal_only
```

解释：这 4 次命中主要来自 `data:` 相关样本。它说明模型可以被定向语料推到 required-term continuation 方向，但仍不是通用 benchmark 能力；报告中特意把 `model_quality_claim` 限制为 `targeted_micro_training_signal_only`。

## 测试覆盖

新增测试覆盖：

- fake generator 续写 required term 时，报告必须转为 `required_term_micro_training_uptake_observed`。
- fake generator 不续写 required term 时，训练结构仍可 pass，但 decision 必须是 completed without uptake。
- v482 source 行全被标记为 over block 时，报告必须 fail，`--require-pass` 返回非零。
- JSON/CSV/text/Markdown/HTML 五类输出必须全部生成。
- 输入路径必须支持文件和目录。
- 微训练语料必须真实包含 prompt-to-term 重复样本。

这些测试没有模拟 PyTorch 训练本身，而是把训练过程作为可替换边界；真实训练由 v483 运行证据和全量测试覆盖。

## 运行证据

运行证据位于：

```text
e/483/解释/model-capability-required-term-micro-training/
e/483/图片/01-model-capability-required-term-micro-training.png
e/483/解释/model-capability-required-term-micro-training-snapshot.md
```

这些产物不是只读审计，而是包含新的 `micro-run/checkpoint.pt`、训练语料和生成结果。它们说明 v483 已经从“证明为什么没生成”推进到“尝试通过小训练让模型开始生成”。

## 一句话总结

v483 用一个真实 tiny micro-training repeat 证明 required-term continuation 可以出现少量定向学习信号，但这个信号还需要 held-out 验证，不能直接当作通用模型能力提升。
