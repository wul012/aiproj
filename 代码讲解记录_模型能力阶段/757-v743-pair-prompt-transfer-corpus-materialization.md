# v743 pair prompt transfer corpus materialization 代码讲解

## 本版目标和边界

v743 的目标是把 v742 生成的 `pair_readiness_pair_prompt_transfer_contract_patch_ready` contract 变成真实训练输入：一个文本训练 corpus 和一个 heldout eval fixture。

本版解决的问题是：v742 已经把 16 条 direct-completion rows 扩成 24 条包含 surrogate pair-transfer rows 的训练契约，但训练器不能直接消费 contract；它需要稳定的 corpus 文件和独立的 heldout fixture。v743 就是这层从 contract 到训练输入的落地。

本版明确不做三件事：

- 不训练 checkpoint。
- 不比较模型路线。
- 不把 exact heldout pair prompt `fixed=|loss=` 写进训练数据。

## 前置路线

v740 发现 v738 的 direct-completion checkpoint 只在 `fixed=` / `loss=` direct probes 上有效，遇到 `fixed=|loss=` 这类 pair prompt 就不能迁移。

v741 将这个失败整理为 repair plan：保留 direct-completion surface，同时新增非 exact heldout 的 surrogate pair-transfer rows。

v742 根据 repair plan 生成 checked contract patch，并把新 decision 注册到 materializer 可接受列表。

v743 接在 v742 后面，只做 materialization，让下一版可以直接训练。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_readiness_corpus_materialization.py`
  - 核心 materializer。
  - `PAIR_READINESS_READY_CONTRACT_DECISIONS` 现在包含 `pair_readiness_pair_prompt_transfer_contract_patch_ready`。
  - `PAIR_READINESS_CONTRACT_JSON_FILENAMES` 现在包含 `model_capability_required_term_pair_readiness_pair_prompt_transfer_contract_patch.json`。
  - `locate_pair_readiness_corpus_materialization_source()` 支持从 v742 输出目录自动找到 patch JSON。
  - `build_pair_readiness_corpus_materialization()` 负责生成 report、corpus path、fixture path、checks 和后续 action。

- `scripts/run_model_capability_required_term_pair_readiness_corpus_materialization.py`
  - CLI 入口。
  - 输入可以是 contract JSON，也可以是 contract 输出目录。
  - `--repeat 320` 控制每条训练行重复次数。
  - `--require-pass` 让 materialization check 失败时返回非零退出码。
  - `--force` 保证归档目录可以被重新生成。

- `e/743/解释/model-capability-required-term-pair-readiness-pair-prompt-transfer-corpus-materialization/`
  - v743 的最终证据目录。
  - 包含 JSON/CSV/TXT/Markdown/HTML report、`pair_readiness_training_corpus.txt` 和 `pair_readiness_heldout_eval_fixture.json`。

- `e/743/图片/v743-pair-prompt-transfer-corpus-materialization.png`
  - Playwright 截图证据。
  - 证明 HTML 报告可以正常打开，并且显示 pass、7680 条训练行和 3 条 eval probes。

## 核心数据结构

materialization report 的关键字段包括：

- `status`
  - `pass` 表示 contract、repeat、training rows 和 heldout isolation checks 均通过。

- `decision`
  - v743 为 `pair_readiness_corpus_materialized`，表示 contract 已被物化为训练输入。

- `training_line_count`
  - v743 为 `7680`。
  - 来源是 v742 的 24 条 training rows 乘以 `repeat=320`。

- `evaluation_probe_count`
  - v743 为 `3`。
  - 这些 probes 仍用于下一版训练后的 heldout replay。

- `model_quality_claim`
  - v743 为 `data_artifact_only`。
  - 这个字段故意不写成能力提升，因为当前没有训练和 generation replay。

- `checks`
  - `contract_passed`：源 contract 必须 pass。
  - `contract_decision`：源 contract decision 必须在 materializer 白名单内。
  - `repeat_positive`：repeat 必须大于 0。
  - `training_rows_present`：训练行不能为空。
  - `heldout_not_in_training_rows`：heldout pair probe 不能等于任一训练行。
  - `heldout_not_in_corpus`：heldout pair probe 不能作为 corpus line 出现。

## 运行流程

CLI 先通过 `locate_pair_readiness_corpus_materialization_source()` 定位输入。如果用户传入的是 v742 输出目录，它会按已注册文件名查找 `model_capability_required_term_pair_readiness_pair_prompt_transfer_contract_patch.json`。

随后 CLI 读取 JSON report，并把它交给 `build_pair_readiness_corpus_materialization()`。

builder 从 `contract.training_rows` 提取 24 条训练行，从 `contract.evaluation_probes` 提取 3 条 heldout probes，再调用内部语料生成逻辑按 `repeat=320` 展开训练行。

当 report 的 `status=pass` 时，CLI 调用 `write_materialized_pair_readiness_inputs()` 写出两个可消费文件：

- `pair_readiness_training_corpus.txt`
- `pair_readiness_heldout_eval_fixture.json`

最后 artifact writer 输出 JSON、CSV、TXT、Markdown 和 HTML。下一版训练脚本只需要读取 v743 输出目录即可。

## 测试和验证

本版真实运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_corpus_materialization.py e\742\解释\model-capability-required-term-pair-readiness-pair-prompt-transfer-contract-patch --out-dir e\743\解释\model-capability-required-term-pair-readiness-pair-prompt-transfer-corpus-materialization --repeat 320 --require-pass --force
```

核心输出：

```text
status=pass
decision=pair_readiness_corpus_materialized
training_line_count=7680
evaluation_probe_count=3
```

Playwright 打开 HTML 后，快照确认页面包含：

- `Status pass`
- `Decision pair_readiness_corpus_materialized`
- `Train lines 7680`
- `Eval probes 3`

这些断言保护的是数据链路本身：下一版训练必须基于可复核的 v742 patch，而不是手写临时文本。

## 证据链角色

v743 是训练前的证据层，不是能力层。它的价值在于把 v742 的 contract patch 变成训练器可以直接消费的文件，同时保持 heldout pair probe 的隔离。

这意味着如果 v744 训练成功，能力提升可以追溯到 v742 的非泄漏 transfer rows 和 v743 的 materialized corpus；如果 v744 失败，也可以排除“训练输入没有生成好”这一类低级原因。

一句话总结：v743 把 pair prompt transfer contract patch 从可审计设计推进到可训练数据，但没有把数据准备误写成模型能力提升。
