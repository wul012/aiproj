# v1146 decoder anchor probe：用 v1145 checkpoint 做局部片段信号验证

## 本版目标与边界

v1146 的目标非常明确：接住 v1145 报告里的 `next_step=run_decoder_anchor_probe_against_v1145_checkpoint`，用 v1145 真实训练产生的 checkpoint 跑一组短 prompt 的 decoder-anchor probe。v1145 已经证明两件事：第一，bounded CPU training 真实执行，并且 train loss 与 val loss 都下降；第二，训练语料中的 carry-forward、direct-answer、decoder-bridge 三类样本分布均衡，没有触发 rebalanced seed 风险。v1146 在这个基础上继续往模型输出侧推进，检查这个 checkpoint 是否已经出现局部 anchor-assisted fragment signal。

本版边界同样重要。v1146 不做模型 promotion，不宣称 unassisted holdout replay 已经恢复，也不把短 anchor prompt 的片段命中解释成完整模型能力提升。报告里的 `model_quality_claim` 被写为 `decoder_anchor_fragment_signal_only`，`promotion_ready=False`，并且额外写入 `unassisted_success_claim=False`。这三个字段是本版最关键的约束：它承认 checkpoint 有一点真实输出信号，但拒绝把这个信号膨胀成更大的模型质量结论。

## 为什么需要 v1146

如果 v1145 之后直接做新的治理报告，模型能力路线又会回到文档和证据链内部循环。v1145 的真实训练已经给出了一个 checkpoint，下一步自然应该问：这个 checkpoint 在输出层面有没有一点可观察变化？但这个问题不能粗暴地设成“必须完整回答 fixed loss”。真实试探发现，v1145 checkpoint 学到的是局部字符片段和局部关联，而不是稳定的长 prompt 问答能力。长 prompt 会因为 block size、字符 tokenizer 和短训练共同作用而产生截断或片段化输出。因此 v1146 采用短 anchor prompt，例如 `fixed `、`lo`、`los`、`fi`，检查的是局部 fragment signal，而不是完整任务成功。

这个设计比“强行要求完整 required terms”更诚实。一个学习型 MiniGPT 项目在 40 step 小训练之后，合理预期是局部 token/字符关联增强，而不是具备可靠问答能力。v1146 把这个判断写进代码与报告：只要求 `fragment_hit_count >= 4`，以及 `anchor_assisted_loss_hit_count >= 3`；同时在 summary 中明确 `unassisted_success_claim=False`。这既给模型输出信号留了空间，也不越界。

## 关键路径漂移问题

v1146 还修复并显式记录了一个真实工程问题：v1145 主报告是在 `output/model-capability-loss-signal-bridge-decoder-anchor-distribution-v1145` 目录中生成的，然后整体复制到 `f/1145` 归档。报告 JSON 里的 `training_signal.checkpoint_path` 和 `training_signal.tokenizer_path` 因此仍指向 `output/...`。提交前清理掉 `output` 后，这些路径就变成了 stale path。文件本身没有丢，因为 checkpoint 和 tokenizer 被复制到了 `f/1145/解释/.../real-loss-signal-training-run/`，但报告里的路径不再直接可用。

v1146 没有回改已经发布的 v1145 tag，而是在新模块里加入 `resolve_v1145_checkpoint_paths`。这个 resolver 先读取报告中记录的路径，如果存在就使用；如果不存在，并且调用方提供了 v1145 报告路径，就从报告所在目录查找 `real-loss-signal-training-run/checkpoint.pt` 和 `tokenizer.json`。如果 fallback 成功，报告会写入 `used_archive_relative_fallback=True`，同时保留 `reported_checkpoint_exists=False`、`reported_tokenizer_exists=False`。这比悄悄替换路径更好，因为它把归档路径漂移变成了可审计事实。

这个小修复很有工程价值。它提醒后续版本：归档报告中如果记录中间目录路径，最终证据迁移后必须有 archive-relative resolver，或者在生成报告时就写最终归档路径。v1146 先用 resolver 兜住，不破坏旧 tag，不回写历史文件，也让新报告说明自己如何找到真实 checkpoint。

## 新增模块

核心文件是 `src/minigpt/model_capability_decoder_anchor_probe_v1146.py`。它没有复用旧的 route-promotion decoder probe 入口，因为旧入口依赖 prompt-aligned replay report 和 failure diagnostic report，语义偏 route promotion。v1146 的输入更简单：一个 v1145 loss-signal/distribution report，加上解析出的 checkpoint/tokenizer。为了不硬套旧结构，本版写了一个轻量 wrapper。

模块的主函数有四个：

- `resolve_v1145_checkpoint_paths`
- `build_decoder_anchor_probe_v1146`
- `write_decoder_anchor_probe_v1146_outputs`
- `resolve_exit_code`

`resolve_v1145_checkpoint_paths` 负责路径解析。它返回的不只是最终 checkpoint/tokenizer，还包括 reported path 是否存在、是否使用 fallback 等诊断字段。这个返回对象会进入主报告 `path_resolution`，用于解释为什么本版能在 `output` 被清理后仍找到 v1145 checkpoint。

`build_decoder_anchor_probe_v1146` 是主 builder。它接收 v1145 report、checkpoint、tokenizer、device、可选 generator runner，然后跑 `_probe_cases` 定义的五个短 prompt。默认 runner 使用 `MiniGPTGenerator` 和 `GenerationRequest`，所以真实 CLI 路径确实会加载 v1145 checkpoint，而不是读取 fixture。测试中可以注入 fake runner，避免单测依赖真实 torch checkpoint 行为。

## Probe case 设计

本版的五个 case 分别是：

- `fixed-space-loss`：prompt 是 `fixed `，期望 combined output 里出现 `loss`。
- `lo-to-loss`：prompt 是 `lo`，期望 combined output 里出现 `loss`。
- `los-to-loss`：prompt 是 `los`，期望 combined output 里出现 `loss`。
- `fixed-retention`：prompt 是 `fixed`，期望 combined output 里保留 `fixed`。
- `fi-to-loss-association`：prompt 是 `fi`，期望 combined output 里出现 `loss`。

这些 prompt 很短，避免了 v1145 checkpoint 的 `block_size=16` 在长 prompt 下截断上下文。每个 case 使用固定 seed 和 `top_k=5`，temperature 固定为 `0.2`，让本版输出可复现。真实运行结果是 `fragment_hit_count=5`，`anchor_assisted_loss_hit_count=4`。这说明模型不是完整掌握任务，但在局部 anchor 下已经能产生和 `loss` 相关的片段。

`_row` 会记录 prompt、generated、continuation、combined、expected_fragment、fragment_hit、anchor_assisted_loss_hit。这里的 `combined` 很重要，因为像 `lo` 这种 anchor，本身只提供前缀，continuation 可能是 `sssss`，单看 continuation 不包含 `loss`，但 combined 是 `losssss`，能说明 anchor-assisted fragment 成立。v1146 因此没有只看 continuation，而是同时保留 generated/continuation/combined。

## 检查规则

v1146 的 check rows 覆盖十个点。首先检查 v1145 report 必须 `status=pass`，并且 `summary.loss_signal_bridge_decoder_anchor_distribution_ready=True`。然后检查 v1145 的 next step 必须等于 `run_decoder_anchor_probe_against_v1145_checkpoint`，避免本版脱离前置路线。接着检查 checkpoint/tokenizer 是否存在，五个 probe case 是否全部执行，是否无 generation error。最后检查 fragment threshold 和 loss anchor threshold。

阈值被刻意设为“片段信号”而不是“完整能力”：`fragment_hit_threshold` 要求至少 4 个 case 命中 expected fragment，`loss_anchor_hit_threshold` 要求至少 3 个 case 在 anchor assistance 下出现 loss。真实运行分别得到 5 和 4，所以报告 pass。最后的 `promotion_boundary_kept` 是固定 pass 的边界行，用于提醒读者：本版不是 promotion。

summary 字段也围绕这个边界展开：`decoder_anchor_probe_ready=True` 表示 probe 本身可用；`fragment_hit_rate=1.0` 和 `anchor_assisted_loss_hit_rate=0.8` 表示局部信号强度；`model_quality_claim=decoder_anchor_fragment_signal_only` 表示结论范围；`promotion_ready=False` 与 `unassisted_success_claim=False` 表示不能把结果外推。下一步写成 `compare_decoder_anchor_probe_with_unassisted_holdout_replay`，说明后续应该把 anchor-assisted 与 unassisted 做对照，而不是直接继续推广。

## CLI 入口

CLI 文件是 `scripts/run_model_capability_decoder_anchor_probe_v1146.py`。它默认读取：

```text
f/1145/解释/model-capability-loss-signal-bridge-decoder-anchor-distribution-v1145/model_capability_loss_signal_bridge_decoder_anchor_distribution_v1145.json
```

默认输出：

```text
output/model-capability-decoder-anchor-probe-v1146
```

CLI 支持 `--checkpoint` 和 `--tokenizer` 覆盖路径，测试中会用这个能力注入 tiny checkpoint。真实运行不传覆盖参数，于是走 v1145 report resolver，发现报告里的 `output/...` 路径已经不存在，再 fallback 到 `f/1145/.../real-loss-signal-training-run`。这条路径解析被写入 JSON，所以后续排查不会困惑为什么源报告写的是 output，实际用的是 f。

输出仍复用 `write_readability_outputs`，生成 JSON、CSV、TXT、Markdown、HTML 五种格式。HTML 被 Playwright MCP 打开并截图归档到 `f/1146/图片`。

## 测试覆盖

测试文件是 `tests/test_model_capability_decoder_anchor_probe_v1146.py`。第一组测试注入 fake runner，确认五个 fragment 都能命中，报告 status/decision/summary 都符合预期，并且 `promotion_ready` 和 `unassisted_success_claim` 都是 False。它保护的是主 builder 的成功路径和边界表达。

第二组测试专门验证 archive-relative resolver。测试创建一个假归档目录，在 report JSON 旁边放 `real-loss-signal-training-run/checkpoint.pt` 和 `tokenizer.json`，但 report 自己的 training_signal 指向不存在的 `output/stale/...`。resolver 应该报告原始路径不存在，同时成功 fallback 到归档目录。这个测试保护 v1146 的实际价值点之一：修复归档路径漂移。

第三组测试把 v1145 ready flag 改成 False，报告必须失败并给出 `v1145_report_ready` issue。它保护前置链路，防止 v1146 被孤立运行。

第四组测试覆盖输出和 CLI。它用 `create_required_term_tiny_checkpoint` 创建一个可真实加载的 tiny checkpoint，再调用 CLI 的 `--checkpoint` 和 `--tokenizer` 参数，确保命令行路径可以真实写出 `model_capability_decoder_anchor_probe_v1146.json`。这个测试不依赖 f/1145 真实归档，所以在 CI 中稳定。

## 运行证据

真实命令如下：

```powershell
python scripts/run_model_capability_decoder_anchor_probe_v1146.py --out-dir output/model-capability-decoder-anchor-probe-v1146 --require-pass --force
```

输出为 `status=pass`，`decision=model_capability_decoder_anchor_probe_found_fragment_signal`。关键指标是 `probe_case_count=5`、`fragment_hit_count=5`、`anchor_assisted_loss_hit_count=4`、`fragment_hit_rate=1.0`、`anchor_assisted_loss_hit_rate=0.8`。这说明 v1145 checkpoint 确实有 anchor-assisted fragment signal。报告归档到 `f/1146/解释/model-capability-decoder-anchor-probe-v1146`，截图保存到 `f/1146/图片/model-capability-decoder-anchor-probe-v1146.png`。

## 一句话总结

v1146 没有夸大模型能力，而是把 v1145 checkpoint 的真实输出推进到一个更精确的位置：局部 decoder-anchor 片段信号已经出现，但下一步必须与 unassisted holdout replay 做对照后，才能讨论更强的模型能力结论。
