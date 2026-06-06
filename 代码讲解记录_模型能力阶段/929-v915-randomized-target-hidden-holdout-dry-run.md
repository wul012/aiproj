# v915 randomized target-hidden holdout dry-run 代码讲解

## 本版目标和边界

v915 的目标是 dry-run v914 的随机化 holdout suite。

v914 构造了 20 条 seeded randomized target-hidden prompt，并证明它们 tokenizer-covered、target-hidden、无 task hint、唯一且不同于 source prompt。v915 不急着跑模型，而是先验证 scoring contract：正向 continuation 必须全过，负向 continuation 必须全不过。

明确不做：

- 不重新训练。
- 不读取 checkpoint。
- 不做真实 replay。
- 不批准 promotion。
- 不修改 v914 suite。

本版只证明评估集的评分逻辑是可用的。

## 前置链路

```text
v914 randomized target-hidden suite
  -> v915 dry-run scoring contract
  -> next real checkpoint replay
```

## 关键文件

### `src/minigpt/randomized_target_hidden_holdout_dry_run.py`

这是本版核心 builder。

入口函数：

```python
build_randomized_target_hidden_holdout_dry_run(...)
```

输入：

- `holdout_suite_report`：来自 v914。
- `positive_continuation`：默认 ` fixed loss`。
- `negative_continuation`：默认 ` fixed only`。
- 可选 `holdout_suite_path`。

输出：

- `status`
- `decision`
- `failed_count`
- `issues`
- `source_holdout_suite`
- `source_holdout_suite_summary`
- `positive_continuation`
- `negative_continuation`
- `check_rows`
- `dry_run_rows`
- `summary`
- `interpretation`

### `_dry_run_rows`

`_dry_run_rows` 遍历 v914 的 20 条 case。

每条 case 会对两段 continuation 打分：

```text
positive_continuation = " fixed loss"
negative_continuation = " fixed only"
```

行字段包括：

- `case_id`
- `source_case_id`
- `random_draw_index`
- `expected_terms`
- `positive_case_pass`
- `positive_hit_terms`
- `positive_missed_terms`
- `negative_case_pass`
- `negative_hit_terms`
- `negative_missed_terms`

这样后续如果 dry-run 失败，可以直接定位是哪条 case 或哪个 continuation 出问题。

### `_score`

`_score` 的逻辑很窄：

```python
case_pass = bool(expected_terms) and not missed_terms
```

也就是 continuation 必须同时包含 `fixed` 和 `loss`。这和前面 replay 系列保持一致，不引入新的评分标准。

### `_checks`

v915 checks 包括：

- v914 suite 必须 pass。
- `randomized_target_hidden_holdout_suite_ready=True`。
- benchmark suite 必须 ready。
- cases 必须存在。
- summary 的 `candidate_case_count` 必须等于实际 case 数。
- `randomized_case_factor >= 2.0`。
- 所有 case 都 tokenizer-covered。
- 所有 case 都 target-hidden。
- `task_hint_case_count=0`。
- `unique_prompt_count` 等于 case 数。
- expected terms 必须是 `fixed/loss`。
- 正向 continuation 必须 20/20 通过。
- 负向 continuation 必须 0/20 通过。

这套 checks 保护的是“评估契约”，不是模型能力。

### `_summary`

真实 v915 summary：

```text
randomized_target_hidden_holdout_dry_run_ready=True
case_count=20
source_random_seed=914
source_randomized_case_factor=2.0
source_unique_prompt_count=20
positive_passed_case_count=20
negative_passed_case_count=0
negative_control_passed=False
promotion_ready=False
model_quality_claim=dry_run_only
next_step=run_randomized_target_hidden_holdout_real_replay
```

`negative_control_passed=False` 是关键字段：如果负向 continuation 也能通过，就说明 scoring contract 太松，不能进入真实 replay。

### `src/minigpt/randomized_target_hidden_holdout_dry_run_artifacts.py`

这是输出层。

它写出：

- JSON：后续 real replay 可以引用。
- CSV：逐 case 查看正负样例。
- text：命令行摘要。
- Markdown：人工阅读。
- HTML：截图证据。

HTML 卡片展示 `Status`、`Cases`、`Seed`、`Factor`、`Positive passed`、`Negative passed`、`Negative control`、`Next`。

### `scripts/dry_run_randomized_target_hidden_holdout.py`

这是 CLI。

关键参数：

```powershell
--holdout-suite
--positive-continuation
--negative-continuation
--out-dir
--require-dry-run-ready
--force
```

真实运行只读 v914 suite，并写入 `e/915/解释/randomized-target-hidden-holdout-dry-run`。

## 测试覆盖

新增测试：

```text
tests/test_randomized_target_hidden_holdout_dry_run.py
```

覆盖内容：

- 正向 continuation 4/4 通过，负向 0/4 通过。
- 负向 continuation 改成 ` fixed loss` 时 dry-run 失败。
- source suite 未 ready 时 dry-run 失败。
- artifact writer 和 CLI 写出 JSON/CSV/text/Markdown/HTML。

这些测试确保 dry-run 不是装饰性报告，而是真实守住 scoring contract。

## 运行证据

真实命令：

```powershell
python scripts\dry_run_randomized_target_hidden_holdout.py --holdout-suite e\914\解释\randomized-target-hidden-holdout-suite --out-dir e\915\解释\randomized-target-hidden-holdout-dry-run --require-dry-run-ready --force
```

结果：

```text
status=pass
decision=randomized_target_hidden_holdout_dry_run_passed
case_count=20
source_random_seed=914
positive_passed_case_count=20
negative_passed_case_count=0
negative_control_passed=False
next_step=run_randomized_target_hidden_holdout_real_replay
```

截图：

```text
e/915/图片/v915-randomized-target-hidden-holdout-dry-run.png
```

## 链路角色

v915 是 v914 和真实 replay 之间的契约闸门。

它没有证明模型变好，但证明下一步 replay 用的 20-case randomized suite 的评分方式是正常的：能识别完整目标，也能拒绝缺少 `loss` 的负向样例。

## 一句话总结

v915 把 randomized target-hidden suite 从“已构造”推进到“评分契约已验证”，为 v916 真实 replay 铺好入口。
