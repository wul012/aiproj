# v893 bounded objective loss signal bridge target-only memory loss-token probability probe

## 本版目标和边界

v893 的目标是解释 v891 为什么只停在 `\nfixed l`。v892 已经证明 v891 相比 v886 只是把 surface 统一到换行 `fixed l`，没有新增 `loss` 命中。继续盲目训练之前，必须先知道模型在 `fixed l` 后是不想生成 `oss`，还是被 replay 解码预算截断。

本版不重新训练，不修改 replay contract，不把概率探针当作 replay pass。它只做 teacher-forced next-token probability probe。

## 前置能力

本版承接：

- v836 bounded objective contract，定义三条 `fixed loss` contract case。
- v890 stagnation-aware suffix checkpoint，是真实训练产物。
- v891 replay comparison，显示三条 continuation 都是 `\nfixed l`。
- v892 replay delta diagnostic，确认这是 surface convergence without loss gain。

v893 在这些证据上增加一层概率检查：把上下文固定为 `prompt + "\nfixed l"`，然后逐步看目标 `o`、`s`、`s` 的 next-token 概率。

## 关键文件

`src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe.py`

核心概率探针模块。它会读取 objective contract 和 v892 delta report，加载 checkpoint/tokenizer，构造 probe rows，并输出诊断 summary。

`src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe_artifacts.py`

artifact 输出层，负责 JSON、CSV、TXT、Markdown 和 HTML。HTML 用于运行截图，CSV 保留逐 token 概率。

`scripts/probe_bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability.py`

CLI 入口。它接收 objective contract、replay delta、checkpoint、tokenizer、device、top-k 和 out-dir。

`tests/test_bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe.py`

测试文件。它用 fake scorer 验证低概率和 top-k 可见两类诊断，也用一个 tiny checkpoint 验证 CLI 确实能跑 torch 加载链路。

## 核心数据结构

`probe_rows` 是逐 token 表。每行描述一个 case 的一个目标 token：

- `case_id`：contract case。
- `step_index`：`oss` 中的第几个 token。
- `target_token`：当前要检查的目标字符。
- `target_probability`：模型在当前上下文下给目标 token 的概率。
- `target_rank`：目标 token 在全词表分布中的排名。
- `target_in_top_k`：目标 token 是否进入 top-k。
- `top_token` / `top_token_probability`：当前最高概率 token。
- `state_label`：例如 `target_top1`、`target_visible_in_top_k` 或 `target_low_probability`。

`case_rows` 是逐 case 汇总。它把三步 `o/s/s` 合并成：

- `target_probability_product`
- `min_target_probability`
- `max_target_rank`
- `top1_step_count`
- `topk_step_count`
- `loss_suffix_top1`
- `loss_suffix_topk`

`summary` 再聚合到全局：

- `target_top1_rate`
- `target_topk_rate`
- `min_target_probability`
- `mean_target_probability`
- `max_target_rank`
- `low_probability_step_count`
- `all_cases_loss_suffix_top1`
- `all_cases_loss_suffix_topk`

## 核心函数

`build_loss_token_probability_probe()`

这是总入口。它先读取 contract 和 replay delta 的 summary，检查 checkpoint/tokenizer 路径，然后构造 scorer，最后生成 report。

`_probe_rows()`

它为每条 contract case 构造 `prompt + "\nfixed l"`，再 teacher-force 检查 `oss` 三步。每检查一步，就把目标 token 追加进上下文，因此第二个 `s` 的概率是在 `prompt + "\nfixed los"` 后计算的。

`_build_torch_scorer()`

这是实际模型概率计算。它使用 `torch.load()` 读取 checkpoint，用 `GPTConfig(**checkpoint["config"])` 重建 MiniGPT，加载 tokenizer，再取最后一个位置的 logits 做 softmax。

`_decision()`

它不判断 replay 是否通过，只判断概率状态：

- 全部目标 token top-1：说明模型知道怎么接 `oss`，下一步查解码预算或停止条件。
- 全部目标 token 进 top-k 但非 top-1：下一步可测试低温/贪心 replay。
- 目标 token 低概率：才需要补数据修概率。

## 本版真实结果

真实 v890 checkpoint 上的结果是：

```text
status=pass
decision=bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe_loss_suffix_top1_but_decode_blocked
target_top1_rate=1.0
target_topk_rate=1.0
min_target_probability=0.9280321598052979
mean_target_probability=0.952898469236162
max_target_rank=1
low_probability_step_count=0
```

逐 token 结果显示：

- canonical：`o`、`s`、`s` 全部 rank 1。
- minimal：`o`、`s`、`s` 全部 rank 1。
- completion label surface：`o`、`s`、`s` 全部 rank 1。

这很重要：模型不是不会从 `fixed l` 接到 `fixed loss`，而是 replay 阶段很可能没有给它继续生成 `oss` 的预算。

## 测试覆盖

测试覆盖四件事：

- fake scorer 低概率时，decision 必须指向 targeted suffix probability repair。
- fake scorer top-k 可见但非 top-1 时，decision 必须指向低温/贪心 replay。
- replay delta 不 ready 时，probe 必须 fail，不能绕过 v892 的前置证据。
- CLI 使用 tiny checkpoint/tokenizer 真实跑通 torch 加载和 artifact 输出。

## 运行证据

运行证据保存在：

- `e/893/解释/说明.md`
- `e/893/解释/bounded-objective-loss-signal-bridge-target-only-memory-loss-token-probability-probe/`
- `e/893/图片/v893-bounded-objective-loss-signal-bridge-target-only-memory-loss-token-probability-probe-html.png`

截图证明 HTML artifact 可打开，并展示 `target_top1_rate=1.0`、`max_target_rank=1`、`low_probability_step_count=0` 和下一步解码预算检查路线。

## 一句话总结

v893 把失败原因从“模型没学会 loss 后缀”推进到“模型会接 oss，但 replay 解码预算可能截断”，下一版应检查 max-new-tokens 和 continuation 长度。
