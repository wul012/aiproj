# v186 real training run evidence

## 本版目标

v186 的目标是把项目从连续多版“结构拆分/收口”切回真实功能推进：给 `scripts/train.py` 产出的真实训练目录增加一层可审计证据摘要。

它解决的问题是：训练规模链路已经有 plan、gate、run、comparison、decision、workflow、promotion、seed 等治理产物，但真实 checkpoint 训练完以后，缺少一个轻量报告来回答：

- checkpoint、tokenizer、train config、metrics、run manifest 是否真的存在。
- metrics 是否能解析，训练是否达到 `max_iters`。
- best/last validation loss、sample、dataset provenance、eval suite 状态是否清楚。
- 这个 run 现在是 `ready`、`review` 还是 `blocked`。

本版明确不做：

- 不扩大模型规模，不声称模型质量提升。
- 不自动运行 eval suite 或 benchmark scorecard。
- 不改变 `scripts/train.py` 的训练行为和 checkpoint 格式。
- 不继续做“为了拆分而拆分”的 utils migration。

## 前置路线

v67 引入 training portfolio pipeline，让 prepare/train/eval/registry/maturity 可以按步骤执行。

v70-v82 建立 training scale 的 plan、gate、run、comparison、decision、workflow、handoff、promotion 和 seed 链路。

v183-v185 做了维护收口和 helper 拆分，但用户指出不能继续只拆分。v186 因此切回功能：把一次真实 PyTorch 训练结果接到治理证据链里。

## 关键文件

### `src/minigpt/training_run_evidence.py`

这是本版新增的核心 builder。

核心输入是一个 run 目录，例如 `runs/v186-real-train`。该目录通常由 `scripts/train.py` 生成，包含：

- `checkpoint.pt`
- `tokenizer.json`
- `train_config.json`
- `metrics.jsonl`
- `history_summary.json`
- `run_manifest.json`
- `sample.txt`

核心函数：

- `build_training_run_evidence()`：构建完整 evidence report。
- `_artifact_rows()`：基于 `manifest.collect_run_artifacts()` 汇总训练产物，并额外加入 `run_manifest.json` 自身作为 core artifact。
- `_checks()`：生成检查项，包括核心产物存在、metrics 可解析、目标 step 达成、loss summary、sample 和 eval suite 状态。
- `_summary()`：把 check 状态汇总为 `ready`、`review` 或 `blocked`，并给出 readiness score。
- `_training_section()`：抽取 tokenizer、device、batch/block size、learning rate、target step、actual last step、loss 和 parameter count。
- `_data_section()`：抽取数据来源、token count、dataset quality、fingerprint 和 dataset id。
- `_sample_section()`：读取 sample prompt、字符数和 preview。

状态语义：

- `ready`：核心训练证据、sample、loss、manifest 等都满足，且没有 warn/fail。
- `review`：核心证据齐，但还有非阻塞缺口，例如 eval suite 未跑。
- `blocked`：缺 checkpoint、tokenizer、config、metrics、manifest 或无法证明训练完成。

这让治理链能区分“真的训练过，但还没做完整评估”和“训练证据本身不可信”。

### `src/minigpt/training_run_evidence_artifacts.py`

这是新增的 artifact writer。

它负责：

- 写 `training_run_evidence.json`
- 写 `training_run_evidence.csv`
- 渲染 `training_run_evidence.md`
- 渲染 `training_run_evidence.html`

JSON 是机器可消费的最终证据，CSV 用于快速汇总，Markdown 用于代码审查和讲解，HTML 用于浏览器查看。HTML 不写入额外业务状态，只展示 builder 已经算出的 report。

### `scripts/build_training_run_evidence.py`

这是新增 CLI。

典型用法：

```powershell
python -B scripts\build_training_run_evidence.py --run-dir runs\v186-real-train --out-dir runs\v186-training-run-evidence
```

它输出：

- `status`
- `readiness_score`
- core artifact 覆盖率
- 总 artifact 覆盖率
- blocker/warning 数量
- JSON/CSV/Markdown/HTML 路径

`--require-sample` 可以把 sample 缺失变成 blocker。`--require-eval-suite` 可以把 eval suite 缺失变成 blocker。`--fail-on-blocked` 适合 CI 或 release gate 前置检查。

### `src/minigpt/training_portfolio.py`

本版把新证据接入 training portfolio pipeline。

原流程中 `train` 之后直接进入 `eval_suite`。v186 在两者之间插入：

```text
training_run_evidence
```

这样 pipeline 执行时会先检查真实训练输出是否完整，再进入固定 prompt eval 和后续 benchmark。这个顺序更合理：如果 checkpoint、metrics 或 manifest 都不完整，后面 benchmark 即使跑了也缺少可信训练来源。

新增 artifact key：

- `training_run_evidence`
- `training_run_evidence_html`

这两个路径会进入 portfolio 的 artifact rows，后续 portfolio HTML 也能看到它们。

### `tests/test_training_run_evidence.py`

本版新增测试覆盖：

- 完整模拟 run 目录会被判定为 `ready`。
- 删除 `checkpoint.pt` 后会被判定为 `blocked`。
- JSON/CSV/Markdown/HTML 输出都能写出。
- HTML 对标题做转义，避免把报告内容误渲染成 HTML 标签。

### `tests/test_training_portfolio.py`

本版更新 pipeline 顺序断言，确认 `training_run_evidence` 位于 `train` 和 `eval_suite` 之间，并确认 plan 中包含 `build_training_run_evidence.py` 命令和 evidence artifact 路径。

## 数据结构和输出

`training_run_evidence.json` 的主要结构：

```text
schema_version
title
generated_at
run_dir
summary
training
data
sample
checks
artifacts
warnings
recommendations
```

`summary` 是总览：

- `status`
- `readiness_score`
- `critical_missing_count`
- `warning_count`
- `core_available_count`
- `core_artifact_count`
- `available_artifact_count`
- `artifact_count`

`checks` 是判断依据，每条包含：

- `code`
- `category`
- `status`
- `message`
- `recommendation`
- `details`

`artifacts` 是产物清单，每条包含：

- `key`
- `path`
- `description`
- `exists`
- `size_bytes`
- `sha256`
- `required_level`
- `absolute_path`

其中 `required_level` 分为：

- `core`：promotion review 的基础证据。
- `review`：人工审查强相关，但不一定阻塞。
- `optional`：数据卡、eval、model report、dashboard 等后续增强产物。

## 运行流程

本版新增链路：

```text
scripts/train.py
 -> run directory
 -> scripts/build_training_run_evidence.py
 -> build_training_run_evidence()
 -> checks + artifacts + summary
 -> JSON/CSV/Markdown/HTML evidence
```

接入 training portfolio 后：

```text
prepare_dataset
 -> train
 -> training_run_evidence
 -> eval_suite
 -> generation_quality
 -> benchmark_scorecard
 -> dataset_card
 -> registry
 -> maturity_summary
 -> maturity_narrative
```

这说明 v186 不是孤立报告，而是放在真实训练后、质量评估前的证据门。

## 测试和证据

v186 的截图归档在 `c/186`。

关键验证包括：

- focused tests：训练证据 builder、artifact writer 和 training portfolio 顺序都通过。
- real PyTorch train smoke：用 CPU 跑 2 iter，真实写出 checkpoint、tokenizer、metrics、manifest、loss curve 和 sample。
- evidence CLI smoke：读取真实 run 目录并输出 `review`，因为核心证据齐全但 eval suite 未跑。
- Playwright/Chrome HTML screenshot：确认 evidence HTML 可以在真实浏览器中打开。
- source encoding hygiene：确认新增 Python 文件无 BOM、语法错误和 Python 3.11 兼容问题。

## 边界说明

v186 的 `review` 结果不是失败，而是正确表达边界：真实训练跑通了，checkpoint 证据齐了，但还没有固定 prompt eval suite，所以不能把它当成完整模型质量证据。

这也是本版最重要的价值：不把治理工具包装成模型质量提升，而是把训练事实、缺口和下一步评价要求讲清楚。

## 一句话总结

v186 把真实 PyTorch 训练输出接入 MiniGPT 治理链，让项目从“计划和发布治理很完整”向“真实 checkpoint 训练证据可审计”推进了一层。
