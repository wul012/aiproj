# v1174：distillation common helper dedup

## 本版目标与边界

v1174 是一个合同保持型维护版本，发生在 v1172 deterministic distillation 和 v1173 stochastic dark-knowledge distillation 之后。前两版已经分别给出一组互补结论：在确定性字符串操作任务里，teacher 的 completion 分布接近 one-hot，所谓 dark knowledge 没有存在空间，蒸馏不如把等价计算还给 student 继续训练；在显式构造的随机多模态输出任务里，teacher 的 soft distribution 真实承载了单个 hard label 缺失的概率结构，soft distillation 能在少样本学生里恢复这部分分布信息。也就是说，v1172/v1173 的价值主要在实验设计和对照结论，而不是某一个 helper 函数本身。

问题在于，v1173 为了复用 v1172 已经写好的 KD 训练原语，直接从 `minigpt.distill_v1172` 导入了 `kl_term`、`shuffle_residual_mass` 和 `train_student`，测试里还从 v1172 导入 `_build_xy`。这在短期内可以工作，但它让“历史实验模块”承担了“共享库”的角色。以后如果继续做 v1175、v1176 一类蒸馏变体，最自然的动作就会变成继续改 `distill_v1172.py`，因为 helper 在那里；而一旦旧版本模块被不断回改，读者就很难分清哪些代码属于 v1172 的原始实验，哪些代码是后续版本为了复用而追加的通用能力。

所以本版的边界非常清楚：不重新训练，不改变 v1172/v1173 的报告结论，不引入新的蒸馏算法，也不扩大模型能力声称。它只把已经被两个版本共同使用的底层训练原语抽成一个稳定的 `distill_common` 层，让版本实验模块重新回到“描述本版实验”的位置。这个动作属于工程保养，价值不在于增加一条新指标，而在于降低后续实验扩展的维护风险。

## 前置路线

v1174 接在一条比较清晰的模型能力路线后面。v1164 做 SFT instruction-following，v1165 做 base-to-SFT transfer，v1166/v1168 做 DPO 与 DPO+SFT-aux 的正反实验，v1169 做 reward model 和 best-of-N，v1170 做 speculative decoding，v1172/v1173 做 knowledge distillation 的确定性与随机性对照。中间穿插了 v1167、v1171 这样的维护版本，把重复的 experiment utils 和 script setup 抽出来。

这条路线有一个很好的节奏：连续几个功能实验之后，出现明显重复或职责漂移时就做一次小心的合同保持型重构。v1174 延续的就是这个节奏。它不是为了“看起来更干净”而随便移动文件，而是回应一个已经出现的具体耦合：v1173 依赖 v1172 的底层 helper。这个耦合如果放任，下一步的 distillation 变体会继续沿着版本文件互相导入，最后让实验层和公共训练层混在一起。

## 新增文件：`src/minigpt/distill_common.py`

`distill_common.py` 是本版的核心新增文件。它集中承载六个共享原语：

第一是 `_build_xy`。它把 `(full_tokens, n_prompt)` 形式的训练样本转换成 padded `X` 和 completion-masked `Y`。这里的关键不是 padding 本身，而是 mask 合同：prompt 位置必须是 `IGNORE_INDEX`，completion token 才参与 CE 或 KL。v1172 的 deterministic corpus 和 v1173 的 EOS-free stochastic corpus 都依赖这个合同。对 v1173 来说，`[ctx, sep, x]` 且 `n_prompt=2` 时，mask 应该精确落在随机输出字符那一个位置；如果 mask 错了，KL 就会测到 prompt 或 padding，整个 dark-knowledge 结论都会失真。

第二是 `kl_term`。它实现 Hinton-style knowledge distillation 的 completion-token KL：

```text
tau^2 * KL(softmax(z_teacher / tau) || softmax(z_student / tau))
```

这里 `teacher_probs` 已经是 softmax 后的概率，函数内部只对 student logits 做 `log_softmax`。`tau^2` 不是装饰项，它用于补偿温度缩放后的梯度尺度。v1172 测试里已有 identity 和 tau-scaling 断言，本版把这个函数移到 common 后继续保留这些行为。

第三是 `shuffle_residual_mass`。这是蒸馏实验里很重要的 disentangling control：保留每个 token 的 argmax 类别、最大概率和熵，但打乱非 argmax 类别之间的 residual probability mass。它回答的是“student 是否真的利用了 teacher 对具体非正确类别的偏好结构”，而不是只吃到了置信度和熵形状。v1172 里这个 control 用来说明 deterministic teacher 下 residual identity 没有实际帮助；v1173 里它作为随机任务的反面对照，打乱 soft target identity 后 KL 明显变差。

第四是 `train_student`。它统一覆盖 `loss_mode="ce"` 和 `loss_mode="distill"` 两条路径。CE 模式等价于 hard-label SFT，可选 label smoothing；distill 模式则可以使用 teacher model 产生 soft target，也可以通过 `teacher_probs_fn` 注入外部 soft target。这个 `teacher_probs_fn` 是 v1173 oracle arm 的关键入口：它允许把构造出来的 `P_true` 映射成完整 vocab 上的概率分布，避免硬把 oracle 当成一个 MiniGPT teacher。

第五是 `teacher_logit_stats`。它读取 teacher 在 completion-token 位置的平均最大概率和熵，用来判断 deterministic distillation 中 dark knowledge 是否“有存在空间”。v1172 的重要结论之一就是 teacher 近似 one-hot，因此 soft target 没有额外类别结构可传；这个 helper 的职责就是把这种判断变成可测量字段。

第六是 `make_distill_model`。v1172/v1173 都使用 zero-dropout、RoPE-enabled 的小 MiniGPT。这个模型工厂本来在两个版本中各自定义 `_make_model`，职责完全一致。抽到 common 后，后续蒸馏实验不用继续复制同一个 `GPTConfig` 构造。

## 修改 v1172：保留旧合同，减少本地职责

`src/minigpt/distill_v1172.py` 的修改方式比较保守。原来定义在本文件里的 `_build_xy`、`kl_term`、`shuffle_residual_mass`、`train_student`、`teacher_logit_stats` 和 `_make_model` 被移除，文件顶部改为从 `distill_common` 导入。其中 `make_distill_model` 在 v1172 内部仍被别名成 `_make_model`，这样后面的 `run_distill` 主流程不需要改动。

这里有一个刻意保留的兼容点：v1172 仍然在模块级暴露这些 helper。也就是说，旧代码如果写了：

```python
from minigpt.distill_v1172 import kl_term, train_student
```

仍然可以工作，只是拿到的对象实际来自 `minigpt.distill_common`。这比直接要求所有调用方迁移更稳，也符合“合同保持型重构”的原则。测试新增了 re-export 断言，确保 v1172 的导出和 common 的对象是同一个函数，而不是复制出第二套实现。

## 修改 v1173：切断对版本模块的穿透依赖

`src/minigpt/distill_v1173.py` 的关键变化是导入路径。它不再从 `minigpt.distill_v1172` 导入 KD helper，而是直接从 `minigpt.distill_common` 导入 `make_distill_model`、`shuffle_residual_mass` 和 `train_student`。本地 `_make_model` 定义也被移除，统一使用 common 的模型工厂。

这一步的意义比代码行数更重要。v1173 是 v1172 的“镜像实验”，但镜像关系应该体现在实验设计和报告解释上，而不是 Python import 依赖上。现在 v1173 仍然可以在讲解里引用 v1172 的结论作为前置对照，但代码层面已经不需要把 v1172 当作共享库。这让后续新增 v1175+ 时有一个自然位置可依赖：公共训练原语找 `distill_common`，具体实验结论找各自版本模块。

## 测试覆盖

本版新增 `tests/test_distill_common_v1174.py`。它覆盖四类合同。

第一类是 re-export 合同：断言 `minigpt.distill_v1172.kl_term is minigpt.distill_common.kl_term`，`shuffle_residual_mass` 也是同一个对象，并检查 `train_student` 的所属模块是 `minigpt.distill_common`。这保证 v1172 没有偷偷保留旧实现，也保证旧导入路径没有断。

第二类是 completion mask 合同。测试构造一个简单样本 `([4, 5, 6, 7], 2)`，断言 `X` 是 shifted input，`Y` 在 prompt 之前为 `-100`，completion 位置保留目标 token，padding 位置继续忽略。这是整个 SFT/KD 训练的地基。

第三类是 KL identity 合同。用同一组 logits 同时作为 teacher 和 student，在 `tau=2.0` 下计算 KL，结果应接近 0。这个断言保护 `tau^2` 缩放和 `log_softmax` 方向没有写反。

第四类是模型工厂合同。测试 `make_distill_model` 生成的模型保留传入 vocab/block 参数，启用 RoPE，并关闭 dropout。这样后续实验不会因为 common factory 改动而悄悄改变训练条件。

此外，`tests/test_distill_v1173.py` 中原来从 v1172 导入 `_build_xy` 和在局部重新导入 `shuffle_residual_mass` 的位置改为从 common 导入。这个测试迁移本身就是防回归信号：v1173 的测试现在也不再依赖 v1172 的版本模块。

## 验证命令与结果

本版先跑了编译检查：

```text
python -m py_compile src\minigpt\distill_common.py src\minigpt\distill_v1172.py src\minigpt\distill_v1173.py tests\test_distill_common_v1174.py tests\test_distill_v1172.py tests\test_distill_v1173.py
```

然后跑 focused distillation suite：

```text
python -m pytest tests\test_distill_common_v1174.py tests\test_distill_v1172.py tests\test_distill_v1173.py -q -o cache_dir=runs\pytest-cache-v1174-focused
```

结果是 `35 passed`。这组测试覆盖了新增 common、v1172 原测试、v1173 原测试，说明抽取后核心训练行为和报告 shape 没有被破坏。

## 证据归档

`f/1174/解释/说明.md` 记录本版目标、关键文件、验证命令和边界。`f/1174/解释/distill-common-v1174.html` 是用于截图的轻量 HTML 证据页，展示 `status=pass`、新增 common、迁移范围和 focused suite 结果。截图归档到 `f/1174/图片`。

这类维护版的证据不应该伪装成模型能力证据。它证明的是“代码结构更健康，合同未破”，不是“模型更强”。因此 README 里也把 v1174 描述为 maintenance release，明确说不改变 v1172/v1173 的 model-quality claims。

## 后续影响

v1174 给后续 distillation 分支留下了更干净的落脚点。如果继续做 teacher calibration、multi-token stochastic outputs、不同温度/样本预算、或真实文本不确定性近似，底层 KD helper 都可以从 `distill_common` 取，而不是继续在 `distill_v1172.py` 上叠加职责。

更重要的是，它把项目当前的工程节奏拉回健康状态：连续几版功能实验之后，及时抽出第二个以上调用方共用的训练原语；保留旧导入合同；用 focused tests 证明行为不变；用归档明确本版不声称模型提升。这比为了“拆分”而大规模搬家更克制，也更像长期可维护项目的节奏。

## 一句话总结

v1174 把 v1172/v1173 共用的蒸馏训练地基从历史实验模块里抽出来，形成稳定的 `distill_common` 复用层，让后续蒸馏实验可以继续扩展而不回改旧版本结论。
