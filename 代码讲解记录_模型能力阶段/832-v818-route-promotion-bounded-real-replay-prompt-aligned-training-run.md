# v818 route promotion bounded real replay prompt-aligned training run

## 本版目标和边界

v818 的目标是把 v817 生成的 prompt-aligned seed corpus 进入真实训练，而不是继续停留在“语料已经准备好”的状态。本版新增一个训练运行证据模块，用来确认 checkpoint、tokenizer、metrics、run manifest、sample 和 prepared corpus 都真实存在，并把训练 loss、训练步数、exact prompt answer 数量写成可复核报告。

本版不做 bounded benchmark replay，也不把 loss 下降解释成模型能力提升。它只证明“v817 语料已经训练出一个可进入下一步 replay 的 checkpoint”。模型能否恢复 v806 baseline 的 2/5 表现，要由下一版 replay 证明。

## 前置路线

本版沿着 v811-v817 的失败闭环继续推进：

- v811/v815 证明 repair checkpoint 相比 v806 baseline 回归。
- v816 把失败原因定位为 `benchmark_prompt_training_corpus_gap` 和 `loss_improvement_not_sufficient_for_exact_terms`。
- v817 根据 v816 诊断，把 v803 benchmark 的 5 个 exact prompt 都加入训练语料。
- v818 负责训练这份 prompt-aligned corpus，并生成训练运行证据。

## 关键文件

- `src/minigpt/model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run.py`
  - 核心证据构建器。
  - 读取 v817 seed summary 和训练 run 目录。
  - 生成 `status`、`decision`、`issues`、`artifacts`、`metrics`、`train_config`、`manifest`、`summary` 和 `interpretation`。

- `src/minigpt/model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run_artifacts.py`
  - 输出层。
  - 把同一份 report 写成 JSON、CSV、TXT、Markdown、HTML。
  - HTML 只展示训练证据，不宣称能力通过。

- `scripts/build_model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run.py`
  - CLI 入口。
  - 支持 `--prompt-aligned-seed`、`--run-dir`、`--out-dir`、`--require-prompt-aligned-training-ready`、`--force`。
  - 当 `run/` 嵌在 `out-dir` 里面时，`--force` 会保留 `run/`，只删除旧报告文件，避免误删刚训练出的 checkpoint。

- `tests/test_model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run.py`
  - 单测覆盖 ready 报告、缺 checkpoint 失败、CLI 输出、嵌套 run 保留。

- `e/818/解释/model-capability-route-promotion-bounded-real-replay-prompt-aligned-training-run/`
  - v818 的真实训练证据目录。

## 核心数据结构

主报告的关键字段如下：

- `status`
  - 所有检查通过时为 `pass`。
  - 任一训练产物缺失、seed 不 ready、metrics 不完整时为 `fail`。

- `decision`
  - `pass` 时为 `model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run_ready`。
  - `fail` 时为 `fix_model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run`。

- `artifacts`
  - 逐项记录 `checkpoint.pt`、`tokenizer.json`、`metrics.jsonl`、`train_config.json`、`run_manifest.json`、`sample.txt`、`prepared_corpus.txt` 是否存在和文件大小。

- `metrics`
  - 从 `metrics.jsonl` 读取首尾记录。
  - 计算 `train_loss_delta` 和 `val_loss_delta`。
  - v818 的真实结果是 train loss 下降约 `-0.3491`，val loss 下降约 `-0.3065`。

- `summary`
  - 给 README 和 HTML 使用的压缩摘要。
  - 包括 `prompt_aligned_training_ready`、`final_step`、`final_train_loss`、`final_val_loss`、`exact_prompt_answer_count` 和 `next_step`。

- `interpretation`
  - 明确写入 `model_quality_claim=training_artifact_only`。
  - 这是本版最重要的边界字段：训练成功不是能力成功，下一步仍要 replay。

## 核心函数

`build_model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run()` 是主入口。它的流程是：

1. 读取 v817 的 `summary`，确认 seed revision 已 ready。
2. 扫描训练 run 目录，构造 artifact rows。
3. 解析 `metrics.jsonl`、`train_config.json` 和 `run_manifest.json`。
4. 调用 `_checks()` 生成检查行。
5. 根据检查行得到 `status` 和 `issues`。
6. 调用 `_training()` 生成训练摘要。
7. 调用 `_summary()` 和 `_interpretation()` 输出面向人和后续模块消费的压缩结论。

`_checks()` 保护的关键合同包括：

- prompt-aligned seed report 必须是 `status=pass`。
- `prompt_aligned_seed_revision_ready` 必须为 `True`。
- `exact_prompt_answer_count` 必须大于 0。
- checkpoint、tokenizer、metrics、manifest、prepared corpus 必须存在。
- metrics 至少有首尾两条记录。
- `max_iters` 必须为正数。

这些检查让 v818 不只是“训练脚本跑过”，而是能证明训练结果可以进入下一步 replay。

## CLI 运行链路

本版先运行真实训练：

```powershell
python -B scripts\train.py --prepared-data e\817\解释\...\model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_corpus.txt --out-dir e\818\解释\...\run --max-iters 30 --eval-interval 10 --eval-iters 2 --batch-size 4 --block-size 32 --n-layer 2 --n-head 2 --n-embd 32 --dropout 0.0 --seed 993 --device cpu
```

随后运行证据构建器：

```powershell
python -B scripts\build_model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run.py --prompt-aligned-seed e\817\解释\...\model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision.json --run-dir e\818\解释\...\run --out-dir e\818\解释\... --require-prompt-aligned-training-ready --force
```

输出结果为：

- `status=pass`
- `failed_count=0`
- `final_step=30`
- `final_train_loss=4.1787`
- `final_val_loss=4.2154`
- `exact_prompt_answer_count=5`

## 测试覆盖

本版新增 4 个 focused tests：

- ready 报告测试确认正常 fake run 能得到 `prompt_aligned_training_ready=True`。
- 缺 checkpoint 测试确认关键训练产物缺失会进入 `issues`。
- CLI 输出测试确认 JSON/CSV/TXT/MD/HTML 都能生成。
- nested run 保护测试确认 `--force` 不会删掉 `out-dir/run` 里的 checkpoint。

这些测试覆盖的是本版真实风险：训练证据目录往往和报告输出目录嵌套在一起，如果 `--force` 误删 run 目录，下一步 replay 就会直接断链。

## 运行证据

v818 的证据在：

- `e/818/解释/说明.md`
- `e/818/解释/model-capability-route-promotion-bounded-real-replay-prompt-aligned-training-run/`
- `e/818/图片/v818-bounded-real-replay-prompt-aligned-training-run-html.png`

Playwright MCP 已打开 HTML 报告并完成截图，证明浏览器端可读页面能够显示 ready 状态、训练指标和 artifact 清单。

## 一句话总结

v818 把 v817 的提示对齐语料推进成一个真实可复核 checkpoint，但仍把“模型是否变好”的判断留给下一版 bounded replay。
