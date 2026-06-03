# v817 route promotion bounded real replay prompt-aligned seed revision 代码讲解

## 本版目标和边界

v817 根据 v816 的 failure alignment diagnostic 构建 prompt-aligned seed revision。v816 已经指出：revised corpus 虽然包含 `fixed/loss`，但没有完全覆盖 bounded benchmark 的 exact prompt。v817 的目标就是把 v803 suite 的 exact prompt 直接写入训练样本。

本版不训练模型，也不证明模型能力提升。它只准备更贴近评估 prompt 的训练语料。

## 关键文件

- `src/minigpt/model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision.py`
  - 核心 builder。
  - 消费 benchmark suite、failure diagnostic、repair seed revision。
  - 生成 carry-forward 样本和 exact prompt 样本。

- `src/minigpt/model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_artifacts.py`
  - 输出 JSON/CSV/JSONL/corpus/text/Markdown/HTML。

- `scripts/build_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision.py`
  - CLI 入口。

- `tests/test_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision.py`
  - 覆盖 exact prompt answer 样本数量、输出和 CLI。

## 样本设计

v817 生成三类样本：

- `carry_forward_seed_revision`
  - 保留 v813 seed revision 的 18 条样本。

- `exact_benchmark_prompt_answer`
  - 对每个 v803 suite case 生成一条 exact prompt + `fixed loss` completion。
  - 真实运行生成 5 条，覆盖 5 个 case。

- `exact_benchmark_prompt_self_check`
  - 对每个 case 再生成一条 self-check prompt。
  - 用来强化 exact-term 约束。

真实输出：

```text
original_example_count=18
added_example_count=10
example_count=28
exact_prompt_answer_count=5
```

## 核心检查

`_checks()` 要求：

- benchmark suite 必须 pass；
- diagnostic 必须 pass 且 ready；
- repair seed revision 必须 pass；
- suite cases 必须存在；
- exact prompt answer 数必须等于 case 数；
- 所有 seed example 必须有 text。

这些检查保证 v817 真正修复的是 prompt/corpus gap，而不是只增加普通样本数量。

## 产物角色

- JSON/JSONL：结构化训练样本。
- Corpus：下一版训练直接消费。
- HTML/截图：人工检查 exact prompt 样本是否存在。

本版产物仍然只是训练输入。是否有效，必须等下一版训练和 replay。

## 一句话总结

v817 把 bounded benchmark 的 exact prompts 写入训练语料，修复了 v816 发现的 prompt gap，并为下一轮 prompt-aligned training 建立输入。
