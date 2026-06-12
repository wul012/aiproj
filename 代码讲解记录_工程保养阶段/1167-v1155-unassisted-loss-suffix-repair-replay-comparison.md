# v1155 unassisted loss suffix repair replay comparison 代码讲解

## 本版目标与边界

v1155 的目标很窄，但它在模型能力路线里很关键：把 v1154 真实训练出来的 checkpoint 放回到 target-free holdout prompts 上重放，确认 v1153 的 loss-suffix repair seed 是否真的把 `fixed loss` 这个目标从训练产物推进到了未污染提示词的生成结果里。v1154 已经证明训练过程本身是完整的：checkpoint、tokenizer、metrics、manifest、prepared corpus、sample 都存在，训练 loss 和验证 loss 都下降，而且 sample 里已经能看到 `fixed` 与 `loss`。但是训练样本的 sample 不能直接等价于能力提升，因为它只说明训练运行本身能产出一个看起来相关的样本，不说明模型在独立的 target-free holdout 上也能稳定恢复目标词对。

所以 v1155 做的是一层真实 generation replay。它读取 v1154 交接文件 `unassisted_loss_suffix_repair_training_handoff_v1154.json`，从里面解析 checkpoint、tokenizer、holdout prompts 路径，再对 v1153 保留的 5 条 target-free prompts 调用 `MiniGPTGenerator` 生成 continuation。每条 continuation 都被重新评分，检查 `fixed`、`loss`、full-pair 是否命中。这个版本不重新训练，不改语料，不调参，不生成新的 seed corpus，也不把 `promotion_ready` 改成 true。它只负责把“训练产物存在”升级成“真实 replay 证据存在”，并把结果导向下一步诊断。

这个边界很重要。前一版 v1154 的 `model_quality_claim=training_artifact_only`，本版如果只看训练 sample 里的 `loss` 就直接宣布恢复，会把训练证据误当成模型能力证据。v1155 因此把结果压回 replay 视角：只要 holdout prompts 没有完整命中 `fixed loss`，就只能给出 `bounded_holdout_replay_partial_signal`，不能升级为恢复候选。

## 前置链路

这一版接在 v1152、v1153、v1154 后面：

- v1152 读取 v1151 replay，发现旧 checkpoint 在 5 条 holdout 里主要只输出 `fixed`，`loss` 没有命中，并把原因推向 loss suffix 上下文不足。
- v1153 根据这个诊断生成修复 seed：在训练语料里补充 `fixed -> loss` 的后缀记忆，同时继续保留 target-free holdout prompts，避免把答案写进提示词。
- v1154 用 v1153 的修复语料做一次 bounded CPU training，并输出训练 handoff，把 checkpoint、tokenizer、holdout prompts、promotion boundary 和下一步 `run_unassisted_loss_suffix_repair_replay_comparison` 写清楚。
- v1155 只消费 v1154 handoff，不自己猜路径，不绕过 handoff 去找旧产物。

这条链路让每一版都承担单一角色。v1153 是“改训练输入”，v1154 是“产生训练产物”，v1155 是“检查训练产物在真实 holdout 上的生成表现”。这样做的好处是，后续如果结果仍然不理想，可以明确判断问题出在 seed、训练、生成预算、prompt 表面，还是评分逻辑，而不会把多个变量混在一个版本里。

## 新增模块

核心新增文件是 `src/minigpt/unassisted_loss_suffix_repair_replay_comparison_v1155.py`。它从 v1151 的 replay comparison 形态继承了最重要的几个设计：默认 handoff 路径、输入定位、预检、真实生成、行级评分、汇总决策、输出写入和 CLI exit code。不同之处在于，本版的默认路径指向 v1154 的训练归档：

```text
f/1154/解释/unassisted-loss-suffix-repair-training-run-v1154/unassisted_loss_suffix_repair_training_handoff_v1154.json
```

`default_v1154_training_handoff_path()` 负责生成这个路径。这样 CLI 在没有额外参数时就会自然消费上一版的正式归档，而不是消费临时 `output/`。`locate_v1154_training_handoff()` 则允许用户传入 handoff 文件或包含 handoff 的目录，便于测试和手动复核。

`build_unassisted_loss_suffix_repair_replay_comparison_v1155()` 是主构建函数。它接受 handoff JSON，支持覆盖 checkpoint、tokenizer、holdout prompts，也支持 `precomputed_generations`。后者只用于测试或离线复核，不是默认运行路径。真实运行时，函数会读取 handoff 中的 checkpoint/tokenizer，并对 holdout prompts 逐条调用 `_generate_case()`。

## 输入输出模型

本版的输入来自 v1154 handoff，核心字段包括：

- `status`：必须是 `pass`。
- `checkpoint`：v1154 训练出的 `checkpoint.pt`。
- `tokenizer`：v1154 训练出的 `tokenizer.json`。
- `holdout_prompts`：v1153 保留下来的 target-free prompt JSON。
- `promotion_ready`：必须保持 false。
- `next_step`：必须是 `run_unassisted_loss_suffix_repair_replay_comparison`。

输出报告保持 readability report 结构，主文件名为 `unassisted_loss_suffix_repair_replay_comparison_v1155.json`，并同步写出 CSV、text、Markdown、HTML 和 generation rows sidecar。sidecar 文件 `unassisted_loss_suffix_repair_replay_generation_rows_v1155.json` 专门保留逐条生成结果，便于后续诊断直接读取 continuation，而不用从 HTML 或 CSV 里反向解析。

报告的 `summary` 是后续版本最关心的入口。本次真实运行得到：

```text
unassisted_loss_suffix_repair_replay_comparison_ready=True
case_count=5
fixed_hit_case_count=5
loss_hit_case_count=0
full_pair_case_count=0
any_hit_case_count=5
full_pair_rate=0.0
all_full_pair_hit=False
partial_signal_visible=True
model_quality_claim=bounded_holdout_replay_partial_signal
promotion_ready=False
next_step=diagnose_unassisted_loss_suffix_repair_partial_signal
failed_check_count=0
```

这里最值得注意的是 `fixed_hit_case_count=5` 与 `loss_hit_case_count=0` 的组合。v1154 的 sample 曾经显示 `loss`，但 v1155 的 5 条 holdout replay 没有一条完整命中 `loss`。这说明模型在未污染提示词上确实更稳地输出了 `fixed`，但还没有恢复完整目标词对。

## 预检逻辑

`_preflight_checks()` 防止 replay 建在错误输入上。它检查 8 件事：

- handoff 本身必须 `status=pass`。
- handoff 的 `next_step` 必须指向本版 replay。
- checkpoint 必须存在。
- tokenizer 必须存在。
- holdout prompts 文件或显式传入的 prompts 必须存在。
- prompt 数量至少覆盖 v1153 的 5 条 target-free prompts。
- prompt 文本不能提前包含 expected terms，避免把答案写进输入。
- `promotion_ready` 必须保持 false。

这些检查保护的是证据边界，而不仅是运行方便。比如如果有人把 holdout prompt 改成 `answer fixed loss:`，模型即使复读答案也没有意义；如果有人把 v1154 handoff 的 `promotion_ready` 改成 true，本版也必须阻止这种越界说法。v1155 的真实运行里 `failed_check_count=0`，说明 replay 输入完整且边界成立。

## 真实生成与评分

`_generate_case()` 是本版和纯治理报告的区别。它不是读取旧 JSON 里的判断，而是用 `MiniGPTGenerator(checkpoint, tokenizer, device=device)` 加载 v1154 的训练产物，然后构造 `GenerationRequest`。每条 prompt 使用自己的 `max_new_tokens`、`temperature`、`top_k`、`seed`；如果 prompt 没有 seed，本版默认使用 `115500 + index`，保证 generation replay 可复核。

`_scored_generation()` 对生成结果做行级评分。它把 continuation 转成小写，然后检查：

- `fixed_hit`：continuation 里是否出现 `fixed`。
- `loss_hit`：continuation 里是否出现 `loss`。
- `term_hits`：对 expected terms 做逐项命中映射。
- `full_pair_hit`：所有 expected terms 是否都命中。
- `status`：full pair 为 `pass`，部分命中为 `partial`，完全不命中为 `fail`。

真实生成里有几条 continuation 形如 ` fixed l`，其中 `fixed` 已经完整出现，`loss` 只露出了开头的 `l`，没有达到完整词命中。这个现象很有价值：它说明 v1153 的 loss-suffix 修复没有白费，模型已经把输出推向了 `fixed l` 这种近命中表面；但它也说明当前训练或解码预算仍不足以稳定完成 `loss`。因此本版没有把结果包装成成功，而是把下一步指向 partial-signal diagnostic。

## 决策与下一步

`_comparison()` 汇总所有行级评分。它不是只看单条最佳输出，而是看 5 条 holdout 的整体结果。只要 `full_pair_case_count` 不等于 `case_count`，`all_full_pair_hit` 就是 false。真实结果里 5 条全部命中 `fixed`，但 0 条命中 `loss`，所以 `partial_signal_visible=True`，`model_quality_claim=bounded_holdout_replay_partial_signal`。

`_decision()` 根据三个层级返回稳定决策：

- 输入或预检失败：`fix_unassisted_loss_suffix_repair_replay_comparison`。
- 所有 holdout 都 full-pair：`unassisted_loss_suffix_repair_replay_full_pair_recovered_candidate`。
- 有任意 required term 命中但没有 full-pair：`unassisted_loss_suffix_repair_replay_partial_signal`。
- 完全没有 required term：`unassisted_loss_suffix_repair_replay_zero_hit`。

真实运行落在第三类。这是一个比 v1151 更强的 partial signal，因为 v1151 是 4/5 命中 `fixed`，本版是 5/5 命中 `fixed`；但它仍不是完整恢复，因为 `loss` 没有被完整生成。下一步 `diagnose_unassisted_loss_suffix_repair_partial_signal` 应该专门分析为什么模型停在 `fixed l`，例如检查 max_new_tokens、prompt 表面、训练样本里的 suffix 位置、以及是否需要把 `loss` 的完整词边界做得更清晰。

## CLI 与测试

新增脚本是 `scripts/run_unassisted_loss_suffix_repair_replay_comparison_v1155.py`。它默认读取 v1154 的正式归档 handoff，默认输出到 `output/unassisted-loss-suffix-repair-replay-comparison-v1155`，支持 `--require-comparison-ready` 和 `--require-full-pair` 两个门控。实际验证只使用 `--require-comparison-ready`，因为本版不能预设 full-pair 成功；如果用户或 CI 想把 full-pair 当成硬门槛，可以显式加 `--require-full-pair`。

测试文件 `tests/test_unassisted_loss_suffix_repair_replay_comparison_v1155.py` 覆盖了五类风险：

- partial signal 能 pass comparison ready，但不能通过 require-full-pair。
- all full-pair 的模拟输出会被标成 recovered candidate。
- prompt 里提前出现 `fixed` 时，预检失败且不会生成 rows。
- archived handoff 里的旧 `output/.../checkpoint.pt` 路径失效时，可以回落到 handoff 同级的 `run/checkpoint.pt`。
- 输出写入和 CLI 能消费 precomputed generation rows。

这些测试不是只看函数能跑，而是保护了本版的证据契约：输入必须干净，路径必须可复原，输出必须可归档，exit code 必须能区分“比较器就绪”和“能力完全恢复”。

## 证据归档

本版真实输出归档在 `f/1155/解释/unassisted-loss-suffix-repair-replay-comparison-v1155/`。其中 HTML 报告通过 Playwright MCP 打开并截图，截图保存到 `f/1155/图片/unassisted-loss-suffix-repair-replay-comparison-v1155.png`。截图里能直接看到 `case_count=5`、`fixed_hit_case_count=5`、`loss_hit_case_count=0`、`partial_signal_visible=True` 和 `promotion_ready=False`，也能看到下方 `Replay Generations` 表格。

这类截图不是为了装饰，而是给后续人工复核一个入口：不需要打开 JSON，也可以确认本版不是 promotion，而是 partial signal。JSON/CSV/Markdown/HTML 则是机器消费和长期归档入口。

## 一句话总结

v1155 把 v1154 的训练产物真正放回 target-free holdout 上生成，证明 loss-suffix repair 已经让 `fixed` 稳定出现，但 `loss` 仍未完整恢复，因此下一步应做 partial-signal diagnostic，而不是继续宣传模型已恢复。
