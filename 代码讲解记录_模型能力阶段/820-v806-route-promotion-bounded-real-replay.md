# v806 route promotion bounded real replay

## 本版目标和边界

v806 是功能版本，接在 v805 bounded benchmark dry-run 后面。v805 只证明评分契约能识别 `fixed loss` 正样例和 `fixed only` 负控；v806 开始加载真实 MiniGPT checkpoint，把 v803 的 5 个 bounded prompt cases 交给模型生成，再按同一套 expected terms 评分。

本版不做：

- 不训练新模型。
- 不修改 v803 benchmark suite。
- 不扩大 `fixed/loss` scoring contract。
- 不把治理链通过当作模型质量通过。
- 不要求 5/5 才认为 replay artifact 可写出；执行成功和模型质量结论分开记录。

## 前置链路

本版消费三类上游证据：

```text
v803 bounded benchmark suite
v804 bounded benchmark suite review
v805 bounded benchmark dry-run
```

真实 checkpoint 来自历史模型能力阶段的 v770 训练证据：

```text
e/770/解释/model-capability-required-term-pair-readiness-objective-level-contrast-seed-3838-training-run/pair-readiness-training-run/checkpoint.pt
e/770/解释/model-capability-required-term-pair-readiness-objective-level-contrast-seed-3838-training-run/pair-readiness-training-run/tokenizer.json
```

这让 v806 从“评分器自己验证自己”推进到“真实模型输出接受同一评分合约检查”。

## 关键新增文件

### `src/minigpt/model_capability_route_promotion_bounded_real_replay.py`

这是 v806 的核心 builder，提供：

- `locate_route_promotion_bounded_benchmark_suite(path)`
- `locate_route_promotion_bounded_benchmark_suite_review(path)`
- `locate_route_promotion_bounded_benchmark_dry_run(path)`
- `read_json_report(path)`
- `build_model_capability_route_promotion_bounded_real_replay(...)`
- `resolve_exit_code(report, require_execution_pass=..., require_model_pass=...)`

输入可以是 JSON 文件，也可以是输出目录。目录输入会自动定位：

```text
model_capability_route_promotion_bounded_benchmark_suite.json
model_capability_route_promotion_bounded_benchmark_suite_review.json
model_capability_route_promotion_bounded_benchmark_dry_run.json
```

builder 的核心保护是把执行状态和模型质量状态拆开：

- `status=pass` 只表示 replay 输入和生成执行通过。
- `summary.model_route_quality_ready=True/False` 才表示模型是否全部命中 required terms。
- `decision=model_capability_route_promotion_bounded_real_replay_completed_with_model_gaps` 表示真实 replay 已完成，但模型还有缺口。

### `replay_rows`

每个 replay row 包含：

- `case_id`
- `prompt`
- `continuation`
- `generated`
- `expected_terms`
- `hit_terms`
- `missed_terms`
- `case_pass`
- `seed`
- `max_new_tokens`
- `temperature`
- `top_k`

这里的 `continuation` 来自真实 `MiniGPTGenerator`，不是 dry-run 中手写的 `fixed loss`。

### `check_rows`

本版 checks 关注执行链路：

- `suite_review_passed`
- `suite_review_approved`
- `benchmark_suite_passed`
- `dry_run_passed`
- `dry_run_ready`
- `checkpoint_exists`
- `tokenizer_exists`
- `cases_present`
- `all_cases_executed`
- `no_replay_errors`

注意：是否 5/5 命中不放进 `failed_count`，否则会把“模型能力没达标”和“replay 产物不可用”混在一起。v806 的判断是：产物可用，但模型质量未 ready。

### `src/minigpt/model_capability_route_promotion_bounded_real_replay_artifacts.py`

这是 artifact writer，输出：

- JSON
- CSV
- text
- Markdown
- HTML

CSV 保存每个 case 的 hit/missed terms 和 continuation。HTML 用于人工检查，它在首页直接显示：

```text
Executed=True
Quality ready=False
Passed=2/5
Pass rate=0.4
```

### `scripts/run_model_capability_route_promotion_bounded_real_replay.py`

这是 CLI 入口，支持：

- `--benchmark-suite`
- `--suite-review`
- `--dry-run`
- `--checkpoint`
- `--tokenizer`
- `--device`
- `--require-execution-pass`
- `--require-model-pass`
- `--force`

`--require-execution-pass` 只要求 replay 能正常执行；`--require-model-pass` 才要求所有 cases 都命中 required terms。这个拆分是 v806 的关键设计，避免 CI 或人工验证误把“模型未达标”当作“工具损坏”。

## 真实运行证据

本版实际运行：

```powershell
python -B scripts/run_model_capability_route_promotion_bounded_real_replay.py --benchmark-suite <v803 suite> --suite-review <v804 review> --dry-run <v805 dry-run> --checkpoint <v770 checkpoint.pt> --tokenizer <v770 tokenizer.json> --device cpu --out-dir e/806/解释/model-capability-route-promotion-bounded-real-replay --require-execution-pass --force
```

结果：

```text
status=pass
decision=model_capability_route_promotion_bounded_real_replay_completed_with_model_gaps
failed_count=0
bounded_real_replay_executed=True
model_route_quality_ready=False
case_count=5
passed_case_count=2
failed_case_count=3
pass_rate=0.4
next_step=review_bounded_route_promotion_real_replay
```

这说明 v806 的链路已经跑到真实模型输出，但模型在 5 个 bounded cases 中只通过 2 个。它是有价值的模型能力证据，也暴露了下一步需要修复的能力缺口。

## 测试覆盖

本版测试位于 `tests/test_model_capability_route_promotion_bounded_real_replay.py`，覆盖：

- fake runner 部分命中时，执行状态通过但 `model_route_quality_ready=False`。
- fake runner 全部命中时，`decision=model_capability_route_promotion_bounded_real_replay_passed`。
- checkpoint 缺失时，`checkpoint_exists` check 失败。
- artifact writer 输出 JSON/CSV/text/Markdown/HTML。
- CLI 在 fake checkpoint 路径下仍能写失败 sidecar，便于排查。

本版运行：

```powershell
python -m py_compile src/minigpt/model_capability_route_promotion_bounded_real_replay.py src/minigpt/model_capability_route_promotion_bounded_real_replay_artifacts.py scripts/run_model_capability_route_promotion_bounded_real_replay.py tests/test_model_capability_route_promotion_bounded_real_replay.py
python -m pytest tests/test_model_capability_route_promotion_bounded_benchmark_suite.py tests/test_model_capability_route_promotion_bounded_benchmark_suite_review.py tests/test_model_capability_route_promotion_bounded_benchmark_dry_run.py tests/test_model_capability_route_promotion_bounded_real_replay.py -q -o cache_dir=runs/pytest-cache-v806-focused
```

结果：

- focused tests: `13 passed`

## 截图和归档

运行证据归档在：

- `e/806/解释/说明.md`
- `e/806/解释/model-capability-route-promotion-bounded-real-replay/`
- `e/806/图片/v806-bounded-real-replay-html.png`

Playwright MCP 快照确认 HTML 页面展示：

- `Status: pass`
- `Quality ready: False`
- `Passed: 2/5`
- `Pass rate: 0.4`

## 一句话总结

v806 把 bounded route promotion 从 dry-run scorer 推进到真实 checkpoint replay，用 2/5 的真实命中率证明模型能力链路已能实测，也明确指出当前模型还没有达到全部 fixed/loss case 通过。
