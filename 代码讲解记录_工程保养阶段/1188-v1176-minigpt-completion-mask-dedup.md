# v1176：completion mask helper dedup

## 本版目标与边界

v1176 是 v1175 post-training weight quantization 之后的维护版。Claude 做的 v1175 整体方向是对的：它不是空泛地说“量化可以压缩模型”，而是在 MiniGPT 上做了 weight-only fake quantization，用 held-out completion-token cross entropy、EM、KL 和 weight relative error 衡量质量成本，并且诚实地区分“质量退化曲线”与“真实 int kernel 带来的内存/速度收益”。v1175 的 CI 已经通过，报告和 tag 也已收口。

但检查代码时有一个非常具体的维护问题：v1175 在 `ptq_v1175.py` 里新增了 `_padded_xy`，它和 v1174 刚刚从 distillation 分支抽出来的 `_build_xy` 本质上是同一类逻辑，都是把 `(full_token_ids, prompt_length)` 样本转换成 padded `X` 和 completion-masked `Y`。如果继续放任，每个新实验都会有自己的 mask 构造版本：distillation 一份、PTQ 一份，之后的 QAT、activation quantization、calibration scorecard、completion-only CE 评估可能又各写一份。这样的重复不是大文件问题，而是更危险的“训练合同分裂”：每一份看起来都差不多，但只要其中一份 prompt mask 的边界不同，实验结果就可能不可比。

所以 v1176 的目标是把 completion-token mask 合同提到一个中性的公共位置。它不改变 v1175 的 PTQ verdict，不重新训练，不重新解释量化曲线，也不把维护版伪装成模型能力提升。它只保证：以后只要实验输入形状是 `(full_token_ids, prompt_length)`，就用同一个 helper 得到 `X` 和 `Y`。

## 为什么不是继续放在 `distill_common`

v1174 新增的 `distill_common.py` 是为了给 v1172/v1173 蒸馏实验提供共享 KD 原语，包括 Hinton KL、residual mass shuffle、student training 和 model factory。当时 `_build_xy` 放在那里是合理的，因为第二个调用方还是 distillation 家族内部。

v1175 出现后，调用方变成了另一个实验家族：post-training quantization。PTQ 不做 KD loss，也不关心 teacher soft target，但它需要同一个 completion-mask 评估合同：held-out prompt 作为上下文，completion token 才参与 CE/KL。此时如果让 PTQ 从 `distill_common` 导入 `_build_xy`，虽然能减少重复，但名字会误导读者，好像 PTQ 依赖蒸馏实验。更好的做法是新增一个更中性的模块 `completion_masking.py`，让 distillation 和 PTQ 都依赖它。

这也是本版的一个工程判断：不是所有复用都应该塞进已有 helper。helper 的名字也在表达架构边界。`completion_masking` 表达的是“completion-only loss/eval 的数据合同”，比 `distill_common` 更适合作为跨实验家族的依赖。

## 新增文件：`src/minigpt/completion_masking.py`

新增模块只做一件事：提供 `build_completion_xy(examples, block_size, pad_id)`。

输入 `examples` 的每一行是：

```text
(full_token_ids, prompt_length)
```

其中 `full_token_ids` 是 prompt 和 completion 拼在一起的 token 序列，`prompt_length` 表示 prompt 部分有多长。函数输出：

```text
X: padded input ids
Y: padded target ids, prompt/pad 位置为 IGNORE_INDEX
```

它的核心规则是 next-token 训练的 shifting：`X` 使用 `full[:-1]`，`Y` 使用 `full[1:]`。然后通过 `prompt_length` 决定哪些 target 位置应该忽略。只要 `(t + 1) < prompt_length`，这个 target 仍属于 prompt 区域，就写成 `IGNORE_INDEX`；否则保留真实 token，参与 CE 或 KL。

例如：

```text
full = [7, 8, 9, 10]
prompt_length = 2
```

得到：

```text
X = [7, 8, 9, 0, 0, 0]
Y = [-100, 9, 10, -100, -100, -100]
```

这里 `-100` 是 PyTorch `cross_entropy` 的 ignore index。它说明第一个位置还在 prompt 里，不训练；后面两个位置是 completion 的目标 token，要训练；padding 位置也不训练。

## 修改 `distill_common`

`distill_common.py` 删除了本地 `_build_xy` 实现，改为：

```python
from minigpt.completion_masking import build_completion_xy as _build_xy
```

这个设计有两个好处。第一，旧合同不破。v1172/v1173 和测试里如果还显式使用 `distill_common._build_xy`，仍然可以拿到同一个函数对象。v1174 的 re-export 合同仍然成立。第二，职责更清楚。`distill_common` 继续负责蒸馏特有的东西，例如 `kl_term`、`shuffle_residual_mass`、`train_student`、`teacher_logit_stats`、`make_distill_model`；而 completion mask 的通用数据合同移到 `completion_masking`。

## 修改 `ptq_v1175`

`ptq_v1175.py` 原来的 `_padded_xy` 被删除，`run_ptq` 里构造 heldout CE/KL 评估批次的位置改成：

```python
X, Y = build_completion_xy(held_full, bs, pad_id)
```

这不改变输入输出，只改变 helper 的来源。PTQ 的评估逻辑仍然是：先把 heldout prompt + expected output + EOS 拼成完整 token 序列，再只在 completion 区域计算 CE 和 KL。也就是说，v1175 的量化质量曲线和 verdict 不应因为 v1176 改动而改变。

## 新增测试

`tests/test_completion_masking_v1176.py` 保护三件事。

第一，prompt token 被忽略、completion token 被监督。测试构造 `[7, 8, 9, 10]` 和 `prompt_length=2`，明确断言 `X/Y` 的具体数组。

第二，`distill_common._build_xy` 和 `build_completion_xy` 是同一个函数对象。这不是为了炫技，而是为了保证 v1174 的兼容入口没有变成第二份包装实现。一个真实对象意味着后续修复 mask 合同时不会出现“common 已修、distill alias 未修”的分叉。

第三，EOS-free stochastic completion 的单位置合同仍然成立。v1173 的暗知识实验依赖 `[ctx, sep, x]` 且 `prompt_length=2` 时只监督随机输出字符那一个位置。测试用两行样本断言监督位置数量为 2，并且只落在输出位。

此外，本版 focused suite 继续跑 `tests/test_distill_common_v1174.py` 和 `tests/test_ptq_v1175.py`，证明 distillation compatibility 和 PTQ report shape 都没破。

## README 文档地图

本版还把用户要求新增的 `项目通俗说明/README.md` 接入根 README 的 Documentation Map。这个文件不是实验产物，而是面向人读者的解释入口，回答“这个项目到底在做什么、有价值的地方在哪、每一步输入输出是什么”。把它放进 README 地图，可以让后来读项目的人先从通俗说明进入，再去看 `docs/overview.md`、`model-training.md` 和各版本证据。

这也是工程后期很重要的一类维护：不是每个读者都应该从 1000 多个版本文件里找入口。项目越成熟，越需要几篇稳定、通俗、可信的入口文档。

## 验证结果

本版先跑编译：

```text
python -m py_compile src\minigpt\completion_masking.py src\minigpt\distill_common.py src\minigpt\ptq_v1175.py tests\test_completion_masking_v1176.py tests\test_distill_common_v1174.py tests\test_ptq_v1175.py
```

再跑 focused tests：

```text
python -m pytest tests\test_completion_masking_v1176.py tests\test_distill_common_v1174.py tests\test_ptq_v1175.py -q -o cache_dir=runs\pytest-cache-v1176-focused
```

结果是 `26 passed`。这组测试覆盖了新增 helper、distillation compatibility、PTQ quantization tests 和 run smoke。

## 链路角色

v1176 的链路角色很明确：它不是模型能力推进版，而是跨实验家族的合同收束版。它把“completion-only 训练/评估到底监督哪些 token”这个核心合同变成单一来源。后续如果做 QAT、activation quantization、calibration data replay、completion CE scorecard 或新的 distillation variant，都应该优先复用 `completion_masking.build_completion_xy`。

## 一句话总结

v1176 把 completion-token mask 合同从各实验模块的局部副本里抽出来，形成 PTQ、distillation 和后续 completion-only 实验都能复用的中性公共入口，同时把项目通俗说明接入 README，降低后续维护和阅读成本。
