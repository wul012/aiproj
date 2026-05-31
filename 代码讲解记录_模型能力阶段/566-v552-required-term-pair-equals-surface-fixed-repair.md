# v552 required-term pair equals-surface fixed repair 代码讲解

## 本版目标和边界

v551 把唯一 held-out gap 定位为 `fixed_term_surface_gap`，也就是 `fixed=` prompt 下 fixed continuation 没命中。v552 的目标是做一个最小、可验证的修复候选：在真实 tiny 训练 corpus 中加入 equals surface，并把 replay prompt 也切到 `fixed=` / `loss=`。

本版不新建治理链，不做大规模 sweep，也不把失败包装成能力提升。它只回答一个窄问题：`equals_surface_fixed_repair` 是否能让 seed `1535` 的 equals surface 达到 fixed/loss pair-full。

## 前置链路

链路来自：

- v550：held-out replay 发现 `8/9`，唯一 gap 是 `equals + 1535`。
- v551：gap diagnostic 证明缺的是 `fixed=` 的 fixed continuation。

v552 在这个基础上回到训练侧，扩展已有 `model_capability_required_term_pair_coexistence_refresh.py`，避免再新造一个相似训练脚本。

## 关键修改文件

- `src/minigpt/model_capability_required_term_pair_coexistence_refresh.py`
  - `PAIR_COEXISTENCE_CORPUS_MODES` 新增 `equals_surface_fixed_repair`。
  - `build_pair_coexistence_refresh_corpus()` 新增 equals surface corpus branch。
  - `_source_report()` 增加 `corpus_mode` 参数。
  - `_source_prompts()` 对新 mode 返回 `fixed=` / `loss=`，其他 mode 保持 `fixed:` / `loss:`。
- `tests/test_model_capability_required_term_pair_coexistence_refresh.py`
  - 新增 corpus 内容测试。
  - 新增 replay prompt 测试，防止以后该 mode 又误用 `fixed:`。

## 核心设计

`equals_surface_fixed_repair` 的 corpus 明确偏向 v551 指出的 fixed miss：

```text
fixed=fixed
fixed=fixed
loss=loss
fixed=f
fixed=fi
fixed=fix
loss=l
loss=lo
loss=los
prompt=fixed=target=fixed
prompt=loss=target=loss
```

同时保留 loss 分支样本，避免只训练 fixed 后完全丢掉 loss。真实结果显示这个担心是对的：fixed 在 suppression profile 下命中了，但 loss 仍没命中，所以 pair-full 没出现。

## 运行流程

复用已有 colon-immediate stability CLI：

1. 用 `equals_surface_fixed_repair` 生成 corpus。
2. 训练 seed `1535` 的 tiny checkpoint。
3. 用 `fixed=` / `loss=` 作为 replay prompts。
4. 对 default 和 newline-suppression 两个 profile 做 generation-profile replay。
5. 输出 stability 主报告和 seed 级 sidecar。

这样 v552 的结果能直接接回 v551 的 gap 证据。

## 真实结果

真实运行结果：

```text
pair_full_seed_count=0
pair_full_seed_rate=0.0
stable_pair_full=False
```

case 级观察：

```text
fixed= + suppress_newline_tokens -> continuation_hit=True
loss=  + default/suppress_newline_tokens -> continuation_hit=False
```

这说明简单 fixed repair 不是足够方案；它修到了 fixed 分支的一部分，但损伤或没有保护 loss 分支。

## 测试覆盖

测试保护两件事：

- corpus branch 必须包含 equals surface 和 fixed repair 样本。
- 选择 `equals_surface_fixed_repair` 时，generation-profile replay 的 prompt 必须是 `fixed=` / `loss=`，不能退回旧的 colon prompt。

这两个断言直接覆盖 v552 的行为边界。

## 归档角色

`e/552` 保存真实训练输出、seed `1535` checkpoint、tokenizer、metrics、generation-profile replay sidecar、HTML 截图和 snapshot。它是负结果证据：后续修复需要同时约束 fixed 与 loss，而不是只补 fixed surface。

一句话总结：v552 把 v551 的 fixed-surface 诊断落到真实训练候选上，并证明“单边 fixed repair”不足以恢复 pair-full。
