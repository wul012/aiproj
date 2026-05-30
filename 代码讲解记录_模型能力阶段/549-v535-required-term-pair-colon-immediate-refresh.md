# v535 required-term pair colon-immediate refresh 代码讲解

## 本版目标和边界

v534 已经定位到 v533 的关键问题：`fixed:` 和 `loss:` 后的第一 token 被空格强烈压住，expected `f/l` 排名很低。v535 因此不继续盲目增加训练轮数，而是修改 corpus 形态，新增 `colon_immediate` 模式，用 `fixed:fixed` 和 `loss:loss` 直接训练冒号后的目标 token。

本版仍然是 tiny targeted 训练，不声明泛化模型能力。只有当 pair-full 在单 seed 出现时，称为 targeted signal。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_coexistence_refresh.py`
  - 新增 `corpus_mode` 参数。
  - `build_pair_coexistence_refresh_corpus()` 支持 `spaced_answer` 和 `colon_immediate` 两种模式。
- `scripts/run_model_capability_required_term_pair_coexistence_refresh.py`
  - 新增 `--corpus-mode` CLI 参数。
- `tests/test_model_capability_required_term_pair_coexistence_refresh.py`
  - 新增测试，确认 colon-immediate corpus 包含 `fixed:fixed` / `loss:loss`，且不包含旧的 `fixed: fixed` / `loss: loss`。
- `e/535/解释/model-capability-required-term-pair-coexistence-refresh-colon-immediate/`
  - 保存真实训练、checkpoint、replay 和 HTML 证据。
- `e/535/解释/model-capability-required-term-pair-first-token-preference-colon-immediate/`
  - 保存 first-token logits 诊断证据。

## Corpus 改动

旧模式 `spaced_answer` 保留不变，用于兼容 v533：

```text
fixed: fixed
loss: loss
term=fixed prompt=fixed: answer=fixed
term=loss prompt=loss: answer=loss
```

新模式 `colon_immediate` 去掉冒号后的空格：

```text
fixed:fixed
loss:loss
comparison-baseline|fixed:fixed
factual-val-loss|loss:loss
prompt=fixed:target=fixed
prompt=loss:target=loss
select fixed:fixed
select loss:loss
```

bridge 行也同步改成：

```text
fixed/loss are separate branches.
fixed:fixed;loss:loss
prefix fixed:fixed
prefix loss:loss
```

## 真实训练结果

真实命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_coexistence_refresh.py --out-dir e\535\解释\model-capability-required-term-pair-coexistence-refresh-colon-immediate --seed 535 --corpus-mode colon_immediate --repeat 260 --bridge-repeat 20 --max-iters 1400 --eval-iters 2 --batch-size 16 --block-size 16 --n-layer 1 --n-head 1 --n-embd 64 --learning-rate 0.02 --force --require-pass
```

结果：

```text
decision=required_term_pair_coexistence_refresh_pair_full_observed
default_pair_full_variant_count=1
suppression_pair_full_variant_count=1
pair_full_observed=True
model_quality_claim=targeted_pair_refresh_signal_only
```

replay CSV 显示：

```text
fixed: continuation contains fixed
loss:  continuation contains loss
```

## First-Token 诊断结果

v535 继续跑 v534 的 first-token diagnostic：

```text
decision=pair_first_token_expected_terms_top_ranked
expected_top_count=2
whitespace_prefix_top_count=0
max_expected_rank=1
```

这说明 corpus 改动确实消除了 v534 观察到的 whitespace-prefix drift。`fixed:` 的 expected `f` 和 `loss:` 的 expected `l` 都成为 top-ranked first token。

## 测试覆盖

本版测试重点不是重新覆盖 PyTorch 训练，而是保护 corpus 模式：

- 默认 `spaced_answer` 仍包含旧格式，保证历史行为兼容。
- 新 `colon_immediate` 明确包含 `fixed:fixed` / `loss:loss`。
- 新模式不包含 `fixed: fixed` / `loss: loss`，防止空格偏置回流。
- 原有 fake train/generate 测试继续保护 pair-full 与 no-pair-full 决策。

真实训练和 logits 诊断由 `e/535` 证据覆盖。

## 链路角色

v535 是 v534 诊断后的修复式训练版本。它不是简单加数据，而是根据 first-token 证据改变 corpus 形态，并得到单 seed pair-full 正向结果。下一步不应马上宣称稳定能力，而应跨 seeds 重复这个 colon-immediate refresh。

一句话总结：v535 证明“去掉冒号后空格”可以把 fixed/loss pair 从失败推进到单 seed targeted pair-full。
