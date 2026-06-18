# v1186 MiniGPT grokking checkpoint 推理/demo 代码讲解

## 本版目标与边界

v1185 把 grokking 产品化成一个自包含的标准 checkpoint（权重 + meta 存进一个 `.pt`，能 `load_checkpoint` 重建并复现）。但“保存了”不等于“好用”。v1186 闭合产品化回路：提供一个极小的推理 API，把保存的 checkpoint 加载回来、真正用它计算 `a + b (mod p)`，并用一个 demo 从磁盘上的 `.pt` **独立**复现 held-out 准确率、解码出模型学到的整张模数加法表。

这是工程，不是新科学：没有训练、不需要 GPU、不扩大任何模型质量声明。边界字段写成 `toy_scale_single_task_inference_demo_not_a_scaling_claim`。它要回答的是一个很实在的问题——“别人拿到这个 checkpoint 文件，怎么用它，它是不是真的能泛化”。

## 推理的关键细节：4-token prompt

训练时模型看的是 5 个 token 的完整序列 `[a, +, b, =, c]`，损失只在 `=` 位置（index 3）预测答案 token `c`（index 4）。使用时我们手里只有问题，没有答案，所以喂 4 个 token 的 prompt `[a, +, b, =]`，读最后一个位置（`=`）的 next-token logits，argmax 就是预测的 `c`。这就是标准自回归“生成下一个 token”，和训练时的监督位置一致。

`encode_problem(a, b, p)` 返回 `[[a, p, b, p+1]]`（PLUS=p、EQ=p+1，和 v1179 的 token 方案一致），`predict(model, a, b, p)` 前向后取 `logits[:, -1, :].argmax`。模块对外的核心就是这两个加上 `predict_pairs`（批量解码成 `(a,b,predicted,truth,correct)` 行）和 `evaluate_table`。

## evaluate_table：从磁盘独立复现泛化

`evaluate_table(model, meta)` 是本版最有价值的函数。它对全部 `p^2` 个 `(a,b)` 对做预测，然后用 checkpoint 自带的 `seed` 和 `train_frac` 重算出 train/val 划分（`split_indices`），把准确率拆成 train 和 held-out 两部分。

这一步的意义在于：held-out 准确率是**完全独立于 v1185 训练过程**重算出来的——只依赖磁盘上的 `.pt` 和它内嵌的 meta。如果保存/加载有任何损坏，或者 meta 里的 seed/train_frac 和训练时不一致，这里算出的 held-out 准确率就不会等于 v1185 报告的 0.966。真实结果：train_acc=1.0、heldout_acc=0.965989、overall=0.972792（256 个错误全部落在 held-out 上）——和 v1185 一致，证明 checkpoint 文件真实保留了泛化能力。

## build_report 与 verdict

`build_report` 输出可读性报告：用的哪个 checkpoint、重算的 train/held-out 准确率、解码的 demo 行。verdict 阶梯：`grokking_checkpoint_usable`（held-out≥0.90 且 train≥0.99 且 demo 全对）/ `checkpoint_loaded_but_weak`（准确率不达标）/ `checkpoint_usable_but_demo_pair_wrong`（已知 demo 对解码错了——通常意味着 prompt 编码写错）。只有第一种 `status=pass`。

`DEMO_PAIRS` 选了几个有代表性的对（小操作数、大操作数、进位）：`(36,37) (4,1) (50,50) (96,96) (0,0) (40,80)`，真实运行全部正确，例如 `96+96=95`、`40+80=23`（mod 97）。

## CLI

`scripts/use_grok_checkpoint_v1186.py` 默认加载 v1185 出厂 checkpoint（`--checkpoint` 可换），跑 `evaluate_table` 打印 train/held-out 准确率，解码 `DEMO_PAIRS`，并支持 `--pairs 36 37 4 1 ...` 回答任意指定的对。默认 device 是 cpu（推理很轻）。输出五件套报告。

## 测试

`tests/test_grok_predict_v1186.py` 共 7 个，全部 CPU 且快：

- prompt 编码（`[a, p, b, p+1]`，shape `[1,4]`）。
- `predict`/`predict_pairs` 在一个 tiny 模型上的 plumbing（truth==(a+b)%p、correct 标志一致、预测落在 vocab 内）——只验证管线，不假设 tiny 模型答对。
- verdict 阶梯三种（usable / weak / demo_pair_wrong），用合成指标。
- **集成测试**：直接加载磁盘上**已提交**的 v1185 checkpoint（`DEFAULT_CHECKPOINT`），断言 `predict(36,37)=73`、`predict(96,96)=95`、`evaluate_table` 的 train_acc≥0.99 且 heldout_acc≥0.90。这条用例真正证明“出厂 checkpoint 文件可加载、可泛化”，并且把 v1186 和 v1185 的产物绑在一起（文件缺失时 skip）。

## 链路角色与一句话总结

v1185 保存 checkpoint → v1186 用 checkpoint。这是产品化的最后一步：从“我训练并存了一个会 grok 的模型”到“这是加载它、用它、并验证它确实泛化的最小代码”。配合 v1186 的加法表正确性图（train 格浅灰、held-out 正确为绿、错误为红），读者能一眼看到模型把整张 `a+b mod 97` 表填满、并泛化到没见过的格子。

一句话总结：v1186 给 v1185 的 grokking checkpoint 配上一个 `load + predict` 的极小推理 API 和 demo，从磁盘加载就能算 `a+b mod 97`、独立复现 0.966 的 held-out 准确率，并把学到的整张加法表画出来。
