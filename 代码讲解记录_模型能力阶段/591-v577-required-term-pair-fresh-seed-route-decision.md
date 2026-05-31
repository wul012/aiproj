# v577 required-term pair fresh-seed route decision

## 本版目标和边界

v577 接在 v576 后面，把 fresh seed `3535` 的三路变量比较转成可复核的 route decision。它解决的问题不是“哪个模型更强”，而是“哪些路线已经不该继续消耗版本”。

这一版不重新训练、不新增 corpus mode、不扩大模型。输入是 v576 的 comparison JSON，输出是 JSON/CSV/text/Markdown/HTML 五种决策产物。

## 前置能力

v571、v573、v575 分别保留了三份真实训练报告：

```text
v571-loss-balanced
v573-first-token
v575-wider-embd
```

v576 已经确认三者 `pair_full_profile_seed_count=0`，并且 `union_hit_terms=fixed`。v577 只读这份 comparison，把“停止 first-token rows 与 width scaling”变成后续脚本可消费的结论。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_fresh_seed_route_decision.py
src/minigpt/model_capability_required_term_pair_fresh_seed_route_decision_artifacts.py
scripts/run_model_capability_required_term_pair_fresh_seed_route_decision.py
tests/test_model_capability_required_term_pair_fresh_seed_route_decision.py
```

`model_capability_required_term_pair_fresh_seed_route_decision.py` 负责读取 comparison、生成 route rows、判断 route type 和 rejection reasons。

`model_capability_required_term_pair_fresh_seed_route_decision_artifacts.py` 负责渲染 JSON 之外的 CSV、text、Markdown 和 HTML，保证报告能被机器读取，也能被浏览器检查。

CLI 脚本只做输入定位、输出目录保护、调用 builder 和 `--require-pass` 退出码处理。

## 核心数据结构

每条 route row 包含：

```text
source_label
corpus_mode
pair_full_seed_count
seed_count
stable_pair_full
hit_terms
route_type
rejection_reasons
```

`route_type` 由 label 和 corpus mode 推断：

- `first_token`：包含 first-token 或 first_token。
- `width_scaling`：包含 wider、embd 或 width。
- `baseline`：其余路线。

`rejection_reasons` 用三条约束表达失败原因：

- `no_pair_full_seed`
- `loss_term_missing`
- `not_stable`

## 决策逻辑

如果输入 comparison 不通过，decision 是：

```text
fix_required_term_pair_fresh_seed_route_decision_input
```

如果任一路线出现 pair-full，decision 会切到候选推广：

```text
promote_fresh_seed_pair_full_route
```

v577 的实际输入里没有 pair-full，并且同时出现 first-token 与 width scaling 失败路线，因此最终决策是：

```text
stop_first_token_and_width_for_fresh_seed
```

## 运行证据

输出目录：

```text
e/577/解释/model-capability-required-term-pair-fresh-seed-route-decision/
```

关键字段：

```text
status=pass
decision=stop_first_token_and_width_for_fresh_seed
route_count=3
pair_full_route_count=0
best_residual_signal=v571-loss-balanced
model_quality_claim=route_decision_only
```

这里的 `model_quality_claim=route_decision_only` 是边界字段：本版只决定下一步路线，不把 partial fixed signal 包装成模型能力提升。

## 测试覆盖

`tests/test_model_capability_required_term_pair_fresh_seed_route_decision.py` 覆盖四类行为：

- v571/v573/v575 fixture 能生成停止 first-token 和 width scaling 的决策。
- 输入失败时 `--require-pass` 对应的退出码为 `1`。
- JSON/CSV/text/Markdown/HTML 输出都能生成。
- 输入目录会自动定位到 v576 comparison JSON 文件名。

## 链路角色

v577 是 fresh-seed 变量实验的闸门。它让后续版本不再依靠记忆判断，而是可以读取明确的 route decision：继续做 small variant 没有价值，应该先做新的 branch-binding objective。

## 一句话总结

v577 把 v571-v576 的负结果沉淀为机器可读路线决策，为下一轮 objective 设计前先关掉 first-token rows 和 width scaling 两条低收益分支。
