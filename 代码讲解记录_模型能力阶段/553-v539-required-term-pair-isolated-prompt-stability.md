# v539 required-term pair isolated prompt stability 代码讲解

## 本版目标和边界

v538 的短前缀增强没有提升 pair-full 稳定率。v539 尝试另一条数据设计路线：把 fixed 与 loss 放入独立 objective block，降低局部上下文互相抢首 token 的概率。

本版不调整模型结构、不增加训练预算、不把负结果当成功能提升。它只验证 isolated prompt corpus 是否比 v538 更稳。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_coexistence_refresh.py`
  - 新增 `colon_immediate_isolated_prompt` corpus mode。
- `tests/test_model_capability_required_term_pair_coexistence_refresh.py`
  - 覆盖 fixed/loss objective block、直接目标行和无空格形态。
- `e/539/解释/model-capability-required-term-pair-colon-immediate-isolated-prompt-stability/`
  - 保存真实三 seed stability 报告。
- `e/539/解释/model-capability-required-term-pair-colon-immediate-isolated-prompt-missed-seed-diagnostic/`
  - 保存 first-token 诊断 sidecar。

## 核心 corpus 改动

新增 mode 生成类似结构：

```text
[fixed-objective]
prompt fixed:
target fixed
fixed:fixed
fixed:f
fixed:fi
fixed:fix
fixed branch answer fixed
[/fixed-objective]

[loss-objective]
prompt loss:
target loss
loss:loss
loss:l
loss:lo
loss:los
loss branch answer loss
[/loss-objective]
```

这个设计的直觉是减少 fixed/loss 在同一局部窗口中的干扰。但真实结果证明，对于字符级 tiny GPT，块状上下文没有自动变成更强的 prompt 映射。

## 真实结果

stability 结果：

```text
decision=required_term_pair_colon_immediate_not_stable
pair_full_seed_count=0/3
pair_full_seed_rate=0.0
```

first-token 诊断：

```text
535  -> fixed rank=1, loss rank=2
1535 -> fixed rank=1, loss rank=2
2535 -> fixed rank=2, loss rank=1
```

所有 seed 都只偏向其中一个分支，说明 isolated prompt 没有解决 first-token 分离问题。

## 测试覆盖

单测确保：

- `colon_immediate_isolated_prompt` mode 被纳入统一 corpus mode 常量。
- corpus 中存在 `[fixed-objective]` 和 `[loss-objective]`。
- fixed/loss block 中保留直接 `fixed:fixed`、`loss:loss` 的无空格目标形态。

真实 PyTorch 三 seed 训练和 first-token 诊断由 `e/539` 证据覆盖，HTML 截图由 Playwright MCP 生成。

## 链路角色

v539 是一次方向裁剪。它把“分块隔离可能更好”的假设排除掉，让后续路线回到更直接的 prompt 映射、重复比例、训练参数和采样边界对照。

一句话总结：v539 用真实训练证明 isolated prompt corpus 不适合作为当前 fixed/loss pair objective 的下一步。
