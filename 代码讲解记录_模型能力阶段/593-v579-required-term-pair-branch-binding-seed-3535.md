# v579 required-term pair branch-binding seed 3535

## 本版目标和边界

v579 接在 v578 closeout 后面，开始新的 branch-binding objective。v578 的结论是 first-token rows 和 width scaling 不值得继续，因此 v579 不再沿旧变量微调，而是让语料显式表达：

```text
fixed= -> fixed
loss=  -> loss
```

这一版不做 seed sweep、不扩大模型、不宣称模型能力提升。它只建立新 objective 的第一条真实训练基线。

## 为什么先拆文件

`model_capability_required_term_pair_coexistence_corpus.py` 已经接近 500 行。继续把新 objective 的长语料函数塞进去，会降低可维护性。

因此本版新增：

```text
src/minigpt/model_capability_required_term_pair_branch_binding_corpus.py
```

旧 corpus 文件只导入 mode tuple、薄路由函数和 mode 判断函数。这样新增 objective 有自己的承载位置，后续继续扩展 branch-binding 时不会把旧文件推成巨型文件。

## 关键新增文件

```text
src/minigpt/model_capability_required_term_pair_branch_binding_corpus.py
tests/test_model_capability_required_term_pair_coexistence_refresh.py
```

新组件暴露三类入口：

```text
PAIR_BRANCH_BINDING_CORPUS_MODES
extend_pair_branch_binding_corpus(...)
is_pair_branch_binding_corpus_mode(...)
```

`extend_pair_branch_binding_corpus` 返回 bool，主 corpus builder 可以尝试交给它处理；如果不认识该 mode，再进入旧的 unknown mode 错误。

## 语料设计

新 mode 名称：

```text
equals_surface_no_pair_id_branch_binding_repair
```

核心样本包括：

```text
branch fixed prompt fixed= answer fixed
branch loss prompt loss= answer loss
fixed= continues fixed only
loss= continues loss only
fixed= never continues loss
loss= never continues fixed
paired binding fixed=fixed loss=loss
paired binding loss=loss fixed=fixed
```

它刻意不加入 `pair=01`，也不加入 first-token prefix rows，避免回到 v573/v575 已被关闭的路线。

## 真实运行

运行目录：

```text
e/579/解释/model-capability-required-term-pair-branch-binding-seed-3535/
```

关键结果：

```text
status=pass
decision=required_term_pair_colon_immediate_not_stable
pair_full_seed_count=0
continuation_hit_count=0
```

结果是负的：branch-binding v1 没有恢复 seed `3535` 的 pair-full。

## 测试覆盖

测试新增了 branch-binding corpus 断言：

- 包含 explicit fixed/loss binding rows。
- 包含 `fixed= never continues loss` 和 `loss= never continues fixed`。
- 不包含 numeric `pair=01`。
- 不回退到 colon surface。

这保证新 objective 的语料边界和 v578 的路线决策一致。

## 链路角色

v579 是新路线的起点，不是成功证明。它最重要的价值是把“branch-binding objective”从建议变成可运行代码，并记录第一条真实负基线。

## 一句话总结

v579 用拆分后的 branch-binding corpus 开启新路线，但 seed `3535` 仍未 pair-full，下一步应先诊断为什么新 objective 连 partial hit 都没有保住。
