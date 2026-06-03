# v809 route promotion bounded real replay repair seed

## 本版目标和边界

v809 接在 v808 bounded real replay repair plan 后面。v808 说明要修 3 个 failed cases；v809 把这些 repair tasks 落成可训练的 seed examples，并输出 JSONL 与 corpus。

本版不做：

- 不启动训练。
- 不改 v806 replay 结果。
- 不声明模型已经提升。
- 不扩展到通用模型能力。

## 输入输出

输入有两个：

```text
e/808/解释/model-capability-route-promotion-bounded-real-replay-repair-plan/model_capability_route_promotion_bounded_real_replay_repair_plan.json
e/806/解释/model-capability-route-promotion-bounded-real-replay/model_capability_route_promotion_bounded_real_replay.json
```

为什么需要两个输入：

- v808 plan 告诉我们要修哪些 case。
- v806 replay 保存原始 prompt，能让 seed 对准真实失败表面。

输出：

```text
model_capability_route_promotion_bounded_real_replay_repair_seed.json
model_capability_route_promotion_bounded_real_replay_repair_seed.csv
model_capability_route_promotion_bounded_real_replay_repair_seed.jsonl
model_capability_route_promotion_bounded_real_replay_repair_seed_corpus.txt
model_capability_route_promotion_bounded_real_replay_repair_seed.txt
model_capability_route_promotion_bounded_real_replay_repair_seed.md
model_capability_route_promotion_bounded_real_replay_repair_seed.html
```

## 关键新增文件

### `src/minigpt/model_capability_route_promotion_bounded_real_replay_repair_seed.py`

这是 seed builder，提供：

- `locate_route_promotion_bounded_real_replay_repair_plan(path)`
- `locate_route_promotion_bounded_real_replay(path)`
- `read_json_report(path)`
- `build_model_capability_route_promotion_bounded_real_replay_repair_seed(...)`
- `resolve_exit_code(report, require_seed_ready=...)`

它会把 v808 的 `repair_tasks` 与 v806 的 `replay_rows` 按 `case_id` 对齐，尽量复用真实 failed prompt。

### `seed_examples`

每个 repair task 生成两条 seed examples：

- `direct_case_answer`
- `self_check_answer`

字段包括：

- `example_id`
- `case_id`
- `task_id`
- `example_type`
- `prompt`
- `completion`
- `text`
- `repair_type`
- `missed_terms`
- `required_terms`

当前 completion 固定为：

```text
fixed loss
```

这是有意保持 bounded：目标只是修复 fixed/loss pair route，不把 seed 扩展成泛化语言任务。

### `src/minigpt/model_capability_route_promotion_bounded_real_replay_repair_seed_artifacts.py`

artifact writer 输出 JSON/CSV/JSONL/corpus/text/Markdown/HTML。

其中：

- JSON 是完整证据。
- JSONL 是结构化训练样本。
- corpus txt 是可直接喂给训练脚本的文本种子。
- HTML 用于人工确认 prompt/completion 是否对准真实 failed case。

### `scripts/build_model_capability_route_promotion_bounded_real_replay_repair_seed.py`

CLI 支持：

- `--repair-plan`
- `--real-replay`
- `--out-dir`
- `--require-seed-ready`
- `--force`

## 真实运行证据

本版实际运行：

```powershell
python -B scripts/build_model_capability_route_promotion_bounded_real_replay_repair_seed.py --repair-plan e/808/解释/model-capability-route-promotion-bounded-real-replay-repair-plan/model_capability_route_promotion_bounded_real_replay_repair_plan.json --real-replay e/806/解释/model-capability-route-promotion-bounded-real-replay/model_capability_route_promotion_bounded_real_replay.json --out-dir e/809/解释/model-capability-route-promotion-bounded-real-replay-repair-seed --require-seed-ready --force
```

结果：

```text
status=pass
decision=model_capability_route_promotion_bounded_real_replay_repair_seed_ready
failed_count=0
bounded_real_replay_repair_seed_ready=True
example_count=6
case_count=3
proposed_next_artifact=model_capability_route_promotion_bounded_real_replay_repair_training_run
next_step=run_bounded_real_replay_repair_training
```

## 测试覆盖

测试文件是 `tests/test_model_capability_route_promotion_bounded_real_replay_repair_seed.py`，覆盖：

- plan + replay 可以生成 seed examples。
- seed 会复用 replay prompt。
- plan 不 ready 时 seed fail。
- writer 输出 JSON/CSV/JSONL/corpus/text/Markdown/HTML。
- CLI 能真实写出全部产物。

本版运行：

```powershell
python -m py_compile src/minigpt/model_capability_route_promotion_bounded_real_replay_repair_seed.py src/minigpt/model_capability_route_promotion_bounded_real_replay_repair_seed_artifacts.py scripts/build_model_capability_route_promotion_bounded_real_replay_repair_seed.py tests/test_model_capability_route_promotion_bounded_real_replay_repair_seed.py
python -m pytest tests/test_model_capability_route_promotion_bounded_real_replay_repair_plan.py tests/test_model_capability_route_promotion_bounded_real_replay_repair_seed.py -q -o cache_dir=runs/pytest-cache-v809-focused
```

结果：

- focused tests: `6 passed`

## 截图和归档

运行证据归档在：

- `e/809/解释/说明.md`
- `e/809/解释/model-capability-route-promotion-bounded-real-replay-repair-seed/`
- `e/809/图片/v809-bounded-real-replay-repair-seed-html.png`

Playwright MCP 快照确认 HTML 页面展示：

- `Ready: True`
- `Examples: 6`
- `Cases: 3`
- `Next: run_bounded_real_replay_repair_training`

## 一句话总结

v809 把 bounded replay repair plan 落成可训练 JSONL/corpus seed，让后续版本可以真正执行 repair training。
